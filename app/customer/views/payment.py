from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from core.permissions import (
    IsAdminUser,
    IsAuthenticated,
    IsAdminUserOrReadOnly,
    IsManager,
    IsStaff,
    AllowAny,
)
from customer.models import Payment
from customer.serializers.payment import (
    PaymentListSerializer,
    PaymentDetailSerializer,
)


class PaymentsList(ListCreateAPIView):
    # queryset = Payment().get_all_actives()
    serializer_class = PaymentListSerializer
    permission_classes = [IsAdminUser | IsManager | IsStaff]

    def get_queryset(self):
        queryset = Payment().get_all_actives()
        customer_name = self.request.query_params.get("customer_name", None)
        customer_phone = self.request.query_params.get("customer_phone", None)
        if customer_phone:
            queryset = (
                Payment().get_all_actives().filter(customer__phone=customer_phone)
            )

        if customer_name:
            queryset = queryset.filter(customer__name__icontains=customer_name)
        return queryset


class PaymentDetail(RetrieveUpdateDestroyAPIView):
    queryset = Payment().get_all_actives()
    serializer_class = PaymentDetailSerializer
    permission_classes = [IsAdminUser | IsManager | IsStaff]
    lookup_field = "uid"
