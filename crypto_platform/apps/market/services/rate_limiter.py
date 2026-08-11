"""Rate limiter for API throttling."""
import asyncio
import time
from typing import Dict, Optional
from collections import defaultdict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration for an exchange."""
    requests_per_second: float = 10
    requests_per_minute: int = 600
    requests_per_hour: int = 3600
    burst_size: int = 20  # Max burst requests


@dataclass
class RateLimitState:
    """Current state of rate limiting."""
    requests_this_second: int = 0
    requests_this_minute: int = 0
    requests_this_hour: int = 0
    last_second_reset: float = 0
    last_minute_reset: float = 0
    last_hour_reset: float = 0
    total_requests: int = 0
    total_throttled: int = 0


class RateLimiter:
    """Rate limiter for exchange API calls."""

    # Default rate limits per exchange
    DEFAULT_LIMITS = {
        'binance': RateLimitConfig(
            requests_per_second=10,
            requests_per_minute=600,
            requests_per_hour=3600,
            burst_size=20,
        ),
        'bybit': RateLimitConfig(
            requests_per_second=10,
            requests_per_minute=600,
            requests_per_hour=3600,
            burst_size=20,
        ),
        'okx': RateLimitConfig(
            requests_per_second=20,
            requests_per_minute=1200,
            requests_per_hour=7200,
            burst_size=30,
        ),
    }

    def __init__(self):
        self._states: Dict[str, RateLimitState] = defaultdict(RateLimitState)
        self._configs: Dict[str, RateLimitConfig] = dict(self.DEFAULT_LIMITS)
        # Pre-create locks for known exchanges
        self._locks: Dict[str, asyncio.Lock] = {
            exchange: asyncio.Lock() for exchange in self.DEFAULT_LIMITS
        }

    def configure(self, exchange: str, config: RateLimitConfig):
        """Configure rate limits for an exchange."""
        self._configs[exchange] = config
        if exchange not in self._locks:
            self._locks[exchange] = asyncio.Lock()

    def _get_lock(self, exchange: str) -> asyncio.Lock:
        """Get or create lock for exchange."""
        if exchange not in self._locks:
            self._locks[exchange] = asyncio.Lock()
        return self._locks[exchange]

    def _reset_counters(self, state: RateLimitState, config: RateLimitConfig):
        """Reset rate limit counters if time window has passed."""
        now = time.time()

        if now - state.last_second_reset >= 1.0:
            state.requests_this_second = 0
            state.last_second_reset = now

        if now - state.last_minute_reset >= 60.0:
            state.requests_this_minute = 0
            state.last_minute_reset = now

        if now - state.last_hour_reset >= 3600.0:
            state.requests_this_hour = 0
            state.last_hour_reset = now

    def _calculate_wait_time(self, state: RateLimitState, config: RateLimitConfig) -> float:
        """Calculate wait time needed before next request."""
        wait_times = []

        if state.requests_this_second >= config.requests_per_second:
            wait_times.append(1.0 - (time.time() - state.last_second_reset))

        if state.requests_this_minute >= config.requests_per_minute:
            wait_times.append(60.0 - (time.time() - state.last_minute_reset))

        if state.requests_this_hour >= config.requests_per_hour:
            wait_times.append(3600.0 - (time.time() - state.last_hour_reset))

        return max(wait_times) if wait_times else 0

    async def acquire(self, exchange: str) -> bool:
        """Acquire rate limit permission for an exchange."""
        lock = self._get_lock(exchange)
        async with lock:
            state = self._states[exchange]
            config = self._configs.get(exchange, RateLimitConfig())

            self._reset_counters(state, config)

            wait_time = self._calculate_wait_time(state, config)
            if wait_time > 0:
                logger.debug(f"Rate limited for {exchange}, waiting {wait_time:.2f}s")
                state.total_throttled += 1
                await asyncio.sleep(wait_time)
                self._reset_counters(state, config)

            state.requests_this_second += 1
            state.requests_this_minute += 1
            state.requests_this_hour += 1
            state.total_requests += 1

            return True

    async def wait_if_needed(self, exchange: str):
        """Wait if rate limit would be exceeded."""
        await self.acquire(exchange)

    def get_stats(self, exchange: str) -> Dict:
        """Get rate limit statistics for an exchange."""
        state = self._states[exchange]
        config = self._configs.get(exchange, RateLimitConfig())
        return {
            'exchange': exchange,
            'requests_this_second': state.requests_this_second,
            'requests_this_minute': state.requests_this_minute,
            'requests_this_hour': state.requests_this_hour,
            'limit_per_second': config.requests_per_second,
            'limit_per_minute': config.requests_per_minute,
            'limit_per_hour': config.requests_per_hour,
            'total_requests': state.total_requests,
            'total_throttled': state.total_throttled,
            'throttle_rate': state.total_throttled / max(state.total_requests, 1) * 100,
        }

    def get_all_stats(self) -> Dict:
        """Get statistics for all exchanges."""
        return {exchange: self.get_stats(exchange) for exchange in self._states}


# Global rate limiter instance
rate_limiter = RateLimiter()
