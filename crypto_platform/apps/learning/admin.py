from django.contrib import admin
from .models import SignalResult, ModelPerformance, StrategyWeight, BacktestResult

@admin.register(SignalResult)
class SignalResultAdmin(admin.ModelAdmin):
    list_display = ['signal', 'success', 'profit_loss', 'duration_hours', 'evaluated_at']
    list_filter = ['success']


@admin.register(ModelPerformance)
class ModelPerformanceAdmin(admin.ModelAdmin):
    list_display = ['model_name', 'accuracy', 'precision_score', 'recall', 'date']
    list_filter = ['model_name']


@admin.register(StrategyWeight)
class StrategyWeightAdmin(admin.ModelAdmin):
    list_display = ['component', 'weight', 'performance_score', 'last_updated']


@admin.register(BacktestResult)
class BacktestResultAdmin(admin.ModelAdmin):
    list_display = ['strategy_name', 'symbol', 'win_rate', 'total_return', 'created_at']
    list_filter = ['strategy_name']
