"""Sentiment Intelligence admin configuration."""
from django.contrib import admin
from .models import (
    SocialSentiment, FearGreedIndex, WhaleActivity,
    InfluencerSentiment, MarketSentimentAggregated, SentimentAlert
)


@admin.register(SocialSentiment)
class SocialSentimentAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'platform', 'sentiment_label', 'sentiment_score', 'volume', 'timestamp']
    list_filter = ['platform', 'sentiment_label']
    search_fields = ['symbol']
    ordering = ['-timestamp']


@admin.register(FearGreedIndex)
class FearGreedIndexAdmin(admin.ModelAdmin):
    list_display = ['value', 'label', 'volatility', 'momentum', 'social_media', 'timestamp']
    list_filter = ['label']
    ordering = ['-timestamp']


@admin.register(WhaleActivity)
class WhaleActivityAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'whale_type', 'usd_value', 'sentiment_impact', 'confidence', 'timestamp']
    list_filter = ['whale_type', 'sentiment_impact']
    search_fields = ['symbol', 'wallet_address']
    ordering = ['-timestamp']


@admin.register(InfluencerSentiment)
class InfluencerSentimentAdmin(admin.ModelAdmin):
    list_display = ['influencer_name', 'platform', 'followers', 'sentiment_label', 'credibility_score', 'timestamp']
    list_filter = ['platform', 'sentiment_label']
    search_fields = ['influencer_name']
    ordering = ['-timestamp']


@admin.register(MarketSentimentAggregated)
class MarketSentimentAggregatedAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'overall_label', 'overall_score', 'confidence', 'fear_greed_value', 'timestamp']
    list_filter = ['overall_label']
    search_fields = ['symbol']
    ordering = ['-timestamp']


@admin.register(SentimentAlert)
class SentimentAlertAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'alert_type', 'severity', 'title', 'is_read', 'created_at']
    list_filter = ['alert_type', 'severity', 'is_read']
    search_fields = ['symbol', 'title']
    ordering = ['-created_at']
