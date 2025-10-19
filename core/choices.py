from django.db.models import TextChoices


class SubscriptionType(TextChoices):
    FREE = "FREE", "Free"
    BASIC = "BASIC", "Basic"
    PREMIUM = "PREMIUM", "Premium"
    ENTERPRISE = "ENTERPRISE", "Enterprise"


class SubscriptionStatus(TextChoices):
    ACTIVE = "ACTIVE", "Active"
    EXPIRED = "EXPIRED", "Expired"
    CANCELLED = "CANCELLED", "Cancelled"
    PENDING = "PENDING", "Pending"


class UserKind(TextChoices):
    ADMIN = "ADMIN", "Admin"
    CUSTOMER = "CUSTOMER", "Customer"
    MANAGER = "MANAGER", "Manager"
    STAFF = "STAFF", "Staff"
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    OWNER = "OWNER", "Owner"
    OTHER = "OTHER", "Other"


class UserGender(TextChoices):
    FEMALE = "FEMALE", "Female"
    MALE = "MALE", "Male"
    UNKNOWN = "UNKNOWN", "Unknown"


class RouterType(TextChoices):
    MIKROTIK = "MIKROTIK", "Mikrotik"
    UBIQUITI = "UBIQUITI", "Ubiquiti"
    CISCO = "CISCO", "Cisco"
    OTHER = "OTHER", "Other"


class OTPType(TextChoices):
    FORGOT_PASSWORD = "FORGOT_PASSWORD", "Forgot Password"
    USER_VERIFICATION = "USER_VERIFICATION", "User Verification"
    TRANSACTION_VERIFICATION = "TRANSACTION_VERIFICATION", "Transaction Verification"
