from django.utils import timezone
from django.db.models import Q, Count, Sum

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response


# from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser

from core.permissions import (
    IsAdminUser,
    IsAuthenticated,
    IsAdminUserOrReadOnly,
    IsManager,
    IsStaff,
    AllowAny,
)

from customer.models import Customer, Payment, Package
from customer.serializers.customer import (
    CustomerListSerializer,
    CustomerDetailSerializer,
    StatusToggleSerializer,
)
from customer.serializers.payment import PaymentListSerializer
from customer.utils import toggle_ppp_user


class CustomerList(ListCreateAPIView):
    serializer_class = CustomerListSerializer
    permission_classes = [IsAdminUser | IsManager | IsStaff]

    # def get_permissions(self):
    #     if self.request.method in SAFE_METHODS:
    #         return [(IsAdminUser | IsManager | IsStaff)()]
    #     return [
    #         (IsAdminUser | IsManager)()
    #     ]  # Only Admin and Manager can create customers

    def get_queryset(self):
        queryset = Customer().get_all_actives().select_related("package")
        name: str = self.request.query_params.get("name", None)
        username: str = self.request.query_params.get("username", None)
        user_id: int = self.request.query_params.get("user_id", None)
        phone: str = self.request.query_params.get("phone", None)
        package_id = self.request.query_params.get("package_id", None)
        is_active: bool = self.request.query_params.get("is_active", None)
        is_free: bool = self.request.query_params.get("is_free", None)
        if is_free:
            queryset = queryset.filter(is_free=is_free)
        if username:
            queryset = queryset.filter(username__icontains=username)
        if is_active:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
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
    queryset = Customer().get_all_actives().select_related("package", "user")
    serializer_class = CustomerDetailSerializer
    permission_classes = [IsAdminUser | IsManager | IsStaff]
    lookup_field = "uid"

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [(IsAdminUser | IsManager | IsStaff)()]
        return [
            (IsAdminUser | IsManager)()
        ]  # Only Admin and Manager can modify customers


class CustomerPaymentsList(ListCreateAPIView):
    serializer_class = PaymentListSerializer
    permission_classes = [IsAdminUser | IsManager | IsStaff]

    # def get_permissions(self):
    #     if self.request.method in SAFE_METHODS:
    #         return [(IsAdminUser | IsManager | IsStaff)()]
    #     return [
    #         (IsAdminUser | IsManager)()
    #     ]  # Only Admin and Manager can create payments

    def get_queryset(self):
        return (
            Payment()
            .get_all_actives()
            .filter(customer__uid=self.kwargs["uid"])
            .select_related("customer", "entry_by")
        )


class GenerateBill(APIView):
    """
    Placeholder for GenerateBill API view.
    This can be implemented later as per requirements.
    """

    permission_classes = [IsAdminUser | IsManager]

    def post(self, request, *args, **kwargs):
        month = request.query_params.get("month", timezone.now().strftime("%B").upper())

        # Step 1: Get all active customers
        active_customers = Customer.objects.filter(
            is_active=True, is_free=False, package__price__gt=0
        ).select_related("package")

        # Step 2: Get customer IDs with existing payments for current month
        existing_payments = Payment.objects.filter(billing_month=month)
        paid_customer_ids = set(existing_payments.values_list("customer_id", flat=True))

        # Step 3: Filter customers who haven't been billed
        customers_to_bill = [
            c for c in active_customers if c.id not in paid_customer_ids
        ]

        # Step 4: Create payment records in bulk
        payments_to_create = []
        for customer in customers_to_bill:
            bill_amount = customer.package.price if customer.package else 0.0
            payments_to_create.append(
                Payment(
                    customer=customer,
                    bill_amount=bill_amount,
                    amount=0.0,
                    billing_month=month,
                    payment_method="OTHER",
                    paid=False,
                    note=f"Auto-generated bill for {month}",
                )
            )

        # Bulk create payments
        Payment.objects.bulk_create(payments_to_create)

        return Response(
            {
                "message": f"Billing for {month} processed.",
                "created_payments_count": len(payments_to_create),
                # "payments": payments_to_create,
            }
        )


class Dashboard(APIView):
    """
    Optimized dashboard API returning key metrics and recent activity.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        now = timezone.now()
        current_month = now.strftime("%B").upper()  # e.g., "April"
        # thirty_days_ago = now - timezone.timedelta(days=30)

        # === 1. Aggregated Stats ===
        customer_stats = Customer.objects.aggregate(
            total=Count("id"), active=Count("id", filter=Q(is_active=True))
        )

        package_stats = Package.objects.aggregate(total=Count("id"))

        payment_stats = Payment.objects.aggregate(
            total_paid=Count("id", filter=Q(paid=True)),
            total_amount=Sum("amount", filter=Q(paid=True)),
            pending=Count("id", filter=Q(paid=False)),
            current_month_count=Count(
                "id", filter=Q(paid=True, billing_month=current_month)
            ),
        )

        # === 2. Recent Data ===
        # recent_customers = (
        #     Customer.objects.filter(created_at__gte=thirty_days_ago)
        #     .select_related("package")
        #     .order_by("-created_at")[:10]
        # )

        # recent_payments = (
        #     Payment.objects.filter(paid=True, created_at__gte=thirty_days_ago)
        #     .select_related("customer", "entry_by")
        #     .order_by("-created_at")[:10]
        # )

        # === 3. Response ===
        return Response(
            {
                "total_customers": customer_stats["total"],
                "active_customers": customer_stats["active"],
                "total_packages": package_stats["total"],
                "total_payments": payment_stats["total_paid"],
                "total_revenue": f"{payment_stats['total_amount'] or 0.0:.2f}",
                "pending_payments": payment_stats["pending"],
                "current_month_payments": payment_stats["current_month_count"],
                # "recent_customers": CustomerListSerializer(
                #     recent_customers, many=True
                # ).data,
                # "recent_payments": PaymentListSerializer(
                #     recent_payments, many=True
                # ).data,
            },
            status=status.HTTP_200_OK,
        )


class StatusToggle(APIView):
    """
    API to toggle the status of a customer.
    """

    permission_classes = [IsAdminUser | IsManager]
    serializer_class = StatusToggleSerializer

    def post(self, request, *args, **kwargs):
        serialier = self.serializer_class(data=request.data)
        if not serialier.is_valid():
            return Response(serialier.errors, status=status.HTTP_400_BAD_REQUEST)
        username = serialier.validated_data.get("username")
        is_active = serialier.validated_data.get("is_active")

        customer = Customer.objects.filter(username=username).first()
        if not customer:
            return Response(
                {"error": "Customer not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        customer.is_active = is_active
        success, message = toggle_ppp_user(username, not is_active)
        if not success:
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

        customer.save(update_fields=["is_active"])

        return Response({"message": message}, status=status.HTTP_200_OK)
