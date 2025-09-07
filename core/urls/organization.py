from django.urls import path


from core.views.organization import OrganizationList, OrganizationDetail


urlpatterns = [
    path("", OrganizationList.as_view(), name="organization-list"),
    path(
        "/<str:uid>",
        OrganizationDetail.as_view(),
        name="organization-detail",
    ),
]
