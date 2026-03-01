"""ASGI config for agro_platform project."""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agro_platform.settings.prod')
application = get_asgi_application()
