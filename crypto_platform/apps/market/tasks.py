"""Celery tasks for market data collection."""
from celery import shared_task
from celery.utils.log import get_task_logger
import asyncio

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3)
def collect_market_data(self, symbols=None, timeframes=None):
    """Collect market data from exchanges."""
    from .services.collector import MarketDataCollector
    
    if symbols is None:
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    if timeframes is None:
        timeframes = ['1h', '4h', '1d']
    
    async def _collect():
        collector = MarketDataCollector()
        try:
            await collector.initialize([
                {'name': 'binance'},
                {'name': 'bybit'},
                {'name': 'okx'},
            ])
            result = await collector.collect_all(symbols, timeframes)
            return result
        finally:
            await collector.close_all()
    
    try:
        result = asyncio.run(_collect())
        logger.info(f"Market data collection completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Market data collection failed: {e}")
        raise self.retry(exc=e, countdown=60)


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
def collect_derivatives_task(exchange_name: str, symbol: str):
    """Collect derivatives data for a specific pair."""
    from .services.collector import MarketDataCollector
    
    async def _collect():
        collector = MarketDataCollector()
        try:
            await collector.initialize([{'name': exchange_name}])
            result = await collector.collect_derivatives(exchange_name, symbol)
            return f"Collected derivatives for {symbol}"
        finally:
            await collector.close_all()
    
    return asyncio.run(_collect())


@shared_task
def get_rate_limit_stats():
    """Get rate limiting statistics."""
    from .services.rate_limiter import rate_limiter
    return rate_limiter.get_all_stats()
