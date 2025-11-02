# from core.views import organization


from rest_framework import status
from rest_framework.views import APIView


from rest_framework.response import Response

from core.permissions import IsAdminUser, IsManager, AllowAny

from customer.tasks import (
    generate_customer_bills,
    deactivate_due_payment_customers,
    generate_organizations_bills,
    deactivate_organizations_due_payment_customers,
    deactivate_all_organizations_expired_subscription_customers,
)


class GenerateBillTask(APIView):
    permission_classes = [IsAdminUser | IsManager]

    def get(self, request, *args, **kwargs):
        user = request.user
        organization = request.user.organization
        if not organization:
            return Response(
                {"message": "This user doesn't belongs to any organization"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            not organization.router_ip
            or not organization.router_username
            or not organization.router_password
        ):
            return Response(
                {"message": "Organization MikroTik router details are not configured."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        generate_customer_bills.delay(user.organization_id)
        # generate_customer_bills(user.organization_id)
        return Response(
            {"message": "Customer bills generation backgroud Task started!"},
            status=status.HTTP_200_OK,
        )


class DeactiveDueCustomer(APIView):
    permission_classes = [IsAdminUser | IsManager]

    def get(self, request, *args, **kwargs):
        user = request.user
        organization = request.user.organization or None
        if not organization:
            return Response(
                {"message": "This user doesn't belongs to any organization"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if (
            not organization.router_ip
            or not organization.router_username
            or not organization.router_password
        ):
            return Response(
                {"message": "Organization MikroTik router details are not configured."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        deactivate_due_payment_customers.delay(user.organization_id)
        # deactivate_due_payment_customers(user.organization_id)
        return Response(
            {"message": "Deactivate due customers backgroud Task started!"},
            status=status.HTTP_200_OK,
        )


class GenerateOrganizationsBillTask(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        generate_organizations_bills.delay()
        # generate_organizations_bills()
        return Response(
            {"message": "Organizations bills generation backgroud Task started!"},
            status=status.HTTP_200_OK,
        )


class DeactiveOrganizationsDueCustomer(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        deactivate_organizations_due_payment_customers.delay()
        # deactivate_organizations_due_payment_customers()
        return Response(
            {
                "message": "Deactivate organizations due customers backgroud Task started!"
            },
            status=status.HTTP_200_OK,
        )


class DeactiveExpiredSubscriptionCustomer(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        deactivate_all_organizations_expired_subscription_customers.delay()
        return Response(
            {
                "message": "Deactivate expired subscription customers backgroud Task started!"
            },
            status=status.HTTP_200_OK,
        )
