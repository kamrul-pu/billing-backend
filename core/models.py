"""Core models for our app."""

from django.contrib.auth.base_user import (
    BaseUserManager,
)
from django.contrib.auth.models import AbstractBaseUser
from django.db import models


from common.models import BaseModelWithUID, NameDescriptionBaseModel

from core.choices import (
    UserKind,
    UserGender,
    SubscriptionType,
    SubscriptionStatus,
    OTPType,
)
from core.utils import get_user_media_path_prefix


class Subscription(NameDescriptionBaseModel):
    """Model representing organization subscriptions."""

    plan = models.CharField(
        max_length=20,
        choices=SubscriptionType.choices,
        default=SubscriptionType.FREE,
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    max_customers = models.IntegerField(default=100)

    def __str__(self):
        return f"{self.name} - {self.plan}"

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        ordering = ["-pk"]


class Organization(NameDescriptionBaseModel):
    """Model representing an ISP organization."""

    # owner = models.ForeignKey(
    #     "User", on_delete=models.PROTECT, related_name="owned_organizations"
    # )
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, blank=True
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.PENDING,
    )
    # Mikrotik credentials
    router_ip = models.CharField(max_length=64, blank=True)
    router_username = models.CharField(max_length=150, blank=True)
    router_password = models.CharField(max_length=128, blank=True)
    router_port = models.IntegerField(default=8728, blank=True)
    router_secret = models.CharField(max_length=150, blank=True)
    router_ssl = models.BooleanField(
        default=False, help_text="Use SSL for Mikrotik connection"
    )
    # Additional fields for better organization management

    # Organization status
    # is_active = models.BooleanField(default=True)
    subscription_end_date = models.DateField(null=True, blank=True)
    logo = models.ImageField(upload_to="organizations/", blank=True)
    allowed_customer = models.IntegerField(default=0)
    total_customer = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        ordering = ["-pk"]


class UserManager(BaseUserManager):
    """Managers for users."""

    def create_user(self, first_name, last_name, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("User must have a Phone Number.")

        user = self.model(
            first_name=first_name, last_name=last_name, phone=phone, **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, first_name, last_name, phone, password):
        """Create a new superuser and return superuser"""

        user = self.create_user(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            password=password,
        )

        user.is_superuser = True
        user.is_staff = True
        user.kind = UserKind.SUPER_ADMIN
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, BaseModelWithUID):
    """Users in the System"""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        related_name="users",
        null=True,
        blank=True,
        help_text="The organization this user belongs to.",
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        db_index=True,
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        db_index=True,
    )
    phone = models.CharField(
        max_length=20,
        db_index=True,
        unique=True,
        verbose_name="Phone Number",
    )
    email = models.EmailField(
        max_length=255,
        unique=True,
        db_index=True,
        blank=True,
    )
    gender = models.CharField(
        max_length=20,
        blank=True,
        choices=UserGender.choices,
        default=UserGender.UNKNOWN,
    )
    image = models.ImageField(
        "Profile_image",
        upload_to="profile_images/",
        default="profile_images/default.png",
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(
        default=True,
    )
    is_staff = models.BooleanField(
        default=False,
    )
    is_superuser = models.BooleanField(
        default=False,
    )
    kind = models.CharField(
        max_length=20,
        choices=UserKind.choices,
        default=UserKind.OTHER,
    )

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = (
        "first_name",
        "last_name",
    )

    def has_perm(self, perm, obj=None):
        return self.is_staff or self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_staff or self.is_superuser

    class Meta:
        verbose_name = "System User"
        verbose_name_plural = "System Users"


class OTP(BaseModelWithUID):
    """Model to store OTPs for user verification."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="otps",
    )
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    otp_type = models.CharField(
        max_length=30,
        choices=OTPType.choices,
        default=OTPType.FORGOT_PASSWORD,
    )

    def __str__(self):
        return f"OTP for {self.user.phone} - {'Used' if self.is_used else 'Unused'}"

    class Meta:
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"
        ordering = ["-created_at"]
