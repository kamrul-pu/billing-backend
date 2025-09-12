from drf_spectacular.extensions import OpenApiAuthenticationExtension


class CustomJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = (
        "core.token_authentication.JWTAuthentication"  # path to your custom class
    )
    name = "BearerAuth"  # This name must match the one used in `SPECTACULAR_SETTINGS['SECURITY']`

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": 'JWT Authorization header using the Bearer scheme. Example: "Bearer <your-token>"',
        }
