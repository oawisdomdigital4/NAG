import os
import socket
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment detection
HOSTNAME = socket.gethostname()
# Detect PythonAnywhere: hostname may not contain 'pythonanywhere' on all runtimes,
# so also check known environment variables that PA sets when running web apps.
ON_PYTHONANYWHERE = (
    "pythonanywhere" in HOSTNAME
    or "newafricagroup" in HOSTNAME
    or bool(os.environ.get("PYTHONANYWHERE_DOMAIN"))
    or bool(os.environ.get("PYTHONANYWHERE_USERNAME"))
)

# Load local settings if not in production. If `local_settings.py` is missing,
# prefer to continue and allow configuration via environment variables.
if not ON_PYTHONANYWHERE:
    # Try a few common local settings filenames so development machines can
    # use either `local_settings.py` or `local_dev_settings.py` without
    # editing the main settings file. If neither exists, fall back to
    # environment variables and sensible defaults below.
    try:
        from .local_settings import *
    except ImportError:
        try:
            from .local_dev_settings import *
        except ImportError:
            # No local settings file found; leave it to environment vars.
            # Ensure DEBUG has a default value to avoid NameError later.
            DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('1', 'true', 'yes')
else:
    # Production settings
    DEBUG = False
    SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-=h5qyq6ims%&1xawe!c(m99n=ns!pql1cuxpij3w+vqpcdh$#_')

    # Add production hostnames here (your custom domain and pythonanywhere hostname)
    ALLOWED_HOSTS = [
        'newafricagroup.pythonanywhere.com',
        'superadmin.thenewafricagroup.com',
        'myproject-zeta-indol.vercel.app',
    ]

    # Production database: prefer DATABASE_URL if provided (e.g., managed DB URL),
    # otherwise fall back to the PythonAnywhere MySQL credentials.
    if os.environ.get('DATABASE_URL'):
        try:
            import dj_database_url
            DATABASES = {
                'default': dj_database_url.parse(os.environ['DATABASE_URL'], conn_max_age=600),
            }
        except Exception:
            # If dj_database_url is not available or parsing fails, keep a safe fallback
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.mysql',
                    'NAME': os.environ.get('DB_NAME', 'mrokaimoses$default'),
                    'USER': os.environ.get('DB_USER', 'mrokaimoses'),
                    'PASSWORD': os.environ.get('DB_PASSWORD', '@Nag123456'),
                    'HOST': os.environ.get('DB_HOST', 'mrokaimoses.mysql.pythonanywhere-services.com'),
                    'PORT': os.environ.get('DB_PORT', '3306'),
                }
            }
    else:
        DATABASES = {
            'default': {
                    'ENGINE': 'django.db.backends.mysql',
                    'NAME': os.environ.get('DB_NAME', 'mrokaimoses$default'),
                    'USER': os.environ.get('DB_USER', 'mrokaimoses'),
                    'PASSWORD': os.environ.get('DB_PASSWORD', '@Nag123456'),
                    'HOST': os.environ.get('DB_HOST', 'mrokaimoses.mysql.pythonanywhere-services.com'),
                    'PORT': os.environ.get('DB_PORT', '3306'),
                }
        }

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
    'homepagecommunity',
    'notifications',
    'payments',
    'utils',
    'magazine',
    'newsletter',
    'promotions',
    'summit',
    'tv',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # ← add this line here
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'myproject.middleware.TokenAuthCsrfMiddleware',  # ← bypass CSRF for token auth
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'myproject.urls'
WSGI_APPLICATION = 'myproject.wsgi.application'

# Database settings are loaded from local_settings.py in development
# or set above in production environment

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

STATIC_URL = '/static/'
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
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # PythonAnywhere Media Settings
    MEDIA_ROOT = '/home/mrokaimoses/Nag/media'
    MEDIA_URL = '/media/'

else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# In production we want the CSRF and session cookies usable by a cross-site
# frontend (e.g. a Vercel app). Browsers require SameSite=None plus Secure
# for third-party cookies; keep these guarded to production only.
if ON_PYTHONANYWHERE:
    CSRF_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SAMESITE = 'None'


# CORS settings
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'https://superadmin.thenewafricagroup.com',
    'https://www.superadmin.thenewafricagroup.com',
    'https://thenewafricagroup.com',
    'https://127.0.0.1:8000',
    'https://myproject-zeta-indol.vercel.app',
]
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:5173',
    'https://superadmin.thenewafricagroup.com',
    'https://www.superadmin.thenewafricagroup.com',
    'https://thenewafricagroup.com',
    'https://127.0.0.1:8000',
    'https://myproject-zeta-indol.vercel.app',
]

# Additional CORS settings
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-auth-token',
    'cache-control',
    'access-control-allow-origin',
    'access-control-allow-headers'
]

CORS_ALLOW_CREDENTIALS = True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'testserver',
    'superadmin.thenewafricagroup.com',
    'www.superadmin.thenewafricagroup.com',
    'thenewafricagroup.com',
    'myproject-zeta-indol.vercel.app',
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

# Ensure DEBUG is always defined (local_settings may not set it when imported)
if 'DEBUG' not in globals():
    DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('1', 'true', 'yes')

if DEBUG:
    REST_FRAMEWORK.setdefault("DEFAULT_RENDERER_CLASSES", [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ])
else:
    REST_FRAMEWORK.setdefault("DEFAULT_RENDERER_CLASSES", [
        "rest_framework.renderers.JSONRenderer",
    ])

# Use local memory cache for development
# This is a simple caching backend that doesn't require any external services
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,  # Maximum number of cache entries
            'CULL_FREQUENCY': 3,  # Fraction of entries to cull when max is reached
        }
    }
}

# Use database-backed sessions for reliability and persistence across page refreshes
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Keep users logged in for 7 days in the admin site
SESSION_COOKIE_AGE = 7 * 24 * 60 * 60  # 7 days in seconds (604800)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Don't expire when browser closes
SESSION_SAVE_EVERY_REQUEST = True  # Save on every request to ensure persistence

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
    "site_title": "",
    "site_header": "",
    "site_brand": "",
    "site_logo": "admin/img/logo.png",
    "show_sidebar_logo": False,  # Hide from sidebar
    "site_brand_classes": "nag-header-logo-container",  # for positioning in navbar
    "site_logo_classes": "nag-logo",
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
        "homepagecommunity": "fas fa-globe",
        "courses": "fas fa-book",
        "notifications": "fas fa-bell",
        "payments": "fas fa-credit-card",
        "utils": "fas fa-cogs",
        "magazine": "fas fa-book",
        "newsletter": "fas fa-envelope-open",
        "promotions": "fas fa-bullhorn",
        "summit": "fas fa-mountain",
        "tv": "fas fa-tv",

        # accounts models
        "accounts.user": "fas fa-user-circle",
        "accounts.userprofile": "fas fa-id-badge",
        "accounts.usertoken": "fas fa-key",
        "accounts.otpverification": "fas fa-hourglass-half",

        # homepagecommunity models
        "homepagecommunity.herosection": "fas fa-image",
        "homepagecommunity.aboutcommunitymission": "fas fa-lightbulb",
        "homepagecommunity.communityfeature": "fas fa-star",
        "homepagecommunity.subscriptiontier": "fas fa-crown",
        "homepagecommunity.subscriptionbenefit": "fas fa-gift",
        "homepagecommunity.testimonial": "fas fa-quote-left",
        "homepagecommunity.finalcta": "fas fa-rocket",
        "homepagecommunity.communitymetrics": "fas fa-chart-bar",

        # community models
        "community.post": "fas fa-sticky-note",
        "community.comment": "fas fa-comment",
        "community.group": "fas fa-layer-group",
        "community.groupinvite": "fas fa-envelope-open-text",
        "community.communitysection": "fas fa-layer-group",
        "community.ctabanner": "fas fa-bullhorn",
        "community.corporateconnection": "fas fa-handshake",
        "community.corporateopportunity": "fas fa-lightbulb",
        "community.opportunityapplication": "fas fa-file-alt",
        "community.collaborationrequest": "fas fa-people-arrows",
        "community.corporateverification": "fas fa-building",
        "community.communitysectionadmin": "fas fa-users",
        "community.communityengagementlog": "fas fa-history",
        "community.mentionlog": "fas fa-at",
        "community.userreputation": "fas fa-trophy",
        "community.userengagementscore": "fas fa-fire",
        "community.subscriptiontier": "fas fa-crown",
        "community.sponsoredpost": "fas fa-star",
        "community.trendingtopic": "fas fa-chart-line",
        "community.platformanalytics": "fas fa-chart-bar",
        "community.engagementnotification": "fas fa-bell",

        # courses models
        "courses.course": "fas fa-book-open",
        "courses.coursemodule": "fas fa-layer-group",
        "courses.coursereview": "fas fa-star",
        "courses.enrollment": "fas fa-user-graduate",
        "courses.lesson": "fas fa-book",
        "courses.quizquestion": "fas fa-question-circle",
        "courses.quizsubmission": "fas fa-check-square",
        "courses.assignmentsubmission": "fas fa-file-alt",
        "courses.analyticssettings": "fas fa-cog",
        "courses.facilitatortarget": "fas fa-bullseye",
        "courses.analyticsreport": "fas fa-file-chart-line",

        # notifications models
        "notifications.notification": "fas fa-envelope",
        "notifications.notificationpreference": "fas fa-sliders-h",

        # payments models
        "payments.payment": "fas fa-credit-card",
        "payments.subscription": "fas fa-calendar-check",
        "payments.plan": "fas fa-list-alt",

        # promotions models
        "promotions.sponsorcampaign": "fas fa-bullhorn",
        "promotions.campaignanalytics": "fas fa-chart-line",
        "promotions.promotionmetrics": "fas fa-chart-bar",
        "promotions.withdrawalrequest": "fas fa-money-bill-wave",
        "promotions.facilitatorearning": "fas fa-dollar-sign",

        # magazine models
        "magazine.author": "fas fa-user",
        "magazine.category": "fas fa-folder",
        "magazine.tag": "fas fa-tag",
        "magazine.article": "fas fa-newspaper",
        "magazine.magazine": "fas fa-book",

        # newsletter models
        "newsletter.newslettersubscriber": "fas fa-envelope-open",

        # summit models
        "summit.organizer": "fas fa-user-tie",
        "summit.featuredspeaker": "fas fa-microphone",
        "summit.partner": "fas fa-handshake",
        "summit.pastedition": "fas fa-history",
        "summit.summithero": "fas fa-image",
        "summit.summitabout": "fas fa-info-circle",
        "summit.summitkeythemes": "fas fa-lightbulb",
        "summit.summitagenda": "fas fa-calendar",
        "summit.summitagendaday": "fas fa-clock",
        "summit.partnersection": "fas fa-users",
        "summit.registrationpackage": "fas fa-ticket-alt",

        # tv models
        "tv.videocategory": "fas fa-film",
        "tv.video": "fas fa-play-circle",

        # utils models
        "utils.abouthero": "fas fa-image",
        "utils.faq": "fas fa-question-circle",
        "utils.career": "fas fa-briefcase",
        "utils.contactmessage": "fas fa-envelope",
        "utils.contactdetails": "fas fa-address-book",
        "utils.officelocation": "fas fa-map-marker-alt",
        "utils.departmentcontact": "fas fa-address-card",
        "utils.footercontent": "fas fa-shoe-prints",
        "utils.teammember": "fas fa-user-tie",
    },
}

# ============================================================================
# EMAIL CONFIGURATION - Mailjet
# ============================================================================
# Use Django's built-in SMTP backend with Mailjet credentials
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# Use provided Mailjet credentials directly (should be stored in environment in production)
MAILJET_API_KEY = os.environ.get('MAILJET_API_KEY', 'f378fb1358a57d5e6aba848d75f4a38c')
MAILJET_SECRET_KEY = os.environ.get('MAILJET_SECRET_KEY', '8dd1624c61c9cc168773252797cc8793')
MAILJET_FROM_EMAIL = os.environ.get('MAILJET_FROM_EMAIL', 'no-reply@thenewafricagroup.com')
MAILJET_FROM_NAME = 'The New Africa Group'

# Django email settings (Mailjet SMTP configuration)
EMAIL_HOST = 'in-v3.mailjet.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = MAILJET_API_KEY
EMAIL_HOST_PASSWORD = MAILJET_SECRET_KEY
DEFAULT_FROM_EMAIL = MAILJET_FROM_EMAIL
SERVER_EMAIL = MAILJET_FROM_EMAIL
