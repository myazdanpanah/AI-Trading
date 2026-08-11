"""Learning engine models."""
import uuid
from django.db import models


class SignalResult(models.Model):
    """Track signal outcomes for learning."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    signal = models.ForeignKey('signals.Signal', on_delete=models.CASCADE, related_name='results')
    exit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    profit_loss = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    profit_loss_percent = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    success = models.BooleanField(default=False)
    duration_hours = models.IntegerField(default=0)
    market_condition = models.CharField(max_length=50, blank=True)
    evaluated_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'signal result'
        verbose_name_plural = 'signal results'
        db_table = 'signal_results'
        ordering = ['-evaluated_at']

    def __str__(self):
        return f"Signal {self.signal_id} - {'Win' if self.success else 'Loss'}"


class ModelPerformance(models.Model):
    """Track AI model performance."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_name = models.CharField(max_length=100)
    accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    precision_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    recall = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    f1_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_predictions = models.IntegerField(default=0)
    correct_predictions = models.IntegerField(default=0)
    date = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'model performance'
        verbose_name_plural = 'model performance'
        db_table = 'model_performance'
        unique_together = ['model_name', 'date']

    def __str__(self):
        return f"{self.model_name} - {self.date}"


class StrategyWeight(models.Model):
    """Adaptive weights for signal components."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    component = models.CharField(max_length=50, unique=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    performance_score = models.DecimalField(max_digits=5, decimal_places=2, default=50)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'strategy weight'
        verbose_name_plural = 'strategy weights'
        db_table = 'strategy_weights'

    def __str__(self):
        return f"{self.component}: {self.weight}%"


class BacktestResult(models.Model):
    """Backtest results for strategies."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    strategy_name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20)
    timeframe = models.CharField(max_length=10)
    start_date = models.DateField()
    end_date = models.DateField()
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    profit_factor = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    total_return = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    parameters = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'backtest result'
        verbose_name_plural = 'backtest results'
        db_table = 'learning_backtest_results'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.strategy_name} - {self.symbol}"
