"""Management command to encrypt existing plain text router credentials."""

from django.core.management.base import BaseCommand
from core.models import Organization


class Command(BaseCommand):
    help = "Encrypt existing plain text router credentials in the database"

    def handle(self, *args, **options):
        organizations = Organization.objects.all()
        count = 0

        for org in organizations:
            # Re-saving will trigger the encryption via the EncryptedField
            org.save(update_fields=['router_ip', 'router_username', 'router_password', 'router_secret'])
            count += 1
            self.stdout.write(
                self.style.SUCCESS(f"Encrypted credentials for: {org.name}")
            )

        self.stdout.write(
            self.style.SUCCESS(f"\nSuccessfully encrypted credentials for {count} organizations")
        )
