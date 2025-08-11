"""Customer models for the application."""

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from customer.utils import toggle_ppp_user
from common.models import NameDescriptionBaseModel, BaseModelWithUID
from customer.choices import ConnectionType, PaymentMethod, Months


class Package(NameDescriptionBaseModel):
    """Model representing a package."""

    speed_mbps = models.PositiveIntegerField(
        help_text="Speed in Mbps for the package.", blank=True, default=10
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        help_text="Price of the package in USD.",
    )

    def __str__(self):
        return f"{self.name} - {self.speed_mbps} Mbps - ${self.price:.2f}"

    class Meta:
        verbose_name = "Package"
        verbose_name_plural = "Packages"
        ordering = ["-created_at"]


class Customer(NameDescriptionBaseModel):
    user = models.OneToOneField(
        "core.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=("user"),
        related_name="customer_user",
    )
    phone = models.CharField(max_length=20, blank=True)
    secret_id = models.CharField(
        max_length=64,
        blank=True,
    )
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    nid = models.CharField(
        max_length=20, blank=True, help_text="National ID number of the customer."
    )

    package = models.ForeignKey(
        Package, on_delete=models.SET_NULL, null=True, related_name="packages_customers"
    )
    connection_start_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_free = models.BooleanField(
        default=False, help_text="Indicates if the customer has a free package."
    )

    # Credentials
    ip_address = models.CharField(max_length=45, blank=True)
    mac_address = models.CharField(max_length=32, blank=True)
    username = models.CharField(max_length=150, blank=True)
    password = models.CharField(max_length=128, blank=True)
    connection_type = models.CharField(
        max_length=32,
        choices=ConnectionType.choices,
        default=ConnectionType.DHCP,
        help_text="Type of connection for the customer.",
    )
    credentials = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        help_text="Additional credentials for the customer.",
    )

    def __str__(self):
        return f"{self.name} ({self.phone})"

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ["-created_at"]


class Payment(NameDescriptionBaseModel):
    """Model representing a payment."""

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="payments"
    )
    bill_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        help_text="Total bill amount for the payment.",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    billing_month = models.CharField(
        max_length=32,
        choices=Months.choices,
        default=Months.JANUARY,
        help_text="Month for which the payment is made.",
    )
    payment_method = models.CharField(
        max_length=32,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        help_text="Method of payment.",
    )
    paid = models.BooleanField(
        default=False, help_text="Indicates if the payment is completed."
    )
    note = models.TextField(
        blank=True, null=True, help_text="Additional notes for the payment."
    )
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Payment of ${self.amount:.2f} by {self.customer.name} on {self.payment_date}"

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-created_at"]


@receiver(pre_save, sender=Customer)
def customer_status_toggle(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if old_instance.is_active != instance.is_active:
                print("Signal: Toggling user status in MikroTik")
                toggle_ppp_user(instance.username, not instance.is_active)
        except sender.DoesNotExist:
            pass  #
