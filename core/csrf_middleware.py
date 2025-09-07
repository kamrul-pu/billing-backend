import re
from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware


class CSRFExemptMiddleware:
    """
    Middleware to exempt API endpoints from CSRF protection.
    This is needed for APIs that use JWT authentication instead of session-based auth.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.csrf_exempt_urls = getattr(settings, 'CSRF_EXEMPT_URLS', [])
        
    def __call__(self, request):
        # Check if the current URL should be exempt from CSRF
        if self._is_csrf_exempt(request.path):
            setattr(request, '_dont_enforce_csrf_checks', True)
        
        response = self.get_response(request)
        return response
    
    def _is_csrf_exempt(self, path):
        """Check if the given path should be exempt from CSRF protection."""
        for pattern in self.csrf_exempt_urls:
            if re.match(pattern, path):
                return True
        return False


class CustomCsrfViewMiddleware(CsrfViewMiddleware):
    """
    Custom CSRF middleware that respects the CSRF exemption settings.
    """
    
    def process_view(self, request, callback, callback_args, callback_kwargs):
        # If CSRF is exempt for this URL, skip CSRF validation
        if getattr(request, '_dont_enforce_csrf_checks', False):
            return None
        
        return super().process_view(request, callback, callback_args, callback_kwargs)
