"""Technical Analysis models."""
import uuid
from django.db import models


class TechnicalIndicator(models.Model):
    """Technical indicator results."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(max_length=10, db_index=True)
    indicator_type = models.CharField(
        max_length=30,
        choices=[
            ('rsi', 'RSI'),
            ('macd', 'MACD'),
            ('bollinger_bands', 'Bollinger Bands'),
            ('ema', 'EMA'),
            ('sma', 'SMA'),
            ('stochastic', 'Stochastic'),
            ('atr', 'ATR'),
            ('adx', 'ADX'),
            ('obv', 'OBV'),
            ('vwap', 'VWAP'),
            ('ichimoku', 'Ichimoku Cloud'),
            ('cci', 'CCI'),
            ('williams_r', 'Williams %R'),
            ('mfi', 'Money Flow Index'),
            ('roc', 'Rate of Change'),
        ]
    )
    value = models.JSONField(default=dict, help_text='Indicator value(s)')
    signal = models.CharField(
        max_length=20,
        choices=[
            ('bullish', 'Bullish'),
            ('bearish', 'Bearish'),
            ('neutral', 'Neutral'),
        ],
        default='neutral'
    )
    strength = models.IntegerField(default=50, help_text='Signal strength 0-100')
    period = models.IntegerField(default=14, help_text='Indicator period')
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Technical indicator'
        verbose_name_plural = 'Technical indicators'
        db_table = 'technical_indicators'
        unique_together = ['symbol', 'timeframe', 'indicator_type', 'timestamp']
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.symbol} {self.indicator_type} - {self.signal}"


class TechnicalPattern(models.Model):
    """Chart pattern detection results."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(max_length=10, db_index=True)
    pattern_type = models.CharField(
        max_length=50,
        choices=[
            ('head_shoulders', 'Head and Shoulders'),
            ('head_shoulders_inv', 'Inverse Head and Shoulders'),
            ('double_top', 'Double Top'),
            ('double_bottom', 'Double Bottom'),
            ('triple_top', 'Triple Top'),
            ('triple_bottom', 'Triple Bottom'),
            ('ascending_triangle', 'Ascending Triangle'),
            ('descending_triangle', 'Descending Triangle'),
            ('symmetrical_triangle', 'Symmetrical Triangle'),
            ('bull_flag', 'Bull Flag'),
            ('bear_flag', 'Bear Flag'),
            ('wedge_falling', 'Falling Wedge'),
            ('wedge_rising', 'Rising Wedge'),
            ('channel_up', 'Ascending Channel'),
            ('channel_down', 'Descending Channel'),
            ('cup_handle', 'Cup and Handle'),
            ('rounding_bottom', 'Rounding Bottom'),
        ]
    )
    direction = models.CharField(
        max_length=20,
        choices=[
            ('bullish', 'Bullish'),
            ('bearish', 'Bearish'),
            ('neutral', 'Neutral'),
        ]
    )
    confidence = models.FloatField(default=0.5, help_text='Pattern confidence 0-1')
    start_price = models.DecimalField(max_digits=20, decimal_places=8)
    end_price = models.DecimalField(max_digits=20, decimal_places=8)
    target_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    stop_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Technical pattern'
        verbose_name_plural = 'Technical patterns'
        db_table = 'technical_analysis_patterns'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.symbol} {self.pattern_type} - {self.direction}"


class SupportResistance(models.Model):
    """Support and resistance levels."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(max_length=10, db_index=True)
    level_type = models.CharField(
        max_length=20,
        choices=[
            ('support', 'Support'),
            ('resistance', 'Resistance'),
            ('pivot', 'Pivot Point'),
        ]
    )
    price = models.DecimalField(max_digits=20, decimal_places=8)
    strength = models.IntegerField(default=50, help_text='Level strength 0-100')
    touch_count = models.IntegerField(default=1, help_text='Number of times tested')
    last_test_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Support/Resistance level'
        verbose_name_plural = 'Support/Resistance levels'
        db_table = 'support_resistance'
        unique_together = ['symbol', 'timeframe', 'level_type', 'price']
        ordering = ['symbol', 'price']

    def __str__(self):
        return f"{self.symbol} {self.level_type} @ {self.price}"


class TrendAnalysis(models.Model):
    """Trend analysis results."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(max_length=10, db_index=True)
    trend_direction = models.CharField(
        max_length=20,
        choices=[
            ('strong_uptrend', 'Strong Uptrend'),
            ('uptrend', 'Uptrend'),
            ('sideways', 'Sideways'),
            ('downtrend', 'Downtrend'),
            ('strong_downtrend', 'Strong Downtrend'),
        ]
    )
    trend_strength = models.IntegerField(default=50, help_text='Trend strength 0-100')
    adx_value = models.FloatField(default=0, help_text='ADX value for trend strength')
    trend_start_price = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    trend_start_time = models.DateTimeField(null=True)
    current_price = models.DecimalField(max_digits=20, decimal_places=8)
    ema_short = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    ema_long = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    ema_signal = models.CharField(
        max_length=20,
        choices=[
            ('bullish_cross', 'Bullish Cross'),
            ('bearish_cross', 'Bearish Cross'),
            ('bullish_alignment', 'Bullish Alignment'),
            ('bearish_alignment', 'Bearish Alignment'),
            ('neutral', 'Neutral'),
        ],
        default='neutral'
    )
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Trend analysis'
        verbose_name_plural = 'Trend analyses'
        db_table = 'trend_analysis'
        unique_together = ['symbol', 'timeframe', 'timestamp']
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.symbol} {self.trend_direction} - {self.trend_strength}%"


class SmartMoneyEvent(models.Model):
    """Smart money / institutional activity events."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    event_type = models.CharField(
        max_length=30,
        choices=[
            ('accumulation', 'Accumulation'),
            ('distribution', 'Distribution'),
            ('breakout', 'Breakout'),
            ('fakeout', 'Fakeout'),
            ('stop_hunt', 'Stop Hunt'),
            ('liquidity_sweep', 'Liquidity Sweep'),
            ('order_block', 'Order Block'),
            ('fair_value_gap', 'Fair Value Gap'),
            ('breaker_block', 'Breaker Block'),
            ('mitigation_block', 'Mitigation Block'),
        ]
    )
    direction = models.CharField(
        max_length=20,
        choices=[
            ('bullish', 'Bullish'),
            ('bearish', 'Bearish'),
        ]
    )
    confidence = models.FloatField(default=0.5, help_text='Event confidence 0-1')
    price_level = models.DecimalField(max_digits=20, decimal_places=8)
    volume_confirmation = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    timeframe = models.CharField(max_length=10)
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Smart money event'
        verbose_name_plural = 'Smart money events'
        db_table = 'technical_analysis_smart_money_events'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.symbol} {self.event_type} @ {self.price_level}"


class TechnicalAnalysisResult(models.Model):
    """Combined technical analysis result."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(max_length=10, db_index=True)
    overall_signal = models.CharField(
        max_length=20,
        choices=[
            ('strong_buy', 'Strong Buy'),
            ('buy', 'Buy'),
            ('neutral', 'Neutral'),
            ('sell', 'Sell'),
            ('strong_sell', 'Strong Sell'),
        ]
    )
    confidence = models.FloatField(default=0.5, help_text='Overall confidence 0-1')
    indicators_summary = models.JSONField(default=dict, help_text='Summary of all indicators')
    patterns_summary = models.JSONField(default=list, help_text='Detected patterns')
    support_levels = models.JSONField(default=list, help_text='Key support levels')
    resistance_levels = models.JSONField(default=list, help_text='Key resistance levels')
    trend_summary = models.JSONField(default=dict, help_text='Trend analysis summary')
    smart_money_summary = models.JSONField(default=list, help_text='Smart money events')
    entry_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    stop_loss = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    take_profit_1 = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    take_profit_2 = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    take_profit_3 = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    risk_reward_ratio = models.FloatField(default=0, help_text='Risk/Reward ratio')
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Technical analysis result'
        verbose_name_plural = 'Technical analysis results'
        db_table = 'technical_analysis_results'
        unique_together = ['symbol', 'timeframe', 'timestamp']
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.symbol} {self.timeframe} - {self.overall_signal}"
