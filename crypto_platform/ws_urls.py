"""WebSocket URL patterns for real-time streaming."""
from django.urls import re_path
from apps.market.consumers import PriceConsumer, OrderBookConsumer
from apps.signals.consumers import SignalConsumer

websocket_urlpatterns = [
    re_path(r'ws/prices/(?P<symbol>\w+[-/]\w+)/$', PriceConsumer.as_asgi()),
    re_path(r'ws/orderbook/(?P<symbol>\w+[-/]\w+)/$', OrderBookConsumer.as_asgi()),
    re_path(r'ws/signals/$', SignalConsumer.as_asgi()),
]
