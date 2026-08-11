"""ASGI config for crypto_platform project."""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crypto_platform.settings.production')
application = get_asgi_application()
