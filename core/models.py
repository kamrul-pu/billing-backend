"""Core models for our app."""

from django.contrib.auth.base_user import (
    BaseUserManager,
)
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from cryptography.fernet import Fernet
import base64
import hashlib

from common.models import BaseModelWithUID, NameDescriptionBaseModel

from core.choices import (
    UserKind,
    UserGender,
    SubscriptionType,
    SubscriptionStatus,
    OTPType,
    BillingCycle,
)
# from core.utils import get_user_media_path_prefix


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
    # Mikrotik credentials (stored encrypted)
    router_ip = models.CharField(max_length=256, blank=True)
    router_username = models.CharField(max_length=256, blank=True)
    router_password = models.CharField(max_length=256, blank=True)
    router_port = models.IntegerField(default=8728, blank=True)
    router_secret = models.CharField(max_length=256, blank=True)
    router_ssl = models.BooleanField(
        default=False, help_text="Use SSL for Mikrotik connection"
    )
    # Additional fields for better organization management

    # Organization status
    # is_active = models.BooleanField(default=True)
    subscription_end_date = models.DateField(null=True, blank=True)
    logo = models.URLField(blank=True, null=True)
    allowed_customer = models.IntegerField(default=0)
    total_customer = models.IntegerField(default=0)
    billing_cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
    )
    sms_feature = models.BooleanField(default=False)
    email_feature = models.BooleanField(default=False)

    @staticmethod
    def _get_cipher_suite():
        """Generate Fernet cipher suite from Django's SECRET_KEY."""
        from django.conf import settings
        
        secret_key = settings.SECRET_KEY
        derived_key = hashlib.sha256(secret_key.encode()).digest()
        encoded_key = base64.urlsafe_b64encode(derived_key)
        return Fernet(encoded_key)
    
    def _encrypt_value(self, value):
        """Encrypt a string value."""
        if not value or value == "":
            return value
        try:
            cipher_suite = self._get_cipher_suite()
            if isinstance(value, str):
                value = value.encode()
            encrypted_value = cipher_suite.encrypt(value)
            return encrypted_value.decode()
        except Exception:
            return value
    
    def _decrypt_value(self, value, strict=False):
        """Decrypt a string value."""
        if not value or value == "":
            return value
        try:
            cipher_suite = self._get_cipher_suite()
            if isinstance(value, str):
                value = value.encode()
            decrypted_value = cipher_suite.decrypt(value)
            return decrypted_value.decode()
        except Exception as e:
            if strict:
                raise e
            # If decryption fails, assume it's already plain text
            if isinstance(value, bytes):
                return value.decode()
            return value
    
    def _is_encrypted(self, value):
        """Check if a value is already encrypted."""
        if not value:
            return True # Nothing to encrypt
        try:
            self._decrypt_value(value, strict=True)
            return True
        except Exception:
            return False

    def save(self, *args, **kwargs):
        """Encrypt router credentials before saving to database."""
        # Encrypt credentials if they're not already encrypted
        if self.router_ip and not self._is_encrypted(self.router_ip):
            self.router_ip = self._encrypt_value(self.router_ip)
        
        if self.router_username and not self._is_encrypted(self.router_username):
            self.router_username = self._encrypt_value(self.router_username)
        
        if self.router_password and not self._is_encrypted(self.router_password):
            self.router_password = self._encrypt_value(self.router_password)
        
        if self.router_secret and not self._is_encrypted(self.router_secret):
            self.router_secret = self._encrypt_value(self.router_secret)
        
        super().save(*args, **kwargs)
    
    def get_router_ip(self):
        """Get decrypted router IP."""
        return self._decrypt_value(self.router_ip)
    
    def get_router_username(self):
        """Get decrypted router username."""
        return self._decrypt_value(self.router_username)
    
    def get_router_password(self):
        """Get decrypted router password."""
        return self._decrypt_value(self.router_password)
    
    def get_router_secret(self):
        """Get decrypted router secret."""
        return self._decrypt_value(self.router_secret)

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
    image = models.URLField(blank=True, null=True)
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

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone})"

    @property
    def username(self):
        """Compatibility property for templates accessing `user.username`.

        The application uses `phone` as `USERNAME_FIELD`. Some admin templates or
        third-party code still access `user.username`. Map the property to the
        configured `USERNAME_FIELD` to avoid template errors.
        """
        return getattr(self, self.USERNAME_FIELD)


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
        default=OTPType.PASSWORD_RESET,
    )

    def __str__(self):
        return f"OTP for {self.user.phone} - {'Used' if self.is_used else 'Unused'}"

    class Meta:
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"
        ordering = ("-pk",)
