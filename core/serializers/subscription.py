from rest_framework import serializers

from core.models import Subscription


class SubscriptionBase(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = (
            "id",
            "uid",
            "name",
            "description",
            "plan",
            "price",
            "max_customers",
        )
        read_only_fields = ("id", "uid")


class SubscriptionListSerializer(SubscriptionBase):
    class Meta(SubscriptionBase.Meta):
        fields = SubscriptionBase.Meta.fields + ()


class SubscriptionDetailSerializer(SubscriptionListSerializer):
    class Meta(SubscriptionListSerializer.Meta):
        fields = SubscriptionListSerializer.Meta.fields + (
            "created_at",
            "updated_at",
        )
        read_only_fields = SubscriptionListSerializer.Meta.read_only_fields + (
            "created_at",
            "updated_at",
        )
