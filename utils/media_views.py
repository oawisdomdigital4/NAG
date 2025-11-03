from django.views.static import serve
from django.http import HttpResponse
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes, api_view

@api_view(['GET'])
@permission_classes([AllowAny])
def serve_media(request, path):
    """Serve media files without requiring authentication"""
    return serve(request, path, document_root=settings.MEDIA_ROOT)