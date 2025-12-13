"""
Django admin customization
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from core.models import User, Organization, Subscription, OTP


class UserAdmin(BaseUserAdmin, ModelAdmin):
    """Defines the admin pages for users."""

    # Disable Unfold auto-added tracking fields
    # unfold_include_tracked_fields = False
    # unfold_exclude = ("created_by", "updated_by", "created_at", "updated_at")

    ordering = ["-id"]
    list_display = [
        "id",
        "uid",
        "phone",
        "first_name",
        "last_name",
        "kind",
        "status",
    ]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "phone",
                    "email",
                    "password",
                    "first_name",
                    "last_name",
                    "organization",
                    "image",
                    "kind",
                    "gender",
                    "status",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login",)}),
    )
    readonly_fields = ["last_login"]

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "phone",
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "organization",
                    "image",
                    "kind",
                    "gender",
                    "status",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
    filter_horizontal = ()
    list_filter = ("is_active", "is_staff", "is_superuser", "kind")


admin.site.register(User, UserAdmin)


class SubscriptionAdmin(ModelAdmin):
    list_display = ["id", "name", "name", "plan", "price", "max_customers", "status"]
    list_filter = ("status", "plan")
    ordering = ["-id"]


admin.site.register(Subscription, SubscriptionAdmin)


class OrganizationAdmin(ModelAdmin):
    list_display = ["id", "name", "phone", "subscription_end_date", "status"]
    list_filter = ("status",)
    ordering = ["-id"]


admin.site.register(Organization, OrganizationAdmin)


class OTPAdmin(ModelAdmin):
    list_display = ["id", "otp_type", "is_used", "created_at"]
    list_filter = ("otp_type", "is_used")
    ordering = ("-pk",)


admin.site.register(OTP, OTPAdmin)
