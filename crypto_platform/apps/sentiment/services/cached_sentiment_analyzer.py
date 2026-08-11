"""Cached sentiment analysis service for performance optimization."""
from typing import Dict, Optional
from apps.core.caching import cached, SentimentCache, CACHE_TIMEOUT_MEDIUM
from apps.sentiment.services.aggregator import SentimentAggregator


class CachedSentimentAnalyzer:
    """Sentiment analyzer with Redis caching for frequently-called methods."""
    
    def __init__(self):
        self.aggregator = SentimentAggregator()
    
    @cached(timeout=CACHE_TIMEOUT_MEDIUM, prefix="sentiment:fear_greed")
    def get_fear_greed_index(self) -> Dict:
        """Get Fear & Greed Index with caching."""
        return self.aggregator.get_fear_greed_index()
    
    @cached(timeout=CACHE_TIMEOUT_MEDIUM, prefix="sentiment:social")
    def analyze_social_sentiment(self, symbol: str) -> Dict:
        """Analyze social sentiment for a symbol with caching."""
        return self.aggregator.analyze_social_sentiment(symbol)
    
    @cached(timeout=CACHE_TIMEOUT_MEDIUM, prefix="sentiment:aggregate")
    def aggregate_sentiment(self, symbol: str) -> Dict:
        """Aggregate all sentiment sources for a symbol with caching."""
        return self.aggregator.aggregate_sentiment(symbol)
    
    def invalidate_symbol_cache(self, symbol: str):
        """Invalidate all cached sentiment data for a symbol."""
        SentimentCache.invalidate_symbol_cache(symbol)
