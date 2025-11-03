from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

# This module provides proxy viewsets that expose community-managed contact
# data under the /api/utils/ namespace so existing frontend pages continue
# to work without changing their endpoints.

class ContactDetailsViewSet(viewsets.ReadOnlyModelViewSet):
    """Return the latest published ContactDetails instance (from community app)

    Falls back to an empty response if community.ContactDetails is not available.
    """
    permission_classes = [AllowAny]

    def get_queryset(self):
        try:
            from community.models import ContactDetails
            return ContactDetails.objects.filter(is_published=True).order_by('-created_at')
        except Exception:
            return []

    def get_serializer_class(self):
        try:
            from community.serializers import ContactDetailsSerializer
            return ContactDetailsSerializer
        except Exception:
            return None

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if not qs:
            return Response({}, status=200)
        obj = qs.first()
        serializer_class = self.get_serializer_class()
        if not serializer_class:
            return Response({}, status=200)
        serializer = serializer_class(obj, context={'request': request})
        return Response(serializer.data)


    @ensure_csrf_cookie
    def ensure_csrf(request):
        """Lightweight endpoint that ensures the CSRF cookie is set.

        Frontends should GET this endpoint with credentials included before
        POSTing to session-protected endpoints. It returns a small JSON
        payload and sets the csrftoken cookie via Django's middleware.
        """
        return JsonResponse({"csrf": "set"})
