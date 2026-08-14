"""Feedback Loop URL configuration."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'market-memories', views.MarketMemoryViewSet)
router.register(r'signal-memories', views.SignalMemoryViewSet)
router.register(r'pattern-memories', views.PatternMemoryViewSet)
router.register(r'insights', views.LearningInsightViewSet)
router.register(r'cycles', views.FeedbackCycleViewSet, basename='feedback-cycle')
router.register(r'analysis', views.PerformanceAnalysisViewSet, basename='analysis')

urlpatterns = [
    path('', include(router.urls)),
]
