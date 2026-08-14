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


class WeightHistory(models.Model):
    """Track how factor weights change over time as AI learns."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    factor_name = models.CharField(max_length=50, db_index=True)
    old_weight = models.DecimalField(max_digits=5, decimal_places=4)
    new_weight = models.DecimalField(max_digits=5, decimal_places=4)
    reason = models.TextField(blank=True)
    win_rate_before = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    win_rate_after = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    signals_evaluated = models.IntegerField(default=0)
    adjustment_type = models.CharField(
        max_length=20,
        choices=[
            ('performance', 'Performance-based'),
            ('manual', 'Manual adjustment'),
            ('scheduled', 'Scheduled optimization'),
        ],
        default='scheduled',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'weight history'
        verbose_name_plural = 'weight history'
        db_table = 'weight_history'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.factor_name}: {self.old_weight} -> {self.new_weight}"


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


class AlertRule(models.Model):
    """User-configurable alert rules that trigger when scores cross thresholds."""
    ALERT_TYPES = [
        ('rsi_above', 'RSI Above'),
        ('rsi_below', 'RSI Below'),
        ('confidence_above', 'Confidence Above'),
        ('confidence_below', 'Confidence Below'),
        ('composite_above', 'Composite Score Above'),
        ('composite_below', 'Composite Score Below'),
        ('technical_above', 'Technical Score Above'),
        ('technical_below', 'Technical Score Below'),
        ('sentiment_above', 'Sentiment Score Above'),
        ('sentiment_below', 'Sentiment Score Below'),
        ('price_above', 'Price Above'),
        ('price_below', 'Price Below'),
        ('change_pct_above', '24h Change Above %'),
        ('change_pct_below', '24h Change Below %'),
        ('signal_buy', 'Buy Signal'),
        ('signal_sell', 'Sell Signal'),
        ('signal_strong_buy', 'Strong Buy Signal'),
        ('signal_strong_sell', 'Strong Sell Signal'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='alert_rules')
    symbol = models.CharField(max_length=20, db_index=True)
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    threshold = models.FloatField(default=50, help_text='Threshold value to trigger alert')
    is_active = models.BooleanField(default=True)
    cooldown_minutes = models.IntegerField(default=60, help_text='Minutes between repeated alerts')
    last_triggered = models.DateTimeField(null=True, blank=True)
    message_template = models.CharField(max_length=200, blank=True, help_text='Custom alert message')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'alert rule'
        verbose_name_plural = 'alert rules'
        db_table = 'alert_rules'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.symbol} {self.get_alert_type_display()} {self.threshold}"


class AlertHistory(models.Model):
    """Record of triggered alerts."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='history')
    triggered_at = models.DateTimeField(auto_now_add=True)
    trigger_value = models.FloatField(default=0, help_text='Actual value that triggered the alert')
    message = models.TextField(blank=True)
    read = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'alert history'
        verbose_name_plural = 'alert histories'
        db_table = 'alert_history'
        ordering = ['-triggered_at']

    def __str__(self):
        return f"{self.rule.symbol} - {self.rule.get_alert_type_display()} at {self.triggered_at}"


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
    """Backtesting results for strategy validation with full reproducibility."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Strategy identification
    strategy_name = models.CharField(max_length=100)
    strategy_version = models.CharField(max_length=50, default='1.0')
    feature_version = models.CharField(max_length=50, default='1.0')
    # Asset & timeframe
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(max_length=10)
    # Period
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    # Capital
    initial_capital = models.DecimalField(max_digits=20, decimal_places=2, default=10000)
    final_capital = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    # Core metrics
    total_return = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    total_return_percent = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    sortino_ratio = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    cagr = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    expectancy = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    # Trade stats
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    avg_win = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    avg_loss = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    profit_factor = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    # MFE / MAE
    max_favorable_excursion = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    max_adverse_excursion = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    # Fees & slippage
    total_fees = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    total_slippage = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    fee_rate = models.DecimalField(max_digits=10, decimal_places=6, default=0.001, help_text='Fee rate per trade (e.g. 0.001 = 0.1%)')
    slippage_rate = models.DecimalField(max_digits=10, decimal_places=6, default=0.0005, help_text='Slippage rate per trade (e.g. 0.0005 = 0.05%)')
    # Execution mode
    execution_mode = models.CharField(
        max_length=20,
        choices=[
            ('paper', 'Paper Trading'),
            ('shadow', 'Shadow Trading'),
            ('backtest', 'Backtest'),
        ],
        default='backtest'
    )
    # Data & results
    trades_data = models.JSONField(default=list)
    equity_curve = models.JSONField(default=list)
    # Reproducibility
    signal_snapshot = models.JSONField(default=dict, blank=True, help_text='Snapshot of signal engine state at time of backtest')
    weight_snapshot = models.JSONField(default=dict, blank=True, help_text='Factor weights used during backtest')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'backtest result'
        verbose_name_plural = 'backtest results'
        db_table = 'backtest_results'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.strategy_name} v{self.strategy_version} - {self.symbol} - {self.total_return_percent}%"


class WalkForwardRun(models.Model):
    """Walk-forward validation run — prevents strategy overfitting."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Strategy identification
    strategy_name = models.CharField(max_length=100)
    strategy_version = models.CharField(max_length=50, default='1.0')
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(max_length=10)
    # Window configuration
    train_days = models.IntegerField(default=90, help_text='Training window in days')
    validate_days = models.IntegerField(default=30, help_text='Validation window in days')
    test_days = models.IntegerField(default=30, help_text='Test/OOS window in days')
    step_days = models.IntegerField(default=30, help_text='Rolling step in days')
    # Overall period
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    # Capital
    initial_capital = models.DecimalField(max_digits=20, decimal_places=2, default=10000)
    fee_rate = models.DecimalField(max_digits=10, decimal_places=6, default=0.001)
    slippage_rate = models.DecimalField(max_digits=10, decimal_places=6, default=0.0005)
    # Aggregate metrics (across all windows)
    total_windows = models.IntegerField(default=0)
    avg_oos_return = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    avg_oos_sharpe = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    avg_oos_win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    oos_vs_is_ratio = models.DecimalField(max_digits=5, decimal_places=4, default=0, help_text='OOS performance / IS performance ratio')
    max_oos_drawdown = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    # Leakage detection
    leakage_detected = models.BooleanField(default=False)
    leakage_details = models.JSONField(default=dict, blank=True)
    # Weight snapshot at run start
    weight_snapshot = models.JSONField(default=dict, blank=True)
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'walk-forward run'
        verbose_name_plural = 'walk-forward runs'
        db_table = 'walk_forward_runs'
        ordering = ['-created_at']

    def __str__(self):
        return f"WF: {self.strategy_name} - {self.symbol} ({self.total_windows} windows)"


class WalkForwardWindow(models.Model):
    """Individual window within a walk-forward run."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(WalkForwardRun, on_delete=models.CASCADE, related_name='windows')
    window_index = models.IntegerField(default=0)
    # Window periods
    train_start = models.DateTimeField()
    train_end = models.DateTimeField()
    validate_start = models.DateTimeField()
    validate_end = models.DateTimeField()
    test_start = models.DateTimeField()
    test_end = models.DateTimeField()
    # IS (in-sample) metrics — from training + validation
    is_return_percent = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    is_sharpe = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    is_win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_trades = models.IntegerField(default=0)
    is_max_drawdown = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    # OOS (out-of-sample) metrics — from test window
    oos_return_percent = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    oos_sharpe = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    oos_win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    oos_trades = models.IntegerField(default=0)
    oos_max_drawdown = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    # Frozen parameters (captured at end of training)
    frozen_weights = models.JSONField(default=dict, blank=True)
    # Equity curves
    is_equity_curve = models.JSONField(default=list, blank=True)
    oos_equity_curve = models.JSONField(default=list, blank=True)
    # Full backtest results
    is_backtest_result = models.JSONField(default=dict, blank=True)
    oos_backtest_result = models.JSONField(default=dict, blank=True)
    # Leakage check
    has_leakage = models.BooleanField(default=False)
    leakage_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'walk-forward window'
        verbose_name_plural = 'walk-forward windows'
        db_table = 'walk_forward_windows'
        ordering = ['run', 'window_index']

    def __str__(self):
        return f"Window {self.window_index}: IS {self.is_return_percent}% / OOS {self.oos_return_percent}%"


class RiskConfig(models.Model):
    """Independent risk configuration — the safety gate between Signal and Execution."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    # Position limits
    max_risk_per_trade = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, help_text='Max risk per trade as % of account')
    max_position_size_pct = models.DecimalField(max_digits=5, decimal_places=2, default=10.0, help_text='Max single position as % of account')
    max_concurrent_positions = models.IntegerField(default=5, help_text='Maximum open positions')
    max_correlated_positions = models.IntegerField(default=3, help_text='Max positions in correlated assets')
    # Portfolio limits
    max_portfolio_risk_pct = models.DecimalField(max_digits=5, decimal_places=2, default=5.0, help_text='Max total portfolio risk as %')
    max_portfolio_exposure_pct = models.DecimalField(max_digits=5, decimal_places=2, default=50.0, help_text='Max total exposure as %')
    # Drawdown limits
    max_drawdown_pct = models.DecimalField(max_digits=5, decimal_places=2, default=15.0, help_text='Max drawdown before kill switch')
    daily_loss_limit_pct = models.DecimalField(max_digits=5, decimal_places=2, default=3.0, help_text='Max daily loss as %')
    # Kill switch triggers
    kill_switch_enabled = models.BooleanField(default=True)
    kill_on_drawdown = models.BooleanField(default=True, help_text='Trigger on max drawdown')
    kill_on_daily_loss = models.BooleanField(default=True, help_text='Trigger on daily loss limit')
    kill_on_data_feed_failure = models.BooleanField(default=True, help_text='Trigger if data feeds fail')
    kill_on_api_failure = models.BooleanField(default=True, help_text='Trigger if exchange API fails')
    kill_on_extreme_volatility = models.BooleanField(default=True, help_text='Trigger on extreme volatility')
    kill_on_risk_engine_failure = models.BooleanField(default=True, help_text='Trigger if risk engine itself fails')
    # Active state
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'risk config'
        verbose_name_plural = 'risk configs'
        db_table = 'risk_configs'

    def __str__(self):
        return self.name


class RiskEvent(models.Model):
    """Log of all risk engine decisions and events."""
    EVENT_TYPES = [
        ('signal_approved', 'Signal Approved'),
        ('signal_rejected', 'Signal Rejected'),
        ('position_sized', 'Position Sized'),
        ('kill_switch_activated', 'Kill Switch Activated'),
        ('kill_switch_deactivated', 'Kill Switch Deactivated'),
        ('drawdown_warning', 'Drawdown Warning'),
        ('daily_loss_warning', 'Daily Loss Warning'),
        ('exposure_warning', 'Exposure Warning'),
        ('risk_limit_hit', 'Risk Limit Hit'),
        ('portfolio_assessed', 'Portfolio Assessed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    risk_config = models.ForeignKey(RiskConfig, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES, db_index=True)
    symbol = models.CharField(max_length=20, blank=True)
    signal_id = models.UUIDField(null=True, blank=True)
    # Event details
    decision = models.CharField(max_length=20, choices=[('approved', 'Approved'), ('rejected', 'Rejected'), ('modified', 'Modified')])
    reason = models.TextField(blank=True)
    risk_data = models.JSONField(default=dict, blank=True)
    # Risk state at time of event
    portfolio_exposure_pct = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    portfolio_risk_pct = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    current_drawdown_pct = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    daily_pnl_pct = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    active_positions = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'risk event'
        verbose_name_plural = 'risk events'
        db_table = 'risk_events'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type}: {self.symbol} - {self.decision}"


class KillSwitchState(models.Model):
    """Tracks kill switch state — must be independent from LLM and Signal Engine."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=False)
    triggered_by = models.CharField(max_length=100, blank=True, help_text='What triggered the kill switch')
    triggered_at = models.DateTimeField(null=True, blank=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivation_reason = models.TextField(blank=True)
    # Snapshot at time of activation
    portfolio_drawdown_pct = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    daily_pnl_pct = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    active_positions = models.IntegerField(default=0)
    total_exposure_pct = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'kill switch state'
        verbose_name_plural = 'kill switch states'
        db_table = 'kill_switch_state'

    def __str__(self):
        return f"Kill Switch: {'ACTIVE' if self.is_active else 'inactive'}"


class SignalLineage(models.Model):
    """Full data lineage for signal reproducibility.

    Every signal must store enough information to answer:
    'Why was this signal generated at this exact moment?'

    Stores:
    - Strategy/feature/model/prompt versions
    - Weight snapshot (exact factor weights used)
    - Market snapshot (price, indicators at T)
    - News snapshot (articles, sentiment at T)
    - Social snapshot (fear/greed, X/Twitter at T)
    - Regime snapshot (detected regime at T)
    - LLM context/output (if AI was used)
    - Agent ensemble output (if ensemble was used)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    signal = models.OneToOneField(Signal, on_delete=models.CASCADE, related_name='lineage')

    # ── Version Tracking ─────────────────────────────────────────────
    strategy_version = models.CharField(max_length=50, default='2.0')
    feature_version = models.CharField(max_length=50, default='1.2')
    model_version = models.CharField(max_length=50, blank=True, help_text='LLM model version if AI was used')
    prompt_version = models.CharField(max_length=50, default='1.0')
    ensemble_version = models.CharField(max_length=50, blank=True)
    risk_version = models.CharField(max_length=50, default='1.0')

    # ── Factor Weights Snapshot ──────────────────────────────────────
    weights_snapshot = models.JSONField(default=dict, help_text='Exact factor weights used for this signal')
    regime = models.CharField(max_length=50, default='unknown', help_text='Detected market regime')
    regime_confidence = models.FloatField(default=0.0)

    # ── Data Snapshots ───────────────────────────────────────────────
    factor_scores = models.JSONField(default=dict, help_text='Individual factor scores')
    market_snapshot = models.JSONField(default=dict, help_text='Price, indicators, candles at signal time')
    news_snapshot = models.JSONField(default=dict, help_text='News articles and sentiment at signal time')
    social_snapshot = models.JSONField(default=dict, help_text='Fear/greed, social sentiment at signal time')
    derivatives_snapshot = models.JSONField(default=dict, help_text='Funding, OI, liquidations at signal time')

    # ── AI/LLM Context ──────────────────────────────────────────────
    llm_context = models.JSONField(default=dict, help_text='What was sent to LLM')
    llm_output = models.JSONField(default=dict, help_text='What LLM returned')
    ensemble_output = models.JSONField(default=dict, help_text='Agent ensemble results')

    # ── Risk Decision ────────────────────────────────────────────────
    risk_decision = models.JSONField(default=dict, help_text='Risk engine decision')

    # ── Full Lineage ─────────────────────────────────────────────────
    data_lineage = models.JSONField(default=dict, help_text='Complete lineage data for reproducibility')

    # ── Metadata ─────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'signal lineage'
        verbose_name_plural = 'signal lineages'
        db_table = 'signal_lineages'
        ordering = ['-created_at']

    def __str__(self):
        return f"Lineage: {self.signal.symbol} v{self.strategy_version} at {self.created_at}"

    def explain(self) -> str:
        """Generate human-readable explanation."""
        from .services.versioning import VersionTracker
        tracker = VersionTracker()
        return tracker.explain_signal(self.data_lineage)
