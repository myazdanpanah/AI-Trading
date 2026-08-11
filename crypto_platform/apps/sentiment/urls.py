"""Sentiment Intelligence URL configuration."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SocialSentimentViewSet, FearGreedIndexViewSet,
    WhaleActivityViewSet, InfluencerSentimentViewSet,
    MarketSentimentAggregatedViewSet, SentimentAlertViewSet,
    SentimentAnalysisViewSet
)

router = DefaultRouter()
router.register(r'social', SocialSentimentViewSet)
router.register(r'fear-greed', FearGreedIndexViewSet)
router.register(r'whale', WhaleActivityViewSet)
router.register(r'influencer', InfluencerSentimentViewSet)
router.register(r'aggregated', MarketSentimentAggregatedViewSet)
router.register(r'alerts', SentimentAlertViewSet)
router.register(r'analysis', SentimentAnalysisViewSet, basename='analysis')

urlpatterns = [
    path('', include(router.urls)),
]
