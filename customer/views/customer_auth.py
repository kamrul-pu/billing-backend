"""Customer Authentication and Self-Service Views."""

import uuid
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed

from core.permissions import AllowAny
from customer.permissions import IsCustomer
from customer.authentication import CustomerJWTAuthentication
from customer.models import Customer, Payment
from customer.serializers.customer import (
    CustomerLoginSerializer,
    CustomerProfileSerializer,
)
from customer.serializers.payment import PaymentListSerializer, PaymentDetailSerializer
from customer.helpers.bkash import BKashPayment
from customer.choices import PaymentMethod
from core.choices import BillingCycle


class CustomerLogin(APIView):
    """View for customer login."""

    permission_classes = [AllowAny]
    serializer_class = CustomerLoginSerializer

    def post(self, request):
        serializer = CustomerLoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            customer_data = serializer.validated_data
            # Create token payload with customer data
            token_payload = customer_data.copy()

            access_token, refresh_token, access_exp, refresh_exp = (
                CustomerJWTAuthentication.generate_tokens(token_payload)
            )

            return Response(
                {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "access_token_exp": access_exp,
                    "refresh_token_exp": refresh_exp,
                    "customer": customer_data,
                },
                status=status.HTTP_200_OK,
            )


class CustomerLoginRefresh(APIView):
    """View for refreshing customer access token."""

    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"message": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            access_token, access_exp = CustomerJWTAuthentication.refresh_access_token(
                refresh_token
            )

            return Response(
                {"access_token": access_token, "access_token_exp": access_exp},
                status=status.HTTP_200_OK,
            )

        except AuthenticationFailed as e:
            return Response({"message": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class CustomerProfile(RetrieveAPIView):
    """View for customer to see their own profile."""

    permission_classes = [IsCustomer]
    authentication_classes = [CustomerJWTAuthentication]
    serializer_class = CustomerProfileSerializer

    def get_object(self):
        """Return the authenticated customer."""
        return self.request.customer


class CustomerPaymentsList(ListAPIView):
    """View for customer to see their own payments."""

    permission_classes = [IsCustomer]
    authentication_classes = [CustomerJWTAuthentication]
    serializer_class = PaymentListSerializer

    def get_queryset(self):
        """Return payments for the authenticated customer."""
        customer = self.request.customer
        queryset = (
            Payment()
            .get_all_actives()
            .filter(customer=customer)
            .select_related("customer", "entry_by")
            .order_by("-created_at")
        )

        # Optional filters
        paid = self.request.query_params.get("paid", None)
        month = self.request.query_params.get("month", None)
        year = self.request.query_params.get("year", None)

        if paid is not None:
            paid = paid.lower() == "true"
            queryset = queryset.filter(paid=paid)
        if month:
            queryset = queryset.filter(billing_month=month)
        if year:
            try:
                year = int(year)
                queryset = queryset.filter(billing_year=year)
            except (ValueError, TypeError):
                queryset = queryset.filter(billing_year=timezone.now().year)
        else:
            queryset = queryset.filter(billing_year=timezone.now().year)

        return queryset


class CustomerPaymentDetail(RetrieveAPIView):
    """View for customer to see a specific payment detail."""

    permission_classes = [IsCustomer]
    authentication_classes = [CustomerJWTAuthentication]
    serializer_class = PaymentDetailSerializer
    lookup_field = "uid"

    def get_queryset(self):
        """Return payments for the authenticated customer only."""
        customer = self.request.customer
        return (
            Payment()
            .get_all_actives()
            .filter(customer=customer)
            .select_related("customer", "entry_by")
        )


class CustomerCreatePayment(APIView):
    """View for customer to create a payment via bKash."""

    permission_classes = [IsCustomer]
    authentication_classes = [CustomerJWTAuthentication]

    @transaction.atomic
    def post(self, request):
        """
        Create a payment request via bKash.

        Expected payload:
        {
            "payment_uid": "uid-of-unpaid-payment",  # Optional: if paying existing bill
            "amount": 1000.00,  # Required: payment amount
            "billing_month": "JANUARY",  # Optional: for monthly billing
            "billing_year": 2024  # Optional: defaults to current year
        }
        """
        customer = request.customer
        payment_uid = request.data.get("payment_uid")
        amount = request.data.get("amount")
        billing_month = request.data.get("billing_month", "")
        billing_year = request.data.get("billing_year", timezone.now().year)

        if not amount:
            return Response(
                {"message": "Amount is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                raise ValueError("Amount must be greater than 0")
        except (ValueError, TypeError):
            return Response(
                {"message": "Invalid amount"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        organization = customer.organization
        if not organization:
            return Response(
                {"message": "Customer does not belong to any organization"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if paying existing payment
        payment = None
        if payment_uid:
            try:
                payment = Payment.objects.get(
                    uid=payment_uid,
                    customer=customer,
                    paid=False,
                )
                if payment.paid:
                    return Response(
                        {"message": "This payment has already been paid"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except Payment.DoesNotExist:
                return Response(
                    {"message": "Payment not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Generate unique invoice number
        merchant_invoice_number = f"INV-{customer.id}-{uuid.uuid4().hex[:8].upper()}-{int(timezone.now().timestamp())}"

        # Initialize bKash payment
        bkash = BKashPayment()
        success, result = bkash.create_payment(
            amount=float(amount),
            merchant_invoice_number=merchant_invoice_number,
        )

        if not success:
            return Response(
                {"message": "Failed to create payment request", "error": result.get("error")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Create or update payment record
        if payment:
            # Update existing payment
            payment.amount = amount
            payment.payment_method = PaymentMethod.BKASH
            payment.transaction_id = result.get("payment_id", "")
            payment.note = f"bKash payment initiated - Payment ID: {result.get('payment_id')}"
            payment.save(
                update_fields=["amount", "payment_method", "transaction_id", "note"]
            )
        else:
            # Create new payment record
            bill_amount = customer.package.price if customer.package else Decimal("0.00")
            payment = Payment.objects.create(
                organization=organization,
                customer=customer,
                bill_amount=bill_amount,
                amount=amount,
                billing_month=billing_month,
                billing_year=billing_year,
                payment_method=PaymentMethod.BKASH,
                paid=False,
                transaction_id=result.get("payment_id", ""),
                note=f"bKash payment initiated - Payment ID: {result.get('payment_id')}",
            )

        return Response(
            {
                "message": "Payment request created successfully",
                "payment_uid": str(payment.uid),
                "bkash_payment_id": result.get("payment_id"),
                "redirect_url": result.get("redirect_url"),
                "amount": str(amount),
            },
            status=status.HTTP_200_OK,
        )


class BKashPaymentCallback(APIView):
    """View to handle bKash payment callback and verify payment."""

    permission_classes = [AllowAny]  # bKash will call this endpoint

    def post(self, request):
        """
        Handle bKash payment callback.

        Expected payload from bKash:
        {
            "paymentID": "payment-id-from-bkash",
            "status": "success" or "failure"
        }
        """
        payment_id = request.data.get("paymentID")
        status_param = request.data.get("status")

        if not payment_id:
            return Response(
                {"message": "Payment ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Query payment from bKash
        bkash = BKashPayment()
        success, result = bkash.query_payment(payment_id)

        if not success:
            return Response(
                {"message": "Failed to verify payment", "error": result.get("error")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Find payment record by transaction_id
        try:
            payment = Payment.objects.get(transaction_id=payment_id, paid=False)
        except Payment.DoesNotExist:
            return Response(
                {"message": "Payment record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if payment was successful
        transaction_status = result.get("transaction_status", "").upper()
        if transaction_status == "COMPLETED":
            # Mark payment as paid
            payment.paid = True
            payment.payment_date = timezone.now()
            payment.transaction_id = result.get("bkash_trx_id", payment_id)
            payment.note = f"bKash payment completed - Transaction ID: {result.get('bkash_trx_id')}"
            payment.save(update_fields=["paid", "payment_date", "transaction_id", "note"])

            # Activate customer if fully paid and currently inactive
            customer = payment.customer
            if not customer.is_active:
                customer.is_active = True
                customer.save(update_fields=["is_active"])

            # Handle subscription extension for day-based billing
            organization = payment.organization
            if organization and organization.billing_cycle == BillingCycle.DAYS30:
                from datetime import timedelta
                bill_amount = customer.package.price if customer.package else Decimal("0.00")
                paid_months = int(payment.amount // bill_amount) if bill_amount > 0 else 1
                extend_days = paid_months * 30

                last_end = customer.subscription_end_date
                today = timezone.now().date()

                if last_end and last_end > today:
                    new_end = last_end + timedelta(days=extend_days)
                else:
                    new_end = today + timedelta(days=extend_days)

                customer.subscription_end_date = new_end
                customer.save(update_fields=["subscription_end_date"])

            return Response(
                {
                    "message": "Payment verified and completed successfully",
                    "payment_uid": str(payment.uid),
                    "transaction_id": result.get("bkash_trx_id"),
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "message": "Payment verification failed",
                    "status": transaction_status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class CustomerVerifyPayment(APIView):
    """View for customer to manually verify a payment status."""

    permission_classes = [IsCustomer]
    authentication_classes = [CustomerJWTAuthentication]

    def post(self, request):
        """
        Verify payment status from bKash.

        Expected payload:
        {
            "payment_id": "payment-id-from-bkash"
        }
        """
        payment_id = request.data.get("payment_id")
        if not payment_id:
            return Response(
                {"message": "Payment ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        customer = request.customer

        # Find payment record
        try:
            payment = Payment.objects.get(transaction_id=payment_id, customer=customer)
        except Payment.DoesNotExist:
            return Response(
                {"message": "Payment record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Query payment from bKash
        bkash = BKashPayment()
        success, result = bkash.query_payment(payment_id)

        if not success:
            return Response(
                {"message": "Failed to verify payment", "error": result.get("error")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        transaction_status = result.get("transaction_status", "").upper()
        if transaction_status == "COMPLETED" and not payment.paid:
            # Update payment status
            payment.paid = True
            payment.payment_date = timezone.now()
            payment.transaction_id = result.get("bkash_trx_id", payment_id)
            payment.note = f"bKash payment verified - Transaction ID: {result.get('bkash_trx_id')}"
            payment.save(update_fields=["paid", "payment_date", "transaction_id", "note"])

            # Activate customer if needed
            if not payment.customer.is_active:
                payment.customer.is_active = True
                payment.customer.save(update_fields=["is_active"])

        return Response(
            {
                "payment_uid": str(payment.uid),
                "paid": payment.paid,
                "transaction_status": transaction_status,
                "amount": str(payment.amount),
            },
            status=status.HTTP_200_OK,
        )

