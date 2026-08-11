"""Signal admin - Enhanced with all models."""
from django.contrib import admin
from .models import (
    Signal, SignalReason, SignalGenerationRequest,
    FactorWeight, RiskProfile, PortfolioPosition,
    SignalPerformance, BacktestResult,
)


class SignalReasonInline(admin.TabularInline):
    model = SignalReason
    extra = 0


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'direction', 'confidence', 'risk_score', 'composite_score', 'timeframe', 'is_active', 'created_at']
    list_filter = ['direction', 'timeframe', 'is_active']
    search_fields = ['symbol']
    inlines = [SignalReasonInline]


@admin.register(SignalReason)
class SignalReasonAdmin(admin.ModelAdmin):
    list_display = ['signal', 'reason_type', 'confidence', 'created_at']
    list_filter = ['reason_type']


@admin.register(SignalGenerationRequest)
class SignalGenerationRequestAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'timeframe', 'status', 'execution_time_ms', 'created_at']
    list_filter = ['status', 'timeframe']


@admin.register(FactorWeight)
class FactorWeightAdmin(admin.ModelAdmin):
    list_display = ['name', 'weight', 'is_active', 'updated_at']
    list_filter = ['is_active']


@admin.register(RiskProfile)
class RiskProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'max_portfolio_risk', 'max_position_size', 'risk_per_trade', 'is_active']
    list_filter = ['is_active']


@admin.register(PortfolioPosition)
class PortfolioPositionAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'side', 'quantity', 'entry_price', 'current_price', 'unrealized_pnl', 'is_active']
    list_filter = ['side', 'is_active']
    search_fields = ['symbol']


@admin.register(SignalPerformance)
class SignalPerformanceAdmin(admin.ModelAdmin):
    list_display = ['signal', 'actual_return_percent', 'was_correct', 'holding_period_hours']
    list_filter = ['was_correct', 'hit_stop_loss', 'hit_take_profit']


@admin.register(BacktestResult)
class BacktestResultAdmin(admin.ModelAdmin):
    list_display = ['strategy_name', 'symbol', 'timeframe', 'total_return_percent', 'win_rate', 'sharpe_ratio', 'created_at']
    list_filter = ['strategy_name', 'timeframe']
    search_fields = ['symbol', 'strategy_name']
