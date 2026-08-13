"""ASGI config for crypto_platform project."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crypto_platform.settings.local')
django.setup()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from crypto_platform.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
