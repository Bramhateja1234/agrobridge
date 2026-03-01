from .base import *
from decouple import config
import dj_database_url
import os

DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')
if not any(ALLOWED_HOSTS):
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.onrender.com']

# Ensure the Render hostname is always included
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# CSRF Security for Render
CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    print("✅ DATABASE_URL found. Connecting to PostgreSQL...")
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    print("⚠️ DATABASE_URL not found! Falling back to SQLite (Data will not persist).")
    # Fallback for build phase only
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "build.sqlite3",
        }
    }

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
