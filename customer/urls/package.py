from django.urls import path

from customer.views.package import PackageList, PackageDetail, PackageCustomerList

urlpatterns = [
    path("", PackageList.as_view(), name="package-list"),
    path("/<str:uid>", PackageDetail.as_view(), name="package-detail"),
    path(
        "/<str:uid>/customers",
        PackageCustomerList.as_view(),
        name="package-customer-list",
    ),
]
