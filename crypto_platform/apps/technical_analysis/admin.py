"""Technical Analysis admin configuration."""
from django.contrib import admin
from .models import (
    TechnicalIndicator, TechnicalPattern, SupportResistance,
    TrendAnalysis, SmartMoneyEvent, TechnicalAnalysisResult
)


@admin.register(TechnicalIndicator)
class TechnicalIndicatorAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'timeframe', 'indicator_type', 'signal', 'strength', 'timestamp']
    list_filter = ['indicator_type', 'signal', 'timeframe']
    search_fields = ['symbol']
    ordering = ['-timestamp']


@admin.register(TechnicalPattern)
class TechnicalPatternAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'timeframe', 'pattern_type', 'direction', 'confidence', 'created_at']
    list_filter = ['pattern_type', 'direction', 'timeframe']
    search_fields = ['symbol']
    ordering = ['-created_at']


@admin.register(SupportResistance)
class SupportResistanceAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'timeframe', 'level_type', 'price', 'strength', 'touch_count']
    list_filter = ['level_type', 'timeframe']
    search_fields = ['symbol']
    ordering = ['symbol', 'price']


@admin.register(TrendAnalysis)
class TrendAnalysisAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'timeframe', 'trend_direction', 'trend_strength', 'timestamp']
    list_filter = ['trend_direction', 'timeframe']
    search_fields = ['symbol']
    ordering = ['-timestamp']


@admin.register(SmartMoneyEvent)
class SmartMoneyEventAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'event_type', 'direction', 'confidence', 'price_level', 'timestamp']
    list_filter = ['event_type', 'direction']
    search_fields = ['symbol']
    ordering = ['-timestamp']


@admin.register(TechnicalAnalysisResult)
class TechnicalAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'timeframe', 'overall_signal', 'confidence', 'risk_reward_ratio', 'timestamp']
    list_filter = ['overall_signal', 'timeframe']
    search_fields = ['symbol']
    ordering = ['-timestamp']
