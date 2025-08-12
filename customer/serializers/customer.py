from django.db import transaction

from rest_framework import serializers

from customer.models import Customer, Package

from core.serializers.user import UserListSerializer
from core.models import User

from customer.serializers.package import PackageBase

# from customer.utils import toggle_ppp_user


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
            "nid",
            "is_free",
        )
        read_only_fields = (
            "id",
            "uid",
        )


class CustomerListSerializer(CustomerBase):
    """Serializer for listing customers."""

    package = PackageBase(read_only=True)
    package_id = serializers.IntegerField(write_only=True, required=False)

    class Meta(CustomerBase.Meta):
        fields = CustomerBase.Meta.fields + (
            "package",
            "package_id",
            "connection_start_date",
            "is_active",
            "ip_address",
            "mac_address",
            "username",
            "password",
            "connection_type",
            "credentials",
        )
        read_only_fields = CustomerBase.Meta.read_only_fields + ()
        write_only_fields = ("first_name", "last_name", "add")

    @transaction.atomic
    def create(self, validated_data):
        phone = validated_data.get("phone")
        email = validated_data.get("email", None)
        # Check if the phone number is already in use
        if email and (
            Customer.objects.filter(email=email).exists()
            or User.objects.filter(email=email).exists()
        ):
            raise serializers.ValidationError(
                {"email": "This email is already in use."}
            )
        if Customer.objects.filter(phone=phone).exists():
            raise serializers.ValidationError(
                {"phone": "This phone number is already in use."}
            )
        # Create an user object for this customer for future use
        # user = User.objects.filter(phone=phone).first()
        # if user:
        #     raise serializers.ValidationError(
        #         {"phone": "This phone number is already associated with a user."}
        #     )
        # name = validated_data.get("name", "")
        # name = name.split(" ")
        # first_name = name[0]
        # last_name = name[1] if len(name) > 1 else ""
        # user = User.objects.create_user(
        #     phone=validated_data.get("phone"),
        #     first_name=first_name,
        #     last_name=last_name,
        #     email=validated_data.get("email", None),
        #     password="123456",  # Default password, can be changed later
        # )
        # validated_data["user_id"] = user.id
        validated_data["entry_by_id"] = self.context["request"].user.id
        validated_data["updated_by_id"] = self.context["request"].user.id
        return Customer.objects.create(**validated_data)


class CustomerDetailSerializer(CustomerBase):
    """Serializer for customer details."""

    user = UserListSerializer(read_only=True)
    package = PackageBase(read_only=True)
    package_id = serializers.IntegerField(write_only=True, required=False)

    class Meta(CustomerBase.Meta):
        fields = CustomerBase.Meta.fields + (
            "user",
            "package",
            "package_id",
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
            # "is_active",
        )

    def update(self, instance, validated_data):
        validated_data["update_by_id"] = self.context["request"].user.id
        # is_active = validated_data.get("is_active", None)
        # if instance.is_active != is_active:
        #     # Need to toggle the user status in MikroTik
        #     print("Need to toggle the user status in MikroTik")
        #     toggle_ppp_user(instance.username, not is_active)
        # else:
        #     print("No need to toggle the user status in MikroTik")
        return super().update(instance, validated_data)


class StatusToggleSerializer(serializers.Serializer):
    """Serializer for toggling customer status."""

    username = serializers.CharField(required=True, max_length=150)
    is_active = serializers.BooleanField(required=True)
