"""Custom exception handler for consistent error responses."""

from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, APIException


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns errors in consistent format:
    {"message": "error message"} with proper status codes.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # If response is None, it's an unhandled exception
    if response is None:
        if isinstance(exc, Exception):
            return Response(
                {"message": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return response

    # Customize the response data
    if isinstance(exc, ValidationError):
        # Handle ValidationError - check if it already has message format
        if isinstance(response.data, dict):
            # If the error is already in {"message": "..."} format, use it
            if "message" in response.data:
                message = response.data["message"]
                # Handle case where message might be a list
                if isinstance(message, list):
                    message = message[0] if message else "Validation error"
                return Response(
                    {"message": message},
                    status=response.status_code,
                )
            # Otherwise, extract the first error message
            error_message = None
            for key, value in response.data.items():
                if isinstance(value, list) and value:
                    error_message = value[0]
                    break
                elif isinstance(value, dict):
                    # Nested validation errors - get first value
                    if value:
                        nested_values = list(value.values())
                        if nested_values:
                            nested_msg = nested_values[0]
                            if isinstance(nested_msg, list) and nested_msg:
                                error_message = nested_msg[0]
                            else:
                                error_message = str(nested_msg)
                            break
                elif value is not None:
                    error_message = str(value)
                    break

            if error_message:
                return Response(
                    {"message": error_message},
                    status=response.status_code,
                )
            # Fallback if no message found
            return Response(
                {"message": "Validation error"},
                status=response.status_code,
            )
        elif isinstance(response.data, list):
            # If response.data is a list, use the first item
            return Response(
                {"message": response.data[0] if response.data else "Validation error"},
                status=response.status_code,
            )

    # Handle APIException (includes AuthenticationFailed, PermissionDenied, etc.)
    if isinstance(exc, APIException):
        # Check if detail is already a dict with message
        if isinstance(exc.detail, dict):
            if "message" in exc.detail:
                message = exc.detail["message"]
                # Handle case where message might be a list
                if isinstance(message, list):
                    message = message[0] if message else str(exc)
                return Response(
                    {"message": message},
                    status=exc.status_code,
                )
            # If dict but no message key, try to extract first value
            if exc.detail:
                first_value = list(exc.detail.values())[0]
                if isinstance(first_value, list) and first_value:
                    return Response(
                        {"message": first_value[0]},
                        status=exc.status_code,
                    )
                return Response(
                    {"message": str(first_value)},
                    status=exc.status_code,
                )
        elif isinstance(exc.detail, list):
            # If detail is a list, use first item
            return Response(
                {"message": exc.detail[0] if exc.detail else str(exc)},
                status=exc.status_code,
            )
        else:
            # Detail is a string or other type
            error_message = str(exc.detail) if hasattr(exc, "detail") and exc.detail else str(exc)
            return Response(
                {"message": error_message},
                status=exc.status_code,
            )

    # For other exceptions, format the response
    if isinstance(response.data, dict):
        if "message" in response.data:
            return response
        # Try to extract a meaningful error message
        error_message = None
        for key, value in response.data.items():
            if isinstance(value, list):
                error_message = value[0] if value else "An error occurred"
            else:
                error_message = str(value)
            break

        if error_message:
            return Response(
                {"message": error_message},
                status=response.status_code,
            )

    # Default fallback
    return Response(
        {"message": "An error occurred"},
        status=response.status_code,
    )

