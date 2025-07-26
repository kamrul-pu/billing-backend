from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request

from core.choices import UserKind


class AllowAny(BasePermission):
    def has_permission(self, request: Request, view) -> bool:
        return True


class IsAuthenticated(BasePermission):
    def has_permission(self, request: Request, view) -> bool:
        return request.user and request.user.is_authenticated


class IsAdminUser(BasePermission):
    def has_permission(self, request: Request, view) -> bool:
        return request.user.is_authenticated and (
            request.user.kind == UserKind.ADMIN
            or request.user.kind == UserKind.SUPER_ADMIN
        )


class IsManager(BasePermission):
    def has_permission(self, request: Request, view) -> bool:
        return request.user.is_authenticated and request.user.kind in [
            UserKind.MANAGER,
            UserKind.SUPER_ADMIN,
        ]


class IsStaff(BasePermission):
    def has_permission(self, request: Request, view) -> bool:
        return request.user.is_authenticated and request.user.kind == UserKind.STAFF


class IsAdminUserOrReadOnly(BasePermission):
    def has_permission(self, request: Request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.kind == UserKind.ADMIN
