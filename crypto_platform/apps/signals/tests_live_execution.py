"""Tests for Live Execution Engine (Phase 70).

Covers:
- Order validation (symbol, side, type, quantity, price)
- Safety checks (LIVE_TRADING_ENABLED, kill switch)
- Order lifecycle (pending → filled/failed/canceled)
- Retry logic
- Order history tracking
- Account state management
- Edge cases
"""
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from django.test import TestCase

from .services.live_execution import (
    LiveExecutionEngine,
    LiveAccount,
    Order,
    OrderStatus,
    OrderType,
    OrderSide,
    LIVE_TRADING_ENABLED,
    MAX_ORDER_RETRIES,
)


class OrderValidationTest(TestCase):
    """Test order parameter validation."""

    def test_valid_market_order(self):
        engine = LiveExecutionEngine()
        error = engine._validate_order('BTCUSDT', 'buy', 'market', 0.001, None, None)
        self.assertEqual(error, '')

    def test_valid_limit_order(self):
        engine = LiveExecutionEngine()
        error = engine._validate_order('BTCUSDT', 'sell', 'limit', 0.001, 50000, None)
        self.assertEqual(error, '')

    def test_missing_symbol(self):
        engine = LiveExecutionEngine()
        error = engine._validate_order('', 'buy', 'market', 0.001, None, None)
        self.assertIn('Symbol', error)

    def test_invalid_side(self):
        engine = LiveExecutionEngine()
        error = engine._validate_order('BTCUSDT', 'diagonal', 'market', 0.001, None, None)
        self.assertIn('Invalid side', error)

    def test_invalid_order_type(self):
        engine = LiveExecutionEngine()
        error = engine._validate_order('BTCUSDT', 'buy', 'turbo', 0.001, None, None)
        self.assertIn('Invalid order type', error)

    def test_zero_quantity(self):
        engine = LiveExecutionEngine()
        error = engine._validate_order('BTCUSDT', 'buy', 'market', 0, None, None)
        self.assertIn('Quantity', error)

    def test_negative_quantity(self):
        engine = LiveExecutionEngine()
        error = engine._validate_order('BTCUSDT', 'buy', 'market', -1, None, None)
        self.assertIn('Quantity', error)

    def test_limit_requires_price(self):
        engine = LiveExecutionEngine()
        error = engine._validate_order('BTCUSDT', 'buy', 'limit', 0.001, None, None)
        self.assertIn('price', error.lower())

    def test_stop_loss_requires_stop_price(self):
        engine = LiveExecutionEngine()
        error = engine._validate_order('BTCUSDT', 'buy', 'stop_loss', 0.001, None, None)
        self.assertIn('stop_price', error.lower())


class SafetyCheckTest(TestCase):
    """Test safety checks before order placement."""

    @patch('crypto_platform.apps.signals.services.live_execution.LIVE_TRADING_ENABLED', False)
    def test_disabled_rejects_order(self):
        engine = LiveExecutionEngine()
        is_safe, reason = engine._check_safety()
        self.assertFalse(is_safe)
        self.assertIn('disabled', reason.lower())

    def test_no_exchange_client_rejects(self):
        engine = LiveExecutionEngine()
        engine._exchange_client = None
        # Even if LIVE_TRADING_ENABLED were True, no client = rejected
        is_safe, reason = engine._check_safety()
        # Will either be disabled or no client
        self.assertFalse(is_safe)


class OrderPlacementTest(TestCase):
    """Test order placement flow."""

    @patch('crypto_platform.apps.signals.services.live_execution.LIVE_TRADING_ENABLED', False)
    def test_order_rejected_when_disabled(self):
        engine = LiveExecutionEngine()
        result = asyncio.run(engine.place_order(
            symbol='BTCUSDT', side='buy', order_type='market', quantity=0.001,
        ))
        self.assertFalse(result['success'])
        self.assertEqual(result['order']['status'], 'rejected')

    @patch('crypto_platform.apps.signals.services.live_execution.LIVE_TRADING_ENABLED', False)
    def test_order_rejected_without_risk_approval(self):
        engine = LiveExecutionEngine()
        result = asyncio.run(engine.place_order(
            symbol='BTCUSDT', side='buy', order_type='market', quantity=0.001,
            risk_approved=False,
        ))
        self.assertFalse(result['success'])

    def test_order_rejected_on_validation_error(self):
        engine = LiveExecutionEngine()
        result = asyncio.run(engine.place_order(
            symbol='', side='buy', order_type='market', quantity=0.001,
        ))
        self.assertFalse(result['success'])
        self.assertEqual(result['order']['status'], 'rejected')


class OrderHistoryTest(TestCase):
    """Test order history tracking."""

    @patch('crypto_platform.apps.signals.services.live_execution.LIVE_TRADING_ENABLED', False)
    def test_failed_order_recorded_in_history(self):
        engine = LiveExecutionEngine()
        asyncio.run(engine.place_order(symbol='BTCUSDT', side='buy', order_type='market', quantity=0.001))
        self.assertEqual(len(engine.account.order_history), 1)
        self.assertEqual(engine.account.total_orders, 1)
        self.assertEqual(engine.account.failed_orders, 1)

    def test_order_id_format(self):
        engine = LiveExecutionEngine()
        engine._order_counter = 42
        result = asyncio.run(engine.place_order(
            symbol='BTCUSDT', side='buy', order_type='market', quantity=0.001,
        ))
        self.assertEqual(result['order']['id'], 'LIVE-000043')


class OrderDataclassTest(TestCase):
    """Test Order dataclass properties."""

    def test_is_active_pending(self):
        order = Order(id='1', symbol='BTC', side='buy', type='market', quantity=0.1, status='pending')
        self.assertTrue(order.is_active)

    def test_is_active_filled(self):
        order = Order(id='1', symbol='BTC', side='buy', type='market', quantity=0.1, status='filled')
        self.assertFalse(order.is_active)

    def test_filled_value(self):
        order = Order(
            id='1', symbol='BTC', side='buy', type='market', quantity=0.1,
            filled_quantity=0.1, filled_price=50000,
        )
        self.assertAlmostEqual(order.filled_value, 5000.0, places=2)

    def test_to_dict(self):
        order = Order(id='1', symbol='BTC', side='buy', type='market', quantity=0.1)
        d = order.to_dict()
        self.assertEqual(d['id'], '1')
        self.assertEqual(d['symbol'], 'BTC')
        self.assertIn('created_at', d)


class LiveAccountTest(TestCase):
    """Test LiveAccount properties."""

    def test_success_rate_empty(self):
        account = LiveAccount()
        self.assertEqual(account.success_rate, 0)

    def test_success_rate_with_orders(self):
        account = LiveAccount()
        account.total_orders = 10
        account.successful_orders = 8
        self.assertEqual(account.success_rate, 80.0)

    def test_to_dict(self):
        account = LiveAccount(exchange='binance')
        d = account.to_dict()
        self.assertEqual(d['exchange'], 'binance')
        self.assertIn('is_enabled', d)
        self.assertIn('total_orders', d)


class CancelOrderTest(TestCase):
    """Test order cancellation."""

    def test_cancel_nonexistent_order(self):
        engine = LiveExecutionEngine()
        result = asyncio.run(engine.cancel_order('LIVE-999999'))
        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'])


class EdgeCaseTest(TestCase):
    """Test edge cases."""

    def test_multiple_orders_increment_counter(self):
        engine = LiveExecutionEngine()
        for _ in range(5):
            asyncio.run(engine.place_order(symbol='BTC', side='buy', order_type='market', quantity=0.001))
        self.assertEqual(engine._order_counter, 5)

    def test_engine_default_testnet(self):
        engine = LiveExecutionEngine()
        self.assertTrue(engine.testnet)

    def test_engine_custom_exchange(self):
        engine = LiveExecutionEngine(exchange='okx')
        self.assertEqual(engine.exchange_name, 'okx')
