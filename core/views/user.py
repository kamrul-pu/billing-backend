"""Views for Users."""

from django.contrib.auth import get_user_model

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
)
from core.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAdminUser,
    IsAdminUserOrReadOnly,
    IsManager,
    IsStaff,
)

User = get_user_model()


class UserList(ListCreateAPIView):
    permission_classes = (IsAdminUser | IsManager | IsStaff,)
    serializer_class = UserListSerializer
    queryset = User().get_all_actives()


class UserDetail(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAdminUser | IsManager,)
    serializer_class = UserDetailSerializer
    queryset = User().get_all_actives()
    lookup_field = "uid"


class UserRegistration(CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer
    queryset = User().get_all_actives()


class MeDetail(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user


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
