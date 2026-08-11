"""Learning URLs - Full CRUD + analysis endpoints."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'results', views.SignalResultViewSet)
router.register(r'model-performance', views.ModelPerformanceViewSet)
router.register(r'strategy-weights', views.StrategyWeightViewSet)
router.register(r'backtests', views.BacktestResultViewSet)
router.register(r'accuracy', views.AccuracyAnalysisViewSet, basename='accuracy')

urlpatterns = [
    path('', include(router.urls)),
]
