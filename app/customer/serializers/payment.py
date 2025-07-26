from rest_framework import serializers
from customer.models import Payment


class PaymentBase(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "customer",
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

    class Meta(PaymentBase.Meta):
        fields = PaymentBase.Meta.fields + ("customer_name",)


class PaymentDetailSerializer(PaymentBase):
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta(PaymentBase.Meta):
        fields = PaymentBase.Meta.fields + ("customer_name",)
        read_only_fields = PaymentBase.Meta.read_only_fields + ("customer_name",)
