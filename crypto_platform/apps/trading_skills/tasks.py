"""Celery tasks for trading skills."""
from celery import shared_task
from celery.utils.log import get_task_logger
import asyncio

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=2)
def run_crypto_regime_analysis(self):
    """Periodically run crypto regime analysis and store results."""
    from .services.skills_engine import TradingSkillsEngine
    from .models import RegimeAnalysis
    from apps.market.exchanges.coingecko import CoinGeckoExchange

    async def _collect_data():
        """Collect market data from CoinGecko for regime analysis."""
        ex = CoinGeckoExchange()
        try:
            # Get universe of top coins
            market_data = await ex.fetch_market_data()

            # Get price history for top coins
            series = {}
            ids_to_symbols = {}

            # Get BTC history first (most important)
            btc_candles = await ex.fetch_ohlcv("BTCUSDT", "1d", 365)
            if btc_candles:
                series["BTC"] = [float(c.close) for c in btc_candles]

            # Get top alt histories
            alt_symbols = ["ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "DOTUSDT", "AVAXUSDT", "LINKUSDT"]
            for symbol in alt_symbols:
                try:
                    candles = await ex.fetch_ohlcv(symbol, "1d", 365)
                    if candles:
                        coin_name = symbol.replace("USDT", "").lower()
                        series[coin_name] = [float(c.close) for c in candles]
                except Exception:
                    pass

            return {
                "series": series,
                "funding": {},  # CoinGecko doesn't provide funding
                "dominance_series": [],  # Need accumulation over time
            }
        finally:
            await ex.close()

    try:
        market_data = asyncio.run(_collect_data())

        if not market_data.get("series", {}).get("BTC"):
            logger.warning("No BTC data collected, skipping regime analysis")
            return

        engine = TradingSkillsEngine()
        result = asyncio.run(engine.run_crypto_regime_analysis(market_data))

        # Store result
        RegimeAnalysis.objects.create(
            composite_score=result.get("composite", {}).get("score"),
            zone=result.get("composite", {}).get("zone", "UNKNOWN"),
            guidance=result.get("composite", {}).get("guidance", ""),
            components=result.get("components", {}),
            exposure_posture=result.get("exposure", {}),
            universe_size=result.get("metadata", {}).get("universe_size", 0),
        )

        logger.info(f"Regime analysis: {result['composite']['zone']} ({result['composite']['score']}/100)")
        return result

    except Exception as e:
        logger.error(f"Regime analysis failed: {e}")
        raise self.retry(exc=e, countdown=300)
