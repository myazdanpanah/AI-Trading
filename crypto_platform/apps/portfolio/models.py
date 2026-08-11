"""Portfolio models - Advanced portfolio management, rebalancing, tax optimization."""
import uuid
from django.db import models
from django.conf import settings


class Portfolio(models.Model):
    """Main portfolio container."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portfolios')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    portfolio_type = models.CharField(max_length=30, choices=[
        ('spot', 'Spot'),
        ('futures', 'Futures'),
        ('combined', 'Combined'),
    ], default='spot')
    
    # Portfolio value
    total_value_usd = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_invested_usd = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_pnl_usd = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_pnl_percent = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    # Risk metrics
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    volatility = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    beta = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    
    # Settings
    base_currency = models.CharField(max_length=10, default='USDT')
    auto_rebalance = models.BooleanField(default=False)
    rebalance_threshold_percent = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'portfolio'
        verbose_name_plural = 'portfolios'
        db_table = 'portfolios'
        ordering = ['-total_value_usd']

    def __str__(self):
        return f"{self.name} (${self.total_value_usd})"


class PortfolioAllocation(models.Model):
    """Target allocation for portfolio rebalancing."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='allocations')
    symbol = models.CharField(max_length=20)
    target_percent = models.DecimalField(max_digits=5, decimal_places=2)
    min_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_percent = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    
    # Current state
    current_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    current_value_usd = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    current_quantity = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    
    # Rebalance info
    needs_rebalance = models.BooleanField(default=False)
    rebalance_amount_usd = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'portfolio allocation'
        verbose_name_plural = 'portfolio allocations'
        db_table = 'portfolio_allocations'
        unique_together = ['portfolio', 'symbol']

    def __str__(self):
        return f"{self.symbol}: {self.target_percent}%"


class RebalanceHistory(models.Model):
    """History of portfolio rebalancing events."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='rebalance_history')
    
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('executing', 'Executing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    
    # Changes made
    trades_executed = models.JSONField(default=list, help_text='List of trades executed')
    total_trades = models.IntegerField(default=0)
    total_fees_usd = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    # Performance impact
    portfolio_value_before = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    portfolio_value_after = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    # AI reasoning
    ai_reasoning = models.TextField(blank=True, help_text='AI explanation for rebalance decisions')
    
    triggered_by = models.CharField(max_length=30, choices=[
        ('scheduled', 'Scheduled'),
        ('threshold', 'Threshold Breached'),
        ('manual', 'Manual'),
        ('ai', 'AI Recommendation'),
    ], default='manual')
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'rebalance history'
        verbose_name_plural = 'rebalance histories'
        db_table = 'rebalance_history'
        ordering = ['-created_at']

    def __str__(self):
        return f"Rebalance {self.id} - {self.status}"


class TaxLot(models.Model):
    """Tax lot tracking for cost basis calculation."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='tax_lots')
    symbol = models.CharField(max_length=20, db_index=True)
    
    # Acquisition details
    acquisition_date = models.DateField()
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    cost_basis_usd = models.DecimalField(max_digits=20, decimal_places=8)
    cost_basis_per_unit = models.DecimalField(max_digits=20, decimal_places=8)
    
    # Disposition details
    disposition_date = models.DateField(null=True, blank=True)
    proceeds_usd = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    # Tax calculation
    gain_loss_usd = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    gain_loss_percent = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    holding_period_days = models.IntegerField(default=0)
    is_long_term = models.BooleanField(default=False, help_text='Held for more than 1 year')
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('open', 'Open'),
        ('partially_closed', 'Partially Closed'),
        ('closed', 'Closed'),
    ], default='open')
    
    remaining_quantity = models.DecimalField(max_digits=20, decimal_places=8)
    
    # Source
    source = models.CharField(max_length=30, choices=[
        ('purchase', 'Purchase'),
        ('trade', 'Trade'),
        ('transfer', 'Transfer'),
        ('mining', 'Mining'),
        ('staking', 'Staking'),
        ('airdrop', 'Airdrop'),
    ], default='purchase')
    
    exchange = models.CharField(max_length=50, blank=True)
    tx_hash = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'tax lot'
        verbose_name_plural = 'tax lots'
        db_table = 'tax_lots'
        ordering = ['acquisition_date']
        indexes = [
            models.Index(fields=['symbol', 'status']),
            models.Index(fields=['acquisition_date']),
        ]

    def __str__(self):
        return f"{self.symbol}: {self.quantity} @ ${self.cost_basis_per_unit}"


class TaxReport(models.Model):
    """Tax report summary."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='tax_reports')
    
    tax_year = models.IntegerField()
    tax_country = models.CharField(max_length=3, default='US')
    
    # Summary
    total_proceeds = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_cost_basis = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_gain_loss = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    # Short-term vs long-term
    short_term_proceeds = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    short_term_gain_loss = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    long_term_proceeds = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    long_term_gain_loss = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    # Detailed data
    transactions = models.JSONField(default=list)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'tax report'
        verbose_name_plural = 'tax reports'
        db_table = 'tax_reports'
        ordering = ['-tax_year']

    def __str__(self):
        return f"Tax Report {self.tax_year} - {self.tax_country}"
