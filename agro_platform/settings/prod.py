from .base import *
from decouple import config
import dj_database_url
import os

DEBUG = os.getenv("DEBUG", "False") == "True"
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-me-in-production")

# Trust Render/Railway hostname and any custom domains
ALLOWED_HOSTS = ['*']

# CSRF & CORS Security for Render
CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']
CORS_ALLOWED_ORIGINS = ['https://*.onrender.com']

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')

if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')
    CORS_ALLOWED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')

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
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True
    )
}

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
