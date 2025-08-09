from django.urls import path

from customer.views.payment import PaymentsList, PaymentDetail

urlpatterns = [
    path("", PaymentsList.as_view(), name="payment-list"),
    path("/<str:uid>", PaymentDetail.as_view(), name="payment-detail"),
]
