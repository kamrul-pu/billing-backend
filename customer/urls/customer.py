from django.urls import path

from customer.views.customer import (
    CustomerList,
    CustomerDetail,
    CustomerPaymentsList,
    GenerateBill,
    StatusToggle,
)


urlpatterns = [
    path("", CustomerList.as_view(), name="customer-list"),
    path("/<str:uid>", CustomerDetail.as_view(), name="customer-detail"),
    path("/<str:uid>/payments", CustomerPaymentsList.as_view(), name="customer-detail"),
    path("/bills/generate", GenerateBill.as_view(), name="generate-bill"),
    path("/status/toggle", StatusToggle.as_view(), name="toggle-status"),
]
