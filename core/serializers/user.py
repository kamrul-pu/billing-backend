"""Serializer for user model."""

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import status, serializers
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
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        trim_whitespace=False,
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        trim_whitespace=False,
    )

    def validate_password(self, value):
        password = value
        confirm_password = self.initial_data.get("confirm_password", "")
        if password != confirm_password:
            raise serializers.ValidationError(
                {"message": "Password and confirm password don't match!!!"}
            )
        return value

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone",
            "email",
            "gender",
            "image",
            "password",
            "confirm_password",
        )

    def create(self, validated_data):
        validated_data.pop("confirm_password", None)
        user = User(**validated_data)
        user.set_password(validated_data.get("password", ""))
        user.save()
        return user


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
            "kind",
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
        phone = attrs.get("phone")
        password = attrs.get("password")

        if not phone:
            raise serializers.ValidationError(
                {"message": "Phone number is required for login"},
                status.HTTP_400_BAD_REQUEST,
            )

        if not password:
            raise serializers.ValidationError(
                {"message": "A password is required for login"},
                status.HTTP_400_BAD_REQUEST,
            )

        user = (
            User.objects.filter(phone=phone, is_active=True)
            .select_related("organization")
            .first()
        )

        if not user or not user.check_password(password):
            raise serializers.ValidationError(
                {"message": "Invalid Credentials entered!!!"},
                status.HTTP_400_BAD_REQUEST,
            )

        if user.is_superuser or user.kind == UserKind.SUPER_ADMIN:
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
            raise serializers.ValidationError(
                {"message": "Your organization is not active. Please contact support."}
            )

        if user.organization and not user.organization.subscription_end_date:
            raise serializers.ValidationError(
                {
                    "message": "Your organization subscription end date is not set. Please contact support."
                }
            )

        if (
            user.organization
            and user.organization.subscription_end_date < timezone.now().date()
        ):
            raise serializers.ValidationError(
                {
                    "message": "Your organization subscription has expired. Please contact support."
                }
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
