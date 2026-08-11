from django.contrib import admin
from .models import ArbitrageOpportunity, ArbitrageConfig, ArbitrageExecution


@admin.register(ArbitrageOpportunity)
class ArbitrageOpportunityAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'buy_exchange', 'sell_exchange', 'spread_percent', 
                    'net_profit_percent', 'status', 'detected_at']
    list_filter = ['status', 'buy_exchange', 'sell_exchange']
    search_fields = ['symbol']


@admin.register(ArbitrageConfig)
class ArbitrageConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'min_spread_percent', 'max_risk_score', 'is_active']
    list_filter = ['is_active']


@admin.register(ArbitrageExecution)
class ArbitrageExecutionAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'actual_profit_usd', 'execution_time_ms', 'created_at']
    list_filter = ['status']
