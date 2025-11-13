from celery import shared_task
from django.utils import timezone

from core.choices import BillingCycle
from core.models import Organization
from common.helpers import SMS
from customer.models import Customer, Payment
from customer.utils import toggle_ppp_user, month_name_to_bangla
from customer.helpers import Mikrotik


@shared_task
def add(x=10, y=20):
    print(f"{x} + {y} = {x+y}")
    return x + y


@shared_task
def generate_customer_bills(org_id: int = 1):
    organization = Organization.objects.filter(id=org_id).first()
    if not organization:
        print(f"No organization found with ID {org_id}.")
        return
    if organization.billing_cycle != BillingCycle.MONTHLY:
        print(
            f"Organization ID {org_id} does not have a monthly billing cycle. Skipping bill generation."
        )
        return

    organization_name = organization.name or "M_Online"
    month = timezone.now().strftime("%B").upper()
    year = timezone.now().year

    # Step 1: Get all active customers
    active_customers = Customer.objects.filter(
        is_active=True,
        is_free=False,
        organization_id=org_id,
    ).select_related("package")

    organization_name = organization.name or "M_Online"

    # Step 2: Get customer IDs with existing payments for current month and year
    existing_payments = Payment.objects.filter(
        billing_month=month, billing_year=year, organization_id=org_id
    )
    paid_customer_ids = set(existing_payments.values_list("customer_id", flat=True))

    # Step 3: Filter customers who haven't been billed
    customers_to_bill = [c for c in active_customers if c.id not in paid_customer_ids]
    messages = []
    # Step 4: Create payment records in bulk
    payments_to_create = []
    for customer in customers_to_bill:
        bill_amount = customer.package.price if customer.package else 0.0
        payments_to_create.append(
            Payment(
                organization_id=org_id,
                customer=customer,
                bill_amount=bill_amount,
                amount=0.0,
                billing_month=month,
                billing_year=year,
                payment_method="OTHER",
                paid=False,
                note=f"Auto-generated bill for {month} {year}",
            )
        )
        messages.append(
            {
                "to": customer.phone,
                "message": f"{month_name_to_bangla.get(month, '')} মাসের বিল {bill_amount}TK পরিশোধ করুন - {organization_name}",
            }
        )
    # Bulk create payments
    if payments_to_create:
        Payment.objects.bulk_create(payments_to_create)
        sms_send: bool = False
        if messages and organization.sms_feature:
            sms_send = SMS.send_bulk_sms(messages)
            print(f"SMS sent: {sms_send}")
        if sms_send:
            print("SMS submission successfull!")
        else:
            print("Failed to submit messages")
    else:
        print("No payment data to create")


@shared_task
def deactivate_due_payment_customers(org_id: int = 1):
    month = timezone.now().strftime("%B").upper()
    year = timezone.now().year
    organization = Organization.objects.filter(id=org_id).first()
    if not organization:
        print("No organization found with ID 1.")
        return
    if organization.billing_cycle != BillingCycle.MONTHLY:
        print(
            f"Organization ID {org_id} does not have a monthly billing cycle. Skipping deactivation."
        )
        return

    payments = (
        Payment()
        .get_all_actives()
        .filter(billing_month=month, billing_year=year, paid=False, organization_id=org_id)
        .select_related("customer")
    )
    organization_name = organization.name or "M_Online"
    messages = []
    customers_to_update = []

    success, user_sessions = Mikrotik.get_user_sessions(organization)
    user_to_session_id = {}
    for session in user_sessions:
        user_to_session_id[session.get("name", "")] = session.get(".id", "")

    for payment in payments:
        customer = payment.customer
        if customer.is_active and not customer.is_free:
            print(f"Deactivating customer: {customer.username} for unpaid bill.")
            # Deactive the customer
            success, msg = Mikrotik.toggle_ppp_user(
                username=customer.username,
                disable=True,
                organization=organization,
                session_id=user_to_session_id.get(customer.username, ""),
            )
            if success:
                customer.is_active = False
                customers_to_update.append(customer)
                messages.append(
                    {
                        "to": customer.phone,
                        "message": f"{month_name_to_bangla.get(month, '')} বিল বকেয়া, সংযোগ বন্ধ। চালু করতে বিল পরিশোধ করুন-{organization_name}",
                    }
                )
            else:
                print(f"Error Message: ", msg)

    if customers_to_update:
        Customer.objects.bulk_update(customers_to_update, fields=["is_active"])
        print("Customer updated successfully!")
        sms_send: bool = False
        if messages and organization.sms_feature:
            sms_send = SMS.send_bulk_sms(messages)

        if sms_send:
            print("SMS submission successfull!")
        else:
            print("Failed to submit messages")


@shared_task
def generate_organizations_bills():
    organizations = Organization().get_all_actives()
    for org in organizations:
        print(f"Generating bills for organization: {org.name} (ID: {org.id})")
        generate_customer_bills(org.id)


@shared_task
def deactivate_organizations_due_payment_customers():
    organizations = Organization().get_all_actives()
    for org in organizations:
        print(
            f"Deactivating due payment customers for organization: {org.name} (ID: {org.id})"
        )
        deactivate_due_payment_customers(org.id)


@shared_task
def deactivate_expired_subscription_customers(organization: Organization):
    if organization.billing_cycle == BillingCycle.MONTHLY:
        print(
            f"Organization ID {organization.id} has a monthly billing cycle. Skipping expired subscription deactivation."
        )
        return

    today = timezone.now().date()
    messages = []
    customers_to_update = []
    customers = Customer.objects.filter(
        is_active=True,
        is_free=False,
        subscription_end_date__isnull=False,
        subscription_end_date__lt=today,
        organization_id=organization.id,
    )
    for customer in customers:
        if not customer.is_active or customer.is_free:
            continue
        # print(
        #     f"Deactivating customer: {customer.username} due to expired subscription."
        # )
        success, msg = Mikrotik.toggle_ppp_user(
            username=customer.username,
            disable=True,
            organization=organization,
        )
        if success:
            customer.is_active = False
            customers_to_update.append(customer)
            messages.append(
                {
                    "to": customer.phone,
                    "message": f"বিল বকেয়া, সংযোগ বন্ধ। চালু করতে বিল পরিশোধ করুন-{organization.name}",
                }
            )
        else:
            print(f"Error deactivating {customer.username}: ", msg)
    if customers_to_update:
        Customer.objects.bulk_update(customers_to_update, fields=["is_active"])
        print("Expired subscription customers updated successfully!")
        sms_send: bool = False
        if messages and organization.sms_feature:
            sms_send = SMS.send_bulk_sms(messages)

        if sms_send:
            print("SMS submission successfull!")
        else:
            print("Failed to submit messages")


@shared_task
def deactivate_all_organizations_expired_subscription_customers():
    organizations = (
        Organization().get_all_actives().filter(billing_cycle=BillingCycle.DAYS30)
    )
    for org in organizations:
        print(
            f"Deactivating expired subscription customers for organization: {org.name} (ID: {org.id})"
        )
        deactivate_expired_subscription_customers(org)
