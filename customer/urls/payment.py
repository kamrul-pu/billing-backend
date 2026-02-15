from django.urls import path

from customer.views.payment import PaymentsList, PaymentDetail, MonthlyCollectionList

urlpatterns = [
    path("", PaymentsList.as_view(), name="payment-list"),
    path("/<str:uid>", PaymentDetail.as_view(), name="payment-detail"),
    path("/monthly/collections", MonthlyCollectionList.as_view(), name="monthly-collections"),

]
