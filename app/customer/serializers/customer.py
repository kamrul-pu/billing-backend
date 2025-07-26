from rest_framework import serializers

from customer.models import Customer

from core.serializers.user import UserListSerializer


class CustomerBase(serializers.ModelSerializer):
    """Base serializer for Customer model."""

    class Meta:
        model = Customer
        fields = (
            "id",
            "uid",
            "name",
            "email",
            "phone",
            "address",
            "package",
        )
        read_only_fields = (
            "id",
            "uid",
        )


class CustomerListSerializer(CustomerBase):
    """Serializer for listing customers."""

    package = serializers.CharField(source="package.name", read_only=True)

    class Meta(CustomerBase.Meta):
        fields = CustomerBase.Meta.fields + ()
        read_only_fields = CustomerBase.Meta.read_only_fields + ()


class CustomerDetailSerializer(CustomerBase):
    """Serializer for customer details."""

    user = UserListSerializer(read_only=True)

    class Meta(CustomerBase.Meta):
        fields = CustomerBase.Meta.fields + (
            "user",
            "connection_start_date",
            "is_active",
            "ip_address",
            "mac_address",
            "username",
            "password",
            "connection_type",
        )
        read_only_fields = CustomerBase.Meta.read_only_fields + (
            "user",
            "connection_start_date",
            "is_active",
        )
