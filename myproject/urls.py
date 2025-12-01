"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from utils.views_extra import ensure_csrf
from myproject.admin import admin_site

# Serve media files without requiring authentication
from django.views.static import serve
from django.http import HttpResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
import os
import re

@csrf_exempt
def serve_media(request, path):
    """Serve media files directly from disk without requiring authentication"""
    try:
        import mimetypes
        from django.http import FileResponse
        
        file_path = os.path.join(settings.MEDIA_ROOT, path)
        
        # Security: prevent directory traversal
        if not os.path.abspath(file_path).startswith(os.path.abspath(settings.MEDIA_ROOT)):
            return HttpResponse('Access Denied', status=403)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return HttpResponse('File not found', status=404)
        
        # Verify it's a file and not a directory
        if not os.path.isfile(file_path):
            return HttpResponse('Not a file', status=400)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Determine correct MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # Open file in binary mode and serve directly from disk
        # FileResponse streams the file without loading it entirely into memory
        file_obj = open(file_path, 'rb')
        response = FileResponse(file_obj, content_type=mime_type)
        
        # Get original filename for download
        filename = os.path.basename(file_path)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = str(file_size)
        response['Access-Control-Allow-Origin'] = '*'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        
        return response
    except Exception as e:
        print(f'[serve_media] Error: {str(e)}')
        return HttpResponse(f'File not found: {path}', status=404)

urlpatterns = [
    # Media files MUST come first so they match before admin catch-all
    path('media/<path:path>', serve_media, name='media'),
    
    # CSRF helper endpoint - both /api/csrf/ and /api/utils/csrf/ work
    path('api/csrf/', ensure_csrf, name='api-csrf'),
    path('api/auth/', include('accounts.urls')),
    # Backwards-compatible endpoint used by frontend for member lookup
    path('api/accounts/', include('accounts.urls')),
    path('api/community/', include('community.urls')),
    path('api/homepagecommunity/', include('homepagecommunity.urls')),
    path('api/magazine/', include('magazine.api_urls')),
    path('api/utils/', include('utils.urls')),
    path('api/courses/', include('courses.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/newsletter/', include('newsletter.urls')),
    path('api/promotions/', include('promotions.urls')),
    path('api/summit/', include('summit.urls')),
    path('api/tv/', include('tv.urls')),
    # Keep admin URLs last so they don't override API endpoints
    path('', admin_site.urls),
]
