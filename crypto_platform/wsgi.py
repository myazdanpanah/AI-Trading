"""WSGI config for crypto_platform project."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crypto_platform.settings.production')
application = get_wsgi_application()
