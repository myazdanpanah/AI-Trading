"""Arbitrage URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'opportunities', views.ArbitrageOpportunityViewSet, basename='arbitrage-opportunity')
router.register(r'configs', views.ArbitrageConfigViewSet, basename='arbitrage-config')
router.register(r'executions', views.ArbitrageExecutionViewSet, basename='arbitrage-execution')

urlpatterns = [
    path('', include(router.urls)),
]
