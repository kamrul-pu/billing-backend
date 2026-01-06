"""Jwt schema extension for swagger"""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class CustomJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """Override OpenApiAuthenticationExtension"""

    target_class = (
        "core.token_authentication.JWTAuthentication"  # path to your custom class
    )
    name = "BearerAuth"  # This name must match the one used in `SPECTACULAR_SETTINGS['SECURITY']`

    def get_security_definition(self, auto_schema):
        """
        Docstring for get_security_definition

        :param self: Description
        :param auto_schema: Description
        """
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": 'Example: "Bearer <your-token>"',
        }
