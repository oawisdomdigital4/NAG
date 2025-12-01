"""
Custom middleware to handle CSRF for token-based authentication.

When a request is authenticated via token (Bearer token in Authorization header),
CSRF validation is skipped since tokens provide their own security.
"""

from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse


class TokenAuthCsrfMiddleware(MiddlewareMixin):
    """
    Middleware that disables CSRF validation for requests authenticated with Bearer tokens.
    
    This is safe because:
    1. Token auth doesn't rely on cookies for cross-origin requests
    2. Tokens are explicitly passed in the Authorization header (not sent automatically by the browser)
    3. Django's CSRF is primarily to prevent cookie-based CSRF attacks
    """
    
    def process_request(self, request):
        # Check if the request has a Bearer token in the Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        print(f"[TokenAuthCsrfMiddleware] process_request called")
        print(f"  Path: {request.path}")
        print(f"  Authorization: {auth_header[:30] if auth_header else 'None'}...")
        
        if auth_header.startswith('Bearer '):
            # Mark this request as exempt from CSRF since it's using token auth
            print(f"  [OK] Bearer token detected, exempting from CSRF")
            request._dont_enforce_csrf_checks = True
        else:
            print(f"  No Bearer token")
        
        return None

    def process_view(self, request, view_func, view_args, view_kwargs):
        if '/api/' in request.path:
            print(f"[TokenAuthCsrfMiddleware] process_view called for {request.path}")
            print(f"  View: {view_func}")
        return None

    def process_response(self, request, response):
        if '/api/' in request.path:
            print(f"[TokenAuthCsrfMiddleware] process_response: {response.status_code}")
            if response.status_code == 302:
                print(f"  Redirect to: {response.get('Location')}")
        return response
