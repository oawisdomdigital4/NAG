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
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def serve_media(request, path):
    """Serve media files directly without requiring authentication"""
    try:
        response = serve(request, path, document_root=settings.MEDIA_ROOT, show_indexes=False)
        response['Access-Control-Allow-Origin'] = '*'  # Allow CORS for media files
        response['Cache-Control'] = 'public, max-age=31536000'  # Cache for 1 year
        return response
    except Exception as e:
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
