from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'candles', views.CandleViewSet)
router.register(r'orderbook', views.OrderBookViewSet)
router.register(r'derivatives', views.DerivativesDataViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('status/', views.data_source_status, name='data-source-status'),
    path('ticker/', views.quick_ticker, name='quick-ticker'),
]
