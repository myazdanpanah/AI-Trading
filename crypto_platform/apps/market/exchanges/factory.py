"""Exchange factory for creating exchange instances."""
from typing import Dict, Type
from .base import BaseExchange
from .binance import BinanceExchange
from .bybit import BybitExchange
from .okx import OKXExchange


class ExchangeFactory:
    """Factory for creating exchange instances."""

    _exchanges: Dict[str, Type[BaseExchange]] = {
        'binance': BinanceExchange,
        'bybit': BybitExchange,
        'okx': OKXExchange,
    }

    @classmethod
    def create(cls, exchange_name: str, api_key: str = '', api_secret: str = '', **kwargs) -> BaseExchange:
        """Create an exchange instance."""
        exchange_class = cls._exchanges.get(exchange_name.lower())
        if not exchange_class:
            raise ValueError(f"Unknown exchange: {exchange_name}. Available: {list(cls._exchanges.keys())}")
        return exchange_class(api_key=api_key, api_secret=api_secret, **kwargs)

    @classmethod
    def register(cls, name: str, exchange_class: Type[BaseExchange]):
        """Register a new exchange."""
        cls._exchanges[name.lower()] = exchange_class

    @classmethod
    def available(cls) -> list:
        """List available exchanges."""
        return list(cls._exchanges.keys())


# Default exchange instances
async def get_default_exchanges() -> Dict[str, BaseExchange]:
    """Get default exchange instances (no API keys needed for public data)."""
    return {
        'binance': ExchangeFactory.create('binance'),
        'bybit': ExchangeFactory.create('bybit'),
        'okx': ExchangeFactory.create('okx'),
    }
