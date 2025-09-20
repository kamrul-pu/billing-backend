from django.db import transaction

from rest_framework import serializers

from customer.models import Customer, Package

from core.serializers.user import UserListSerializer
from core.models import User

from customer.choices import ConnectionType
from customer.serializers.package import PackageBase

# from customer.utils import toggle_ppp_user
from customer.helpers import Mikrotik


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
        phone = validated_data.get("phone", None)
        email = validated_data.get("email", None)
        # package_id = validated_data.get("package_id", None)
        # username = validated_data.get("username", None)
        # if not username or username == "":
        #     serializers.ValidationError(
        #         {"username": "Username is required to create user."}
        #     )
        # package = Package.objects.get(id=package_id)
        # if not package:
        #     raise serializers.ValidationError(
        #         {"package": "Packge not found for this id"}
        #     )
        # Check if the phone number is already in use
        if email and (
            Customer.objects.filter(email=email).exists()
            or User.objects.filter(email=email).exists()
        ):
            raise serializers.ValidationError(
                {"message": "This email is already in use."}
            )
        if phone and Customer.objects.filter(phone=phone).exists():
            raise serializers.ValidationError(
                {"message": "This phone number is already in use."}
            )
        # connection_type = validated_data.get("connection_type", ConnectionType.PPPoE)
        # if username and connection_type == ConnectionType.PPPoE:
        #     username: str = validated_data.get("username", None)
        #     existing_user, msg = Mikrotik.get_user_by_username(username)
        #     if existing_user:
        #         raise serializers.ValidationError(
        #             {"username": "User with this username already exists."}
        #         )
        #     # Create an user in miktotik
        #     success, msg = Mikrotik.create_ppp_user(
        #         {
        #             "username": username,
        #             "password": validated_data.get("password", "12345"),
        #             "service": "pppoe",
        #             "profile": str(package.speed_mbps) + "Mbps",
        #         }
        #     )
        #     if not success:
        #         raise serializers.ValidationError(
        #             {"message": "Failed to create user in Server"}
        #         )

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
        organization = self.context["request"].user.organization
        if not organization:
            raise serializers.ValidationError(
                {"message": "Organization not found for this user."}
            )
        if organization.allowed_customer <= organization.total_customer:
            raise serializers.ValidationError(
                {
                    "message": "Customer limit exceeded. Please upgrade your plan or contact support."
                }
            )
        organization.total_customer += 1
        organization.save(update_fields=["total_customer"])
        validated_data["organization_id"] = self.context["request"].user.organization_id
        # Save the entry_by and update_by fields
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
        #     Mikrotik.toggle_ppp_user(instance.username, not is_active)
        # else:
        #     print("No need to toggle the user status in MikroTik")
        return super().update(instance, validated_data)

    def delete(self, instance):
        organization = self.context["request"].user.organization
        if organization and organization.total_customer > 0:
            organization.total_customer -= 1
            organization.save(update_fields=["total_customer"])
        return super().delete(instance)


class StatusToggleSerializer(serializers.Serializer):
    """Serializer for toggling customer status."""

    username = serializers.CharField(required=True, max_length=150)
    is_active = serializers.BooleanField(required=True)
