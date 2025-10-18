import os
import socket
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-=h5qyq6ims%&1xawe!c(m99n=ns!pql1cuxpij3w+vqpcdh$#_'

HOSTNAME = socket.gethostname()
ON_PYTHONANYWHERE = "pythonanywhere" in HOSTNAME or "newafricagroup" in HOSTNAME

DEBUG = not ON_PYTHONANYWHERE

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'newafricagroup.pythonanywhere.com',
]

INSTALLED_APPS = [
    'jazzmin',
    'corsheaders',  # ← add this line (must come before others that use it)
    'rest_framework',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Your custom apps
    'accounts',
    'community',
    'courses',
    'notifications',
    'payments',
    'utils',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # ← add this line here
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'myproject.urls'
WSGI_APPLICATION = 'myproject.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'newafricagroup$nag2',
        'USER': 'newafricagroup',
        'PASSWORD': '@Nag123456',
        'HOST': 'newafricagroup.mysql.pythonanywhere-services.com',
        'PORT': '3306',
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

WSGI_APPLICATION = 'myproject.wsgi.application'
ASGI_APPLICATION = 'myproject.asgi.application'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# Ensure Font Awesome and other Jazzmin assets load properly
JAZZMIN_UI_TWEAKS = {
    "theme": "cosmo",
}


if ON_PYTHONANYWHERE:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'https://newafricagroup.pythonanywhere.com',
    'https://myproject-zeta-indol.vercel.app',
]

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    'https://newafricagroup.pythonanywhere.com',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'https://myproject-zeta-indol.vercel.app',
]


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'

# Django REST Framework config: Browsable API only in DEBUG, JSON in prod
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.authentication.DatabaseTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

if DEBUG:
    REST_FRAMEWORK.setdefault("DEFAULT_RENDERER_CLASSES", [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ])
else:
    REST_FRAMEWORK.setdefault("DEFAULT_RENDERER_CLASSES", [
        "rest_framework.renderers.JSONRenderer",
    ])

# Safety: patch DRF's JSON encoder to defensively decode bytes using replacement
# characters instead of raising UnicodeDecodeError. This prevents 500s when
# corrupted binary data slips into serializer output. We still keep serializer
# sanitizers and a DB scan command; this is a last-resort safety net.
try:
    from rest_framework.utils import encoders as _drf_encoders
    import json as _json

    class SafeDRFJSONEncoder(_drf_encoders.JSONEncoder):
        def default(self, obj):
            # Handle raw byte-like objects safely by decoding with replacement
            try:
                if isinstance(obj, (bytes, bytearray, memoryview)):
                    try:
                        return bytes(obj).decode('utf-8', errors='replace')
                    except Exception:
                        return bytes(obj).decode('latin-1', errors='replace')
            except Exception:
                pass
            # Fallback to parent implementation; if it raises UnicodeDecodeError,
            # coerce to string to avoid blowing up the whole response.
            try:
                return super().default(obj)
            except UnicodeDecodeError:
                try:
                    return str(obj)
                except Exception:
                    return ''

    # Monkeypatch DRF's encoder used by JSONRenderer
    _drf_encoders.JSONEncoder = SafeDRFJSONEncoder
except Exception:
    # If DRF isn't importable in this environment, skip the patch silently.
    pass




JAZZMIN_SETTINGS = {
    "site_title": "New Africa Group Admin",
    "site_header": "New Africa Group",
    "site_brand": "NAG",
    "site_logo": "admin/img/logo.png",
    "site_logo_classes": "img-fluid nag-logo",  # 👈 Add custom class for styling
    "welcome_sign": "Welcome to New Africa Group Admin",
    "copyright": "© 2025 New Africa Group",
    "show_ui_builder": False,

    "theme": "cosmo",
    "custom_css": "admin/css/custom-theme.css",

    "navigation_expanded": True,
    "topmenu_links": [
        {"name": "Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},
    ],

    "icons": {
        # app-level icons
        "auth": "fas fa-users-cog",
        "auth.group": "fas fa-users",
        "accounts": "fas fa-user",
        "community": "fas fa-users",
        "courses": "fas fa-book",
        "notifications": "fas fa-bell",
        "payments": "fas fa-credit-card",
        "utils": "fas fa-cogs",

        # accounts models
        "accounts.user": "fas fa-user-circle",
        "accounts.userprofile": "fas fa-id-badge",
        "accounts.usertoken": "fas fa-key",
        "accounts.follow": "fas fa-user-friends",

        # community models
        "community.organizer": "fas fa-user-tie",
        "community.featuredspeaker": "fas fa-microphone",
        "community.partner": "fas fa-handshake",
        "community.pastedition": "fas fa-history",
        "community.userprofile": "fas fa-id-card-alt",
        "community.course": "fas fa-book-open",
        "community.enrollment": "fas fa-user-graduate",
        "community.group": "fas fa-layer-group",
        "community.groupmembership": "fas fa-user-plus",
        "community.post": "fas fa-sticky-note",
        "community.postattachment": "fas fa-paperclip",
        "community.postbookmark": "fas fa-bookmark",
        "community.comment": "fas fa-comment",
        "community.postreaction": "fas fa-heart",
        "community.commentreaction": "fas fa-thumbs-up",
        "community.plan": "fas fa-list-alt",
        "community.subscription": "fas fa-receipt",
        "community.payment": "fas fa-wallet",
        "community.corporateverification": "fas fa-building",
        "community.chatroom": "fas fa-comments",
        "community.message": "fas fa-comment-dots",

        # courses models
        "courses.course": "fas fa-book-open",
        "courses.coursemodule": "fas fa-layer-group",
        "courses.coursereview": "fas fa-star",
        "courses.enrollment": "fas fa-user-graduate",

        # notifications models
        "notifications.notification": "fas fa-envelope",
        "notifications.notificationpreference": "fas fa-sliders-h",

        # payments models
        "payments.plan": "fas fa-list",
        "payments.subscription": "fas fa-calendar-check",
        "payments.payment": "fas fa-credit-card",

        # utils models
        "utils.faq": "fas fa-question-circle",
        "utils.teammember": "fas fa-user-tie",
        "utils.career": "fas fa-briefcase",
        "utils.contactmessage": "fas fa-envelope",
    },
}
