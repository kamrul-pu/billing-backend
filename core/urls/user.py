"""Urls mappings for users."""

from django.urls import path

from core.views.user import (
    MeDetail,
    UserList,
    UserDetail,
    UserRegistration,
    UserLogin,
    UserLoginRefresh,
    ForceResetUserPassword,
    ChangeUserPassword,
)

urlpatterns = [
    path("", UserList.as_view(), name="user-list"),
    path("/<uuid:uid>", UserDetail.as_view(), name="user-details"),
    path(
        "/<uuid:uid>/force-reset-password",
        ForceResetUserPassword.as_view(),
        name="force-reset-password",
    ),
    path("/register", UserRegistration.as_view(), name="user-registration"),
    path("/me", MeDetail.as_view(), name="me-detail"),
    path(
        "/me/change-password", ChangeUserPassword.as_view(), name="change-user-password"
    ),
    path("/login", UserLogin.as_view(), name="user-login"),
    path("/login/refresh", UserLoginRefresh.as_view(), name="user-login-refresh"),
]
