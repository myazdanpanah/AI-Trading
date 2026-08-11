"""Base CCXT exchange adapter - eliminates code duplication."""
import ccxt.async_support as ccxt
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
from .base import BaseExchange, OHLCV, OrderBook, OrderBookLevel, FundingRate, OpenInterest
import asyncio


class CCXTExchange(BaseExchange):
    """Base class for CCXT-based exchanges."""

    # Subclasses must set this
    exchange_class = None
    default_config = {}

    def __init__(self, api_key: str = '', api_secret: str = '', testnet: bool = False, **kwargs):
        super().__init__(api_key, api_secret)
        
        config = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            **self.default_config,
            **kwargs,
        }
        
        if testnet and hasattr(self.exchange_class, 'urls'):
            config['options'] = config.get('options', {})
            config['options']['sandboxMode'] = True
        
        self.exchange = self.exchange_class(config)

    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> List[OHLCV]:
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return [
                OHLCV(
                    symbol=symbol,
                    timeframe=timeframe,
                    open=Decimal(str(candle[1])),
                    high=Decimal(str(candle[2])),
                    low=Decimal(str(candle[3])),
                    close=Decimal(str(candle[4])),
                    volume=Decimal(str(candle[5])),
                    timestamp=datetime.fromtimestamp(candle[0] / 1000)
                )
                for candle in ohlcv
            ]
        except Exception as e:
            print(f"Error fetching OHLCV from {self.name}: {e}")
            return []

    async def fetch_order_book(self, symbol: str, limit: int = 20) -> OrderBook:
        try:
            orderbook = await self.exchange.fetch_order_book(symbol, limit=limit)
            return OrderBook(
                symbol=symbol,
                bids=[OrderBookLevel(
                    price=Decimal(str(level[0])),
                    amount=Decimal(str(level[1]))
                ) for level in orderbook['bids']],
                asks=[OrderBookLevel(
                    price=Decimal(str(level[0])),
                    amount=Decimal(str(level[1]))
                ) for level in orderbook['asks']],
                timestamp=datetime.now()
            )
        except Exception as e:
            print(f"Error fetching order book from {self.name}: {e}")
            return OrderBook(symbol=symbol, bids=[], asks=[], timestamp=datetime.now())

    async def fetch_ticker(self, symbol: str) -> Dict:
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'last': ticker.get('last'),
                'bid': ticker.get('bid'),
                'ask': ticker.get('ask'),
                'high': ticker.get('high'),
                'low': ticker.get('low'),
                'volume': ticker.get('baseVolume'),
                'quoteVolume': ticker.get('quoteVolume'),
                'percentage': ticker.get('percentage'),
            }
        except Exception as e:
            print(f"Error fetching ticker from {self.name}: {e}")
            return {}

    async def fetch_funding_rate(self, symbol: str) -> FundingRate:
        try:
            funding = await self.exchange.fetch_funding_rate(symbol)
            return FundingRate(
                symbol=symbol,
                rate=Decimal(str(funding.get('fundingRate', 0))),
                timestamp=datetime.now()
            )
        except Exception as e:
            print(f"Error fetching funding rate from {self.name}: {e}")
            return FundingRate(symbol=symbol, rate=Decimal('0'), timestamp=datetime.now())

    async def fetch_open_interest(self, symbol: str) -> OpenInterest:
        try:
            oi = await self.exchange.fetch_open_interest(symbol)
            return OpenInterest(
                symbol=symbol,
                amount=Decimal(str(oi.get('openInterestAmount', 0))),
                value=Decimal(str(oi.get('openInterestValue', 0))),
                timestamp=datetime.now()
            )
        except Exception as e:
            print(f"Error fetching open interest from {self.name}: {e}")
            return OpenInterest(symbol=symbol, amount=Decimal('0'), value=Decimal('0'), timestamp=datetime.now())

    async def fetch_all_tickers(self) -> Dict:
        try:
            tickers = await self.exchange.fetch_tickers()
            return {
                symbol: {
                    'last': ticker.get('last'),
                    'volume': ticker.get('baseVolume'),
                    'percentage': ticker.get('percentage'),
                }
                for symbol, ticker in tickers.items()
            }
        except Exception as e:
            print(f"Error fetching all tickers from {self.name}: {e}")
            return {}

    async def close(self):
        await self.exchange.close()
