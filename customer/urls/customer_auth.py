"""URLs for customer authentication and self-service endpoints."""

from django.urls import path

from customer.views.customer_auth import (
    CustomerLogin,
    CustomerLoginRefresh,
    CustomerProfile,
    CustomerPaymentsList,
    CustomerPaymentDetail,
    CustomerCreatePayment,
    BKashPaymentCallback,
    CustomerVerifyPayment,
)

urlpatterns = [
    # Authentication endpoints
    path("auth/login", CustomerLogin.as_view(), name="customer-login"),
    path("auth/login/refresh", CustomerLoginRefresh.as_view(), name="customer-login-refresh"),
    
    # Profile and information endpoints
    path("auth/me", CustomerProfile.as_view(), name="customer-profile"),
    
    # Payment endpoints
    path("auth/payments", CustomerPaymentsList.as_view(), name="customer-payments-list"),
    path("auth/payments/<str:uid>", CustomerPaymentDetail.as_view(), name="customer-payment-detail"),
    path("auth/payments/create", CustomerCreatePayment.as_view(), name="customer-create-payment"),
    path("auth/payments/verify", CustomerVerifyPayment.as_view(), name="customer-verify-payment"),
    
    # bKash callback (public endpoint)
    path("auth/payments/bkash/callback", BKashPaymentCallback.as_view(), name="bkash-payment-callback"),
]

