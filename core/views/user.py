"""Views for Users."""

from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import SAFE_METHODS

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
    IsAdminUserOrReadOnly,
    IsManager,
    IsStaff,
)
from core.choices import UserKind, OTPType
from core.models import OTP
from core.utils import generate_unique_otp

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
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
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
        if serializer.is_valid(raise_exception=True):
            phone = serializer.validated_data.get("phone", None)
            new_password = serializer.validated_data.get("password", None)
            otp = serializer.validated_data.get("otp", None)

            try:
                # Check if a user with the provided phone number exists
                user = User().get_all_actives().get(phone=phone)
            except User.DoesNotExist:
                return Response(
                    {"detail": "Person with the provided phone number does not exist."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if not otp:
                # Check if there is an existing OTP created in the last 5 minutes
                five_minutes_ago = timezone.now() - timedelta(minutes=5)
                existing_otp = OTP.objects.filter(
                    user_id=user.id,
                    type=OTPType.PASSWORD_RESET,
                    is_used=False,
                    created_at__gte=five_minutes_ago,
                ).exists()

                if existing_otp:
                    # User already has a valid OTP created in the last 5 minutes
                    return Response(
                        {
                            "detail": "You already have an OTP. Please wait for the message."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                else:
                    # Generate a new OTP and send it to the user's phone
                    otp = generate_unique_otp()
                    OTP.objects.create(
                        user_id=user.id, otp=otp, type=OTPType.PASSWORD_RESET
                    )
                    # sending sms
                    # message = f"Your otp is {otp}."
                    # send_sms(user.phone_number, message)

                    # Return a response indicating that OTP will be sent to the user's phone
                    return Response(
                        {"detail": "OTP has sent to your phone number.", "code": "OTP"},
                        status=status.HTTP_200_OK,
                    )

            elif new_password:
                try:
                    # Verify the OTP provided by the user
                    otp_record = OTP.objects.get(
                        user_id=user.id,
                        otp=otp,
                        is_used=False,
                        type=OTPType.PASSWORD_RESET,
                    )
                except OTP.DoesNotExist:
                    return Response(
                        {"detail": "Invalid OTP."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if timezone.now() < (otp_record.created_at + timedelta(minutes=5)):
                    # Update the user's password
                    # user.password = make_password(new_password)
                    user.set_password(new_password)
                    user.save(update_fields=["password"])

                    # Mark the OTP as used
                    otp_record.is_used = True
                    otp_record.save(update_fields=["is_used"])

                    return Response(
                        {"detail": "Password reset successfully done"},
                        status=status.HTTP_200_OK,
                    )

                else:
                    return Response(
                        {"detail": "OTP has expired."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                return Response(
                    {"detail": "Please provide new password and confirm password"},
                    status=status.HTTP_400_BAD_REQUEST,
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
                    {"error": "Old password is incorrect."},
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

        serializer = self.serializer_class(request.user)
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
                {"error": "Refresh token is required"},
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
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
