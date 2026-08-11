"""Admin for analytics and global events."""
from django.contrib import admin
from .models import (
    Indicator, TechnicalPattern, CPRAnalysis, SmartMoneyEvent
)
from .global_events import (
    EconomicEvent, RegulatoryEvent, GeopoliticalEvent,
    BlockchainEvent, GlobalEventImpact
)


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'indicator_name', 'timeframe', 'value', 'score', 'signal', 'timestamp']
    list_filter = ['indicator_name', 'timeframe', 'signal']
    search_fields = ['symbol']
    ordering = ['-timestamp']


@admin.register(TechnicalPattern)
class TechnicalPatternAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'pattern', 'confidence', 'direction', 'detected_at']
    list_filter = ['pattern', 'direction']
    search_fields = ['symbol']


@admin.register(CPRAnalysis)
class CPRAnalysisAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'timeframe', 'pivot', 'cpr_width', 'cpr_type', 'confidence', 'timestamp']
    list_filter = ['timeframe', 'cpr_type']
    search_fields = ['symbol']


@admin.register(SmartMoneyEvent)
class SmartMoneyEventAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'event_type', 'direction', 'confidence', 'timestamp']
    list_filter = ['event_type', 'direction']
    search_fields = ['symbol']


@admin.register(EconomicEvent)
class EconomicEventAdmin(admin.ModelAdmin):
    list_display = ['name', 'event_type', 'country', 'impact_level', 'scheduled_date', 'is_released']
    list_filter = ['event_type', 'country', 'impact_level', 'is_released']
    search_fields = ['name']
    ordering = ['scheduled_date']


@admin.register(RegulatoryEvent)
class RegulatoryEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'jurisdiction', 'severity', 'direction', 'event_date']
    list_filter = ['event_type', 'jurisdiction', 'direction']
    search_fields = ['title', 'summary']


@admin.register(GeopoliticalEvent)
class GeopoliticalEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'region', 'severity', 'direction', 'event_date']
    list_filter = ['event_type', 'region', 'direction']
    search_fields = ['title', 'summary']


@admin.register(BlockchainEvent)
class BlockchainEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'blockchain', 'severity', 'direction', 'event_date']
    list_filter = ['event_type', 'blockchain', 'direction']
    search_fields = ['title', 'summary']


@admin.register(GlobalEventImpact)
class GlobalEventImpactAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'event_id', 'impact_score', 'created_at']
    list_filter = ['event_type']
