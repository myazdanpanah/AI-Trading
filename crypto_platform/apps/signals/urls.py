"""Signal URLs - Full CRUD + analysis endpoints."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'signals', views.SignalViewSet)
router.register(r'reasons', views.SignalReasonViewSet)
router.register(r'factor-weights', views.FactorWeightViewSet)
router.register(r'weight-history', views.WeightHistoryViewSet, basename='weight-history')
router.register(r'risk-profiles', views.RiskProfileViewSet)
router.register(r'positions', views.PortfolioPositionViewSet)
router.register(r'performance', views.SignalPerformanceViewSet)
router.register(r'backtests', views.BacktestResultViewSet)
router.register(r'alerts', views.AlertRuleViewSet, basename='alert-rules')
router.register(r'alert-history', views.AlertHistoryViewSet, basename='alert-history')

urlpatterns = [
    path('', include(router.urls)),
]
