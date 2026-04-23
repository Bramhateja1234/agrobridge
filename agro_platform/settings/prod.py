from .base import *
from decouple import config
import dj_database_url
import os

DEBUG = os.getenv("DEBUG", "False") == "True"
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-me-in-production")

# Trust Render/Railway hostname and any custom domains
ALLOWED_HOSTS = ['*']

# CSRF & CORS Security for Railway
CSRF_TRUSTED_ORIGINS = ['https://*.up.railway.app']
CORS_ALLOWED_ORIGINS = ['https://*.up.railway.app']

RAILWAY_STATIC_URL = os.environ.get('RAILWAY_STATIC_URL')

if RAILWAY_STATIC_URL:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RAILWAY_STATIC_URL}')
    CORS_ALLOWED_ORIGINS.append(f'https://{RAILWAY_STATIC_URL}')

# HTTPS/SSL Settings for Proxy (Render)
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False

# Static files (WhiteNoise)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MANIFEST_STRICT = False

DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600
    )
}

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
