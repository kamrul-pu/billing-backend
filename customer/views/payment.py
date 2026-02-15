from collections import defaultdict
from django.db.models import Q
from django.utils import timezone
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from core.permissions import (
    IsAdminUser,
    IsManager,
    IsStaff,
    IsAuthenticated
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
        if not self.request.user.organization_id:
            return Payment.objects.none()
        queryset = (
            Payment()
            .get_all_actives()
            .filter(organization_id=self.request.user.organization_id)
            .select_related("customer", "entry_by")
        )

        # Text search filters
        # Individual filters
        paid = self.request.query_params.get("paid", None)
        customer_name = self.request.query_params.get("customer_name", None)
        customer_phone = self.request.query_params.get("customer_phone", None)
        collected_by = self.request.query_params.get("collected_by", None)
        month = self.request.query_params.get("month", None)
        year = self.request.query_params.get("year", None)
        payment_method = self.request.query_params.get("payment_method", None)
        payment_date = self.request.query_params.get("payment_date", None)

        # Apply filters
        if paid:
            paid = paid.lower() == "true"
            queryset = queryset.filter(paid=paid)
        if month:
            queryset = queryset.filter(billing_month=month)
        # Year filter: default to current year if not provided
        if year:
            try:
                year = int(year)
                queryset = queryset.filter(billing_year=year)
            except (ValueError, TypeError):
                # If invalid year provided, default to current year
                queryset = queryset.filter(billing_year=timezone.now().year)
        else:
            # Default to current year if year not specified
            queryset = queryset.filter(billing_year=timezone.now().year)
        if collected_by:
            queryset = queryset.filter(
                Q(entry_by__first_name__icontains=collected_by)
                | Q(entry_by__last_name__icontains=collected_by)
            )
        if customer_phone:
            queryset = queryset.filter(customer__phone__icontains=customer_phone)
        if customer_name:
            queryset = queryset.filter(customer__name__icontains=customer_name)
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        if payment_date:
            queryset = queryset.filter(payment_date=payment_date)

        return queryset


class PaymentDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = PaymentDetailSerializer
    permission_classes = []  # Leave empty; we override with `get_permissions`
    lookup_field = "uid"

    def get_permissions(self):
        # Only Admin, Manager, or SuperAdmin can DELETE
        if self.request.method == "DELETE":
            return [IsAdminUser() or IsManager()]

        # Admin, Manager, or Staff can view or update
        return [IsAdminUser() or IsManager() or IsStaff()]

    def get_queryset(self):
        queryset = (
            Payment()
            .get_all_actives()
            .filter(organization_id=self.request.user.organization_id)
            .select_related("customer", "entry_by")
        )

        return queryset


class MonthlyCollectionList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        if not request.user.organization_id:
            return Response({"detail": "Organization not found."}, status=404)

        now = timezone.now()
        first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        monthly_payments = (
            Payment.objects.filter(
                organization_id=request.user.organization_id,
                payment_date__gte=first_day_of_month,
                paid=True,
            )
            .select_related("customer", "entry_by")
        )

        # Group payments by collecting user
        collections_by_user = defaultdict(lambda: {'payments': [], 'total_amount': 0})

        for payment in monthly_payments:
            user_key = (payment.entry_by.id, payment.entry_by.first_name, payment.entry_by.last_name)
            collections_by_user[user_key]['payments'].append({
                'customer_name': payment.customer.name,
                'customer_phone': payment.customer.phone,
                'customer_address': payment.customer.address,
                "bill_amount": payment.bill_amount,
                'amount': payment.amount,
                'payment_date': payment.payment_date.date(),
            })
            collections_by_user[user_key]['total_amount'] += payment.amount

        # Format the response
        result = []
        for (user_id, first_name, last_name), data in collections_by_user.items():
            result.append({
                'user_id': user_id,
                'first_name': first_name,
                'last_name': last_name,
                'total_payments': len(data['payments']),
                'total_amount': data['total_amount'],
                'payments': data['payments']
            })

        return Response({"results": result, "message": "Monthly collections retrieved successfully"}, status=status.HTTP_200_OK)