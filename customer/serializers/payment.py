import uuid
from decimal import Decimal
from datetime import timedelta
from django.db import transaction
import logging
from django.utils import timezone
from rest_framework import serializers

from common.helpers import SMS
from customer.models import Payment, Customer
from core.choices import BillingCycle
from core.serializers.user import UserLiteSerializer
from customer.serializers.customer import CustomerBase
from customer.utils import month_name_to_bangla

logger = logging.getLogger(__name__)


class PaymentBase(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "uid",
            "customer",
            "entry_by",
            "bill_amount",
            "amount",
            "billing_month",
            "payment_method",
            "paid",
            "transaction_id",
            "payment_date",
            "note",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class PaymentListSerializer(PaymentBase):
    customer = CustomerBase(read_only=True)
    customer_id = serializers.IntegerField(write_only=True, required=True)
    entry_by = UserLiteSerializer(read_only=True)

    class Meta(PaymentBase.Meta):
        fields = PaymentBase.Meta.fields + (
            "customer",
            "customer_id",
            "entry_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = PaymentBase.Meta.read_only_fields + (
            "customer",
            "entry_by",
            "created_at",
            "updated_at",
        )

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        organization = getattr(request.user, "organization", None)
        transaction_id = uuid.uuid4()
        payment_date = validated_data.get("payment_date", timezone.now())
        customer_id = validated_data["customer_id"]

        try:
            customer = Customer.objects.select_related("package").get(id=customer_id)
        except Customer.DoesNotExist:
            raise serializers.ValidationError({"message": "Customer does not exist."})

        if customer.is_free:
            raise serializers.ValidationError(
                {"message": "Cannot create payment for free customers."}
            )

        if not organization:
            raise serializers.ValidationError(
                {"message": "This user doesn't belong to any organization."}
            )

        billing_cycle = organization.billing_cycle
        bill_amount = customer.package.price if customer.package else Decimal("0.00")
        amount = validated_data.get("amount", Decimal("0.00"))
        is_fully_paid = validated_data.get("paid", False) or amount >= bill_amount

        # === Handle Day-Based Subscription (Rolling) ===
        if billing_cycle == BillingCycle.DAYS30:
            last_end = customer.subscription_end_date
            today = timezone.now().date()

            # Determine how many 30-day periods were paid for
            # Example: if package.price = 300 and paid 900 → 900/300 = 3 → 3 * 30 days
            paid_months = int(amount // bill_amount) if bill_amount > 0 else 1
            extend_days = paid_months * 30

            # Extend from either current end or today
            if last_end and last_end > today:
                new_end = last_end + timedelta(days=extend_days)
            else:
                new_end = today + timedelta(days=extend_days)

            customer.subscription_end_date = new_end
            customer.save(update_fields=["subscription_end_date"])

            # Create a payment record (no billing month dependency)
            payment = Payment.objects.create(
                organization_id=organization.id,
                customer_id=customer.id,
                bill_amount=bill_amount,
                amount=amount,
                paid=True,  # day-based payments are immediate
                billing_month=validated_data.get("billing_month", ""),  # not applicable
                payment_method=validated_data.get("payment_method", "CASH"),
                payment_date=payment_date,
                transaction_id=str(transaction_id),
                entry_by_id=request.user.id,
                updated_by_id=request.user.id,
                note=f"Subscription extended by {extend_days} days (until {new_end}) by {request.user.first_name}",
            )

            print(f"Subscription extended by {extend_days} days, new end: {new_end}")
            message = f"বিল {amount} BDT জমা হয়েছে-{organization.name or 'M_Online'}"

        # === Handle Monthly Billing ===
        elif billing_cycle == BillingCycle.MONTHLY:
            # Check if there's already a payment for the billing month
            try:
                payment = Payment.objects.get(
                    customer=customer,
                    billing_month=validated_data.get("billing_month", ""),
                )
            except Payment.DoesNotExist:
                payment = None
            except Payment.MultipleObjectsReturned:
                logger.error(
                    f"Multiple payments found for customer {customer.id} in {validated_data['billing_month']}"
                )
                raise serializers.ValidationError(
                    {"message": "Multiple payments detected. Contact admin."}
                )

            if payment and payment.paid:
                raise serializers.ValidationError(
                    {"message": "Payment for this month has already been made."}
                )

            if payment:
                # Update existing unpaid payment
                payment.payment_date = payment_date
                payment.amount = amount
                payment.paid = is_fully_paid
                payment.transaction_id = str(transaction_id)
                payment.entry_by_id = request.user.id
                payment.updated_by_id = request.user.id
                payment.organization_id = organization.id
                payment.note = f"Payment updated by {request.user.first_name}"
                payment.save(
                    update_fields=[
                        "payment_date",
                        "amount",
                        "paid",
                        "transaction_id",
                        "entry_by",
                        "updated_by",
                        "note",
                    ]
                )
                print("Monthly payment updated successfully.")
            else:
                # Create new payment
                payment = Payment.objects.create(
                    organization_id=organization.id,
                    customer_id=customer.id,
                    bill_amount=bill_amount,
                    amount=amount,
                    paid=is_fully_paid,
                    billing_month=validated_data["billing_month"],
                    payment_method=validated_data["payment_method"],
                    payment_date=payment_date,
                    transaction_id=str(transaction_id),
                    entry_by_id=request.user.id,
                    updated_by_id=request.user.id,
                    note=f"Payment received by {request.user.first_name}",
                )
                print("Monthly payment created successfully.")

            message = (
                f"আপনার {month_name_to_bangla.get(validated_data.get('billing_month', ''), '')} এর বিল {amount} BDT পরিশোধ হয়েছে-"
                f"{organization.name or 'M_Online'}"
            )

        else:
            raise serializers.ValidationError(
                {"message": f"Unsupported billing cycle: {billing_cycle}"}
            )

        # Activate customer if fully paid and currently inactive
        if is_fully_paid and not customer.is_active:
            customer.is_active = True
            customer.save(update_fields=["is_active"])
            print("Customer activated due to successful payment.")

        if (
            organization
            and organization.sms_feature
            and is_fully_paid
            and customer.phone
        ):
            SMS.send_single_sms(to=customer.phone, message=message)
        return payment


class PaymentDetailSerializer(PaymentBase):
    customer = CustomerBase(read_only=True)
    entry_by = UserLiteSerializer(read_only=True)

    class Meta(PaymentBase.Meta):
        fields = PaymentBase.Meta.fields + ("customer", "entry_by")
        read_only_fields = PaymentBase.Meta.read_only_fields + (
            "customer",
            "entry_by",
        )

    def update(self, instance, validated_data):
        bill_amount = instance.bill_amount
        amount = validated_data.get("amount", Decimal("0.00"))
        is_fully_paid = validated_data.get("paid", False) or amount >= bill_amount
        validated_data["paid"] = is_fully_paid
        if not instance.entry_by:
            validated_data["entry_by_id"] = self.context["request"].user.id
        validated_data["updated_by_id"] = self.context["request"].user.id
        if validated_data.get("paid") and not instance.customer.is_active:
            instance.customer.is_active = True
            instance.customer.save(update_fields=["is_active"])
        if (
            instance.organization
            and instance.organization.sms_feature
            and is_fully_paid
            and instance.customer.phone
        ):
            SMS.send_single_sms(
                to=instance.customer.phone,
                message=f"আপনার {month_name_to_bangla.get(instance.billing_month, '')} এর বিল {amount} BDT পরিশোধ হয়েছে-{instance.organization.name or 'M_Online'}",
            )

        return super().update(instance, validated_data)
