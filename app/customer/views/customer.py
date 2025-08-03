from django.utils import timezone


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

from customer.models import Customer, Payment
from customer.serializers.customer import (
    CustomerListSerializer,
    CustomerDetailSerializer,
)
from customer.serializers.payment import PaymentListSerializer


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

    def post(self, request, *args, **kwargs):
        month = request.query_params.get("month", timezone.now().strftime("%B").upper())
        print(" Month:", month)

        # Step 1: Get all active customers
        active_customers = Customer.objects.filter(is_active=True).select_related(
            "package"
        )

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
