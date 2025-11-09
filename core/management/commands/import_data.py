"""Management command to import data from exported JSON file."""

from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
from django.utils.dateparse import parse_datetime, parse_date
from django.db.utils import IntegrityError
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
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform a dry run without actually importing data",
        )

    def deserialize_value(self, value, field):
        """Convert serialized values back to their proper types"""
        if value is None:
            return None

        try:
            field_type = field.get_internal_type()
            if field_type == "DateTimeField":
                return parse_datetime(str(value)) if value else None
            elif field_type == "DateField":
                return parse_date(str(value)) if value else None
            elif field_type == "DecimalField":
                return Decimal(str(value)) if value else None
            elif field_type == "UUIDField":
                try:
                    return uuid.UUID(str(value))
                except (ValueError, AttributeError):
                    return None
            elif field_type == "BooleanField":
                return bool(value)
            elif field_type == "IntegerField":
                return int(value) if value is not None else None
        except (ValueError, TypeError, AttributeError) as e:
            self.stdout.write(
                self.style.WARNING(
                    f"  Warning: Could not deserialize {value} for {field.name}: {e}"
                )
            )
            return value

        return value

    def get_import_order(self):
        """Define the order in which models should be imported"""
        return [
            ("core", "Subscription"),  # First, no dependencies
            ("core", "Organization"),  # Depends on Subscription
            ("core", "User"),  # Depends on Organization
            ("customer", "Package"),  # Depends on Organization
            ("customer", "Customer"),  # Depends on Organization, Package
            ("customer", "Payment"),  # Depends on Organization, Customer
            ("core", "OTP"),  # Depends on User (import last)
        ]

    def resolve_related_object(self, related_model, identifier, uid_mappings, model_key):
        """
        Resolve a related object using identifier (UID, phone, name, etc.)
        Returns the related object or None if not found.
        """
        if identifier is None:
            return None

        identifier_str = str(identifier)

        # Try to find using UID mapping first
        related_key = f"{related_model._meta.app_label}.{related_model._meta.model_name.lower()}"
        mapped_uid = uid_mappings.get(related_key, {}).get(identifier_str)
        if mapped_uid:
            try:
                return related_model.objects.get(uid=mapped_uid)
            except related_model.DoesNotExist:
                pass

        # Try direct UID lookup
        try:
            return related_model.objects.get(uid=identifier_str)
        except (related_model.DoesNotExist, ValueError):
            pass

        # Try phone for User model
        if hasattr(related_model, "phone") and hasattr(related_model, "_meta"):
            if related_model._meta.model_name.lower() == "user":
                try:
                    return related_model.objects.get(phone=identifier_str)
                except related_model.DoesNotExist:
                    pass

        # Try name for NameDescriptionBaseModel
        if hasattr(related_model, "name"):
            try:
                return related_model.objects.get(name=identifier_str)
            except related_model.DoesNotExist:
                pass
            except related_model.MultipleObjectsReturned:
                # If multiple objects with same name, this might be an issue
                # Try to get the first one (not ideal, but better than failing)
                try:
                    return related_model.objects.filter(name=identifier_str).first()
                except Exception:
                    pass

        # Try username as fallback
        if hasattr(related_model, "username"):
            try:
                return related_model.objects.get(username=identifier_str)
            except related_model.DoesNotExist:
                pass

        return None

    def handle(self, *args, **options):
        input_file = options["input_file"]
        skip_errors = options["skip_errors"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No data will be imported"))

        try:
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f"Error: File {input_file} not found")
            )
            return
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f"Error: Invalid JSON in {input_file}: {e}")
            )
            return

        # Mapping: model_key -> { old_identifier: new_instance }
        uid_mappings = {}
        stats = {"created": {}, "errors": {}}

        # Phase 1: Create instances without resolving all relations
        try:
            if not dry_run:
                with transaction.atomic():
                    self._phase1_import(data, uid_mappings, stats, skip_errors)
            else:
                self._phase1_import(data, uid_mappings, stats, skip_errors, dry_run=True)

            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS("\n=== DRY RUN COMPLETE ===")
                )
                return

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error during phase 1 import: {e}")
            )
            if not skip_errors:
                import traceback
                self.stdout.write(traceback.format_exc())
            return

        # Phase 2: Update relations that couldn't be resolved in phase 1
        try:
            with transaction.atomic():
                self._phase2_import(data, uid_mappings, stats, skip_errors)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error during phase 2 import: {e}")
            )
            if not skip_errors:
                import traceback
                self.stdout.write(traceback.format_exc())
            return

        # Print summary
        self.stdout.write(self.style.SUCCESS("\n=== IMPORT SUMMARY ==="))
        for model_name, count in stats["created"].items():
            self.stdout.write(
                self.style.SUCCESS(f"  {model_name}: {count} records created")
            )
        if stats["errors"]:
            self.stdout.write(self.style.WARNING("\nErrors:"))
            for model_name, count in stats["errors"].items():
                self.stdout.write(
                    self.style.WARNING(f"  {model_name}: {count} errors")
                )

        self.stdout.write(
            self.style.SUCCESS("\nImport completed successfully!")
        )

    def _phase1_import(self, data, uid_mappings, stats, skip_errors, dry_run=False):
        """Phase 1: Create instances, resolving relations that are already imported"""
        for app_label, model_name in self.get_import_order():
            original_key = f"{app_label}.{model_name}"
            model_key = f"{app_label}.{model_name.lower()}"

            # Try both key formats
            instances = data.get(original_key) or data.get(model_key)
            if not instances:
                self.stdout.write(
                    self.style.WARNING(
                        f"No data for {original_key}, skipping..."
                    )
                )
                continue

            try:
                model = apps.get_model(app_label, model_name)
            except LookupError:
                self.stdout.write(
                    self.style.WARNING(
                        f"Model {app_label}.{model_name} not found, skipping..."
                    )
                )
                continue

            uid_mappings[model_key] = {}
            stats["created"][model_name] = 0
            stats["errors"][model_name] = 0

            self.stdout.write(
                f"\nCreating {len(instances)} {original_key} records (phase 1)..."
            )

            for idx, obj in enumerate(instances, 1):
                original_uid = obj.get("uid")
                create_kwargs = {}

                # Build create_kwargs
                for field in model._meta.fields:
                    field_name = field.name

                    # Skip id, pk, uid (will be auto-generated)
                    if field_name in ["id", "pk", "uid"]:
                        continue

                    # Skip auto fields that will be set automatically
                    if field_name in ["created_at", "updated_at"]:
                        # These will be set automatically
                        continue

                    # Handle status field - use default if not provided
                    if field_name == "status" and field_name not in obj:
                        continue  # Will use model default

                    # Skip entry_by and updated_by - set to None for imported data
                    if field_name in ["entry_by", "updated_by"]:
                        create_kwargs[field_name] = None
                        continue

                    # Get value from exported data
                    if field_name not in obj:
                        continue

                    value = obj[field_name]

                    # Handle relationships
                    if field.is_relation:
                        # Skip reverse relations
                        if field.many_to_many or field.one_to_many:
                            continue

                        # Try to resolve the relationship
                        if value is not None:
                            related_model = field.related_model
                            resolved = self.resolve_related_object(
                                related_model, value, uid_mappings, model_key
                            )
                            if resolved:
                                create_kwargs[field_name] = resolved
                            # If not resolved, we'll handle it in phase 2
                            # Don't set it now to avoid errors
                        else:
                            create_kwargs[field_name] = None
                    else:
                        # Non-relational field
                        create_kwargs[field_name] = self.deserialize_value(
                            value, field
                        )

                # Create the instance
                try:
                    if dry_run:
                        self.stdout.write(
                            f"  [DRY RUN] Would create {model_name} with uid: {original_uid}"
                        )
                        # Create a mock mapping for dry run
                        if original_uid:
                            uid_mappings[model_key][str(original_uid)] = f"dry_run_{idx}"
                    else:
                        instance = model.objects.create(**create_kwargs)
                        if original_uid:
                            uid_mappings[model_key][str(original_uid)] = str(
                                instance.uid
                            )
                        stats["created"][model_name] += 1

                        if (idx % 100 == 0) or (idx == len(instances)):
                            self.stdout.write(
                                f"  Progress: {idx}/{len(instances)} {model_name} records created"
                            )

                except IntegrityError as e:
                    error_msg = str(e)
                    stats["errors"][model_name] += 1
                    if skip_errors:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Skipped {model_name} record (uid: {original_uid}): {error_msg}"
                            )
                        )
                        continue
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"  Error creating {model_name} record (uid: {original_uid}): {error_msg}"
                            )
                        )
                        raise

                except Exception as e:
                    error_msg = str(e)
                    stats["errors"][model_name] += 1
                    if skip_errors:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Skipped {model_name} record (uid: {original_uid}): {error_msg}"
                            )
                        )
                        continue
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"  Error creating {model_name} record (uid: {original_uid}): {error_msg}"
                            )
                        )
                        raise

            self.stdout.write(
                self.style.SUCCESS(
                    f"Phase 1 complete for {model_name}: {stats['created'][model_name]} created, {stats['errors'][model_name]} errors"
                )
            )

    def _phase2_import(self, data, uid_mappings, stats, skip_errors):
        """Phase 2: Update instances with relations that couldn't be resolved in phase 1"""
        self.stdout.write("\n=== Phase 2: Resolving remaining relations ===")

        for app_label, model_name in self.get_import_order():
            original_key = f"{app_label}.{model_name}"
            model_key = f"{app_label}.{model_name.lower()}"

            instances = data.get(original_key) or data.get(model_key)
            if not instances:
                continue

            try:
                model = apps.get_model(app_label, model_name)
            except LookupError:
                continue

            updated_count = 0

            for obj in instances:
                original_uid = obj.get("uid")
                if not original_uid:
                    continue

                # Find the created instance
                new_uid = uid_mappings.get(model_key, {}).get(str(original_uid))
                if not new_uid:
                    continue

                try:
                    instance = model.objects.get(uid=new_uid)
                except model.DoesNotExist:
                    continue

                # Update relations that weren't set in phase 1
                updated = False
                for field in model._meta.fields:
                    field_name = field.name

                    # Only process relational fields
                    if not field.is_relation:
                        continue
                    if field.many_to_many or field.one_to_many:
                        continue

                    # Skip if field is entry_by or updated_by
                    if field_name in ["entry_by", "updated_by"]:
                        continue

                    # Check if value exists in export but wasn't set
                    if field_name not in obj:
                        continue

                    value = obj[field_name]
                    current_value = getattr(instance, field_name, None)

                    # If already set in phase 1, skip
                    if current_value is not None:
                        continue

                    # Try to resolve now
                    if value is not None:
                        related_model = field.related_model
                        resolved = self.resolve_related_object(
                            related_model, value, uid_mappings, model_key
                        )
                        if resolved:
                            setattr(instance, field_name, resolved)
                            updated = True
                        elif not skip_errors:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  Could not resolve {field_name} for {model_name} (uid: {new_uid}), value: {value}"
                                )
                            )

                if updated:
                    instance.save()
                    updated_count += 1

            if updated_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Updated {updated_count} {model_name} records with relations"
                    )
                )
