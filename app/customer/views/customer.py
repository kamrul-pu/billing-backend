from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView


from core.permissions import (
    IsAdminUser,
    IsAuthenticated,
    IsAdminUserOrReadOnly,
    IsManager,
    IsStaff,
    AllowAny,
)

from customer.models import Customer, Payment
from customer.serializers.customer import (
    CustomerListSerializer,
    CustomerDetailSerializer,
)
from customer.serializers.payment import PaymentListSerializer


class CustomerList(ListCreateAPIView):
    serializer_class = CustomerListSerializer
    permission_classes = [IsAdminUser | IsManager | IsStaff]

    def get_queryset(self):
        queryset = Customer().get_all_actives()
        name: str = self.request.query_params.get("name", None)
        user_id: int = self.request.query_params.get("user_id", None)
        phone = self.request.query_params.get("phone", None)
        package_id = self.request.query_params.get("package_id", None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if phone:
            queryset = queryset.filter(phone=phone)
        if package_id:
            queryset = queryset.filter(package_id=package_id)

        return queryset


class CustomerDetail(RetrieveUpdateDestroyAPIView):
    queryset = Customer().get_all_actives()
    serializer_class = CustomerDetailSerializer
    permission_classes = [IsAdminUser | IsManager | IsStaff]
    lookup_field = "uid"


class CustomerPaymentsList(ListCreateAPIView):
    serializer_class = PaymentListSerializer
    permission_classes = [IsAdminUser | IsManager | IsStaff]

    def get_queryset(self):
        return Payment().get_all_actives().filter(customer__uid=self.kwargs["uid"])
