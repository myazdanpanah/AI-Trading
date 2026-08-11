from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ExchangeViewSet, TradingPairViewSet, CandleViewSet,
    OrderBookViewSet, DerivativesDataViewSet, WhaleAlertViewSet
)

router = DefaultRouter()
router.register(r'exchanges', ExchangeViewSet)
router.register(r'pairs', TradingPairViewSet)
router.register(r'candles', CandleViewSet)
router.register(r'orderbook', OrderBookViewSet)
router.register(r'derivatives', DerivativesDataViewSet)
router.register(r'whales', WhaleAlertViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
