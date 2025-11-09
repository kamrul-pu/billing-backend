"""Management command to export data without primary keys for migration."""

from django.core.management.base import BaseCommand
from django.apps import apps
from django.db.models import ForeignKey, OneToOneField
import json
from datetime import datetime, date
import uuid
from decimal import Decimal


class Command(BaseCommand):
    help = "Export specific model data without primary keys for migration"

    def get_models_to_export(self):
        """Define the specific models to export in the correct order based on dependencies"""
        return [
            ("core", "Subscription"),  # First, no dependencies
            ("core", "Organization"),  # Depends on Subscription
            ("core", "User"),  # Depends on Organization
            ("core", "OTP"),  # Depends on User
            ("customer", "Package"),  # Depends on Organization
            ("customer", "Customer"),  # Depends on Organization, Package
            ("customer", "Payment"),  # Depends on Organization, Customer
        ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default=f'data_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
            help="Output file name",
        )

    def serialize_value(self, value):
        """Handle serialization of various data types"""
        if value is None:
            return None
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        elif isinstance(value, uuid.UUID):
            return str(value)
        elif isinstance(value, Decimal):
            return str(value)
        elif hasattr(value, "name") and hasattr(value, "_committed"):
            # Handle FileField and ImageField more safely
            try:
                return value.name if value._committed else None
            except:
                return None
        return value

    def get_relation_identifier(self, related_instance, field):
        """
        Get a unique identifier for a related object.
        Priority: uid > phone (for User) > name > username
        """
        if related_instance is None:
            return None

        # Try uid first (most reliable for models with BaseModelWithUID)
        if hasattr(related_instance, "uid"):
            return str(related_instance.uid)

        # Try phone for User model
        if hasattr(related_instance, "phone"):
            return related_instance.phone

        # Try name for NameDescriptionBaseModel
        if hasattr(related_instance, "name"):
            return related_instance.name

        # Try username as fallback
        if hasattr(related_instance, "username"):
            return related_instance.username

        # Last resort: use primary key (though we're trying to avoid this)
        return str(related_instance.pk)

    def handle(self, *args, **options):
        data = {}
        excluded_fields = ["id", "pk"]
        stats = {}

        # Process only specific models in the defined order
        for app_label, model_name in self.get_models_to_export():
            try:
                model = apps.get_model(app_label, model_name)
                self.stdout.write(f"Exporting {app_label}.{model_name}...")

                # Get all instances
                instances = model.objects.all()
                model_data = []

                for instance in instances:
                    instance_data = {}
                    for field in model._meta.fields:
                        field_name = field.name

                        # Skip excluded fields
                        if field_name in excluded_fields:
                            continue

                        # Skip auto-generated fields that will be recreated
                        if field_name in ["created_at", "updated_at"]:
                            # We can include these, but they'll be set automatically on create
                            # Include them for reference, but they'll be overwritten
                            pass

                        value = getattr(instance, field_name, None)

                        # Handle foreign keys and relationships
                        if field.is_relation:
                            # Skip reverse relations
                            if field.many_to_many or field.one_to_many:
                                continue

                            # Handle ForeignKey and OneToOneField
                            if value is not None:
                                # Get identifier for the related object
                                identifier = self.get_relation_identifier(value, field)
                                if identifier:
                                    instance_data[field_name] = identifier
                                else:
                                    # Skip if we can't find a suitable identifier
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f"  Warning: Could not get identifier for {field_name} on {model_name} (pk: {instance.pk})"
                                        )
                                    )
                            else:
                                # NULL foreign key
                                instance_data[field_name] = None
                        else:
                            # Non-relational field - serialize the value
                            instance_data[field_name] = self.serialize_value(value)

                    # Only add if we have data
                    if instance_data:
                        model_data.append(instance_data)

                if model_data:
                    data[f"{app_label}.{model_name}"] = model_data
                    stats[model_name] = len(model_data)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Successfully exported {len(model_data)} {model_name} records"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"  No data found for {model_name}")
                    )

            except LookupError:
                self.stdout.write(
                    self.style.WARNING(
                        f"Model {app_label}.{model_name} not found, skipping..."
                    )
                )
                continue
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error exporting {app_label}.{model_name}: {str(e)}"
                    )
                )
                continue

        # Write to file
        output_file = options["output"]
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.stdout.write(
                self.style.SUCCESS(f"\nSuccessfully exported data to {output_file}")
            )
            self.stdout.write("\nExport Summary:")
            for model_name, count in stats.items():
                self.stdout.write(f"  {model_name}: {count} records")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error writing to file {output_file}: {str(e)}")
            )
