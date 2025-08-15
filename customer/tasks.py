from celery import shared_task
from django.utils import timezone

from customer.models import Customer, Payment
from customer.utils import toggle_ppp_user


@shared_task
def add(x=10, y=20):
    print(f"{x} + {y} = {x+y}")
    return x + y


@shared_task
def generate_customer_bills():
    month = timezone.now().strftime("%B").upper()
    # Step 1: Get all active customers
    active_customers = Customer.objects.filter(
        is_active=True, is_free=False
    ).select_related("package")

    # Step 2: Get customer IDs with existing payments for current month
    existing_payments = Payment.objects.filter(billing_month=month)
    paid_customer_ids = set(existing_payments.values_list("customer_id", flat=True))

    # Step 3: Filter customers who haven't been billed
    customers_to_bill = [c for c in active_customers if c.id not in paid_customer_ids]

    # Step 4: Create payment records in bulk
    payments_to_create = []
    for customer in customers_to_bill:
        bill_amount = customer.package.price if customer.package else 0.0
        payments_to_create.append(
            Payment(
                customer=customer,
                bill_amount=bill_amount,
                amount=0.0,
                billing_month=month,
                payment_method="OTHER",
                paid=False,
                note=f"Auto-generated bill for {month}",
            )
        )

    # Bulk create payments
    Payment.objects.bulk_create(payments_to_create)


@shared_task
def deactivate_due_payment_customers():
    month = timezone.now().strftime("%B").upper()
    payments = (
        Payment()
        .get_all_actives()
        .filter(billing_month=month, paid=False)
        .select_related("customer")
    )
    customers_to_update = []
    for payment in payments:
        customer = payment.customer
        if customer.is_active and not customer.is_free:
        # Deactive the customer
            success, msg = toggle_ppp_user(username=customer.username, disable=True)
            if success:
                customer.is_active = False
                customers_to_update.append(customer)
            else:
                print(f"Error Message: ", msg)

    if customers_to_update:
        Customer.objects.bulk_update(customers_to_update)
        print("Customer updated successfully!")
