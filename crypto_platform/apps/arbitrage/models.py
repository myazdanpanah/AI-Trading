"""Arbitrage models - Cross-exchange opportunity detection."""
import uuid
from django.db import models


class ArbitrageOpportunity(models.Model):
    """Detected arbitrage opportunity between exchanges."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    buy_exchange = models.CharField(max_length=50)
    sell_exchange = models.CharField(max_length=50)
    buy_price = models.DecimalField(max_digits=20, decimal_places=8)
    sell_price = models.DecimalField(max_digits=20, decimal_places=8)
    spread_percent = models.DecimalField(max_digits=10, decimal_places=4)
    estimated_profit_usd = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    volume_available = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    fees_estimate = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    net_profit_percent = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    risk_score = models.IntegerField(default=50)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('executed', 'Executed'),
        ('missed', 'Missed'),
    ], default='active')
    detected_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'arbitrage opportunity'
        verbose_name_plural = 'arbitrage opportunities'
        db_table = 'arbitrage_opportunities'
        ordering = ['-spread_percent']
        indexes = [
            models.Index(fields=['symbol', 'status']),
            models.Index(fields=['-spread_percent']),
        ]

    def __str__(self):
        return f"{self.symbol}: {self.buy_exchange} -> {self.sell_exchange} ({self.spread_percent}%)"


class ArbitrageConfig(models.Model):
    """Arbitrage detection configuration."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    min_spread_percent = models.DecimalField(max_digits=10, decimal_places=4, default=0.5)
    max_risk_score = models.IntegerField(default=70)
    enabled_exchanges = models.JSONField(default=list, help_text='List of exchanges to monitor')
    monitored_symbols = models.JSONField(default=list, help_text='List of symbols to monitor')
    check_interval_seconds = models.IntegerField(default=30)
    max_position_size_usd = models.DecimalField(max_digits=20, decimal_places=2, default=10000)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'arbitrage config'
        verbose_name_plural = 'arbitrage configs'
        db_table = 'arbitrage_configs'

    def __str__(self):
        return self.name


class ArbitrageExecution(models.Model):
    """Track arbitrage execution history."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opportunity = models.ForeignKey(ArbitrageOpportunity, on_delete=models.CASCADE, related_name='executions')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('buying', 'Buying'),
        ('selling', 'Selling'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    buy_order_id = models.CharField(max_length=100, blank=True)
    sell_order_id = models.CharField(max_length=100, blank=True)
    actual_buy_price = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    actual_sell_price = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    actual_profit_usd = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    fees_paid = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    execution_time_ms = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'arbitrage execution'
        verbose_name_plural = 'arbitrage executions'
        db_table = 'arbitrage_executions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Execution {self.id} - {self.status}"
