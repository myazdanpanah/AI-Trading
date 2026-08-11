"""Feedback Loop admin configuration."""
from django.contrib import admin
from .models import MarketMemory, SignalMemory, PatternMemory, LearningInsight, FeedbackCycle


@admin.register(MarketMemory)
class MarketMemoryAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'timeframe', 'price', 'market_condition', 'dominant_factor', 'created_at']
    list_filter = ['symbol', 'timeframe', 'market_condition']
    search_fields = ['symbol']
    ordering = ['-created_at']


@admin.register(SignalMemory)
class SignalMemoryAdmin(admin.ModelAdmin):
    list_display = ['signal', 'signal_direction', 'signal_confidence', 'was_correct', 'actual_return_percent', 'created_at']
    list_filter = ['was_correct', 'signal_direction']
    search_fields = ['signal__symbol']
    ordering = ['-created_at']


@admin.register(PatternMemory)
class PatternMemoryAdmin(admin.ModelAdmin):
    list_display = ['pattern_type', 'symbol', 'timeframe', 'avg_return', 'win_rate', 'sample_size']
    list_filter = ['pattern_type', 'symbol', 'timeframe']
    ordering = ['-avg_return']


@admin.register(LearningInsight)
class LearningInsightAdmin(admin.ModelAdmin):
    list_display = ['insight_type', 'title', 'confidence', 'impact_score', 'is_active', 'was_implemented', 'created_at']
    list_filter = ['insight_type', 'is_active', 'was_implemented']
    search_fields = ['title', 'description']
    ordering = ['-created_at']


@admin.register(FeedbackCycle)
class FeedbackCycleAdmin(admin.ModelAdmin):
    list_display = ['cycle_type', 'status', 'signals_evaluated', 'signals_correct', 'insights_generated', 'started_at']
    list_filter = ['cycle_type', 'status']
    ordering = ['-started_at']
