"""Tests for market services."""
from django.test import TestCase
from decimal import Decimal
from datetime import datetime
from .normalizer import DataNormalizer, NormalizedCandle
from .validator import DataValidator, ValidationSeverity
from .rate_limiter import RateLimiter, RateLimitConfig
import asyncio


class DataNormalizerTest(TestCase):
    def test_normalize_timeframe(self):
        self.assertEqual(DataNormalizer.normalize_timeframe('1m'), '1m')
        self.assertEqual(DataNormalizer.normalize_timeframe('1min'), '1m')
        self.assertEqual(DataNormalizer.normalize_timeframe('M1'), '1m')
        self.assertEqual(DataNormalizer.normalize_timeframe('1h'), '1h')
        self.assertEqual(DataNormalizer.normalize_timeframe('60m'), '1h')
        self.assertEqual(DataNormalizer.normalize_timeframe('H1'), '1h')

    def test_normalize_symbol(self):
        self.assertEqual(DataNormalizer.normalize_symbol('BTCUSDT', 'binance'), 'BTCUSDT')
        self.assertEqual(DataNormalizer.normalize_symbol('BTCUSDT', 'bybit'), 'BTCUSDT')
        self.assertEqual(DataNormalizer.normalize_symbol('BTC-USDT-SWAP', 'okx'), 'BTCUSDT')

    def test_normalize_decimal(self):
        self.assertEqual(DataNormalizer.normalize_decimal('123.456'), Decimal('123.45600000'))
        self.assertEqual(DataNormalizer.normalize_decimal(123.456), Decimal('123.45600000'))
        self.assertEqual(DataNormalizer.normalize_decimal(None), Decimal('0'))

    def test_normalize_candle(self):
        candle = DataNormalizer.normalize_candle({
            'symbol': 'BTCUSDT',
            'timeframe': '1h',
            'open': '50000',
            'high': '51000',
            'low': '49000',
            'close': '50500',
            'volume': '1000',
            'timestamp': datetime.now(),
        }, 'binance')
        
        self.assertEqual(candle.symbol, 'BTCUSDT')
        self.assertEqual(candle.timeframe, '1h')
        self.assertEqual(candle.open, Decimal('50000.00000000'))
        self.assertEqual(candle.exchange, 'binance')

    def test_candle_hash(self):
        candle1 = DataNormalizer.normalize_candle({
            'symbol': 'BTCUSDT', 'timeframe': '1h',
            'open': '50000', 'high': '51000', 'low': '49000',
            'close': '50500', 'volume': '1000',
            'timestamp': datetime(2024, 1, 1, 12, 0, 0),
        }, 'binance')
        candle2 = DataNormalizer.normalize_candle({
            'symbol': 'BTCUSDT', 'timeframe': '1h',
            'open': '50000', 'high': '51000', 'low': '49000',
            'close': '50500', 'volume': '1000',
            'timestamp': datetime(2024, 1, 1, 12, 0, 0),
        }, 'binance')
        self.assertEqual(candle1.hash, candle2.hash)


class DataValidatorTest(TestCase):
    def test_validate_candle_valid(self):
        result = DataValidator.validate_candle({
            'symbol': 'BTCUSDT',
            'exchange': 'binance',
            'open': '50000',
            'high': '51000',
            'low': '49000',
            'close': '50500',
            'volume': '1000',
            'timestamp': datetime.now(),
        })
        self.assertTrue(result.passed)

    def test_validate_candle_invalid_high_low(self):
        result = DataValidator.validate_candle({
            'symbol': 'BTCUSDT',
            'exchange': 'binance',
            'open': '50000',
            'high': '49000',  # High less than low
            'low': '51000',
            'close': '50500',
            'volume': '1000',
            'timestamp': datetime.now(),
        })
        self.assertFalse(result.passed)

    def test_validate_candle_missing_field(self):
        result = DataValidator.validate_candle({
            'symbol': 'BTCUSDT',
            'exchange': 'binance',
            # Missing required fields
        })
        self.assertFalse(result.passed)

    def test_validate_candle_high_less_than_open(self):
        result = DataValidator.validate_candle({
            'symbol': 'BTCUSDT',
            'exchange': 'binance',
            'open': '50000',
            'high': '49000',  # High less than open
            'low': '48000',
            'close': '50500',
            'volume': '1000',
            'timestamp': datetime.now(),
        })
        self.assertFalse(result.passed)

    def test_validate_orderbook_valid(self):
        result = DataValidator.validate_orderbook({
            'symbol': 'BTCUSDT',
            'exchange': 'binance',
            'bids': [{'price': '50000', 'amount': '1.5'}, {'price': '49999', 'amount': '2.0'}],
            'asks': [{'price': '50001', 'amount': '1.5'}, {'price': '50002', 'amount': '2.0'}],
            'timestamp': datetime.now(),
        })
        self.assertTrue(result.passed)

    def test_validate_orderbook_empty(self):
        result = DataValidator.validate_orderbook({
            'symbol': 'BTCUSDT',
            'exchange': 'binance',
            'bids': [],
            'asks': [],
            'timestamp': datetime.now(),
        })
        self.assertFalse(result.passed)

    def test_validate_derivatives_valid(self):
        result = DataValidator.validate_derivatives({
            'symbol': 'BTCUSDT',
            'exchange': 'binance',
            'funding_rate': '0.0001',
            'open_interest': '50000',
            'timestamp': datetime.now(),
        })
        self.assertTrue(result.passed)

    def test_validate_derivatives_extreme_funding(self):
        result = DataValidator.validate_derivatives({
            'symbol': 'BTCUSDT',
            'exchange': 'binance',
            'funding_rate': '0.05',  # 5% - extreme
            'open_interest': '50000',
            'timestamp': datetime.now(),
        })
        self.assertTrue(any(r.severity == ValidationSeverity.WARNING for r in result.results))

    def test_validate_derivatives_negative_oi(self):
        result = DataValidator.validate_derivatives({
            'symbol': 'BTCUSDT',
            'exchange': 'binance',
            'funding_rate': '0.0001',
            'open_interest': '-1000',  # Negative
            'timestamp': datetime.now(),
        })
        self.assertFalse(result.passed)


class RateLimiterTest(TestCase):
    def test_rate_limiter_creation(self):
        limiter = RateLimiter()
        self.assertIsNotNone(limiter)

    def test_rate_limit_stats(self):
        limiter = RateLimiter()
        stats = limiter.get_stats('binance')
        self.assertEqual(stats['exchange'], 'binance')
        self.assertEqual(stats['total_requests'], 0)
        self.assertEqual(stats['limit_per_second'], 10)
        self.assertEqual(stats['limit_per_minute'], 600)

    def test_rate_limit_config(self):
        limiter = RateLimiter()
        config = RateLimitConfig(
            requests_per_second=5,
            requests_per_minute=300,
            requests_per_hour=1800,
        )
        limiter.configure('custom', config)
        stats = limiter.get_stats('custom')
        self.assertEqual(stats['limit_per_second'], 5)

    def test_all_stats(self):
        limiter = RateLimiter()
        # Trigger stats for default exchanges
        limiter.get_stats('binance')
        limiter.get_stats('bybit')
        limiter.get_stats('okx')
        all_stats = limiter.get_all_stats()
        self.assertIn('binance', all_stats)
        self.assertIn('bybit', all_stats)
        self.assertIn('okx', all_stats)

    def test_async_acquire(self):
        """Test async acquire method."""
        limiter = RateLimiter()
        
        async def _test():
            result = await limiter.acquire('binance')
            return result
        
        result = asyncio.run(_test())
        self.assertTrue(result)
        
        # Check stats were updated
        stats = limiter.get_stats('binance')
        self.assertEqual(stats['total_requests'], 1)
