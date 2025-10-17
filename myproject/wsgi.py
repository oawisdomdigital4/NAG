"""
WSGI config for myproject project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import mimetypes

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# Ensure .webp files are served with the correct MIME type. Some Python
# installations don't include the WebP mapping by default which can cause
# static/media files to be returned as 'application/octet-stream'. That
# combined with 'X-Content-Type-Options: nosniff' prevents browsers from
# rendering the images. Register the mapping before creating the WSGI app.
mimetypes.add_type('image/webp', '.webp')

application = get_wsgi_application()
