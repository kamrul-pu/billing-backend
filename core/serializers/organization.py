from rest_framework import serializers
from core.models import Organization


class OrganizationBase(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = (
            "id",
            "uid",
            "name",
            "address",
            "phone",
            "email",
            "website",
            "subscription",
            "subscription_status",
            "subscription_end_date",
            "logo",
            "allowed_customer",
            "total_customer",
        )
        read_only_fields = ("id", "uid", "subscription_end_date", "logo")


class OrganizationLiteSerializer(serializers.Serializer):
    uid = serializers.UUIDField()
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    subscription_status = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    subscription_end_date = serializers.DateField(required=False, allow_null=True)
    allowed_customer = serializers.IntegerField(required=False, allow_null=True)
    total_customer = serializers.IntegerField(required=False, allow_null=True)


class OrganizationListSerializer(OrganizationBase):
    class Meta(OrganizationBase.Meta):
        fields = OrganizationBase.Meta.fields + ()
        read_only_fields = OrganizationBase.Meta.read_only_fields + ()

    def create(self, validated_data):
        # Custom create logic if needed
        validated_data["status"] = "DRAFT"  # Default status
        return super().create(validated_data)


class OrganizationDetailSerializer(OrganizationListSerializer):
    class Meta(OrganizationListSerializer.Meta):
        fields = OrganizationListSerializer.Meta.fields + (
            "router_ip",
            "router_username",
            "router_password",
            "router_port",
            "router_secret",
            "router_ssl",
            "created_at",
            "updated_at",
        )
        read_only_fields = OrganizationListSerializer.Meta.read_only_fields + (
            "created_at",
            "updated_at",
        )

    def update(self, instance, validated_data):
        validated_data["updated_by_id"] = self.context["request"].user.id
        return super().update(instance, validated_data)
