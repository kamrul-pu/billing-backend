"""Customer Authentication Class."""

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from datetime import datetime, timezone

from customer.models import Customer


class CustomerJWTAuthentication(BaseAuthentication):
    """Custom authentication class for customers using JSON Web Tokens (JWT)."""

    ACCESS_TOKEN_LIFETIME = 7 * 24 * 60 * 60  # 7 days in seconds
    REFRESH_TOKEN_LIFETIME = 30 * 24 * 60 * 60  # 30 days in seconds

    def authenticate(self, request):
        """
        Authenticate the request based on the provided JWT token.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            tuple: (customer, None) if authentication succeeds, None if it fails.
        """
        token = self.extract_token(request)
        if not token:
            return None

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            self.verify_token(payload)

            # Verify token type
            if payload.get("token_type") != "customer_access":
                raise AuthenticationFailed("Invalid token type")

            customer = Customer.objects.get(id=payload["customer_id"])
            if not customer.is_active:
                raise AuthenticationFailed("Customer account is inactive")

            # Set request.customer for easy access in views
            request.customer = customer
            return (customer, None)
        except (InvalidTokenError, ExpiredSignatureError, Customer.DoesNotExist) as e:
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
    def generate_tokens(cls, customer_data):
        """
        Generate both access and refresh tokens for customer.

        Args:
            customer_data (dict): Customer data to include in the token.

        Returns:
            tuple: (access_token, refresh_token, access_exp, refresh_exp)
        """
        from datetime import timedelta

        # Generate access token
        access_exp = datetime.now(timezone.utc) + timedelta(seconds=cls.ACCESS_TOKEN_LIFETIME)
        access_payload = {
            **customer_data,
            "exp": int(access_exp.timestamp()),
            "token_type": "customer_access",
        }
        access_token = jwt.encode(
            access_payload, settings.SECRET_KEY, algorithm="HS256"
        )

        # Generate refresh token
        refresh_exp = datetime.now(timezone.utc) + timedelta(seconds=cls.REFRESH_TOKEN_LIFETIME)
        refresh_payload = {
            "customer_id": customer_data["customer_id"],
            "exp": int(refresh_exp.timestamp()),
            "token_type": "customer_refresh",
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

            if payload.get("token_type") != "customer_refresh":
                raise AuthenticationFailed("Invalid token type")

            # Get customer data
            customer = Customer.objects.get(id=payload["customer_id"])
            if not customer.is_active:
                raise AuthenticationFailed("Customer account is inactive")

            customer_data = {
                "customer_id": customer.id,
                "customer_uid": str(customer.uid),
                "name": customer.name,
                "phone": customer.phone,
                "email": customer.email,
            }

            # Generate new access token
            from datetime import timedelta
            access_exp = datetime.now(timezone.utc) + timedelta(seconds=cls.ACCESS_TOKEN_LIFETIME)
            access_payload = {
                **customer_data,
                "exp": int(access_exp.timestamp()),
                "token_type": "customer_access",
            }

            access_token = jwt.encode(
                access_payload, settings.SECRET_KEY, algorithm="HS256"
            )

            return access_token, int(access_exp.timestamp())

        except (InvalidTokenError, ExpiredSignatureError, Customer.DoesNotExist) as e:
            raise AuthenticationFailed(str(e))

