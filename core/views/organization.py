from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import SAFE_METHODS
from core.permissions import (
    IsSuperAdminOrReadOnly,
    IsAuthenticated,
    IsAdminUser,
    IsManager,
    IsSuperAdmin,
)
from core.models import Organization

from core.serializers.organization import (
    OrganizationListSerializer,
    OrganizationDetailSerializer,
)


class OrganizationList(ListCreateAPIView):
    queryset = Organization().get_all_actives()
    serializer_class = OrganizationListSerializer
    permission_classes = [IsSuperAdminOrReadOnly]


class OrganizationDetail(RetrieveUpdateDestroyAPIView):
    queryset = Organization().get_all_actives()
    serializer_class = OrganizationDetailSerializer
    lookup_field = "uid"
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.kind == "SUPER_ADMIN":
            return Organization().get_all_actives()
        return user.organization

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [(IsAdminUser | IsAuthenticated)()]
        return [
            (IsAdminUser | IsManager | IsSuperAdmin)()
        ]  # Only Admin and Manager can modify customers
