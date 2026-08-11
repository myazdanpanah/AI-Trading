"""Arbitrage serializers."""
from rest_framework import serializers
from .models import ArbitrageOpportunity, ArbitrageConfig, ArbitrageExecution


class ArbitrageOpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ArbitrageOpportunity
        fields = ['id', 'symbol', 'buy_exchange', 'sell_exchange', 'buy_price', 
                  'sell_price', 'spread_percent', 'estimated_profit_usd', 
                  'volume_available', 'net_profit_percent', 'risk_score', 
                  'status', 'detected_at', 'expires_at']
        read_only_fields = ['id', 'detected_at']


class ArbitrageConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArbitrageConfig
        fields = ['id', 'name', 'min_spread_percent', 'max_risk_score', 
                  'enabled_exchanges', 'monitored_symbols', 'check_interval_seconds',
                  'max_position_size_usd', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class ArbitrageExecutionSerializer(serializers.ModelSerializer):
    opportunity = ArbitrageOpportunitySerializer(read_only=True)
    
    class Meta:
        model = ArbitrageExecution
        fields = ['id', 'opportunity', 'status', 'buy_order_id', 'sell_order_id',
                  'actual_buy_price', 'actual_sell_price', 'actual_profit_usd',
                  'fees_paid', 'execution_time_ms', 'error_message', 
                  'created_at', 'completed_at']
        read_only_fields = ['id', 'created_at']
