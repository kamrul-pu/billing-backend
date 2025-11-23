"""Middleware to set request.customer from authenticated customer."""


class CustomerAuthenticationMiddleware:
    """Middleware to set request.customer from authenticated customer."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set request.customer if user is a Customer instance
        if hasattr(request, "user") and hasattr(request.user, "__class__"):
            from customer.models import Customer
            # Check if user is actually a Customer instance
            if isinstance(request.user, Customer):
                request.customer = request.user
            else:
                request.customer = None
        else:
            request.customer = None

        response = self.get_response(request)
        return response

