"""Tests for Shadow Trading Engine (Phase 69).

Covers:
- Shadow signal recording
- Expected vs actual fill comparison
- Slippage tracking (entry and exit)
- Execution quality scoring
- PnL accuracy (expected vs actual)
- By-symbol breakdown
- Edge cases
"""
from django.test import TestCase

from .services.shadow_trading import (
    ShadowTradingEngine,
    ShadowTrade,
    ShadowAccount,
)


class ShadowSignalTest(TestCase):
    """Test recording shadow trades."""

    def test_shadow_long_signal(self):
        engine = ShadowTradingEngine()
        result = engine.shadow_signal(
            symbol='BTCUSDT',
            side='long',
            signal_confidence=75,
            expected_entry=50000,
            expected_exit=52000,
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['trade']['symbol'], 'BTCUSDT')
        self.assertEqual(result['trade']['side'], 'long')

    def test_shadow_short_signal(self):
        engine = ShadowTradingEngine()
        result = engine.shadow_signal(
            symbol='ETHUSDT',
            side='short',
            signal_confidence=60,
            expected_entry=3000,
            expected_exit=2800,
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['trade']['side'], 'short')

    def test_shadow_records_actual_entry(self):
        engine = ShadowTradingEngine(slippage_rate=0.001)
        result = engine.shadow_signal(
            symbol='BTCUSDT',
            side='long',
            signal_confidence=75,
            expected_entry=50000,
        )
        trade = result['trade']
        # Actual entry should be higher than expected (slippage for long)
        self.assertGreater(trade['actual_entry'], trade['expected_entry'])

    def test_shadow_short_actual_lower(self):
        engine = ShadowTradingEngine(slippage_rate=0.001)
        result = engine.shadow_signal(
            symbol='BTCUSDT',
            side='short',
            signal_confidence=75,
            expected_entry=50000,
        )
        trade = result['trade']
        # Actual entry should be lower than expected (slippage for short)
        self.assertLess(trade['actual_entry'], trade['expected_entry'])


class SlippageTrackingTest(TestCase):
    """Test slippage tracking in basis points."""

    def test_entry_slippage_positive_for_long(self):
        engine = ShadowTradingEngine(slippage_rate=0.001)
        result = engine.shadow_signal(
            symbol='BTCUSDT',
            side='long',
            signal_confidence=75,
            expected_entry=50000,
        )
        trade = result['trade']
        # Entry slippage should be positive (paid more)
        self.assertGreater(trade['entry_slippage_bps'], 0)

    def test_entry_slippage_negative_for_short(self):
        engine = ShadowTradingEngine(slippage_rate=0.001)
        result = engine.shadow_signal(
            symbol='BTCUSDT',
            side='short',
            signal_confidence=75,
            expected_entry=50000,
        )
        trade = result['trade']
        # Entry slippage should be negative (sold lower)
        self.assertLess(trade['entry_slippage_bps'], 0)

    def test_spread_increases_slippage(self):
        engine = ShadowTradingEngine(slippage_rate=0.0005)
        result_narrow = engine.shadow_signal(
            symbol='BTCUSDT', side='long', signal_confidence=75,
            expected_entry=50000, spread_bps=1,
        )
        engine2 = ShadowTradingEngine(slippage_rate=0.0005)
        result_wide = engine2.shadow_signal(
            symbol='BTCUSDT', side='long', signal_confidence=75,
            expected_entry=50000, spread_bps=20,
        )
        # Wider spread = more slippage
        self.assertGreater(
            abs(result_wide['trade']['total_slippage_bps']),
            abs(result_narrow['trade']['total_slippage_bps']),
        )

    def test_zero_slippage_when_no_spread(self):
        engine = ShadowTradingEngine(slippage_rate=0, fee_rate=0)
        result = engine.shadow_signal(
            symbol='BTCUSDT', side='long', signal_confidence=75,
            expected_entry=50000, spread_bps=0,
        )
        # With zero slippage and zero spread, entry should match expected
        self.assertAlmostEqual(
            result['trade']['actual_entry'],
            result['trade']['expected_entry'],
            places=2,
        )


class ExecutionQualityTest(TestCase):
    """Test execution quality scoring."""

    def test_perfect_execution_quality(self):
        engine = ShadowTradingEngine(slippage_rate=0, fee_rate=0)
        result = engine.shadow_signal(
            symbol='BTCUSDT', side='long', signal_confidence=75,
            expected_entry=50000, expected_exit=52000, spread_bps=0,
        )
        # With zero slippage and spread, quality should be high
        self.assertGreater(result['trade']['execution_quality_score'], 80)

    def test_quality_decreases_with_slippage(self):
        engine_low = ShadowTradingEngine(slippage_rate=0.0001, fee_rate=0)
        result_low = engine_low.shadow_signal(
            symbol='BTCUSDT', side='long', signal_confidence=75,
            expected_entry=50000, spread_bps=1,
        )
        engine_high = ShadowTradingEngine(slippage_rate=0.005, fee_rate=0)
        result_high = engine_high.shadow_signal(
            symbol='BTCUSDT', side='long', signal_confidence=75,
            expected_entry=50000, spread_bps=20,
        )
        self.assertGreater(
            result_low['trade']['execution_quality_score'],
            result_high['trade']['execution_quality_score'],
        )

    def test_quality_between_0_and_100(self):
        engine = ShadowTradingEngine()
        result = engine.shadow_signal(
            symbol='BTCUSDT', side='long', signal_confidence=75,
            expected_entry=50000, spread_bps=10,
        )
        score = result['trade']['execution_quality_score']
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)


class PnLAccuracyTest(TestCase):
    """Test PnL accuracy tracking."""

    def test_pnl_accuracy_empty(self):
        engine = ShadowTradingEngine()
        status = engine.get_status()
        self.assertEqual(status['pnl_accuracy'], 0)

    def test_pnl_accuracy_perfect(self):
        engine = ShadowTradingEngine(slippage_rate=0, fee_rate=0)
        # Signal expects +4% PnL
        result = engine.shadow_signal(
            symbol='BTCUSDT', side='long', signal_confidence=75,
            expected_entry=50000, expected_exit=52000, spread_bps=0,
        )
        status = engine.get_status()
        # With zero slippage, actual should match expected
        self.assertGreater(status['pnl_accuracy'], 90)

    def test_expected_vs_actual_pnl(self):
        engine = ShadowTradingEngine(slippage_rate=0.001)
        result = engine.shadow_signal(
            symbol='BTCUSDT', side='long', signal_confidence=75,
            expected_entry=50000, expected_exit=52000,
        )
        trade = result['trade']
        # Actual PnL should be less than expected (due to slippage)
        self.assertLess(trade['actual_pnl'], trade['expected_pnl'])


class ExecutionQualityReportTest(TestCase):
    """Test execution quality report generation."""

    def test_report_empty(self):
        engine = ShadowTradingEngine()
        report = engine.get_execution_quality_report()
        self.assertIn('message', report)

    def test_report_with_trades(self):
        engine = ShadowTradingEngine()
        for i in range(5):
            engine.shadow_signal(
                symbol='BTCUSDT', side='long', signal_confidence=70,
                expected_entry=50000 + i * 100, spread_bps=5,
            )
        report = engine.get_execution_quality_report()
        self.assertEqual(report['total_trades'], 5)
        self.assertIn('avg_entry_slippage_bps', report)
        self.assertIn('avg_execution_quality', report)
        self.assertIn('by_symbol', report)
        self.assertIn('BTCUSDT', report['by_symbol'])

    def test_by_symbol_breakdown(self):
        engine = ShadowTradingEngine()
        engine.shadow_signal(symbol='BTCUSDT', side='long', signal_confidence=75, expected_entry=50000)
        engine.shadow_signal(symbol='ETHUSDT', side='long', signal_confidence=65, expected_entry=3000)
        engine.shadow_signal(symbol='BTCUSDT', side='long', signal_confidence=80, expected_entry=51000)
        report = engine.get_execution_quality_report()
        self.assertEqual(report['by_symbol']['BTCUSDT']['trades'], 2)
        self.assertEqual(report['by_symbol']['ETHUSDT']['trades'], 1)


class ShadowAccountTest(TestCase):
    """Test ShadowAccount properties."""

    def test_win_rate_empty(self):
        account = ShadowAccount()
        self.assertEqual(account.win_rate, 0)

    def test_win_rate_with_trades(self):
        account = ShadowAccount()
        account.shadow_trades = [
            ShadowTrade(id='1', symbol='BTC', side='long', expected_entry=50, expected_exit=52,
                       expected_pnl=100, expected_pnl_pct=4, actual_entry=50.1, actual_exit=52,
                       actual_pnl=95, actual_pnl_pct=3.8, entry_slippage=2, exit_slippage=0,
                       total_slippage_bps=2, execution_quality_score=90, signal_confidence=75),
            ShadowTrade(id='2', symbol='ETH', side='long', expected_entry=3000, expected_exit=2900,
                       expected_pnl=-100, expected_pnl_pct=-3.3, actual_entry=3003, actual_exit=2900,
                       actual_pnl=-103, actual_pnl_pct=-3.4, entry_slippage=1, exit_slippage=0,
                       total_slippage_bps=1, execution_quality_score=95, signal_confidence=60),
        ]
        self.assertEqual(account.win_rate, 50.0)

    def test_to_dict(self):
        account = ShadowAccount()
        d = account.to_dict()
        self.assertIn('total_trades', d)
        self.assertIn('win_rate', d)
        self.assertIn('avg_execution_quality', d)


class EdgeCaseTest(TestCase):
    """Test edge cases."""

    def test_shadow_with_current_price(self):
        """Current price different from expected entry."""
        engine = ShadowTradingEngine(slippage_rate=0)
        result = engine.shadow_signal(
            symbol='BTCUSDT', side='long', signal_confidence=75,
            expected_entry=50000, current_price=50500, spread_bps=0,
        )
        # Actual should be based on current_price, not expected_entry
        self.assertAlmostEqual(result['trade']['actual_entry'], 50500, places=2)

    def test_multiple_shadows_accumulate(self):
        engine = ShadowTradingEngine()
        for i in range(10):
            engine.shadow_signal(
                symbol='BTCUSDT', side='long', signal_confidence=70,
                expected_entry=50000 + i * 100,
            )
        status = engine.get_status()
        self.assertEqual(status['total_trades'], 10)

    def test_shadow_trade_to_dict(self):
        trade = ShadowTrade(
            id='TEST-001', symbol='BTC', side='long',
            expected_entry=50000, expected_exit=52000,
            expected_pnl=200, expected_pnl_pct=4.0,
            actual_entry=50050, actual_exit=51950,
            actual_pnl=150, actual_pnl_pct=3.0,
            entry_slippage=10, exit_slippage=-10,
            total_slippage_bps=20, execution_quality_score=85,
            signal_confidence=75,
        )
        d = trade.to_dict()
        self.assertEqual(d['id'], 'TEST-001')
        self.assertEqual(d['execution_quality_score'], 85)
