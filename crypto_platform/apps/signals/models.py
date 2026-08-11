"""Signal models - Multi-factor scoring, risk management, portfolio tracking."""
import uuid
from django.db import models
from django.conf import settings


class Signal(models.Model):
    """Trading signal with multi-factor scoring."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    direction = models.CharField(
        max_length=20,
        choices=[
            ('buy', 'Buy'),
            ('strong_buy', 'Strong Buy'),
            ('sell', 'Sell'),
            ('strong_sell', 'Strong Sell'),
            ('hold', 'Hold'),
            ('wait', 'Wait'),
            ('exit', 'Exit'),
            ('take_profit', 'Take Profit'),
            ('stop_loss', 'Stop Loss'),
        ]
    )
    confidence = models.IntegerField(default=50)
    risk_score = models.IntegerField(default=50)
    entry_price = models.DecimalField(max_digits=20, decimal_places=8)
    stop_loss = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    take_profit = models.JSONField(default=list)
    timeframe = models.CharField(max_length=10)
    technical_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    news_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sentiment_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    ai_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    macro_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    historical_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    composite_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'signal'
        verbose_name_plural = 'signals'
        db_table = 'signals'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.symbol} {self.direction} - {self.confidence}%"


class SignalReason(models.Model):
    """Detailed reasons for a signal."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    signal = models.ForeignKey(Signal, on_delete=models.CASCADE, related_name='reasons')
    reason_type = models.CharField(
        max_length=20,
        choices=[
            ('technical', 'Technical'),
            ('news', 'News'),
            ('macro', 'Macro'),
            ('ai', 'AI'),
            ('sentiment', 'Sentiment'),
            ('risk', 'Risk'),
        ]
    )
    description = models.TextField()
    confidence = models.IntegerField(default=50)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'signal reason'
        verbose_name_plural = 'signal reasons'
        db_table = 'signal_reasons'

    def __str__(self):
        return f"{self.reason_type}: {self.description[:50]}"


class SignalGenerationRequest(models.Model):
    """Tracks signal generation requests for audit and analysis."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(max_length=10)
    input_data = models.JSONField(default=dict)
    weights_used = models.JSONField(default=dict)
    execution_time_ms = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'signal generation request'
        verbose_name_plural = 'signal generation requests'
        db_table = 'signal_generation_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.symbol} - {self.status} at {self.created_at}"


class FactorWeight(models.Model):
    """Configurable weights for signal scoring factors."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    weight = models.DecimalField(max_digits=5, decimal_places=4, default=0.20)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    min_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'factor weight'
        verbose_name_plural = 'factor weights'
        db_table = 'factor_weights'

    def __str__(self):
        return f"{self.name}: {self.weight}"


class RiskProfile(models.Model):
    """Risk management profile for position sizing."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    max_portfolio_risk = models.DecimalField(max_digits=5, decimal_places=2, default=2.0)
    max_position_size = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)
    max_correlated_positions = models.IntegerField(default=3)
    max_drawdown = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)
    risk_per_trade = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    use_kelly_criterion = models.BooleanField(default=False)
    kelly_fraction = models.DecimalField(max_digits=5, decimal_places=2, default=0.25)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'risk profile'
        verbose_name_plural = 'risk profiles'
        db_table = 'risk_profiles'

    def __str__(self):
        return self.name


class PortfolioPosition(models.Model):
    """Active portfolio position."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    side = models.CharField(
        max_length=10,
        choices=[('long', 'Long'), ('short', 'Short')]
    )
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    entry_price = models.DecimalField(max_digits=20, decimal_places=8)
    current_price = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    stop_loss = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    take_profit = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    unrealized_pnl = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    unrealized_pnl_percent = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    risk_amount = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    signal = models.ForeignKey(Signal, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    close_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    close_reason = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'portfolio position'
        verbose_name_plural = 'portfolio positions'
        db_table = 'portfolio_positions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.symbol} {self.side} - {self.quantity} @ {self.entry_price}"


class SignalPerformance(models.Model):
    """Track signal performance for learning."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    signal = models.OneToOneField(Signal, on_delete=models.CASCADE, related_name='performance')
    actual_return = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    actual_return_percent = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    max_favorable = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    max_adverse = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    holding_period_hours = models.IntegerField(default=0)
    hit_stop_loss = models.BooleanField(default=False)
    hit_take_profit = models.BooleanField(default=False)
    was_correct = models.BooleanField(default=False)
    score_accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'signal performance'
        verbose_name_plural = 'signal performances'
        db_table = 'signal_performances'

    def __str__(self):
        return f"{self.signal.symbol} - {self.actual_return_percent}%"


class BacktestResult(models.Model):
    """Backtesting results for strategy validation."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    strategy_name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(max_length=10)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    initial_capital = models.DecimalField(max_digits=20, decimal_places=2, default=10000)
    final_capital = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_return = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    total_return_percent = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    avg_win = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    avg_loss = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    profit_factor = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    trades_data = models.JSONField(default=list)
    equity_curve = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'backtest result'
        verbose_name_plural = 'backtest results'
        db_table = 'backtest_results'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.strategy_name} - {self.symbol} - {self.total_return_percent}%"
