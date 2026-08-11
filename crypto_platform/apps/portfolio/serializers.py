"""Portfolio serializers."""
from rest_framework import serializers
from .models import Portfolio, PortfolioAllocation, RebalanceHistory, TaxLot, TaxReport


class PortfolioAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioAllocation
        fields = ['id', 'portfolio', 'symbol', 'target_percent', 'min_percent',
                  'max_percent', 'current_percent', 'current_value_usd', 
                  'current_quantity', 'needs_rebalance', 'rebalance_amount_usd',
                  'created_at']
        read_only_fields = ['id', 'current_percent', 'current_value_usd', 
                           'current_quantity', 'needs_rebalance', 
                           'rebalance_amount_usd', 'created_at']


class PortfolioSerializer(serializers.ModelSerializer):
    allocations = PortfolioAllocationSerializer(many=True, read_only=True)
    
    class Meta:
        model = Portfolio
        fields = ['id', 'name', 'description', 'portfolio_type', 'total_value_usd',
                  'total_invested_usd', 'total_pnl_usd', 'total_pnl_percent',
                  'sharpe_ratio', 'max_drawdown', 'volatility', 'beta',
                  'base_currency', 'auto_rebalance', 'rebalance_threshold_percent',
                  'is_active', 'allocations', 'created_at', 'updated_at']
        read_only_fields = ['id', 'total_value_usd', 'total_invested_usd', 
                           'total_pnl_usd', 'total_pnl_percent', 'sharpe_ratio',
                           'max_drawdown', 'volatility', 'beta', 'created_at', 
                           'updated_at']


class RebalanceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RebalanceHistory
        fields = ['id', 'portfolio', 'status', 'trades_executed', 'total_trades',
                  'total_fees_usd', 'portfolio_value_before', 'portfolio_value_after',
                  'ai_reasoning', 'triggered_by', 'created_at', 'completed_at']
        read_only_fields = ['id', 'created_at', 'completed_at']


class TaxLotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxLot
        fields = ['id', 'portfolio', 'symbol', 'acquisition_date', 'quantity',
                  'cost_basis_usd', 'cost_basis_per_unit', 'disposition_date',
                  'proceeds_usd', 'gain_loss_usd', 'gain_loss_percent',
                  'holding_period_days', 'is_long_term', 'status', 
                  'remaining_quantity', 'source', 'exchange', 'tx_hash',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'gain_loss_usd', 'gain_loss_percent',
                           'holding_period_days', 'is_long_term', 
                           'remaining_quantity', 'created_at', 'updated_at']


class TaxReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxReport
        fields = ['id', 'portfolio', 'tax_year', 'tax_country', 'total_proceeds',
                  'total_cost_basis', 'total_gain_loss', 'short_term_proceeds',
                  'short_term_gain_loss', 'long_term_proceeds', 'long_term_gain_loss',
                  'transactions', 'generated_at']
        read_only_fields = ['id', 'total_proceeds', 'total_cost_basis', 
                           'total_gain_loss', 'short_term_proceeds',
                           'short_term_gain_loss', 'long_term_proceeds',
                           'long_term_gain_loss', 'generated_at']
