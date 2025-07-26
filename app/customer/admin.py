from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from customer.models import Package, Customer, Payment


class PackageAdmin(ModelAdmin):
    list_display = ("id", "name", "price")
    search_fields = ("name", "price")


admin.site.register(Package, PackageAdmin)


class CustomerAdmin(ModelAdmin):
    list_display = ("id", "name", "phone", "connection_type", "is_active")
    search_fields = ("name", "phone")


admin.site.register(Customer, CustomerAdmin)


class PaymentAdmin(ModelAdmin):
    list_display = ("id", "amount", "billing_month", "paid", "payment_date")
    search_fields = ("customer__name", "amount", "billing_month")
    list_filter = ("paid", "billing_month")


admin.site.register(Payment, PaymentAdmin)
