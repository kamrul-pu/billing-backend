import uuid
from django.utils import timezone
from rest_framework import serializers
from customer.models import Payment, Customer
from core.serializers.user import UserLiteSerializer
from customer.serializers.customer import CustomerBase


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
        transaction_id = uuid.uuid4()
        payment_date = validated_data.get("payment_date", timezone.now())
        customer_id = validated_data.get("customer_id")
        customer = Customer.objects.filter(id=customer_id).first()
        if not customer:
            raise serializers.ValidationError(
                {"customer_id": "Customer does not exist."}
            )
        payment = Payment.objects.filter(
            customer=customer,
            billing_month=validated_data.get("billing_month"),
        ).first()
        if payment and payment.paid:
            raise serializers.ValidationError(
                {
                    "billing_month": "Payment for this month has already been made for the customer."
                }
            )
        if payment and not payment.paid:
            payment.payment_date = payment_date
            if payment.bill_amount == validated_data.get("amount", 0.0):
                print("Payment amount is equeal to bill amount.")
                payment.paid = True
            else:
                print("Payment amount is less so no total paid yet")
                payment.paid = validated_data.get("paid", False)
            payment.transaction_id = str(transaction_id)
            payment.amount = validated_data.get("amount", 0.0)
            payment.entry_by_id = self.context["request"].user.id
            payment.update_by_id = self.context["request"].user.id
            payment.note = (
                "Payment updated by "
                + self.context["request"].user.first_name
                + " "
                + self.context["request"].user.last_name
            )
            payment.save(
                update_fields=[
                    "amount",
                    "entry_by_id",
                    "updated_by_id",
                    "payment_date",
                    "transaction_id",
                    "note",
                    "paid",
                ]
            )
            return payment

        validated_data["payment_date"] = payment_date
        validated_data["transaction_id"] = str(transaction_id)
        validated_data["entry_by_id"] = self.context["request"].user.id
        validated_data["note"] = (
            "Payment received by "
            + self.context["request"].user.first_name
            + " "
            + self.context["request"].user.last_name
        )
        return super().create(validated_data)


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
        validated_data["updated_by_id"] = self.context["request"].user.id
        return super().update(instance, validated_data)
