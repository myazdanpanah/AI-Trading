"""Market data collector service with normalizer, validator, and rate limiter."""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from ..exchanges.factory import ExchangeFactory
from ..models import Candle, OrderBook, DerivativesData, Exchange, TradingPair
from .normalizer import DataNormalizer
from .validator import DataValidator, ValidationSeverity
from .rate_limiter import rate_limiter
import logging

logger = logging.getLogger(__name__)


class MarketDataCollector:
    """Collects market data from multiple exchanges with validation."""

    def __init__(self):
        self.exchanges: Dict = {}
        self.validation_errors: List = []

    async def initialize(self, exchange_configs: List[Dict]):
        """Initialize exchange connections."""
        for config in exchange_configs:
            name = config['name']
            api_key = config.get('api_key', '')
            api_secret = config.get('api_secret', '')
            testnet = config.get('testnet', False)
            
            try:
                exchange = ExchangeFactory.create(
                    name, api_key=api_key, api_secret=api_secret, testnet=testnet
                )
                self.exchanges[name] = exchange
                logger.info(f"Initialized {name} exchange")
            except Exception as e:
                logger.error(f"Failed to initialize {name}: {e}")

    async def collect_candles(self, exchange_name: str, symbol: str, timeframe: str, limit: int = 100) -> List:
        """Collect candle data with normalization and validation."""
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            raise ValueError(f"Exchange {exchange_name} not initialized")

        # Rate limiting
        await rate_limiter.wait_if_needed(exchange_name)

        try:
            ohlcv_data = await exchange.fetch_ohlcv(symbol, timeframe, limit)
            candles = []
            
            for data in ohlcv_data:
                # Normalize data
                normalized = DataNormalizer.normalize_candle({
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'open': data.open,
                    'high': data.high,
                    'low': data.low,
                    'close': data.close,
                    'volume': data.volume,
                    'timestamp': data.timestamp,
                }, exchange_name)

                # Validate data
                validation = DataValidator.validate_candle({
                    'symbol': normalized.symbol,
                    'exchange': normalized.exchange,
                    'open': normalized.open,
                    'high': normalized.high,
                    'low': normalized.low,
                    'close': normalized.close,
                    'volume': normalized.volume,
                    'timestamp': normalized.timestamp,
                })

                if not validation.passed:
                    logger.warning(f"Validation failed for {symbol}: {validation.to_dict()}")
                    self.validation_errors.append(validation.to_dict())
                    continue

                # Save to database
                candle = await asyncio.to_thread(
                    self._save_candle,
                    normalized
                )
                candles.append(candle)
            
            logger.info(f"Collected {len(candles)} candles for {symbol} {timeframe} from {exchange_name}")
            return candles
        except Exception as e:
            logger.error(f"Error collecting candles: {e}")
            return []

    def _save_candle(self, normalized) -> object:
        """Save normalized candle to database (sync helper)."""
        candle, created = Candle.objects.update_or_create(
            symbol=normalized.symbol,
            timeframe=normalized.timeframe,
            timestamp=normalized.timestamp,
            defaults={
                'open': normalized.open,
                'high': normalized.high,
                'low': normalized.low,
                'close': normalized.close,
                'volume': normalized.volume,
            }
        )
        return candle

    async def collect_orderbook(self, exchange_name: str, symbol: str, limit: int = 20) -> Optional[object]:
        """Collect order book data with normalization and validation."""
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            raise ValueError(f"Exchange {exchange_name} not initialized")

        # Rate limiting
        await rate_limiter.wait_if_needed(exchange_name)

        try:
            ob_data = await exchange.fetch_order_book(symbol, limit)
            
            # Normalize data
            normalized = DataNormalizer.normalize_orderbook({
                'symbol': symbol,
                'bids': [{'price': str(l.price), 'amount': str(l.amount)} for l in ob_data.bids],
                'asks': [{'price': str(l.price), 'amount': str(l.amount)} for l in ob_data.asks],
                'timestamp': ob_data.timestamp,
            }, exchange_name)

            # Validate data
            validation = DataValidator.validate_orderbook({
                'symbol': normalized.symbol,
                'exchange': normalized.exchange,
                'bids': normalized.bids,
                'asks': normalized.asks,
                'timestamp': normalized.timestamp,
            })

            if not validation.passed:
                logger.warning(f"Order book validation failed for {symbol}: {validation.to_dict()}")
                self.validation_errors.append(validation.to_dict())
                return None

            # Save to database
            orderbook = await asyncio.to_thread(
                self._save_orderbook,
                normalized
            )
            return orderbook
        except Exception as e:
            logger.error(f"Error collecting orderbook: {e}")
            return None

    def _save_orderbook(self, normalized) -> object:
        """Save normalized order book to database (sync helper)."""
        orderbook, created = OrderBook.objects.update_or_create(
            symbol=normalized.symbol,
            timestamp=normalized.timestamp,
            defaults={
                'bid_volume': normalized.bid_total,
                'ask_volume': normalized.ask_total,
                'spread': normalized.spread,
                'bid_depth': normalized.bids[:20],
                'ask_depth': normalized.asks[:20],
            }
        )
        return orderbook

    async def collect_derivatives(self, exchange_name: str, symbol: str) -> Optional[object]:
        """Collect derivatives data with normalization and validation."""
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            raise ValueError(f"Exchange {exchange_name} not initialized")

        # Rate limiting
        await rate_limiter.wait_if_needed(exchange_name)

        try:
            funding = await exchange.fetch_funding_rate(symbol)
            oi = await exchange.fetch_open_interest(symbol)
            
            # Normalize data
            normalized = DataNormalizer.normalize_derivatives({
                'symbol': symbol,
                'funding_rate': funding.rate,
                'open_interest': oi.amount,
                'open_interest_usd': oi.value,
                'timestamp': datetime.now(),
            }, exchange_name)

            # Validate data
            validation = DataValidator.validate_derivatives({
                'symbol': normalized.symbol,
                'exchange': normalized.exchange,
                'funding_rate': normalized.funding_rate,
                'open_interest': normalized.open_interest,
                'timestamp': normalized.timestamp,
            })

            if not validation.passed:
                logger.warning(f"Derivatives validation failed for {symbol}: {validation.to_dict()}")
                self.validation_errors.append(validation.to_dict())
                return None

            # Save to database
            derivatives = await asyncio.to_thread(
                self._save_derivatives,
                normalized
            )
            return derivatives
        except Exception as e:
            logger.error(f"Error collecting derivatives: {e}")
            return None

    def _save_derivatives(self, normalized) -> object:
        """Save normalized derivatives to database (sync helper)."""
        derivatives, created = DerivativesData.objects.update_or_create(
            symbol=normalized.symbol,
            timestamp=normalized.timestamp,
            defaults={
                'exchange': normalized.exchange,
                'funding_rate': normalized.funding_rate,
                'open_interest': normalized.open_interest,
                'open_interest_usd': normalized.open_interest_usd or 0,
            }
        )
        return derivatives

    async def collect_all(self, symbols: List[str], timeframes: List[str]) -> Dict:
        """Collect all market data."""
        results = {}
        for exchange_name in self.exchanges:
            for symbol in symbols:
                for tf in timeframes:
                    candles = await self.collect_candles(exchange_name, symbol, tf)
                    results[f"{exchange_name}:{symbol}:{tf}"] = len(candles)
        return results

    async def collect_tickers(self) -> Dict:
        """Collect current ticker data for all symbols."""
        tickers = {}
        for exchange_name, exchange in self.exchanges.items():
            try:
                if hasattr(exchange, 'fetch_market_data'):
                    market_data = await exchange.fetch_market_data()
                    tickers.update(market_data)
                else:
                    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT']
                    for symbol in symbols:
                        ticker = await exchange.fetch_ticker(symbol)
                        if ticker:
                            tickers[symbol] = ticker
            except Exception as e:
                logger.error(f"Failed to collect tickers from {exchange_name}: {e}")
        return tickers

    async def close_all(self):
        """Close all exchange connections."""
        for exchange in self.exchanges.values():
            try:
                await exchange.close()
            except Exception as e:
                logger.error(f"Error closing exchange: {e}")
