"""Base exchange adapter - abstract interface for all exchanges."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime


@dataclass
class OHLCV:
    """OHLCV candle data."""
    symbol: str
    timeframe: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    timestamp: datetime


@dataclass
class OrderBookLevel:
    """Single order book level."""
    price: Decimal
    amount: Decimal


@dataclass
class OrderBook:
    """Order book snapshot."""
    symbol: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    timestamp: datetime


@dataclass
class FundingRate:
    """Funding rate data."""
    symbol: str
    rate: Decimal
    timestamp: datetime


@dataclass
class OpenInterest:
    """Open interest data."""
    symbol: str
    amount: Decimal
    value: Decimal
    timestamp: datetime


class BaseExchange(ABC):
    """Abstract base class for all exchange adapters."""

    name: str = "base"

    def __init__(self, api_key: str = '', api_secret: str = ''):
        self.api_key = api_key
        self.api_secret = api_secret

    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> List[OHLCV]:
        """Fetch OHLCV candle data."""
        pass

    @abstractmethod
    async def fetch_order_book(self, symbol: str, limit: int = 20) -> OrderBook:
        """Fetch order book snapshot."""
        pass

    @abstractmethod
    async def fetch_ticker(self, symbol: str) -> Dict:
        """Fetch current ticker data."""
        pass

    @abstractmethod
    async def fetch_funding_rate(self, symbol: str) -> FundingRate:
        """Fetch current funding rate."""
        pass

    @abstractmethod
    async def fetch_open_interest(self, symbol: str) -> OpenInterest:
        """Fetch open interest data."""
        pass

    @abstractmethod
    async def fetch_all_tickers(self) -> Dict:
        """Fetch all tickers."""
        pass

    @abstractmethod
    async def close(self):
        """Close the exchange connection."""
        pass
