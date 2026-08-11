"""Cached signal generation service for performance optimization."""
from decimal import Decimal
from typing import Dict, Optional
from apps.core.caching import cached, MarketDataCache, SignalCache, CACHE_TIMEOUT_MEDIUM
from apps.signals.services.signal_generator import SignalGenerator


class CachedSignalGenerator:
    """Signal generator with Redis caching for frequently-called methods."""
    
    def __init__(self):
        self.generator = SignalGenerator()
    
    @cached(timeout=CACHE_TIMEOUT_MEDIUM, prefix="signal:generate")
    def generate_signal(
        self,
        symbol: str,
        timeframe: str,
        current_price: Decimal,
        technical_data: Optional[Dict] = None,
        sentiment_data: Optional[Dict] = None,
        news_data: Optional[Dict] = None,
        ai_data: Optional[Dict] = None,
    ) -> Dict:
        """Generate a trading signal with caching."""
        return self.generator.generate_signal(
            symbol=symbol,
            timeframe=timeframe,
            current_price=current_price,
            technical_data=technical_data,
            sentiment_data=sentiment_data,
            news_data=news_data,
            ai_data=ai_data,
        )
    
    def get_latest_signal(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """Get latest cached signal for a symbol."""
        return SignalCache.get_latest_signal(symbol, timeframe)
    
    def invalidate_symbol_cache(self, symbol: str):
        """Invalidate all cached data for a symbol."""
        SignalCache.invalidate_symbol_cache(symbol)
