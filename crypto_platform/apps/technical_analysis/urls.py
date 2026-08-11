"""Technical Analysis URL configuration."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TechnicalIndicatorViewSet, TechnicalPatternViewSet,
    SupportResistanceViewSet, TrendAnalysisViewSet,
    SmartMoneyEventViewSet, TechnicalAnalysisResultViewSet,
    AnalysisViewSet
)

router = DefaultRouter()
router.register(r'indicators', TechnicalIndicatorViewSet)
router.register(r'patterns', TechnicalPatternViewSet)
router.register(r'support-resistance', SupportResistanceViewSet)
router.register(r'trends', TrendAnalysisViewSet)
router.register(r'smart-money', SmartMoneyEventViewSet)
router.register(r'results', TechnicalAnalysisResultViewSet)
router.register(r'analysis', AnalysisViewSet, basename='analysis')

urlpatterns = [
    path('', include(router.urls)),
]
