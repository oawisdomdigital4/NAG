from pathlib import Path
import logging

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-=h5qyq6ims%&1xawe!c(m99n=ns!pql1cuxpij3w+vqpcdh$#_'
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# ----------------------------
# Application Definition
# ----------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'accounts',
    'community',
    'courses',
    'notifications',
    'payments',
    'utils',
    'django_filters',
]

# ----------------------------
# Middleware
# ----------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # Must come first for CORS
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",  # Required for CSRF
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'

# ----------------------------
# Database
# ----------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ----------------------------
# Password Validation
# ----------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ----------------------------
# Internationalization
# ----------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ----------------------------
# Static & Media Files
# ----------------------------
STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
STATICFILES_DIRS = [BASE_DIR / 'static']

# ----------------------------
# Custom User Model
# ----------------------------
AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Prevent Django’s default redirect-to-login on 401 responses
LOGIN_URL = None


# --- REST Framework: Allow any for API, use Session for browsable API only
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

# --- CORS: Allow local dev frontend
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

CSRF_COOKIE_SECURE = False  # Dev only
SESSION_COOKIE_SECURE = False  # Dev only

# ----------------------------
# Frontend Base URL
# ----------------------------
FRONTEND_BASE_URL = "http://localhost:5173"

# ----------------------------
# Debug Logging
# ----------------------------
if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('django.server').setLevel(logging.DEBUG)
    print("✅ Django is running in DEBUG mode with CSRF & session debugging enabled.")

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
