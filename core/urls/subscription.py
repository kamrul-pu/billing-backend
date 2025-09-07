from django.urls import path

from core.views.subscription import SubscriptionList, SubscriptionDetail


urlpatterns = [
    path("", SubscriptionList.as_view(), name="subscription-list"),
    path(
        "/<str:uid>",
        SubscriptionDetail.as_view(),
        name="subscription-detail",
    ),
]
