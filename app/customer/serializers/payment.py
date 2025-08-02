import uuid
from django.utils import timezone
from rest_framework import serializers
from customer.models import Payment
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
