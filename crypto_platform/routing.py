"""WebSocket routing for live price feeds."""
from django.urls import re_path
from apps.market import consumers

websocket_urlpatterns = [
    re_path(r'ws/prices/$', consumers.MultiPriceConsumer.as_asgi()),
    re_path(r'ws/prices/(?P<symbol>\w+)/$', consumers.PriceFeedConsumer.as_asgi()),
]
