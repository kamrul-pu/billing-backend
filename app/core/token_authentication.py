"""Custom Authentication Class."""

from datetime import datetime, timedelta, timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from jwt.exceptions import (
    InvalidTokenError,
    ExpiredSignatureError,
)
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt

User = get_user_model()


class JWTAuthentication(BaseAuthentication):
    """Custom authentication class using JSON Web Tokens (JWT)."""

    ACCESS_TOKEN_LIFETIME = timedelta(days=7)  # 7 days for access token
    REFRESH_TOKEN_LIFETIME = timedelta(days=30)  # 30 days for refresh token

    def authenticate(self, request):
        """
        Authenticate the request based on the provided JWT token.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            tuple: (user, None) if authentication succeeds, None if it fails.
        """
        token = self.extract_token(request)
        if not token:
            return None

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            self.verify_token(payload)

            # Verify token type
            if payload.get("token_type") != "access":
                raise AuthenticationFailed("Invalid token type")

            user = User.objects.get(id=payload["id"])
            return (user, None)
        except (InvalidTokenError, ExpiredSignatureError, User.DoesNotExist) as e:
            raise AuthenticationFailed(str(e))

    def verify_token(self, payload):
        """
        Verify the JWT token's expiration and type.

        Args:
            payload (dict): The decoded JWT payload.

        Raises:
            InvalidTokenError: If token has no expiration or invalid type.
            ExpiredSignatureError: If token has expired.
        """
        if "exp" not in payload:
            raise InvalidTokenError("Token has no expiration")

        exp_timestamp = payload["exp"]
        current_timestamp = datetime.now(timezone.utc).timestamp()

        if current_timestamp > exp_timestamp:
            raise ExpiredSignatureError("Token has expired")

    def extract_token(self, request):
        """
        Extract JWT token from Authorization header.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            str: The JWT token or None if not found.
        """
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]
        return None

    @classmethod
    def generate_tokens(cls, user_data):
        """
        Generate both access and refresh tokens.

        Args:
            user_data (dict): User data to include in the token.

        Returns:
            tuple: (access_token, refresh_token, access_exp, refresh_exp)
        """
        # Generate access token
        access_exp = datetime.now(timezone.utc) + cls.ACCESS_TOKEN_LIFETIME
        access_payload = {
            **user_data,
            "exp": int(access_exp.timestamp()),
            "token_type": "access",
        }
        access_token = jwt.encode(
            access_payload, settings.SECRET_KEY, algorithm="HS256"
        )

        # Generate refresh token
        refresh_exp = datetime.now(timezone.utc) + cls.REFRESH_TOKEN_LIFETIME
        refresh_payload = {
            "id": user_data["id"],
            "exp": int(refresh_exp.timestamp()),
            "token_type": "refresh",
        }
        refresh_token = jwt.encode(
            refresh_payload, settings.SECRET_KEY, algorithm="HS256"
        )

        return (
            access_token,
            refresh_token,
            int(access_exp.timestamp()),
            int(refresh_exp.timestamp()),
        )

    @classmethod
    def refresh_access_token(cls, refresh_token):
        """
        Generate new access token using refresh token.

        Args:
            refresh_token (str): The refresh token to verify.

        Returns:
            tuple: (new_access_token, access_exp)

        Raises:
            AuthenticationFailed: If refresh token is invalid.
        """
        try:
            # Verify refresh token
            payload = jwt.decode(
                refresh_token, settings.SECRET_KEY, algorithms=["HS256"]
            )

            if payload.get("token_type") != "refresh":
                raise AuthenticationFailed("Invalid token type")

            # Get user data
            user = User.objects.get(id=payload["id"])
            user_data = {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "email": user.email,
                "kind": user.kind,
            }

            # Generate new access token
            access_exp = datetime.now(timezone.utc) + cls.ACCESS_TOKEN_LIFETIME
            access_payload = {
                **user_data,
                "exp": int(access_exp.timestamp()),
                "token_type": "access",
            }

            access_token = jwt.encode(
                access_payload, settings.SECRET_KEY, algorithm="HS256"
            )

            return access_token, int(access_exp.timestamp())

        except (InvalidTokenError, ExpiredSignatureError, User.DoesNotExist) as e:
            raise AuthenticationFailed(str(e))
