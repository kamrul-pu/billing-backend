from django.urls import path

from customer.views.tasks import GenerateBillTask, DeactiveDueCustomer

urlpatterns = [
    path("/generate-bills", GenerateBillTask.as_view(), name="generate-bills"),
    path(
        "/deactive-due-customer",
        DeactiveDueCustomer.as_view(),
        name="deactive-due-customer",
    ),
]
