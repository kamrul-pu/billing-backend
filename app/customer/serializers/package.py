from rest_framework import serializers

from customer.models import Package

from customer.serializers.customer import CustomerListSerializer


class PackageBase(serializers.ModelSerializer):
    """Base serializer for Package model."""

    class Meta:
        model = Package
        fields = (
            "id",
            "uid",
            "name",
            "speed_mbps",
            "price",
            "description",
        )
        read_only_fields = (
            "id",
            "uid",
        )


class PackageListSerializer(PackageBase):
    """Serializer for listing packages."""

    class Meta(PackageBase.Meta):
        fields = PackageBase.Meta.fields + ()
        read_only_fields = PackageBase.Meta.read_only_fields + ()


class PackageDetailSerializer(PackageBase):
    """Serializer for package details."""

    class Meta(PackageBase.Meta):
        fields = PackageBase.Meta.fields + ("created_at", "updated_at")
        read_only_fields = PackageBase.Meta.read_only_fields + (
            "created_at",
            "updated_at",
        )


class PackageCustomerSerializer(serializers.ModelSerializer):
    """Serializer for listing customers of a package."""

    customers = CustomerListSerializer(many=True, read_only=True)

    class Meta:
        model = Package
        fields = ("id", "uid", "name", "customers")
        read_only_fields = ("id", "uid", "name", "customers")
