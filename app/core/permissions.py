from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request

from core.choices import UserKind


class IsAdminUserOrReadOnly(BasePermission):
    """
    Custom permission to only allow admin users to edit objects.
    All other users can only read the objects.
    """

    def has_permission(self, request: Request, view) -> bool:
        # Allow read-only access for all users
        if request.method in SAFE_METHODS:
            return True

        # Allow write access only for admin users
        return request.user and request.user.kind == UserKind.ADMIN


class IsAdminUser(BasePermission):
    """
    Custom permission to only allow admin users to edit objects.
    """

    def has_permission(self, request: Request, view) -> bool:
        # Allow write access only for admin users
        return request.user and request.user.kind == UserKind.ADMIN


class IsManager(BasePermission):
    """
    Custom permission to only allow manager users to edit objects.
    """

    def has_permission(self, request: Request, view) -> bool:
        # Allow write access only for manager users
        return request.user and (
            request.user.kind == UserKind.MANAGER
            or request.user.kind == UserKind.SUPER_ADMIN
        )


class IsStaff(BasePermission):
    """
    Custom permission to only allow staff users to edit objects.
    """

    def has_permission(self, request: Request, view) -> bool:
        # Allow write access only for staff users
        return request.user and request.user.kind == UserKind.STAFF
