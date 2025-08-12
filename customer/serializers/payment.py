import uuid
from decimal import Decimal
from django.db import transaction
import logging
from django.utils import timezone
from rest_framework import serializers
from customer.models import Payment, Customer
from core.serializers.user import UserLiteSerializer
from customer.serializers.customer import CustomerBase

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

    def create(self, validated_data):
        request = self.context["request"]
        transaction_id = uuid.uuid4()
        payment_date = validated_data.get("payment_date", timezone.now())
        customer_id = validated_data["customer_id"]

        try:
            customer = Customer.objects.select_related("package").get(id=customer_id)
        except Customer.DoesNotExist:
            raise serializers.ValidationError(
                {"customer_id": "Customer does not exist."}
            )

        if customer.is_free:
            raise serializers.ValidationError(
                {"customer_id": "Cannot create payment for free customers."}
            )

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
                {"billing_month": "Multiple payments detected. Contact admin."}
            )

        if payment and payment.paid:
            raise serializers.ValidationError(
                {"billing_month": "Payment for this month has already been made."}
            )

        bill_amount = customer.package.price if customer.package else Decimal("0.00")
        amount = validated_data.get("amount", Decimal("0.00"))

        is_fully_paid = validated_data.get("paid", False) or amount >= bill_amount

        with transaction.atomic():
            if payment:
                # Update existing unpaid payment
                payment.payment_date = payment_date
                payment.amount = amount
                payment.paid = is_fully_paid
                payment.transaction_id = str(transaction_id)
                payment.entry_by = request.user
                payment.updated_by = request.user
                payment.note = f"Payment updated by {request.user.get_full_name() or request.user.username}"
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
                print("Payment updated successfully.")
            else:
                # Create new payment
                payment = Payment.objects.create(
                    customer=customer,
                    bill_amount=bill_amount,
                    amount=amount,
                    paid=is_fully_paid,
                    billing_month=validated_data["billing_month"],
                    payment_method=validated_data["payment_method"],
                    payment_date=payment_date,
                    transaction_id=str(transaction_id),
                    entry_by=request.user,
                    updated_by=request.user,
                    note=f"Payment received by {request.user.first_name} {request.user.last_name}",
                )
                print("New payment created successfully.")

            # Activate customer if fully paid and currently inactive
            if is_fully_paid and not customer.is_active:
                customer.is_active = True
                customer.save(update_fields=["is_active"])
                print("Customer activated due to successful payment.")

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
        return super().update(instance, validated_data)
