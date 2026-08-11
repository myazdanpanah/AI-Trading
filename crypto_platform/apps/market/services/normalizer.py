"""Data normalizer for standardizing exchange formats."""
from typing import Dict, List, Optional
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from dataclasses import dataclass
import hashlib
import json


@dataclass
class NormalizedCandle:
    """Normalized candle data."""
    symbol: str
    exchange: str
    timeframe: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    timestamp: datetime
    quote_volume: Optional[Decimal] = None
    trades_count: Optional[int] = None

    @property
    def hash(self) -> str:
        """Generate unique hash for deduplication."""
        data = f"{self.symbol}:{self.exchange}:{self.timeframe}:{self.timestamp}"
        return hashlib.md5(data.encode()).hexdigest()


@dataclass
class NormalizedOrderBook:
    """Normalized order book data."""
    symbol: str
    exchange: str
    bids: List[Dict]
    asks: List[Dict]
    timestamp: datetime
    bid_total: Decimal = Decimal('0')
    ask_total: Decimal = Decimal('0')
    spread: Decimal = Decimal('0')
    spread_percent: Decimal = Decimal('0')

    def calculate_metrics(self):
        """Calculate order book metrics."""
        if self.bids and self.asks:
            self.bid_total = sum(Decimal(str(b.get('amount', 0))) for b in self.bids)
            self.ask_total = sum(Decimal(str(a.get('amount', 0))) for a in self.asks)
            self.spread = Decimal(str(self.asks[0]['price'])) - Decimal(str(self.bids[0]['price']))
            mid_price = (Decimal(str(self.asks[0]['price'])) + Decimal(str(self.bids[0]['price']))) / 2
            if mid_price > 0:
                self.spread_percent = (self.spread / mid_price) * 100


@dataclass
class NormalizedDerivatives:
    """Normalized derivatives data."""
    symbol: str
    exchange: str
    funding_rate: Decimal
    funding_rate_hourly: Decimal
    open_interest: Decimal
    timestamp: datetime
    open_interest_usd: Optional[Decimal] = None
    long_short_ratio: Optional[Decimal] = None

    @classmethod
    def from_funding(cls, symbol: str, exchange: str, rate: Decimal, timestamp: datetime):
        """Create from funding rate only."""
        return cls(
            symbol=symbol,
            exchange=exchange,
            funding_rate=rate,
            funding_rate_hourly=rate / 8,  # 8 funding intervals per day
            open_interest=Decimal('0'),
            timestamp=timestamp
        )


class DataNormalizer:
    """Normalizes data from different exchanges."""

    # Timeframe mapping from exchange formats to standard
    TIMEFRAME_MAP = {
        '1m': '1m', '1min': '1m', 'M1': '1m',
        '5m': '5m', '5min': '5m', 'M5': '5m',
        '15m': '15m', '15min': '15m', 'M15': '15m',
        '30m': '30m', '30min': '30m', 'M30': '30m',
        '1h': '1h', '60m': '1h', 'H1': '1h',
        '4h': '4h', '240m': '4h', 'H4': '4h',
        '12h': '12h', '720m': '12h', 'H12': '12h',
        '1d': '1d', 'D1': '1d', '1D': '1d',
        '1w': '1w', 'W1': '1w', '1W': '1w',
        '1M': '1M', '1month': '1M',
    }

    # Symbol mapping for OKX (exchange-specific)
    OKX_SYMBOL_MAP = {
        'BTC-USDT-SWAP': 'BTCUSDT',
        'ETH-USDT-SWAP': 'ETHUSDT',
        'SOL-USDT-SWAP': 'SOLUSDT',
        'BTC-USDT': 'BTCUSDT',
        'ETH-USDT': 'ETHUSDT',
        'SOL-USDT': 'SOLUSDT',
    }

    @classmethod
    def normalize_timeframe(cls, timeframe: str) -> str:
        """Normalize timeframe format."""
        return cls.TIMEFRAME_MAP.get(timeframe, timeframe.lower())

    @classmethod
    def normalize_symbol(cls, symbol: str, exchange: str) -> str:
        """Normalize symbol format across exchanges."""
        symbol = symbol.upper()
        
        # Exchange-specific normalization
        if exchange == 'okx':
            # Use predefined mapping for OKX
            return cls.OKX_SYMBOL_MAP.get(symbol, symbol.replace('-', '').replace('-SWAP', ''))
        
        return symbol

    @classmethod
    def normalize_decimal(cls, value, precision: int = 8) -> Decimal:
        """Normalize decimal value with specified precision."""
        if value is None:
            return Decimal('0')
        
        if isinstance(value, str):
            value = Decimal(value)
        elif isinstance(value, (int, float)):
            value = Decimal(str(value))
        
        # Quantize to precision
        quantizer = Decimal(10) ** -precision
        return value.quantize(quantizer, rounding=ROUND_HALF_UP)

    @classmethod
    def normalize_candle(cls, data: Dict, exchange: str) -> NormalizedCandle:
        """Normalize candle data from exchange format."""
        return NormalizedCandle(
            symbol=cls.normalize_symbol(data.get('symbol', ''), exchange),
            exchange=exchange,
            timeframe=cls.normalize_timeframe(data.get('timeframe', '')),
            open=cls.normalize_decimal(data.get('open')),
            high=cls.normalize_decimal(data.get('high')),
            low=cls.normalize_decimal(data.get('low')),
            close=cls.normalize_decimal(data.get('close')),
            volume=cls.normalize_decimal(data.get('volume')),
            timestamp=data.get('timestamp', datetime.now()),
            quote_volume=cls.normalize_decimal(data.get('quote_volume')) if data.get('quote_volume') else None,
            trades_count=data.get('trades_count'),
        )

    @classmethod
    def normalize_orderbook(cls, data: Dict, exchange: str) -> NormalizedOrderBook:
        """Normalize order book data."""
        bids = []
        for bid in data.get('bids', []):
            bids.append({
                'price': str(cls.normalize_decimal(bid.get('price') or bid[0] if isinstance(bid, list) else 0)),
                'amount': str(cls.normalize_decimal(bid.get('amount') or bid[1] if isinstance(bid, list) else 0)),
            })
        
        asks = []
        for ask in data.get('asks', []):
            asks.append({
                'price': str(cls.normalize_decimal(ask.get('price') or ask[0] if isinstance(ask, list) else 0)),
                'amount': str(cls.normalize_decimal(ask.get('amount') or ask[1] if isinstance(ask, list) else 0)),
            })
        
        orderbook = NormalizedOrderBook(
            symbol=cls.normalize_symbol(data.get('symbol', ''), exchange),
            exchange=exchange,
            bids=bids,
            asks=asks,
            timestamp=data.get('timestamp', datetime.now()),
        )
        orderbook.calculate_metrics()
        return orderbook

    @classmethod
    def normalize_derivatives(cls, data: Dict, exchange: str) -> NormalizedDerivatives:
        """Normalize derivatives data."""
        funding_rate = cls.normalize_decimal(data.get('funding_rate', 0))
        
        return NormalizedDerivatives(
            symbol=cls.normalize_symbol(data.get('symbol', ''), exchange),
            exchange=exchange,
            funding_rate=funding_rate,
            funding_rate_hourly=funding_rate / 8,
            open_interest=cls.normalize_decimal(data.get('open_interest', 0)),
            open_interest_usd=cls.normalize_decimal(data.get('open_interest_usd')) if data.get('open_interest_usd') else None,
            long_short_ratio=cls.normalize_decimal(data.get('long_short_ratio')) if data.get('long_short_ratio') else None,
            timestamp=data.get('timestamp', datetime.now()),
        )
