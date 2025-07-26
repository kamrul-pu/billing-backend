from django.db.models import TextChoices


class ConnectionType(TextChoices):
    """Choices for connection type."""

    DHCP = "DHCP", "DHCP"
    STATIC = "STATIC", "Static"
    PPPoE = "PPPoE", "PPPoE"


class PaymentMethod(TextChoices):
    """Choices for payment method."""

    BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"
    BKASH = "BKASH", "Bkash"
    CASH = "CASH", "Cash"
    NAGAD = "NAGAD", "Nagad"
    MOBILE_BANKING = "MOBILE_BANKING", "Mobile Banking"
    ONLINE_PAYMENT = "ONLINE_PAYMENT", "Online Payment"
    ROCKET = "ROCKET", "Rocket"
    OTHER = "OTHER", "Other"


class Months(TextChoices):
    """Choices for months."""

    JANUARY = "JANUARY", "January"
    FEBRUARY = "FEBRUARY", "February"
    MARCH = "MARCH", "March"
    APRIL = "APRIL", "April"
    MAY = "MAY", "May"
    JUNE = "JUNE", "June"
    JULY = "JULY", "July"
    AUGUST = "AUGUST", "August"
    SEPTEMBER = "SEPTEMBER", "September"
    OCTOBER = "OCTOBER", "October"
    NOVEMBER = "NOVEMBER", "November"
    DECEMBER = "DECEMBER", "December"
