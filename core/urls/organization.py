from django.urls import path


from core.views.organization import OrganizationList, OrganizationDetail, CustomerSessionList


urlpatterns = [
    path("", OrganizationList.as_view(), name="organization-list"),
    path(
        "/<str:uid>",
        OrganizationDetail.as_view(),
        name="organization-detail",
    ),
    path(
        "/active/sessions",
        CustomerSessionList.as_view(),
        name="organization-customer-session-list",
    ),
]
