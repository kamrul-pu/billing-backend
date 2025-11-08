from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
from django.utils.dateparse import parse_datetime, parse_date
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
from django.utils.dateparse import parse_datetime, parse_date
import json
import uuid
from decimal import Decimal


class Command(BaseCommand):
    help = "Import data from exported JSON file (two-phase import: create then link relations)"

    def add_arguments(self, parser):
        parser.add_argument("input_file", help="Input JSON file path")
        parser.add_argument(
            "--skip-errors",
            action="store_true",
            help="Continue importing even if some records fail",
        )

    def deserialize_value(self, value, field):
        """Convert serialized values back to their proper types"""
        if value is None:
            return None
        # If value isn't a string for serialized types, coerce to str first
        try:
            if field.get_internal_type() == "DateTimeField":
                return parse_datetime(str(value)) if value is not None else None
            if field.get_internal_type() == "DateField":
                return parse_date(str(value)) if value is not None else None
            if field.get_internal_type() == "DecimalField":
                return Decimal(str(value))
            if field.get_internal_type() == "UUIDField":
                try:
                    return uuid.UUID(str(value))
                except Exception:
                    return None
        except Exception:
            return value
        return value

    def get_import_order(self):
        """Define the order in which models should be imported"""
        return [
            ("core", "Subscription"),
            ("core", "Organization"),
            ("core", "User"),
            ("customer", "Package"),
            ("customer", "Customer"),
            ("customer", "Payment"),
            ("core", "OTP"),
        ]

    def handle(self, *args, **options):
        input_file = options["input_file"]
        skip_errors = options["skip_errors"]

        with open(input_file, "r") as f:
            data = json.load(f)

        # Mapping: model_key -> { old_uid_str: new_instance_uid_str }
        uid_mappings = {}

        # Phase 1: create instances without resolving relations
        try:
            with transaction.atomic():
                for app_label, model_name in self.get_import_order():
                    original_key = f"{app_label}.{model_name}"
                    norm_key = f"{app_label}.{model_name.lower()}"

                    # try to find data using either casing
                    instances = data.get(original_key) or data.get(norm_key)
                    if not instances:
                        self.stdout.write(
                            self.style.WARNING(
                                f"No data for {original_key}/{norm_key}, skipping"
                            )
                        )
                        continue

                    model = apps.get_model(app_label, model_name)
                    model_key = norm_key
                    uid_mappings[model_key] = {}

                    self.stdout.write(
                        f"Creating {len(instances)} {original_key} (phase 1)..."
                    )

                    for obj in instances:
                        original_uid = obj.get("uid")
                        # Build create_kwargs using only non-relational fields
                        create_kwargs = {}
                        for field in model._meta.fields:
                            fname = field.name
                            # Skip uid (auto), status (default), and relational fields for phase1
                            if fname == "uid" or fname == "status":
                                continue
                            if field.is_relation:
                                # Try to resolve relations in phase1 only if the related
                                # model was already created earlier in the import order.
                                related_model = field.related_model
                                related_norm_key = f"{related_model._meta.app_label}.{related_model._meta.model_name.lower()}"
                                related_value = obj.get(fname)

                                resolved = None
                                if related_value:
                                    # Try to find a mapped new UID for the related object
                                    mapped = uid_mappings.get(related_norm_key, {}).get(
                                        str(related_value)
                                    )
                                    if mapped:
                                        try:
                                            resolved = related_model.objects.get(
                                                uid=mapped
                                            )
                                        except Exception:
                                            resolved = None
                                    else:
                                        # Try to lookup by the old UID directly (if it matches)
                                        try:
                                            resolved = related_model.objects.get(
                                                uid=str(related_value)
                                            )
                                        except Exception:
                                            resolved = None

                                if resolved is not None:
                                    create_kwargs[fname] = resolved
                                # otherwise skip setting the FK in phase1 (will be linked in phase2)
                                continue

                            if fname in obj:
                                create_kwargs[fname] = self.deserialize_value(
                                    obj[fname], field
                                )

                        try:
                            instance = model.objects.create(**create_kwargs)
                            if original_uid:
                                uid_mappings[model_key][str(original_uid)] = str(
                                    instance.uid
                                )
                        except Exception as e:
                            if skip_errors:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"Failed to create {model_key} object: {e}"
                                    )
                                )
                                continue
                            raise

                    self.stdout.write(
                        self.style.SUCCESS(f"Created phase1 for {model_key}")
                    )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during phase1 import: {e}"))
            return

        # Phase 2: resolve relations and update instances
        try:
            with transaction.atomic():
                for app_label, model_name in self.get_import_order():
                    original_key = f"{app_label}.{model_name}"
                    norm_key = f"{app_label}.{model_name.lower()}"
                    instances = data.get(original_key) or data.get(norm_key)
                    if not instances:
                        continue

                    model = apps.get_model(app_label, model_name)
                    model_key = norm_key

                    self.stdout.write(
                        f"Linking relations for {original_key} (phase 2)..."
                    )

                    for obj in instances:
                        original_uid = obj.get("uid")
                        if not original_uid:
                            continue
                        new_uid = uid_mappings.get(model_key, {}).get(str(original_uid))
                        if not new_uid:
                            # nothing to update
                            continue

                        instance = model.objects.get(uid=new_uid)
                        updated = False

                        # Resolve fields
                        for field in model._meta.fields:
                            fname = field.name
                            if fname not in obj:
                                continue
                            if not field.is_relation:
                                # already set in phase1
                                continue

                            related_value = obj.get(fname)
                            # clear relation if value falsy
                            if not related_value:
                                setattr(instance, fname, None)
                                updated = True
                                continue

                            related_model = field.related_model
                            # normalize related key to lowercase model name
                            related_key = f"{related_model._meta.app_label}.{related_model._meta.model_name.lower()}"

                            # If related model has UID mapping, use it
                            related_old_uid = None
                            try:
                                related_old_uid = str(related_value)
                            except Exception:
                                related_old_uid = None

                            related_new_uid = None
                            if related_old_uid:
                                related_new_uid = uid_mappings.get(related_key, {}).get(
                                    related_old_uid
                                )

                            related_obj = None
                            if related_new_uid:
                                try:
                                    related_obj = related_model.objects.get(
                                        uid=related_new_uid
                                    )
                                except Exception:
                                    related_obj = None

                            # Try using old UID if mapping not found
                            if not related_obj and related_old_uid:
                                try:
                                    related_obj = related_model.objects.get(
                                        uid=related_old_uid
                                    )
                                except Exception:
                                    related_obj = None

                            # Fallbacks: username or name
                            if not related_obj:
                                if hasattr(related_model, "username"):
                                    try:
                                        related_obj = related_model.objects.get(
                                            username=related_value
                                        )
                                    except Exception:
                                        related_obj = None
                                elif hasattr(related_model, "name"):
                                    try:
                                        related_obj = related_model.objects.get(
                                            name=related_value
                                        )
                                    except Exception:
                                        related_obj = None

                            if related_obj is None:
                                # can't resolve relation
                                if skip_errors:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f"Could not resolve {related_key} for field {fname} on {model_key} ({related_value})"
                                        )
                                    )
                                    continue
                                else:
                                    raise Exception(
                                        f"Could not resolve related object {related_key} for value {related_value}"
                                    )

                            # assign and save
                            setattr(instance, fname, related_obj)
                            updated = True

                        if updated:
                            instance.save()

                    self.stdout.write(
                        self.style.SUCCESS(f"Linked relations for {model_key}")
                    )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during phase2 import: {e}"))
            return

        self.stdout.write(self.style.SUCCESS("Import completed (phase1 + phase2)"))
