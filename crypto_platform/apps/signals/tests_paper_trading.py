"""Tests for Paper Trading Engine (Phase 68).

Covers:
- Position opening (long/short)
- Slippage on entry and exit
- Fee calculation
- Stop loss triggering
- Take profit triggering
- PnL calculation
- Position sizing
- Performance metrics
- Account reset
- Edge cases
"""
import math
from django.test import TestCase

from .services.paper_trading import (
    PaperTradingEngine,
    PaperPosition,
    PaperTrade,
    PaperAccount,
    DEFAULT_FEE_RATE,
    DEFAULT_SLIPPAGE_RATE,
)


class PositionOpeningTest(TestCase):
    """Test opening paper positions."""

    def test_open_long_position(self):
        engine = PaperTradingEngine(initial_capital=10000)
        result = engine.open_position(
            symbol='BTCUSDT',
            side='long',
            entry_price=50000,
            quantity=0.1,
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['position']['symbol'], 'BTCUSDT')
        self.assertEqual(result['position']['side'], 'long')
        self.assertEqual(result['position']['quantity'], 0.1)
        self.assertGreater(result['fill_price'], 50000)  # Slippage up for long

    def test_open_short_position(self):
        engine = PaperTradingEngine(initial_capital=10000)
        result = engine.open_position(
            symbol='ETHUSDT',
            side='short',
            entry_price=3000,
            quantity=1.0,
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['position']['side'], 'short')
        self.assertLess(result['fill_price'], 3000)  # Slippage down for short

    def test_open_position_applies_slippage(self):
        engine = PaperTradingEngine(initial_capital=10000, slippage_rate=0.001)
        result = engine.open_position(
            symbol='BTCUSDT',
            side='long',
            entry_price=50000,
            quantity=0.1,
        )
        expected_fill = 50000 * (1 + 0.001)
        self.assertAlmostEqual(result['fill_price'], expected_fill, places=2)

    def test_open_position_charges_fee(self):
        engine = PaperTradingEngine(initial_capital=10000, fee_rate=0.001)
        result = engine.open_position(
            symbol='BTCUSDT',
            side='long',
            entry_price=50000,
            quantity=0.1,
        )
        self.assertGreater(result['fee'], 0)

    def test_open_position_reduces_cash(self):
        engine = PaperTradingEngine(initial_capital=10000)
        initial_cash = engine.account.cash_balance
        engine.open_position(
            symbol='BTCUSDT',
            side='long',
            entry_price=50000,
            quantity=0.1,
        )
        self.assertLess(engine.account.cash_balance, initial_cash)

    def test_max_positions_limit(self):
        engine = PaperTradingEngine(initial_capital=100000, max_positions=3)
        for i in range(3):
            engine.open_position(
                symbol=f'COIN{i}',
                side='long',
                entry_price=100,
                quantity=1,
            )
        result = engine.open_position(
            symbol='COIN3',
            side='long',
            entry_price=100,
            quantity=1,
        )
        self.assertFalse(result['success'])
        self.assertIn('Max open positions', result['error'])

    def test_invalid_side_rejected(self):
        engine = PaperTradingEngine(initial_capital=10000)
        result = engine.open_position(
            symbol='BTCUSDT',
            side='diagonal',
            entry_price=50000,
            quantity=0.1,
        )
        self.assertFalse(result['success'])

    def test_invalid_price_rejected(self):
        engine = PaperTradingEngine(initial_capital=10000)
        result = engine.open_position(
            symbol='BTCUSDT',
            side='long',
            entry_price=-100,
            quantity=0.1,
        )
        self.assertFalse(result['success'])


class PositionClosingTest(TestCase):
    """Test closing paper positions."""

    def setUp(self):
        self.engine = PaperTradingEngine(initial_capital=10000)
        self.result = self.engine.open_position(
            symbol='BTCUSDT',
            side='long',
            entry_price=50000,
            quantity=0.1,
        )
        self.position_id = self.result['position']['id']

    def test_close_long_profit(self):
        result = self.engine.close_position(self.position_id, 52000, 'manual')
        self.assertTrue(result['success'])
        self.assertGreater(result['trade']['pnl'], 0)

    def test_close_long_loss(self):
        result = self.engine.close_position(self.position_id, 48000, 'manual')
        self.assertTrue(result['success'])
        self.assertLess(result['trade']['pnl'], 0)

    def test_close_removes_position(self):
        self.engine.close_position(self.position_id, 51000, 'manual')
        self.assertNotIn(self.position_id, self.engine.account.open_positions)

    def test_close_increases_trade_count(self):
        initial = self.engine.account.total_trades
        self.engine.close_position(self.position_id, 51000, 'manual')
        self.assertEqual(self.engine.account.total_trades, initial + 1)

    def test_close_records_reason(self):
        result = self.engine.close_position(self.position_id, 51000, 'stop_loss')
        self.assertEqual(result['trade']['close_reason'], 'stop_loss')

    def test_close_unknown_position(self):
        result = self.engine.close_position('PAPER-999999', 50000, 'manual')
        self.assertFalse(result['success'])


class StopLossTakeProfitTest(TestCase):
    """Test stop loss and take profit triggering."""

    def test_stop_loss_triggers_long(self):
        engine = PaperTradingEngine(initial_capital=10000)
        result = engine.open_position(
            symbol='BTCUSDT',
            side='long',
            entry_price=50000,
            quantity=0.1,
            stop_loss=49000,
        )
        pos_id = result['position']['id']

        # Price drops below stop loss
        update = engine.update_prices({'BTCUSDT': 48500})
        self.assertEqual(len(update['triggered_exits']), 1)
        self.assertEqual(update['triggered_exits'][0]['close_reason'], 'stop_loss')

    def test_stop_loss_triggers_short(self):
        engine = PaperTradingEngine(initial_capital=10000)
        result = engine.open_position(
            symbol='BTCUSDT',
            side='short',
            entry_price=50000,
            quantity=0.1,
            stop_loss=51000,
        )
        pos_id = result['position']['id']

        # Price rises above stop loss
        update = engine.update_prices({'BTCUSDT': 51500})
        self.assertEqual(len(update['triggered_exits']), 1)

    def test_take_profit_triggers_long(self):
        engine = PaperTradingEngine(initial_capital=10000)
        result = engine.open_position(
            symbol='BTCUSDT',
            side='long',
            entry_price=50000,
            quantity=0.1,
            take_profit=52000,
        )
        pos_id = result['position']['id']

        # Price rises above take profit
        update = engine.update_prices({'BTCUSDT': 52500})
        self.assertEqual(len(update['triggered_exits']), 1)
        self.assertEqual(update['triggered_exits'][0]['close_reason'], 'take_profit')

    def test_no_trigger_within_range(self):
        engine = PaperTradingEngine(initial_capital=10000)
        result = engine.open_position(
            symbol='BTCUSDT',
            side='long',
            entry_price=50000,
            quantity=0.1,
            stop_loss=49000,
            take_profit=52000,
        )
        pos_id = result['position']['id']

        # Price within range
        update = engine.update_prices({'BTCUSDT': 50500})
        self.assertEqual(len(update['triggered_exits']), 0)
        self.assertIn(pos_id, engine.account.open_positions)


class PnLCalculationTest(TestCase):
    """Test PnL calculation accuracy."""

    def test_long_pnl_positive_when_price_up(self):
        engine = PaperTradingEngine(initial_capital=10000, fee_rate=0, slippage_rate=0)
        result = engine.open_position(
            symbol='BTCUSDT',
            side='long',
            entry_price=50000,
            quantity=0.1,
        )
        pos_id = result['position']['id']
        engine.account.open_positions[pos_id].current_price = 52000
        pos = engine.account.open_positions[pos_id]
        # PnL = (52000 - 50000) * 0.1 = 200
        self.assertAlmostEqual(pos.unrealized_pnl, 200.0, places=2)

    def test_short_pnl_positive_when_price_down(self):
        engine = PaperTradingEngine(initial_capital=10000, fee_rate=0, slippage_rate=0)
        result = engine.open_position(
            symbol='BTCUSDT',
            side='short',
            entry_price=50000,
            quantity=0.1,
        )
        pos_id = result['position']['id']
        engine.account.open_positions[pos_id].current_price = 48000
        pos = engine.account.open_positions[pos_id]
        # PnL = (50000 - 48000) * 0.1 = 200
        self.assertAlmostEqual(pos.unrealized_pnl, 200.0, places=2)

    def test_fees_reduce_net_pnl(self):
        engine = PaperTradingEngine(initial_capital=10000, fee_rate=0.001, slippage_rate=0)
        result = engine.open_position(
            symbol='BTCUSDT',
            side='long',
            entry_price=50000,
            quantity=0.1,
        )
        pos_id = result['position']['id']
        pos = engine.account.open_positions[pos_id]
        self.assertGreater(pos.fees_paid, 0)
        self.assertLess(pos.net_pnl, pos.unrealized_pnl)


class PerformanceMetricsTest(TestCase):
    """Test performance metric calculations."""

    def test_empty_account_metrics(self):
        engine = PaperTradingEngine(initial_capital=10000)
        metrics = engine.get_performance_metrics()
        self.assertEqual(metrics['total_trades'], 0)

    def test_win_rate_calculation(self):
        engine = PaperTradingEngine(initial_capital=100000, fee_rate=0, slippage_rate=0)

        # Win: buy at 50k, sell at 52k
        r = engine.open_position(symbol='BTC', side='long', entry_price=50000, quantity=0.1)
        engine.close_position(r['position']['id'], 52000, 'manual')

        # Loss: buy at 50k, sell at 48k
        r = engine.open_position(symbol='ETH', side='long', entry_price=3000, quantity=1)
        engine.close_position(r['position']['id'], 2800, 'manual')

        metrics = engine.get_performance_metrics()
        self.assertEqual(metrics['total_trades'], 2)
        self.assertEqual(metrics['winning_trades'], 1)
        self.assertEqual(metrics['losing_trades'], 1)
        self.assertAlmostEqual(metrics['win_rate'], 50.0, places=1)


class AccountResetTest(TestCase):
    """Test account reset."""

    def test_reset_clears_positions(self):
        engine = PaperTradingEngine(initial_capital=10000)
        engine.open_position(symbol='BTC', side='long', entry_price=50000, quantity=0.1)
        engine.reset()
        self.assertEqual(len(engine.account.open_positions), 0)
        self.assertEqual(engine.account.total_trades, 0)

    def test_reset_restores_capital(self):
        engine = PaperTradingEngine(initial_capital=10000)
        engine.open_position(symbol='BTC', side='long', entry_price=50000, quantity=0.1)
        engine.reset()
        self.assertEqual(engine.account.cash_balance, 10000)


class EdgeCaseTest(TestCase):
    """Test edge cases."""

    def test_quantity_auto_calculated(self):
        """When quantity is None, it should be calculated from risk."""
        engine = PaperTradingEngine(initial_capital=10000)
        result = engine.open_position(
            symbol='BTCUSDT',
            side='long',
            entry_price=50000,
            stop_loss=49000,
        )
        self.assertTrue(result['success'])
        self.assertGreater(result['position']['quantity'], 0)

    def test_position_pnl_pct(self):
        engine = PaperTradingEngine(initial_capital=10000, fee_rate=0, slippage_rate=0)
        result = engine.open_position(
            symbol='BTCUSDT',
            side='long',
            entry_price=100,
            quantity=10,
        )
        pos_id = result['position']['id']
        engine.account.open_positions[pos_id].current_price = 110
        pos = engine.account.open_positions[pos_id]
        # PnL% = (110-100)*10 / (100*10) * 100 = 10%
        self.assertAlmostEqual(pos.unrealized_pnl_pct, 10.0, places=1)

    def test_to_dict_serialization(self):
        engine = PaperTradingEngine(initial_capital=10000)
        engine.open_position(symbol='BTC', side='long', entry_price=50000, quantity=0.1)
        status = engine.get_status()
        self.assertIn('equity', status)
        self.assertIn('open_positions', status)
        self.assertIn('total_trades', status)
