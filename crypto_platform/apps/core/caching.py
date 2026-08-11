"""Redis caching utilities for performance optimization."""
import hashlib
import json
from functools import wraps
from typing import Any, Callable, Optional
from django.core.cache import cache
from django.conf import settings


# Cache timeout constants (in seconds)
CACHE_TIMEOUT_SHORT = 60 * 5      # 5 minutes
CACHE_TIMEOUT_MEDIUM = 60 * 15    # 15 minutes
CACHE_TIMEOUT_LONG = 60 * 60      # 1 hour
CACHE_TIMEOUT_VERY_LONG = 60 * 60 * 24  # 24 hoursdef make_cache_key(*args, **kwargs) -> str:
    """Generate a deterministic cache key from arguments."""
    try:
        key_parts = [str(a) for a in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        raw_key =":".join(key_parts)
        return hashlib.md5(raw_key.encode()).hexdigest()
    except TypeError:
        # Handle unhashable types (lists, dicts) by JSON serialization
        import json
        raw_key = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True, default=str)
        return hashlib.md5(raw_key.encode()).hexdigest()


def cached(timeout: int = CACHE_TIMEOUT_MEDIUM, prefix: str = ""):
    """Decorator for caching function results in Redis."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Build cache key from function name and arguments
            cache_key = f"{prefix}:{func.__name__}:{make_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Compute and cache
            result = func(*args, **kwargs)
            if result is not None:
                cache.set(cache_key, result, timeout=timeout)
            return result
        
        # Add cache invalidation helper
        wrapper.invalidate = lambda *a, **kw: cache.delete(
            f"{prefix}:{func.__name__}:{make_cache_key(*a, **kw)}"
        )
        wrapper.cache_key = lambda *a, **kw: f"{prefix}:{func.__name__}:{make_cache_key(*a, **kw)}"
        
        return wrapper
    return decorator


def invalidate_pattern(pattern: str) -> int:
    """Invalidate all cache keys matching a pattern (Redis only)."""
    try:
        from django_redis import get_redis_connection
        conn = get_redis_connection("default")
        keys = conn.keys(f"*{pattern}*")
        if keys:
            return conn.delete(*keys)
    except ImportError:
        # django-redis not installed
        pass
    except ConnectionError:
        # Redis connection failed
        pass
    return 0


class MarketDataCache:
    """Specialized cache for market data with shorter TTLs."""
    
    @staticmethod
    def get_ticker(symbol: str) -> Optional[dict]:
        return cache.get(f"ticker:{symbol}")
    
    @staticmethod
    def set_ticker(symbol: str, data: dict, timeout: int = CACHE_TIMEOUT_SHORT):
        cache.set(f"ticker:{symbol}", data, timeout=timeout)
    
    @staticmethod
    def get_ohlcv(symbol: str, timeframe: str) -> Optional[list]:
        return cache.get(f"ohlcv:{symbol}:{timeframe}")
    
    @staticmethod
    def set_ohlcv(symbol: str, timeframe: str, data: list, timeout: int = CACHE_TIMEOUT_SHORT):
        cache.set(f"ohlcv:{symbol}:{timeframe}", data, timeout=timeout)
    
    @staticmethod
    def get_orderbook(symbol: str) -> Optional[dict]:
        return cache.get(f"orderbook:{symbol}")
    
    @staticmethod
    def set_orderbook(symbol: str, data: dict, timeout: int = 30):  # 30 seconds for orderbook
        cache.set(f"orderbook:{symbol}", data, timeout=timeout)
    
    @staticmethod
    def invalidate_symbol(symbol: str):
        invalidate_pattern(symbol)


class SignalCache:
    """Cache for generated signals."""
    
    @staticmethod
    def get_latest_signal(symbol: str, timeframe: str) -> Optional[dict]:
        return cache.get(f"signal:latest:{symbol}:{timeframe}")
    
    @staticmethod
    def set_latest_signal(symbol: str, timeframe: str, signal: dict, timeout: int = CACHE_TIMEOUT_MEDIUM):
        cache.set(f"signal:latest:{symbol}:{timeframe}", signal, timeout=timeout)
    
    @staticmethod
    def get_signal_history(symbol: str) -> Optional[list]:
        return cache.get(f"signal:history:{symbol}")
    
    @staticmethod
    def set_signal_history(symbol: str, signals: list, timeout: int = CACHE_TIMEOUT_LONG):
        cache.set(f"signal:history:{symbol}", signals, timeout=timeout)


class SentimentCache:
    """Cache for sentiment data."""
    
    @staticmethod
    def get_fear_greed() -> Optional[dict]:
        return cache.get("sentiment:fear_greed")
    
    @staticmethod
    def set_fear_greed(data: dict, timeout: int = CACHE_TIMEOUT_MEDIUM):
        cache.set("sentiment:fear_greed", data, timeout=timeout)
    
    @staticmethod
    def get_social_sentiment(symbol: str) -> Optional[dict]:
        return cache.get(f"sentiment:social:{symbol}")
    
    @staticmethod
    def set_social_sentiment(symbol: str, data: dict, timeout: int = CACHE_TIMEOUT_MEDIUM):
        cache.set(f"sentiment:social:{symbol}", data, timeout=timeout)
