"""Market data models."""
import uuid
from django.db import models


class Exchange(models.Model):
    """Exchange configuration."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    api_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('maintenance', 'Maintenance'),
        ],
        default='active'
    )
    base_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'exchange'
        verbose_name_plural = 'exchanges'
        db_table = 'exchanges'

    def __str__(self):
        return self.name


class TradingPair(models.Model):
    """Trading pair configuration."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE, related_name='trading_pairs')
    symbol = models.CharField(max_length=20, db_index=True)
    base_asset = models.CharField(max_length=20)
    quote_asset = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    min_order_size = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    tick_size = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'trading pair'
        verbose_name_plural = 'trading pairs'
        db_table = 'trading_pairs'
        unique_together = ['exchange', 'symbol']

    def __str__(self):
        return f"{self.exchange.name} - {self.symbol}"


class Candle(models.Model):
    """OHLCV candle data."""
    id = models.BigAutoField(primary_key=True)
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(
        max_length=10,
        choices=[
            ('1m', '1 Minute'),
            ('5m', '5 Minutes'),
            ('15m', '15 Minutes'),
            ('30m', '30 Minutes'),
            ('1h', '1 Hour'),
            ('4h', '4 Hours'),
            ('12h', '12 Hours'),
            ('1d', '1 Day'),
            ('1w', '1 Week'),
            ('1M', '1 Month'),
        ],
        db_index=True
    )
    open = models.DecimalField(max_digits=20, decimal_places=8)
    high = models.DecimalField(max_digits=20, decimal_places=8)
    low = models.DecimalField(max_digits=20, decimal_places=8)
    close = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=30, decimal_places=8)
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'candle'
        verbose_name_plural = 'candles'
        db_table = 'candles'
        unique_together = ['symbol', 'timeframe', 'timestamp']
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.symbol} {self.timeframe} - {self.timestamp}"


class OrderBook(models.Model):
    """Order book snapshot."""
    id = models.BigAutoField(primary_key=True)
    symbol = models.CharField(max_length=20, db_index=True)
    bid_volume = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    ask_volume = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    spread = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    bid_depth = models.JSONField(default=dict)
    ask_depth = models.JSONField(default=dict)
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'order book'
        verbose_name_plural = 'order books'
        db_table = 'order_books'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.symbol} OrderBook - {self.timestamp}"


class DerivativesData(models.Model):
    """Derivatives market data — funding, OI, liquidations, L/S ratio, basis."""
    id = models.BigAutoField(primary_key=True)
    symbol = models.CharField(max_length=20, db_index=True)
    # Funding rate
    funding_rate = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    funding_rate_hourly = models.DecimalField(max_digits=10, decimal_places=8, default=0, help_text='Annualized funding rate')
    # Open Interest
    open_interest = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    open_interest_usd = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    open_interest_change_24h = models.DecimalField(max_digits=10, decimal_places=4, default=0, help_text='OI change in % over 24h')
    # Long/Short Ratio
    long_short_ratio = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    long_account_ratio = models.DecimalField(max_digits=5, decimal_places=4, default=0.5, help_text='Ratio of long accounts')
    short_account_ratio = models.DecimalField(max_digits=5, decimal_places=4, default=0.5, help_text='Ratio of short accounts')
    # Liquidations
    liquidations_24h = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    liquidation_longs_24h = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    liquidation_shorts_24h = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    # Basis (futures vs spot)
    basis = models.DecimalField(max_digits=10, decimal_places=6, default=0, help_text='Futures premium over spot (%)')
    annualized_basis = models.DecimalField(max_digits=10, decimal_places=4, default=0, help_text='Annualized basis (%)')
    # Options (where available)
    options_iv = models.DecimalField(max_digits=10, decimal_places=4, default=0, help_text='Implied volatility')
    put_call_ratio = models.DecimalField(max_digits=10, decimal_places=4, default=1, help_text='Put/Call volume ratio')
    # Timestamps
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'derivatives data'
        verbose_name_plural = 'derivatives data'
        db_table = 'derivatives_data'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.symbol} Derivatives - {self.timestamp}"


class WhaleAlert(models.Model):
    """Large transaction alerts."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    amount = models.DecimalField(max_digits=30, decimal_places=8)
    usd_value = models.DecimalField(max_digits=20, decimal_places=2)
    from_address = models.CharField(max_length=100)
    to_address = models.CharField(max_length=100)
    transaction_type = models.CharField(
        max_length=20,
        choices=[
            ('exchange_inflow', 'Exchange Inflow'),
            ('exchange_outflow', 'Exchange Outflow'),
            ('whale_transfer', 'Whale Transfer'),
        ]
    )
    tx_hash = models.CharField(max_length=100, unique=True)
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'whale alert'
        verbose_name_plural = 'whale alerts'
        db_table = 'whale_alerts'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.symbol} Whale Alert - {self.amount}"
