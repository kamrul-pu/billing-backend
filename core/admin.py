"""
Django admin customization
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from core.models import User


class UserAdmin(BaseUserAdmin, ModelAdmin):
    """Defines the admin pages for users."""

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
