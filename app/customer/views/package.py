from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.response import Response
from rest_framework.permissions import SAFE_METHODS

from customer.models import Package, Customer
from customer.serializers.package import (
    PackageListSerializer,
    PackageDetailSerializer,
    PackageCustomerSerializer,
)

from customer.serializers.customer import CustomerListSerializer
from core.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAdminUser,
    IsAdminUserOrReadOnly,
    IsManager,
    IsStaff,
)


class PackageList(ListCreateAPIView):
    """API view to list and create packages."""

    queryset = Package().get_all_actives()
    serializer_class = PackageListSerializer
    permission_classes = [IsAdminUser | IsManager | IsStaff]

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [(IsAdminUser | IsManager | IsStaff)()]


class PackageDetail(RetrieveUpdateDestroyAPIView):
    """API view to retrieve, update, or delete a package."""

    queryset = Package().get_all_actives()
    serializer_class = PackageDetailSerializer
    permission_classes = [IsAdminUser | IsManager | IsStaff]
    lookup_field = "uid"

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        elif self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAdminUser()]
        return [(IsAdminUser | IsManager)()]


class PackageCustomerList(ListAPIView):
    """API view to list customers of a package."""

    serializer_class = CustomerListSerializer
    permission_classes = [IsAdminUser | IsManager | IsStaff]

    def get_queryset(self):
        uid = self.kwargs.get("uid")
        queryset = Customer().get_all_actives().filter(package__uid=uid)
        return queryset
