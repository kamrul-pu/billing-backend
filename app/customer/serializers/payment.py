import uuid
from django.utils import timezone
from rest_framework import serializers
from customer.models import Payment


class PaymentBase(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "customer",
            "entry_by",
            "amount",
            "billing_month",
            "payment_method",
            "paid",
            "transaction_id",
            "payment_date",
            "note",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class PaymentListSerializer(PaymentBase):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    collected_by_name = serializers.CharField(source="entry_by.get_full_name", read_only=True)

    class Meta(PaymentBase.Meta):
        fields = PaymentBase.Meta.fields + ("customer_name", "collected_by_name")

    def create(self, validated_data):
        transaction_id = uuid.uuid4()
        payment_date = validated_data.get("payment_date", timezone.now())
        validated_data["payment_date"] = payment_date
        validated_data["transaction_id"] = str(transaction_id)
        validated_data["entry_by"] = self.context["request"].user
        validated_data["note"] = (
            "Payment received by "
            + self.context["request"].user.first_name
            + " "
            + self.context["request"].user.last_name
        )
        return super().create(validated_data)


class PaymentDetailSerializer(PaymentBase):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    collected_by_name = serializers.CharField(source="entry_by.get_full_name", read_only=True)

    class Meta(PaymentBase.Meta):
        fields = PaymentBase.Meta.fields + ("customer_name", "collected_by_name")
        read_only_fields = PaymentBase.Meta.read_only_fields + ("customer_name", "collected_by_name")
