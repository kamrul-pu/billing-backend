from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from customer.models import Package, Customer, Payment


class PackageAdmin(ModelAdmin):
    list_display = ("id", "name", "price")
    search_fields = ("name", "price")


admin.site.register(Package, PackageAdmin)


class CustomerAdmin(ModelAdmin):
    list_display = ("id", "name", "phone", "nid", "connection_type", "is_active")
    search_fields = ("name", "phone", "nid")


admin.site.register(Customer, CustomerAdmin)


class PaymentAdmin(ModelAdmin):
    list_display = ("id", "customer", "amount", "billing_month", "entry_by", "paid", "payment_date")
    search_fields = ("customer__name", "amount", "billing_month", "entry_by__first_name")
    list_filter = ("paid", "billing_month", "entry_by")


admin.site.register(Payment, PaymentAdmin)
