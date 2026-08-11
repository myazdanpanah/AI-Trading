from django.contrib import admin
from .models import Portfolio, PortfolioAllocation, RebalanceHistory, TaxLot, TaxReport


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'portfolio_type', 'total_value_usd', 
                    'total_pnl_percent', 'is_active']
    list_filter = ['portfolio_type', 'is_active']
    search_fields = ['name', 'user__username']


@admin.register(PortfolioAllocation)
class PortfolioAllocationAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'symbol', 'target_percent', 'current_percent', 
                    'needs_rebalance']
    list_filter = ['needs_rebalance']
    search_fields = ['symbol']


@admin.register(RebalanceHistory)
class RebalanceHistoryAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'status', 'total_trades', 'total_fees_usd', 
                    'triggered_by', 'created_at']
    list_filter = ['status', 'triggered_by']


@admin.register(TaxLot)
class TaxLotAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'portfolio', 'quantity', 'cost_basis_per_unit', 
                    'status', 'is_long_term']
    list_filter = ['status', 'is_long_term', 'source']
    search_fields = ['symbol']


@admin.register(TaxReport)
class TaxReportAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'tax_year', 'total_gain_loss', 'generated_at']
    list_filter = ['tax_year', 'tax_country']
