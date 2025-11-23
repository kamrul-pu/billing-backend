"""
Main URL Mapping of the app.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path, include
from django.http import JsonResponse

from rest_framework import permissions

from customer.views.customer import Dashboard

SWAGGER_BASE_URL = "https://api.mikrolink.artsensebd.com"


def health_check(request):
    """Health check endpoint for Docker."""
    return JsonResponse({"status": "healthy", "service": "billing-backend"})


urlpatterns = [
    # Health check endpoints
    path("", health_check, name="health-check"),
    path("health/", health_check, name="health-check-dedicated"),
    path("admin/", admin.site.urls),
    # include subscription endpoints
    path(
        "api/v1/subscriptions",
        include("core.urls.subscription"),
        name="subscription-urls",
    ),
    # include organization endpoints
    path(
        "api/v1/organizations",
        include("core.urls.organization"),
        name="organization-urls",
    ),
    # include user endpoints
    path("api/v1/users", include("core.urls.user"), name="user-urls"),
    # include package endpoints
    path("api/v1/packages", include("customer.urls.package"), name="package-urls"),
    # include customer endpoints
    path("api/v1/customers", include("customer.urls.customer"), name="customer-urls"),
    # include customer authentication and self-service endpoints
    path("api/v1/customers", include("customer.urls.customer_auth"), name="customer-auth-urls"),
    # include payment endpoints
    path("api/v1/payments", include("customer.urls.payment"), name="payment-urls"),
    # include core endpoints
    # Dashboard endpoints
    path("api/v1/dashboard", Dashboard.as_view(), name="dashboard"),
    path("api/v1/tasks", include("customer.urls.tasks"), name="customer-tasks-urls"),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.ENABLE_DOC:
    from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularRedocView,
        SpectacularSwaggerView,
    )

    urlpatterns += [
        path("api/schema", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/docs",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            "api/redoc",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ]


# drf yasg api documentation
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi

# schema_view = get_schema_view(
#     openapi.Info(
#         title="Billing Backend",
#         default_version="1.0",
#         description="App for Bill Management",
#         terms_of_service="https://www.google.com/policies/terms/",
#         contact=openapi.Contact(email="contact@snippets.local"),
#         license=openapi.License(name="BSD License"),
#     ),
#     public=True,
#     permission_classes=(permissions.AllowAny,),
#     url=SWAGGER_BASE_URL,
# )
# urlpatterns += [
#     path(
#         "api/swagger<format>/",
#         schema_view.without_ui(cache_timeout=0),
#         name="schema-json",
#     ),
#     path(
#         "api/docs",
#         schema_view.with_ui("swagger", cache_timeout=0),
#         name="schema-swagger-ui",
#     ),
#     path(
#         "api/redoc/",
#         schema_view.with_ui("redoc", cache_timeout=0),
#         name="schema-redoc",
#     ),
# ]

if settings.ENABLE_SILK:
    urlpatterns += [re_path(r"^profiler/", include("silk.urls", namespace="silk"))]
