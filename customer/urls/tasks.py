from django.urls import path

from customer.views.tasks import (
    GenerateBillTask,
    DeactiveDueCustomer,
    GenerateOrganizationsBillTask,
    DeactiveOrganizationsDueCustomer,
    DeactiveExpiredSubscriptionCustomer,
)

urlpatterns = [
    path("/generate-bills", GenerateBillTask.as_view(), name="generate-bills"),
    path(
        "/deactive-due-customer",
        DeactiveDueCustomer.as_view(),
        name="deactive-due-customer",
    ),
    path(
        "/generate-organizations-bills",
        GenerateOrganizationsBillTask.as_view(),
        name="generate-organizations-bills",
    ),
    path(
        "/deactive-organizations-due-customer",
        DeactiveOrganizationsDueCustomer.as_view(),
        name="deactive-organizations-due-customer",
    ),
    path(
        "/deactive-expired-subscription-customer",
        DeactiveExpiredSubscriptionCustomer.as_view(),
        name="deactive-expired-subscription-customer",
    ),
]
