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
    queryset = Customer().get_all_actives()
    serializer_class = CustomerListSerializer
    permission_classes = [IsAdminUser | IsManager | IsStaff]


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
