"""Serializer for user model."""

from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone

from rest_framework import status
from rest_framework import serializers
from rest_framework.exceptions import APIException
from core.choices import SubscriptionStatus, UserKind

User = get_user_model()


class UserLiteSerializer(serializers.ModelSerializer):
    """A lightweight serializer for user model, used for listing users."""

    class Meta:
        model = User
        fields = ("id", "uid", "first_name", "last_name", "phone", "email")
        read_only_fields = ("id", "uid")


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "uid",
            "first_name",
            "last_name",
            "phone",
            "email",
            "gender",
            "kind",
            "image",
        )
        read_only_fields = ("id", "uid")

    def create(self, validated_data):
        validated_data["organization_id"] = self.context["request"].user.organization_id
        return super().create(validated_data)


class UserDetailSerializer(UserListSerializer):
    class Meta(UserListSerializer.Meta):
        fields = UserListSerializer.Meta.fields + (
            "status",
            "is_staff",
        )
        read_only_fields = UserListSerializer.Meta.read_only_fields + ()


class UserRegistrationSerializer(serializers.ModelSerializer):
    # Specify password and confirm_password fields as write_only, meaning they won't be included in responses
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},  # Styling to indicate it's a password field
        trim_whitespace=False,
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        trim_whitespace=False,
    )

    # Custom validation for password to check if it matches confirm_password
    def validate_password(self, value):
        password = value
        confirm_password = self.initial_data.get("confirm_password", "")
        if password != confirm_password:
            raise serializers.ValidationError(
                detail="Password and confirm password don't match!!!",  # Error message
                code=status.HTTP_400_BAD_REQUEST,  # HTTP status code
            )
        return value

    class Meta:
        model = User  # Specify the model for the serializer
        fields = (
            "first_name",
            "last_name",
            "phone",
            "email",
            "gender",
            "image",
            "password",
            "confirm_password",
        )  # Fields to include in the serialization

    # Custom create method to handle user creation
    def create(self, validated_data):
        validated_data.pop(
            "confirm_password", None
        )  # Remove confirm_password from validated data
        user = User(**validated_data)  # Create a new user instance with validated data
        user.set_password(validated_data.get("password", ""))  # Set user's password
        user.save()  # Save the user to the database
        return user  # Return the created user instance


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "uid",
            "first_name",
            "last_name",
            "phone",
            "email",
            "gender",
            "image",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "uid",
            "created_at",
            "updated_at",
        )


class LoginSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=15, read_only=True)
    uid = serializers.CharField(max_length=64, read_only=True)
    phone = serializers.CharField(required=True)
    password = serializers.CharField(
        max_length=255,
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        phone = attrs.get("phone", None)
        password = attrs.get("password", None)
        if not phone:
            raise serializers.ValidationError(
                detail="Phone number is required for login",
                code=status.HTTP_400_BAD_REQUEST,
            )
        if not password:
            raise serializers.ValidationError(
                detail="A password is requied for login",
                code=status.HTTP_400_BAD_REQUEST,
            )
        # user = authenticate(username=phone, password=password)
        # if user is None:
        #     raise APIException(
        #         detail="Invalid Credentials", code=status.HTTP_400_BAD_REQUEST
        #     )
        # if not user.is_active:
        #     raise APIException(
        #         detail="User is not active", code=status.HTTP_400_BAD_REQUEST
        #     )
        user = (
            User.objects.filter(phone=phone, is_active=True)
            .select_related("organization")
            .first()
        )
        print("User ", user)
        if not user or not user.check_password(password):
            raise APIException(
                detail="Invalid Credentials", code=status.HTTP_400_BAD_REQUEST
            )
        if user.is_superuser or user.kind == UserKind.SUPER_ADMIN:
            print("super admin login")
            return {
                "id": user.id,
                "uid": str(user.uid),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "email": user.email,
                "kind": user.kind,
                "is_superuser": user.is_superuser,
            }
        if (
            user.organization
            and user.organization.subscription_status != SubscriptionStatus.ACTIVE
        ):
            raise APIException(
                detail="Your organization is not active. Please contact with support.",
                code=status.HTTP_400_BAD_REQUEST,
            )
        # print("user organization end date:", user.organization.subscription_end_date)
        # print("user organization:", user.organization)
        if user.organization and not user.organization.subscription_end_date:
            raise APIException(
                detail="Your organization subscription end date is not set. Please contact with support.",
                code=status.HTTP_400_BAD_REQUEST,
            )
        if (
            user.organization
            and user.organization.subscription_end_date < timezone.now().date()
        ):
            raise APIException(
                detail="Your organization subscription has expired. Please contact with support.",
                code=status.HTTP_400_BAD_REQUEST,
            )

        return {
            "id": user.id,
            "uid": str(user.uid),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "email": user.email,
            "kind": user.kind,
            "is_superuser": user.is_superuser,
            "organization": {
                "id": user.organization_id,
                "name": user.organization.name if user.organization else None,
                "subscription_end_date": (
                    user.organization.subscription_end_date.isoformat()
                    if user.organization
                    else None
                ),
            },
        }
