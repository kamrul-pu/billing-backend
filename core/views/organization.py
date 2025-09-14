from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework import status
from core.permissions import (
    IsSuperAdminOrReadOnly,
    IsAuthenticated,
    IsAdminUser,
    IsManager,
    IsSuperAdmin,
)
from customer.helpers import Mikrotik
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




class CustomerSessionList(APIView):
    permission_classes = [IsAdminUser | IsManager]

    def get(self, request, *args, **kwargs):
        print("API CALLED")
        organization = request.user.organization
        print("Organizaton: ", organization.router_ip, organization.router_username, organization.router_password)
        if not organization:
            return Response({"error": "Organization not found."}, status=status.HTTP_404_NOT_FOUND)
        if not organization.router_ip or not organization.router_username or not organization.router_password:
            return Response({"error": "Mikrotik credentials not found."}, status=status.HTTP_404_NOT_FOUND)
        success, sessions = Mikrotik.get_user_sessions(organization)
        if not success:
            return Response({"error": sessions}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"sessions": sessions}, status=status.HTTP_200_OK)