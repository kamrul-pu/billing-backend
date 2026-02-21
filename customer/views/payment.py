from collections import defaultdict
from django.db.models import Q
from django.utils import timezone
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from core.permissions import IsAdminUser, IsManager, IsStaff, IsAuthenticated
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

        start_date = self.request.query_params.get("start_date", None)
        end_date = self.request.query_params.get("end_date", None)
        if not start_date:
            start_date = timezone.now().date().replace(day=1)
        else:
            try:
                if len(start_date) > 10:
                    start_date = timezone.datetime.fromisoformat(start_date).date()
                else:
                    start_date = timezone.datetime.strptime(
                        start_date, "%Y-%m-%d"
                    ).date()
            except (ValueError, TypeError):
                start_date = timezone.now().date().replace(day=1)
        if not end_date:
            end_date = timezone.now().date()
        else:
            try:
                if len(end_date) > 10:
                    end_date = timezone.datetime.fromisoformat(end_date).date()
                else:
                    end_date = timezone.datetime.strptime(end_date, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                end_date = timezone.now().date()
        queryset = (
            Payment()
            .get_all_actives()
            .filter(
                organization_id=self.request.user.organization_id,
            )
            .filter(
                Q(
                    payment_date__date__gte=start_date,
                    payment_date__date__lte=end_date,
                )
                | Q(
                    payment_date__isnull=True,
                )
            )
            .order_by("-payment_date")
            .distinct()
            .select_related("customer", "entry_by")
        )

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

        # Get query parameters
        user_id = request.query_params.get("user_id", None)
        start_date = request.query_params.get("start_date", None)
        end_date = request.query_params.get("end_date", None)

        now = timezone.now()

        # Determine date range
        if start_date:
            try:
                # Support both YYYY-MM-DD and full ISO format
                if len(start_date) > 10:
                    start_date = timezone.datetime.fromisoformat(start_date).date()
                else:
                    start_date = timezone.datetime.strptime(
                        start_date, "%Y-%m-%d"
                    ).date()
            except (ValueError, TypeError):
                start_date = now.date().replace(day=1)
        else:
            start_date = now.date().replace(day=1)

        if end_date:
            try:
                if len(end_date) > 10:
                    end_date = timezone.datetime.fromisoformat(end_date).date()
                else:
                    end_date = timezone.datetime.strptime(end_date, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                end_date = now.date()
        else:
            end_date = now.date()

        # Base filter - Using __date lookup to filter strictly on the date portion
        filters = Q(
            organization_id=request.user.organization_id,
            payment_date__date__range=(start_date, end_date),
            paid=True,
        )

        # Optional user filter
        if user_id:
            try:
                filters &= Q(entry_by_id=int(user_id))
            except (ValueError, TypeError):
                pass

        monthly_payments = Payment.objects.filter(filters).select_related(
            "customer", "entry_by"
        )

        # Group payments by collecting user
        collections_by_user = defaultdict(lambda: {"payments": [], "total_amount": 0})

        for payment in monthly_payments:
            user_key = (
                payment.entry_by.id,
                payment.entry_by.first_name,
                payment.entry_by.last_name,
            )
            collections_by_user[user_key]["payments"].append(
                {
                    "customer_name": payment.customer.name,
                    "customer_phone": payment.customer.phone,
                    "customer_address": payment.customer.address,
                    "bill_amount": payment.bill_amount,
                    "amount": payment.amount,
                    "payment_date": payment.payment_date.date(),
                }
            )
            collections_by_user[user_key]["total_amount"] += payment.amount

        # Format the response
        result = []
        for (user_id, first_name, last_name), data in collections_by_user.items():
            result.append(
                {
                    "user_id": user_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "total_payments": len(data["payments"]),
                    "total_amount": data["total_amount"],
                    "payments": data["payments"],
                }
            )

        return Response(
            {
                "results": result,
                "message": "Monthly collections retrieved successfully",
            },
            status=status.HTTP_200_OK,
        )
