"""Views for Users."""

from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView


from rest_framework.generics import (
    CreateAPIView,
    ListCreateAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
)

# from rest_framework.permissions import (
#     # IsAdminUser,
#     # IsAuthenticated,
#     # AllowAny,
# )

from core.token_authentication import JWTAuthentication
from core.serializers.user import (
    UserListSerializer,
    UserDetailSerializer,
    UserRegistrationSerializer,
    MeSerializer,
    LoginSerializer,
    UserPasswordForceResetSerializer,
    ForgetPasswordSerializer,
    ChangePasswordSerializer,
)
from core.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAdminUser,
    IsManager,
    IsStaff,
)
from core.choices import UserKind, OTPType
from core.models import OTP
from core.utils import generate_unique_otp
from common.helpers import SMS

User = get_user_model()


class UserList(ListCreateAPIView):
    permission_classes = (IsAdminUser | IsManager | IsStaff,)
    serializer_class = UserListSerializer
    queryset = User().get_all_actives()

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.is_superuser:
            return User().get_all_actives()
        elif (
            self.request.user.kind == UserKind.ADMIN
            or self.request.user.kind == UserKind.MANAGER
        ):
            return (
                User()
                .get_all_actives()
                .filter(organization_id=self.request.user.organization_id)
            )
        return User().get_all_actives().filter(id=self.request.user.id)


class UserDetail(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAdminUser | IsManager,)
    serializer_class = UserDetailSerializer
    queryset = User().get_all_actives()
    lookup_field = "uid"

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.is_superuser:
            return User().get_all_actives()
        elif (
            self.request.user.kind == UserKind.ADMIN
            or self.request.user.kind == UserKind.MANAGER
        ):
            return (
                User()
                .get_all_actives()
                .filter(organization_id=self.request.user.organization_id)
            )
        return User().get_all_actives().filter(id=self.request.user.id)


class ForceResetUserPassword(APIView):
    permission_classes = (IsAdminUser,)
    serializer_class = UserPasswordForceResetSerializer

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.is_superuser:
            return User().get_all_actives()
        return (
            User()
            .get_all_actives()
            .filter(organization_id=self.request.user.organization_id)
        )

    def post(self, request, uid):
        try:
            user = self.get_queryset().get(uid=uid)
        except User.DoesNotExist:
            return Response(
                {"message": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            password = serializer.validated_data["password"]
            user.set_password(password)
            user.save()
            return Response(
                {"message": "Password has been reset successfully."},
                status=status.HTTP_200_OK,
            )


class UserForgetPassword(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ForgetPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data.get("phone")
        otp = serializer.validated_data.get("otp")
        new_password = serializer.validated_data.get("password")

        try:
            user = User.objects.get(phone=phone, is_active=True)
        except User.DoesNotExist:
            return Response(
                {"message": "User with the provided phone number does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # CASE 1: Requesting new OTP
        if not otp:
            five_minutes_ago = timezone.now() - timedelta(minutes=5)
            existing_otp = OTP.objects.filter(
                user=user,
                otp_type=OTPType.PASSWORD_RESET,
                is_used=False,
                created_at__gte=five_minutes_ago,
            ).exists()

            if existing_otp:
                return Response(
                    {
                        "message": "You already have an active OTP. Please wait for it to expire."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Generate and save OTP
            code = generate_unique_otp()
            OTP.objects.create(
                user=user,
                code=code,
                otp_type=OTPType.PASSWORD_RESET,
            )

            # Send SMS (uncomment when integrated)
            # send_sms(user.phone, f"Your OTP is {code}")
            SMS.send_single_sms(
                to=user.phone,
                message=f"Your OTP for password reset is {code}. It is valid for 5 minutes.",
            )

            return Response(
                {
                    "message": "OTP has been sent to your phone number.",
                    "code": "OTP_SENT",
                },
                status=status.HTTP_200_OK,
            )

        # CASE 2: Verifying OTP & Resetting password
        try:
            otp_record = OTP.objects.get(
                user=user,
                code=otp,
                is_used=False,
                otp_type=OTPType.PASSWORD_RESET,
            )
        except OTP.DoesNotExist:
            return Response(
                {"message": "Invalid OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if timezone.now() > otp_record.created_at + timedelta(minutes=5):
            return Response(
                {"message": "OTP has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # OTP valid: reset password
        user.set_password(new_password)
        user.save(update_fields=["password"])

        otp_record.is_used = True
        otp_record.save(update_fields=["is_used"])

        return Response(
            {"message": "Password reset successfully."},
            status=status.HTTP_200_OK,
        )


class ChangeUserPassword(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            old_password = serializer.validated_data["old_password"]
            new_password = serializer.validated_data["new_password"]

            user = request.user
            if not user.check_password(old_password):
                return Response(
                    {"message": "Old password is incorrect."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(new_password)
            user.save()
            return Response(
                {"message": "Password has been changed successfully."},
                status=status.HTTP_200_OK,
            )


class UserRegistration(CreateAPIView):
    permission_classes = (IsAdminUser | IsManager | IsStaff,)
    serializer_class = UserRegistrationSerializer
    queryset = User().get_all_actives()


class MeDetail(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MeSerializer

    # def get_object(self):
    #     return self.request.user
    def get(self, request, *args, **kwargs):
        user_id = request.user.id
        user = (
            User()
            .get_all_actives()
            .filter(id=user_id)
            .select_related("organization")
            .first()
        )

        serializer = self.serializer_class(user)
        return Response(serializer.data)


class UserLogin(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user_data = serializer.validated_data
            # Create token payload with user data
            token_payload = user_data.copy()

            access_token, refresh_token, access_exp, refresh_exp = (
                JWTAuthentication.generate_tokens(token_payload)
            )

            return Response(
                {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "access_token_exp": access_exp,
                    "refresh_token_exp": refresh_exp,
                    "user": user_data,
                },
                status=status.HTTP_200_OK,
            )


class UserLoginRefresh(APIView):
    """View for refreshing access token."""

    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"message": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            access_token, access_exp = JWTAuthentication.refresh_access_token(
                refresh_token
            )

            return Response(
                {"access_token": access_token, "access_token_exp": access_exp},
                status=status.HTTP_200_OK,
            )

        except AuthenticationFailed as e:
            return Response({"message": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
