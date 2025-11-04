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
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from utils.views_extra import ensure_csrf

urlpatterns = [
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
    # Keep admin URLs last so they don't override API endpoints
    path('admin/', admin.site.urls),

]

# Serve media files without requiring authentication
from django.views.static import serve
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@permission_classes([AllowAny])
def serve_media(request, path):
    """Serve media files directly without requiring authentication"""
    return serve(request, path, document_root=settings.MEDIA_ROOT, show_indexes=False)

# Add media serving URLs
urlpatterns += [
    path('media/<path:path>', serve_media, name='media'),
]
