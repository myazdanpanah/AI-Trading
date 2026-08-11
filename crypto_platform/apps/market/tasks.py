"""Celery tasks for market data collection.

Binance is blocked in Iran — system tries Binance first (works with VPN),
falls back to CoinGecko (always accessible) if Binance is unreachable.
"""
from celery import shared_task
from celery.utils.log import get_task_logger
import asyncio

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3)
def collect_market_data(self, symbols=None, timeframes=None):
    """Collect market data. Tries Binance first, falls back to CoinGecko."""
    from .services.collector import MarketDataCollector

    if symbols is None:
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT']
    if timeframes is None:
        timeframes = ['1h', '4h', '1d']

    async def _collect():
        collector = MarketDataCollector()
        try:
            # Try Binance first (needs VPN in Iran)
            try:
                await collector.initialize([{'name': 'binance'}])
                result = await collector.collect_all(symbols, timeframes)
                if any(v > 0 for v in result.values()):
                    logger.info(f"Data collected from Binance: {result}")
                    return result
            except Exception as e:
                logger.warning(f"Binance unavailable (VPN needed?): {e}")

            # Fallback to CoinGecko (always accessible)
            await collector.initialize([{'name': 'coingecko'}])
            result = await collector.collect_all(symbols, timeframes)
            logger.info(f"Data collected from CoinGecko: {result}")
            return result
        finally:
            await collector.close_all()

    try:
        result = asyncio.run(_collect())
        return result
    except Exception as e:
        logger.error(f"Market data collection failed: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task
def collect_tickers_task():
    """Collect current ticker prices for all symbols."""
    from .services.collector import MarketDataCollector

    async def _collect():
        collector = MarketDataCollector()
        try:
            # Try Binance first
            try:
                await collector.initialize([{'name': 'binance'}])
                tickers = await collector.collect_tickers()
                if tickers:
                    return tickers
            except Exception:
                pass

            # Fallback to CoinGecko
            await collector.initialize([{'name': 'coingecko'}])
            return await collector.collect_tickers()
        finally:
            await collector.close_all()

    return asyncio.run(_collect())


@shared_task
def collect_candles_task(exchange_name: str, symbol: str, timeframe: str, limit: int = 100):
    """Collect candles for a specific pair."""
    from .services.collector import MarketDataCollector

    async def _collect():
        collector = MarketDataCollector()
        try:
            await collector.initialize([{'name': exchange_name}])
            candles = await collector.collect_candles(exchange_name, symbol, timeframe, limit)
            return f"Collected {len(candles)} candles for {symbol} {timeframe}"
        finally:
            await collector.close_all()

    return asyncio.run(_collect())


@shared_task
def get_rate_limit_stats():
    """Get rate limiting statistics."""
    from .services.rate_limiter import rate_limiter
    return rate_limiter.get_all_stats()
