from django.core.management.base import BaseCommand
from django.apps import apps
from django.contrib.auth import get_user_model
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

    def handle(self, *args, **options):
        data = {}
        excluded_fields = ["id", "pk"]

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
                        if field.name not in excluded_fields:
                            value = getattr(instance, field.name)

                            # Handle foreign keys
                            if field.is_relation:
                                if value is not None:
                                    if hasattr(value, "uid"):
                                        instance_data[field.name] = str(value.uid)
                                    elif hasattr(value, "username"):
                                        instance_data[field.name] = value.username
                                    elif hasattr(value, "name"):
                                        instance_data[field.name] = value.name
                                    else:
                                        # Skip if we can't find a natural key
                                        continue
                            else:
                                # Serialize the value
                                instance_data[field.name] = self.serialize_value(value)

                    if instance_data:  # Only add if we have data
                        model_data.append(instance_data)

                if model_data:  # Only add if there's data
                    data[f"{app_label}.{model_name}"] = model_data
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully exported {len(model_data)} {model_name} records"
                        )
                    )

            except LookupError:
                self.stdout.write(
                    self.style.WARNING(
                        f"Model {app_label}.{model_name} not found, skipping..."
                    )
                )
                continue

        # Write to file
        output_file = options["output"]
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully exported data to {output_file}")
        )
