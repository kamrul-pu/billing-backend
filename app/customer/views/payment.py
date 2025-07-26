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
    queryset = Payment().get_all_actives()
    serializer_class = PaymentListSerializer
    permission_classes = [IsAdminUser | IsManager | IsStaff]


class PaymentDetail(RetrieveUpdateDestroyAPIView):
    queryset = Payment().get_all_actives()
    serializer_class = PaymentDetailSerializer
    permission_classes = [IsAdminUser | IsManager | IsStaff]
    lookup_field = "uid"
