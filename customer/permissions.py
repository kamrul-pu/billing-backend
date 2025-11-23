"""Customer-specific permissions."""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class IsCustomer(BasePermission):
    """Permission class to check if the request is from an authenticated customer."""

    def has_permission(self, request: Request, view) -> bool:
        """Check if the request has a valid customer in the request."""
        return hasattr(request, "customer") and request.customer is not None

