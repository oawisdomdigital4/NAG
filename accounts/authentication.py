# accounts/authentication.py
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from .models import UserToken
from django.utils import timezone
from django.conf import settings


class DatabaseTokenAuthentication(BaseAuthentication):
    """Authenticate using a token stored in the database.

    Accepts headers of the form `Authorization: Bearer <token>` or
    `Authorization: Token <token>` (and generally will take the last
    whitespace-separated segment as the token). If no Authorization
    header is present, returns None so other auth backends can run.
    """

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        token_value = None

        if auth_header:
            # Accept any scheme; take the last space-separated part as the token
            parts = auth_header.split()
            if len(parts) == 0:
                return None
            token_value = parts[-1]
        else:
            # Development-friendly fallback: allow token via query param or X-Auth-Token
            # This is only enabled when DEBUG=True to aid debugging missing/early header races.
            if getattr(settings, 'DEBUG', False):
                # prefer common query param names
                try:
                    token_value = request.GET.get('authToken') or request.GET.get('auth_token')
                except Exception:
                    token_value = None
                if not token_value:
                    token_value = request.headers.get('X-Auth-Token')
            else:
                return None

        # If no token was provided, do not authenticate here; allow other
        # authentication backends to run or allow anonymous access for read-only endpoints.
        if not token_value:
            return None

        try:
            user_token = UserToken.objects.get(token=token_value)
        except UserToken.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid token")

        if user_token.expires_at < timezone.now():
            # Remove expired token and reject
            user_token.delete()
            raise exceptions.AuthenticationFailed("Token expired")

        return (user_token.user, user_token)
