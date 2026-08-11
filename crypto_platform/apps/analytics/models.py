"""Technical analysis and analytics models."""
import uuid
from django.db import models


class Indicator(models.Model):
    """Technical indicator values."""
    id = models.BigAutoField(primary_key=True)
    symbol = models.CharField(max_length=20, db_index=True)
    indicator_name = models.CharField(
        max_length=50,
        choices=[
            ('ema_9', 'EMA 9'),
            ('ema_21', 'EMA 21'),
            ('ema_50', 'EMA 50'),
            ('ema_200', 'EMA 200'),
            ('sma_20', 'SMA 20'),
            ('rsi_14', 'RSI 14'),
            ('macd', 'MACD'),
            ('stochastic', 'Stochastic'),
            ('bollinger', 'Bollinger Bands'),
            ('atr', 'ATR'),
            ('adx', 'ADX'),
            ('obv', 'OBV'),
            ('mfi', 'MFI'),
            ('cci', 'CCI'),
            ('vwap', 'VWAP'),
        ]
    )
    timeframe = models.CharField(max_length=10, db_index=True)
    value = models.DecimalField(max_digits=20, decimal_places=8)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=50)
    signal = models.CharField(
        max_length=20,
        choices=[
            ('bullish', 'Bullish'),
            ('neutral', 'Neutral'),
            ('bearish', 'Bearish'),
        ],
        default='neutral'
    )
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'indicator'
        verbose_name_plural = 'indicators'
        db_table = 'indicators'
        unique_together = ['symbol', 'indicator_name', 'timeframe', 'timestamp']

    def __str__(self):
        return f"{self.symbol} {self.indicator_name} - {self.value}"


class TechnicalPattern(models.Model):
    """Detected technical patterns."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    pattern = models.CharField(
        max_length=50,
        choices=[
            ('head_shoulders', 'Head and Shoulders'),
            ('inverse_head_shoulders', 'Inverse Head and Shoulders'),
            ('double_top', 'Double Top'),
            ('double_bottom', 'Double Bottom'),
            ('triangle_asc', 'Ascending Triangle'),
            ('triangle_desc', 'Descending Triangle'),
            ('flag_bull', 'Bull Flag'),
            ('flag_bear', 'Bear Flag'),
            ('wedge_rising', 'Rising Wedge'),
            ('wedge_falling', 'Falling Wedge'),
        ]
    )
    confidence = models.IntegerField(default=50)
    direction = models.CharField(
        max_length=20,
        choices=[
            ('bullish', 'Bullish'),
            ('bearish', 'Bearish'),
        ]
    )
    price_zone = models.JSONField(default=dict)
    detected_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'technical pattern'
        verbose_name_plural = 'technical patterns'
        db_table = 'analytics_technical_patterns'
        ordering = ['-detected_at']

    def __str__(self):
        return f"{self.symbol} - {self.pattern}"


class CPRAnalysis(models.Model):
    """Central Pivot Range analysis."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(
        max_length=10,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ]
    )
    pivot = models.DecimalField(max_digits=20, decimal_places=8)
    bc = models.DecimalField(max_digits=20, decimal_places=8)
    tc = models.DecimalField(max_digits=20, decimal_places=8)
    r1 = models.DecimalField(max_digits=20, decimal_places=8)
    r2 = models.DecimalField(max_digits=20, decimal_places=8)
    s1 = models.DecimalField(max_digits=20, decimal_places=8)
    s2 = models.DecimalField(max_digits=20, decimal_places=8)
    cpr_width = models.DecimalField(max_digits=20, decimal_places=8)
    cpr_type = models.CharField(
        max_length=20,
        choices=[
            ('narrow', 'Narrow'),
            ('normal', 'Normal'),
            ('wide', 'Wide'),
        ]
    )
    virgin_cpr = models.BooleanField(default=False)
    breakout_probability = models.IntegerField(default=50)
    reversal_probability = models.IntegerField(default=50)
    confidence = models.IntegerField(default=50)
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'CPR analysis'
        verbose_name_plural = 'CPR analyses'
        db_table = 'cpr_analysis'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.symbol} CPR - {self.timeframe}"


class SmartMoneyEvent(models.Model):
    """Smart money concept events."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    event_type = models.CharField(
        max_length=30,
        choices=[
            ('bos', 'Break of Structure'),
            ('choch', 'Change of Character'),
            ('liquidity_sweep', 'Liquidity Sweep'),
            ('order_block', 'Order Block'),
            ('fvg', 'Fair Value Gap'),
            ('premium_discount', 'Premium/Discount Zone'),
            ('mitigation', 'Mitigation Block'),
        ]
    )
    direction = models.CharField(
        max_length=10,
        choices=[
            ('bullish', 'Bullish'),
            ('bearish', 'Bearish'),
        ]
    )
    price_zone = models.JSONField(default=dict)
    confidence = models.IntegerField(default=50)
    timeframe = models.CharField(max_length=10)
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'smart money event'
        verbose_name_plural = 'smart money events'
        db_table = 'analytics_smart_money_events'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.symbol} - {self.event_type}"
