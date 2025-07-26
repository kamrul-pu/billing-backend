"""Core models for our app."""

from django.contrib.auth.base_user import (
    BaseUserManager,
)
from django.contrib.auth.models import AbstractBaseUser
from django.db import models


from common.models import BaseModelWithUID

from core.choices import (
    UserKind,
    UserGender,
)
from core.utils import get_user_media_path_prefix


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
