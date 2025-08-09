from django.core.management.base import BaseCommand
from customer.models import Customer
from django.db import transaction


class Command(BaseCommand):
    help = "Fix payment bill amount based on customer package price"

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            customers = (
                Customer.objects.filter()
                .select_related("package")
                .prefetch_related("payments")
            )
            if not customers:
                self.stdout.write(self.style.WARNING("No customers found."))
                return
            for customer in customers:
                customer.payments.update(bill_amount=customer.package.price)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updated bill amount for customer {customer.name} ({customer.phone}) to {customer.package.price}"
                    )
                )
        self.stdout.write(self.style.SUCCESS("All payments updated successfully."))
