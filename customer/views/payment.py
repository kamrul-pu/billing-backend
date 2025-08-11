from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import SAFE_METHODS

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
    serializer_class = PaymentListSerializer
    permission_classes = [IsAdminUser | IsManager | IsStaff]

    # def get_permissions(self):
    #     if self.request.method in SAFE_METHODS:
    #         return [(IsAdminUser | IsManager | IsStaff)()]
    #     return [
    #         (IsAdminUser | IsManager)()
    # ]  # Only Admin and Manager can create payments

    def get_queryset(self):
        paid: bool = self.request.query_params.get("paid", None)
        queryset = Payment().get_all_actives().select_related("customer", "entry_by")
        customer_name = self.request.query_params.get("customer_name", None)
        customer_phone = self.request.query_params.get("customer_phone", None)
        collected_by = self.request.query_params.get("collected_by", None)
        month = self.request.query_params.get("month", None)
        if paid:
            paid = paid.lower() == "true"
            queryset = queryset.filter(paid=paid)
        if month:
            queryset = queryset.filter(billing_month=month)
        if collected_by:
            queryset = queryset.filter(entry_by__first_name__icontains=collected_by)
        if customer_phone:
            queryset = (
                Payment().get_all_actives().filter(customer__phone=customer_phone)
            )

        if customer_name:
            queryset = queryset.filter(customer__name__icontains=customer_name)
        return queryset


class PaymentDetail(RetrieveUpdateDestroyAPIView):
    queryset = Payment().get_all_actives().select_related("customer", "entry_by")
    serializer_class = PaymentDetailSerializer
    permission_classes = []  # Leave empty; we override with `get_permissions`
    lookup_field = "uid"

    def get_permissions(self):
        # Only Admin, Manager, or SuperAdmin can DELETE
        if self.request.method == "DELETE":
            return [IsAdminUser() or IsManager()]

        # Admin, Manager, or Staff can view or update
        return [IsAdminUser() or IsManager() or IsStaff()]
