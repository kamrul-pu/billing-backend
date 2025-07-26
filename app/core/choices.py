from django.db.models import TextChoices


class UserKind(TextChoices):
    ADMIN = "ADMIN", "Admin"
    CUSTOMER = "CUSTOMER", "Customer"
    MANAGER = "MANAGER", "Manager"
    STAFF = "STAFF", "Staff"
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    OTHER = "OTHER", "Other"


class UserGender(TextChoices):
    FEMALE = "FEMALE", "Female"
    MALE = "MALE", "Male"
    UNKNOWN = "UNKNOWN", "Unknown"
