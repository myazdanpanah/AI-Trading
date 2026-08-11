"""ASGI config for crypto_platform project with WebSocket support."""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crypto_platform.settings.base')

# Initialize Django ASGI application early to populate the AppRegistry
django_asgi_app = get_asgi_application()

# Import WebSocket URL patterns after Django setup
from crypto_platform.ws_urls import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
