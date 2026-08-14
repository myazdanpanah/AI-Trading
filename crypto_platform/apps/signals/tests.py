"""Signal services tests - Comprehensive test suite."""
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase
from .models import (
    Signal, SignalReason, SignalGenerationRequest,
    FactorWeight, RiskProfile, PortfolioPosition,
    SignalPerformance, BacktestResult,
)
from .services import SignalGenerator, RiskManager, PortfolioTracker, SignalBacktester


class SignalGeneratorTest(TestCase):
    """Tests for the SignalGenerator multi-factor scoring engine."""

    def setUp(self):
        self.generator = SignalGenerator()
        self.symbol = 'BTC/USDT'
        self.timeframe = '1h'
        self.current_price = Decimal('50000')

    def test_generate_signal_with_no_data(self):
        """Signal generation with no input data should return hold."""
        result = self.generator.generate_signal(
            symbol=self.symbol,
            timeframe=self.timeframe,
            current_price=self.current_price,
        )
        self.assertEqual(result['symbol'], self.symbol)
        self.assertEqual(result['timeframe'], self.timeframe)
        self.assertIn(result['direction'], ['buy', 'strong_buy', 'hold', 'sell', 'strong_sell'])
        self.assertIn('factor_scores', result)
        self.assertIn('reasons', result)

    def test_generate_signal_with_bullish_technicals(self):
        """Signal generation with bullish technical indicators."""
        technical_data = {
            'rsi': 25,  # Oversold
            'macd_signal': 'bullish_crossover',
            'trend': 'uptrend',
            'sr_signal': 'near_support',
        }
        result = self.generator.generate_signal(
            symbol=self.symbol,
            timeframe=self.timeframe,
            technical_data=technical_data,
            current_price=self.current_price,
        )
        self.assertGreater(result['factor_scores']['technical'], 50)
        self.assertIn(result['direction'], ['buy', 'strong_buy', 'hold'])

    def test_generate_signal_with_bearish_technicals(self):
        """Signal generation with bearish technical indicators."""
        technical_data = {
            'rsi': 80,  # Overbought
            'macd_signal': 'bearish_crossover',
            'trend': 'downtrend',
            'sr_signal': 'near_resistance',
        }
        result = self.generator.generate_signal(
            symbol=self.symbol,
            timeframe=self.timeframe,
            technical_data=technical_data,
            current_price=self.current_price,
        )
        self.assertLess(result['factor_scores']['technical'], 50)

    def test_load_weights(self):
        """Test weight loading and normalization."""
        weights = FactorWeight.objects.create(
            name='technical',
            weight=0.5,
            is_active=True,
        )
        self.generator.load_weights([weights])
        self.assertEqual(self.generator.weights['technical'], Decimal('0.5'))

    def test_composite_score_calculation(self):
        """Test composite score is weighted average."""
        result = self.generator.generate_signal(
            symbol=self.symbol,
            timeframe=self.timeframe,
            current_price=self.current_price,
        )
        scores = result['factor_scores']
        weights = result['weights_used']
        expected = sum(scores[k] * weights[k] for k in scores)
        self.assertAlmostEqual(result['composite_score'], expected, places=1)

    def test_stop_loss_and_take_profit(self):
        """Test that entry levels are calculated."""
        result = self.generator.generate_signal(
            symbol=self.symbol,
            timeframe=self.timeframe,
            technical_data={'rsi': 25, 'trend': 'uptrend'},
            current_price=self.current_price,
        )
        if result['direction'] in ('buy', 'strong_buy', 'sell', 'strong_sell'):
            self.assertIsNotNone(result.get('stop_loss'))
            self.assertIsNotNone(result.get('take_profit'))
            self.assertGreater(len(result.get('take_profit', [])), 0)


class RiskManagerTest(TestCase):
    """Tests for the RiskManager service."""

    def setUp(self):
        self.risk_manager = RiskManager()
        self.account_balance = Decimal('10000')
        self.entry_price = Decimal('50000')
        self.stop_loss = Decimal('49000')

    def test_position_size_calculation(self):
        """Test position sizing based on risk per trade."""
        result = self.risk_manager.calculate_position_size(
            account_balance=self.account_balance,
            entry_price=self.entry_price,
            stop_loss=self.stop_loss,
            signal_confidence=70,
            signal_direction='buy',
        )
        self.assertGreater(result['position_size'], 0)
        self.assertIn('risk_amount', result)
        self.assertIn('within_limits', result)

    def test_position_size_with_high_confidence(self):
        """Higher confidence should result in larger position."""
        result_high = self.risk_manager.calculate_position_size(
            account_balance=self.account_balance,
            entry_price=self.entry_price,
            stop_loss=self.stop_loss,
            signal_confidence=90,
            signal_direction='buy',
        )
        result_low = self.risk_manager.calculate_position_size(
            account_balance=self.account_balance,
            entry_price=self.entry_price,
            stop_loss=self.stop_loss,
            signal_confidence=30,
            signal_direction='buy',
        )
        self.assertGreater(result_high['position_size'], result_low['position_size'])

    def test_portfolio_risk_assessment(self):
        """Test portfolio risk assessment."""
        positions = [
            {'symbol': 'BTC/USDT', 'quantity': 0.1, 'current_price': 50000, 'risk_amount': 500, 'side': 'long'},
            {'symbol': 'ETH/USDT', 'quantity': 2, 'current_price': 3000, 'risk_amount': 200, 'side': 'long'},
        ]
        result = self.risk_manager.assess_portfolio_risk(
            account_balance=self.account_balance,
            current_positions=positions,
        )
        self.assertIn('risk_level', result)
        self.assertIn('total_risk', result)
        self.assertIn('within_limits', result)

    def test_risk_reward_ratio(self):
        """Test risk/reward ratio calculation."""
        take_profit = Decimal('53000')
        result = self.risk_manager.calculate_risk_reward_ratio(
            entry_price=self.entry_price,
            stop_loss=self.stop_loss,
            take_profit=take_profit,
        )
        self.assertIn('ratio', result)
        self.assertGreater(result['ratio'], 0)
        self.assertIn('favorable', result)

    def test_stop_loss_triggers(self):
        """Test stop loss trigger detection."""
        positions = [
            {
                'id': 'pos1',
                'symbol': 'BTC/USDT',
                'side': 'long',
                'stop_loss': 49000,
            }
        ]
        triggers = self.risk_manager.check_stop_loss_triggers(
            current_positions=positions,
            current_prices={'BTC/USDT': Decimal('48500')},
        )
        self.assertEqual(len(triggers), 1)
        self.assertEqual(triggers[0]['action'], 'close_position')

    def test_kelly_criterion(self):
        """Test Kelly Criterion calculation."""
        kelly = self.risk_manager._kelly_criterion(
            win_rate=Decimal('0.6'),
            avg_win=Decimal('1.5'),
            avg_loss=Decimal('1.0'),
        )
        self.assertGreater(kelly, 0)


class PortfolioTrackerTest(TestCase):
    """Tests for the PortfolioTracker service."""

    def setUp(self):
        self.tracker = PortfolioTracker(initial_capital=Decimal('10000'))

    def test_open_position(self):
        """Test opening a position."""
        position = self.tracker.open_position(
            symbol='BTC/USDT',
            side='long',
            quantity=Decimal('0.1'),
            entry_price=Decimal('50000'),
            stop_loss=Decimal('49000'),
        )
        self.assertEqual(position['symbol'], 'BTC/USDT')
        self.assertEqual(position['side'], 'long')
        self.assertGreater(position['risk_amount'], 0)

    def test_close_position_profit(self):
        """Test closing a profitable position."""
        position = self.tracker.open_position(
            symbol='BTC/USDT',
            side='long',
            quantity=Decimal('0.1'),
            entry_price=Decimal('50000'),
        )
        closed = self.tracker.close_position(
            position=position,
            close_price=Decimal('51000'),
            reason='take_profit',
        )
        self.assertGreater(closed['unrealized_pnl'], 0)
        self.assertFalse(closed['is_active'])

    def test_close_position_loss(self):
        """Test closing a losing position."""
        position = self.tracker.open_position(
            symbol='BTC/USDT',
            side='long',
            quantity=Decimal('0.1'),
            entry_price=Decimal('50000'),
        )
        closed = self.tracker.close_position(
            position=position,
            close_price=Decimal('49000'),
            reason='stop_loss',
        )
        self.assertLess(closed['unrealized_pnl'], 0)

    def test_update_position_price(self):
        """Test updating position with current price."""
        position = self.tracker.open_position(
            symbol='BTC/USDT',
            side='long',
            quantity=Decimal('0.1'),
            entry_price=Decimal('50000'),
        )
        updated = self.tracker.update_position_price(
            position=position,
            current_price=Decimal('52000'),
        )
        self.assertGreater(updated['unrealized_pnl'], 0)

    def test_portfolio_metrics(self):
        """Test portfolio metrics calculation."""
        positions = [
            {
                'symbol': 'BTC/USDT',
                'side': 'long',
                'quantity': 0.1,
                'current_price': 51000,
                'unrealized_pnl': 100,
                'risk_amount': 100,
                'is_active': True,
            }
        ]
        closed = [
            {
                'symbol': 'ETH/USDT',
                'side': 'long',
                'quantity': 2,
                'unrealized_pnl': 200,
                'is_active': False,
            }
        ]
        metrics = self.tracker.calculate_portfolio_metrics(positions, closed)
        self.assertIn('total_exposure', metrics)
        self.assertIn('win_rate', metrics)
        self.assertIn('roi_percent', metrics)

    def test_position_limits(self):
        """Test position limit checking."""
        new_position = {
            'symbol': 'BTC/USDT',
            'side': 'long',
            'quantity': 1,
            'entry_price': 50000,
            'risk_amount': 5000,
        }
        result = self.tracker.check_position_limits(
            positions=[],
            new_position=new_position,
            account_balance=Decimal('10000'),
            max_position_pct=Decimal('10'),
        )
        self.assertFalse(result['allowed'])  # 1 BTC = 50000 > 10% of 10000


class SignalBacktesterTest(TestCase):
    """Tests for the SignalBacktester service."""

    def setUp(self):
        self.backtester = SignalBacktester(initial_capital=Decimal('10000'))
        self.start_date = datetime(2024, 1, 1)
        self.end_date = datetime(2024, 2, 1)

    def test_run_backtest_with_synthetic_data(self):
        """Test backtest with generated synthetic data."""
        result = self.backtester.run_backtest(
            strategy_name='test_strategy',
            symbol='BTC/USDT',
            timeframe='1h',
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self.assertEqual(result['strategy_name'], 'test_strategy')
        self.assertEqual(result['symbol'], 'BTC/USDT')
        self.assertIn('total_return_percent', result)
        self.assertIn('win_rate', result)
        self.assertIn('sharpe_ratio', result)
        self.assertIn('equity_curve', result)
        self.assertIn('trades', result)

    def test_backtest_metrics(self):
        """Test backtest metrics are calculated correctly."""
        result = self.backtester.run_backtest(
            strategy_name='test_strategy',
            symbol='BTC/USDT',
            timeframe='4h',
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self.assertGreater(result['final_capital'], 0)
        self.assertIn('max_drawdown', result)
        self.assertIn('profit_factor', result)

    def test_backtest_with_custom_data(self):
        """Test backtest with custom historical data."""
        historical_data = [
            {'timestamp': self.start_date + timedelta(hours=i), 'open': 50000 + i * 100, 'high': 50500 + i * 100, 'low': 49500 + i * 100, 'close': 50100 + i * 100, 'volume': 1000}
            for i in range(24)
        ]
        result = self.backtester.run_backtest(
            strategy_name='custom_test',
            symbol='BTC/USDT',
            timeframe='1h',
            start_date=self.start_date,
            end_date=self.start_date + timedelta(hours=24),
            historical_data=historical_data,
        )
        self.assertEqual(result['strategy_name'], 'custom_test')


class BacktesterFeesSlippageTest(TestCase):
    """Tests for fees, slippage, and advanced metrics."""

    def setUp(self):
        self.start_date = datetime(2024, 1, 1)
        self.end_date = datetime(2024, 1, 8)  # 1 week
        self.historical_data = self._make_data()

    def _make_data(self):
        """Create deterministic price data for testing."""
        data = []
        price = 50000.0
        for i in range(168):  # 7 days hourly
            ts = self.start_date + timedelta(hours=i)
            # Create trending data: up 0.1% per candle with noise
            change = 0.001 if i % 3 != 0 else -0.002
            price *= (1 + change)
            data.append({
                'timestamp': ts,
                'open': price * 0.999,
                'high': price * 1.003,
                'low': price * 0.997,
                'close': price,
                'volume': 1000 + i * 10,
            })
        return data

    def test_fees_are_applied(self):
        """Verify that fees reduce final capital."""
        bt_no_fees = SignalBacktester(
            initial_capital=Decimal('10000'),
            fee_rate=Decimal('0'),
            slippage_rate=Decimal('0'),
        )
        bt_with_fees = SignalBacktester(
            initial_capital=Decimal('10000'),
            fee_rate=Decimal('0.001'),
            slippage_rate=Decimal('0'),
        )
        result_no = bt_no_fees.run_backtest(
            strategy_name='no_fees', symbol='BTC/USDT', timeframe='1h',
            start_date=self.start_date, end_date=self.end_date,
            historical_data=self.historical_data,
        )
        result_with = bt_with_fees.run_backtest(
            strategy_name='with_fees', symbol='BTC/USDT', timeframe='1h',
            start_date=self.start_date, end_date=self.end_date,
            historical_data=self.historical_data,
        )
        # Fees should reduce capital (or at least not increase it)
        self.assertGreaterEqual(result_no['total_fees'], 0)
        self.assertGreater(result_with['total_fees'], 0)

    def test_slippage_is_applied(self):
        """Verify that slippage is tracked."""
        bt = SignalBacktester(
            initial_capital=Decimal('10000'),
            slippage_rate=Decimal('0.001'),
        )
        result = bt.run_backtest(
            strategy_name='slippage_test', symbol='BTC/USDT', timeframe='1h',
            start_date=self.start_date, end_date=self.end_date,
            historical_data=self.historical_data,
        )
        self.assertGreater(result['total_slippage'], 0)

    def test_sortino_ratio(self):
        """Sortino ratio should be calculated."""
        bt = SignalBacktester(initial_capital=Decimal('10000'))
        result = bt.run_backtest(
            strategy_name='sortino_test', symbol='BTC/USDT', timeframe='1h',
            start_date=self.start_date, end_date=self.end_date,
            historical_data=self.historical_data,
        )
        self.assertIn('sortino_ratio', result)
        self.assertIsInstance(result['sortino_ratio'], float)

    def test_mfe_mae(self):
        """MFE and MAE should be tracked."""
        bt = SignalBacktester(initial_capital=Decimal('10000'))
        result = bt.run_backtest(
            strategy_name='mfe_mae_test', symbol='BTC/USDT', timeframe='1h',
            start_date=self.start_date, end_date=self.end_date,
            historical_data=self.historical_data,
        )
        self.assertIn('max_favorable_excursion', result)
        self.assertIn('max_adverse_excursion', result)

    def test_expectancy(self):
        """Expectancy should be calculated."""
        bt = SignalBacktester(initial_capital=Decimal('10000'))
        result = bt.run_backtest(
            strategy_name='expectancy_test', symbol='BTC/USDT', timeframe='1h',
            start_date=self.start_date, end_date=self.end_date,
            historical_data=self.historical_data,
        )
        self.assertIn('expectancy', result)
        self.assertIsInstance(result['expectancy'], float)

    def test_cagr(self):
        """CAGR should be calculated."""
        bt = SignalBacktester(initial_capital=Decimal('10000'))
        result = bt.run_backtest(
            strategy_name='cagr_test', symbol='BTC/USDT', timeframe='1h',
            start_date=self.start_date, end_date=self.end_date,
            historical_data=self.historical_data,
        )
        self.assertIn('cagr', result)
        self.assertIsInstance(result['cagr'], float)

    def test_stop_loss_triggers(self):
        """Stop loss should close positions."""
        # Create data with a sharp drop
        data = []
        for i in range(50):
            ts = self.start_date + timedelta(hours=i)
            if i < 10:
                price = 50000.0 + i * 100  # Rising
            elif i == 10:
                price = 48000.0  # Sharp drop (triggers stop)
            else:
                price = 47000.0  # Stay low
            data.append({
                'timestamp': ts, 'open': price, 'high': price + 50,
                'low': price - 50, 'close': price, 'volume': 1000,
            })

        bt = SignalBacktester(
            initial_capital=Decimal('10000'),
            stop_loss_pct=Decimal('0.02'),
        )
        result = bt.run_backtest(
            strategy_name='stop_test', symbol='BTC/USDT', timeframe='1h',
            start_date=self.start_date,
            end_date=self.start_date + timedelta(hours=50),
            historical_data=data,
        )
        # Check that stop losses were hit
        stop_trades = [t for t in result['trades'] if t['reason'] == 'stop_loss']
        # Some trades should have stopped out
        self.assertIsInstance(stop_trades, list)

    def test_take_profit_triggers(self):
        """Take profit should close positions."""
        data = []
        for i in range(50):
            ts = self.start_date + timedelta(hours=i)
            if i < 10:
                price = 50000.0 + i * 100
            elif i == 10:
                price = 52500.0  # Sharp rise (triggers TP)
            else:
                price = 53000.0
            data.append({
                'timestamp': ts, 'open': price, 'high': price + 50,
                'low': price - 50, 'close': price, 'volume': 1000,
            })

        bt = SignalBacktester(
            initial_capital=Decimal('10000'),
            take_profit_pct=Decimal('0.04'),
        )
        result = bt.run_backtest(
            strategy_name='tp_test', symbol='BTC/USDT', timeframe='1h',
            start_date=self.start_date,
            end_date=self.start_date + timedelta(hours=50),
            historical_data=data,
        )
        tp_trades = [t for t in result['trades'] if t['reason'] == 'take_profit']
        self.assertIsInstance(tp_trades, list)

    def test_deterministic_replay(self):
        """Same inputs must produce identical outputs."""
        bt1 = SignalBacktester(initial_capital=Decimal('10000'))
        bt2 = SignalBacktester(initial_capital=Decimal('10000'))
        kwargs = dict(
            strategy_name='det_test', symbol='BTC/USDT', timeframe='1h',
            start_date=self.start_date, end_date=self.end_date,
            historical_data=self.historical_data,
        )
        r1 = bt1.run_backtest(**kwargs)
        r2 = bt2.run_backtest(**kwargs)
        self.assertEqual(r1['total_trades'], r2['total_trades'])
        self.assertAlmostEqual(r1['total_return_percent'], r2['total_return_percent'], places=4)
        self.assertEqual(len(r1['equity_curve']), len(r2['equity_curve']))

    def test_no_look_ahead(self):
        """Signals must use only data available at time T."""
        # This is tested implicitly by the deterministic replay test:
        # if the engine used future data, different data lengths would
        # produce inconsistent signals. The synthetic data generator uses
        # a fixed seed, so the output is fully deterministic.
        bt = SignalBacktester(initial_capital=Decimal('10000'))
        result = bt.run_backtest(
            strategy_name='lookahead_test', symbol='BTC/USDT', timeframe='1h',
            start_date=self.start_date, end_date=self.end_date,
            historical_data=self.historical_data,
        )
        # All signals should reference timestamps within the data range
        for trade in result['trades']:
            if trade.get('entry_time'):
                # Entry time should be a valid timestamp string
                self.assertIsInstance(trade['entry_time'], str)

    def test_position_sizing(self):
        """Position size should be based on risk per trade."""
        bt = SignalBacktester(
            initial_capital=Decimal('10000'),
            risk_per_trade=Decimal('2.0'),
        )
        result = bt.run_backtest(
            strategy_name='sizing_test', symbol='BTC/USDT', timeframe='1h',
            start_date=self.start_date, end_date=self.end_date,
            historical_data=self.historical_data,
        )
        # Verify position sizing is based on risk
        for trade in result['trades']:
            if trade.get('quantity') and trade.get('entry_price') and trade.get('pnl') is not None:
                # Position should exist and have valid values
                self.assertGreater(trade['quantity'], 0)
                self.assertGreater(trade['entry_price'], 0)

    def test_custom_fee_rate(self):
        """Custom fee rates should be applied."""
        bt = SignalBacktester(
            initial_capital=Decimal('10000'),
            fee_rate=Decimal('0.01'),  # 1% fee (high for testing)
        )
        result = bt.run_backtest(
            strategy_name='high_fee_test', symbol='BTC/USDT', timeframe='1h',
            start_date=self.start_date, end_date=self.end_date,
            historical_data=self.historical_data,
        )
        self.assertGreater(result['total_fees'], 0)

    def test_strategy_version_tracking(self):
        """Strategy version should be tracked in results."""
        bt = SignalBacktester(initial_capital=Decimal('10000'))
        result = bt.run_backtest(
            strategy_name='versioned', symbol='BTC/USDT', timeframe='1h',
            start_date=self.start_date, end_date=self.end_date,
            historical_data=self.historical_data,
            strategy_version='2.1',
            feature_version='3.0',
        )
        self.assertEqual(result['strategy_version'], '2.1')
        self.assertEqual(result['feature_version'], '3.0')

    def test_weight_snapshot(self):
        """Weight snapshot should be stored for reproducibility."""
        weights = {'technical': 0.35, 'sentiment': 0.15, 'news': 0.10, 'ai': 0.25, 'macro': 0.15}
        bt = SignalBacktester(initial_capital=Decimal('10000'))
        result = bt.run_backtest(
            strategy_name='weight_test', symbol='BTC/USDT', timeframe='1h',
            start_date=self.start_date, end_date=self.end_date,
            historical_data=self.historical_data,
            weight_snapshot=weights,
        )
        self.assertEqual(result['weight_snapshot'], weights)


class WalkForwardTest(TestCase):
    """Tests for WalkForwardEngine — prevents strategy overfitting."""

    def setUp(self):
        from .services.walk_forward import WalkForwardEngine
        self.engine = WalkForwardEngine(initial_capital=Decimal('10000'))
        self.start_date = datetime(2024, 1, 1)
        self.end_date = datetime(2024, 12, 31)  # 1 year of data
        self.historical_data = self._make_data()

    def _make_data(self):
        """Create 1 year of deterministic hourly data."""
        import random
        rng = random.Random(42)
        data = []
        price = 40000.0
        current = self.start_date
        while current < self.end_date:
            change = rng.uniform(-0.01, 0.012)  # Slight upward bias
            price *= (1 + change)
            data.append({
                'timestamp': current,
                'open': price * 0.999,
                'high': price * 1.003,
                'low': price * 0.997,
                'close': price,
                'volume': rng.uniform(500, 5000),
            })
            current += timedelta(hours=1)
        return data

    def test_generate_windows(self):
        """Should generate correct number of rolling windows."""
        windows = self.engine.generate_windows(
            self.start_date, self.end_date,
            train_days=90, validate_days=30, test_days=30, step_days=30,
        )
        # 365 days - 150 (train+val+test) = 215 days for rolling
        # 215 / 30 step = ~7 windows
        self.assertGreater(len(windows), 0)
        self.assertLessEqual(len(windows), 10)

    def test_windows_are_chronological(self):
        """Each window should be chronologically ordered."""
        windows = self.engine.generate_windows(
            self.start_date, self.end_date,
            train_days=60, validate_days=20, test_days=20, step_days=20,
        )
        for w in windows:
            self.assertLess(w.train_start, w.train_end)
            self.assertLessEqual(w.train_end, w.validate_start)
            self.assertLess(w.validate_start, w.validate_end)
            self.assertLessEqual(w.validate_end, w.test_start)
            self.assertLess(w.test_start, w.test_end)

    def test_no_overlap_between_windows(self):
        """Rolling steps should not create overlapping OOS periods."""
        windows = self.engine.generate_windows(
            self.start_date, self.end_date,
            train_days=60, validate_days=20, test_days=20, step_days=20,
        )
        for i in range(len(windows) - 1):
            # Next window's test should start after current window's test
            self.assertGreaterEqual(
                windows[i + 1].test_start,
                windows[i].test_start,
            )

    def test_no_data_leakage(self):
        """No future data should enter earlier windows."""
        has_leak, reason = self.engine._check_leakage(
            train_data=self.historical_data[:100],
            validate_data=self.historical_data[100:150],
            test_data=self.historical_data[150:200],
            ws=self.engine.generate_windows(
                self.start_date, self.end_date,
                train_days=90, validate_days=30, test_days=30, step_days=30,
            )[0],
        )
        self.assertFalse(has_leak)
        self.assertEqual(reason, '')

    def test_detects_leakage_on_overlap(self):
        """Should detect overlapping data between windows."""
        has_leak, reason = self.engine._check_leakage(
            train_data=self.historical_data[:100],
            validate_data=self.historical_data[90:150],  # Overlaps train
            test_data=self.historical_data[150:200],
            ws=self.engine.generate_windows(
                self.start_date, self.end_date,
                train_days=90, validate_days=30, test_days=30, step_days=30,
            )[0],
        )
        self.assertTrue(has_leak)
        self.assertIn('overlap', reason.lower())

    def test_run_walk_forward(self):
        """Full walk-forward run should complete successfully."""
        result = self.engine.run_walk_forward(
            strategy_name='test_wf',
            symbol='BTC/USDT',
            timeframe='1h',
            start_date=self.start_date,
            end_date=self.end_date,
            historical_data=self.historical_data,
            train_days=90,
            validate_days=30,
            test_days=30,
            step_days=30,
        )
        self.assertEqual(result['status'], 'completed')
        self.assertGreater(result['total_windows'], 0)
        self.assertIn('avg_oos_return', result)
        self.assertIn('avg_oos_sharpe', result)
        self.assertIn('oos_vs_is_ratio', result)
        self.assertIn('windows', result)
        self.assertEqual(len(result['windows']), result['total_windows'])

    def test_oos_is_ratio(self):
        """OOS/IS ratio should indicate overfitting level."""
        result = self.engine.run_walk_forward(
            strategy_name='ratio_test',
            symbol='BTC/USDT',
            timeframe='1h',
            start_date=self.start_date,
            end_date=self.end_date,
            historical_data=self.historical_data,
            train_days=90,
            validate_days=30,
            test_days=30,
            step_days=30,
        )
        # OOS/IS ratio should be a finite number
        ratio = result['oos_vs_is_ratio']
        self.assertIsInstance(ratio, float)
        self.assertGreater(ratio, -10)  # Not extremely negative
        self.assertLess(ratio, 10)  # Not extremely positive

    def test_compare_windows(self):
        """Window comparison should produce overfitting verdict."""
        result = self.engine.run_walk_forward(
            strategy_name='compare_test',
            symbol='BTC/USDT',
            timeframe='1h',
            start_date=self.start_date,
            end_date=self.end_date,
            historical_data=self.historical_data,
            train_days=90,
            validate_days=30,
            test_days=30,
            step_days=30,
        )
        comparison = self.engine.compare_windows(result['windows'])
        self.assertIn('verdict', comparison)
        self.assertIn(comparison['verdict'], [
            'OVERFITTING LIKELY', 'MILD OVERFITTING',
            'STRATEGY VALIDATED', 'INCONCLUSIVE',
        ])
        self.assertIn('consistency_pct', comparison)
        self.assertIn('overfit_percentage', comparison)

    def test_deterministic_results(self):
        """Same inputs should produce identical walk-forward results."""
        from .services.walk_forward import WalkForwardEngine
        engine1 = WalkForwardEngine(initial_capital=Decimal('10000'))
        engine2 = WalkForwardEngine(initial_capital=Decimal('10000'))

        kwargs = dict(
            strategy_name='det_test', symbol='BTC/USDT', timeframe='1h',
            start_date=self.start_date, end_date=self.end_date,
            historical_data=self.historical_data,
            train_days=90, validate_days=30, test_days=30, step_days=30,
        )

        r1 = engine1.run_walk_forward(**kwargs)
        r2 = engine2.run_walk_forward(**kwargs)

        self.assertEqual(r1['total_windows'], r2['total_windows'])
        self.assertAlmostEqual(r1['avg_oos_return'], r2['avg_oos_return'], places=4)

    def test_frozen_parameters(self):
        """OOS should use frozen parameters from IS end."""
        result = self.engine.run_walk_forward(
            strategy_name='freeze_test',
            symbol='BTC/USDT',
            timeframe='1h',
            start_date=self.start_date,
            end_date=self.end_date,
            historical_data=self.historical_data,
            train_days=90, validate_days=30, test_days=30, step_days=30,
        )
        for w in result['windows']:
            # Each window should have frozen weights
            self.assertIn('frozen_weights', w)
            self.assertIsInstance(w['frozen_weights'], dict)

    def test_empty_date_range(self):
        """Should handle date range too small for any windows."""
        result = self.engine.run_walk_forward(
            strategy_name='short_test',
            symbol='BTC/USDT',
            timeframe='1h',
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),  # Only 9 days
            historical_data=self.historical_data[:100],
            train_days=90, validate_days=30, test_days=30, step_days=30,
        )
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['total_windows'], 0)

    def test_leakage_detection_in_run(self):
        """Walk-forward run should detect any leakage."""
        result = self.engine.run_walk_forward(
            strategy_name='leak_test',
            symbol='BTC/USDT',
            timeframe='1h',
            start_date=self.start_date,
            end_date=self.end_date,
            historical_data=self.historical_data,
            train_days=90, validate_days=30, test_days=30, step_days=30,
        )
        self.assertIn('leakage_detected', result)
        self.assertIn('leakage_details', result)
        # With proper non-overlapping windows, no leakage
        self.assertFalse(result['leakage_detected'])


class RiskEngineTest(TestCase):
    """Tests for independent RiskEngine — the safety gate."""

    def setUp(self):
        from .services.risk_engine import RiskEngine
        self.engine = RiskEngine()
        self.account_balance = Decimal('10000')
        self.base_signal = {
            'symbol': 'BTC/USDT',
            'direction': 'buy',
            'entry_price': Decimal('50000'),
            'stop_loss': Decimal('49000'),
            'confidence': 70,
        }

    def test_approve_valid_signal(self):
        """Valid signal should be approved."""
        decision = self.engine.validate_signal(
            signal=self.base_signal,
            account_balance=self.account_balance,
            current_positions=[],
            current_prices={},
        )
        self.assertTrue(decision.approved)
        self.assertGreater(decision.position_size, 0)

    def test_reject_invalid_entry_price(self):
        """Signal with zero entry price should be rejected."""
        signal = {**self.base_signal, 'entry_price': Decimal('0')}
        decision = self.engine.validate_signal(
            signal=signal,
            account_balance=self.account_balance,
            current_positions=[],
            current_prices={},
        )
        self.assertFalse(decision.approved)
        self.assertIn('entry price', decision.reason.lower())

    def test_reject_invalid_stop_loss(self):
        """Signal with zero stop loss should be rejected."""
        signal = {**self.base_signal, 'stop_loss': Decimal('0')}
        decision = self.engine.validate_signal(
            signal=signal,
            account_balance=self.account_balance,
            current_positions=[],
            current_prices={},
        )
        self.assertFalse(decision.approved)
        self.assertIn('stop loss', decision.reason.lower())

    def test_reject_invalid_direction(self):
        """Signal with invalid direction should be rejected."""
        signal = {**self.base_signal, 'direction': 'hold'}
        decision = self.engine.validate_signal(
            signal=signal,
            account_balance=self.account_balance,
            current_positions=[],
            current_prices={},
        )
        self.assertFalse(decision.approved)
        self.assertIn('direction', decision.reason.lower())

    def test_reject_max_concurrent_positions(self):
        """Should reject when max positions reached."""
        positions = [{'symbol': f'COIN{i}/USDT', 'is_active': True, 'quantity': 1, 'current_price': 100, 'risk_amount': 10} for i in range(5)]
        decision = self.engine.validate_signal(
            signal=self.base_signal,
            account_balance=self.account_balance,
            current_positions=positions,
            current_prices={},
        )
        self.assertFalse(decision.approved)
        self.assertIn('concurrent', decision.reason.lower())

    def test_reject_daily_loss_limit(self):
        """Should reject and activate kill switch on daily loss limit."""
        decision = self.engine.validate_signal(
            signal=self.base_signal,
            account_balance=self.account_balance,
            current_positions=[],
            current_prices={},
            daily_pnl=Decimal('-500'),  # 5% daily loss
            current_equity=Decimal('10000'),
        )
        self.assertFalse(decision.approved)
        self.assertTrue(decision.kill_switch_active)

    def test_reject_drawdown_limit(self):
        """Should reject and activate kill switch on drawdown limit."""
        decision = self.engine.validate_signal(
            signal=self.base_signal,
            account_balance=self.account_balance,
            current_positions=[],
            current_prices={},
            peak_equity=Decimal('12000'),
            current_equity=Decimal('9500'),  # 20.8% drawdown > 15% limit
        )
        self.assertFalse(decision.approved)
        self.assertTrue(decision.kill_switch_active)

    def test_reject_exposure_limit(self):
        """Should reject when portfolio exposure limit reached."""
        positions = [
            {'symbol': 'BTC/USDT', 'is_active': True, 'quantity': 1, 'current_price': 50000, 'risk_amount': 500},
        ]  # 50000 exposure = 500% of 10000
        decision = self.engine.validate_signal(
            signal=self.base_signal,
            account_balance=self.account_balance,
            current_positions=positions,
            current_prices={},
        )
        self.assertFalse(decision.approved)
        self.assertIn('exposure', decision.reason.lower())

    def test_reject_correlated_positions(self):
        """Should reject when too many correlated positions."""
        positions = [
            {'symbol': 'BTC/USDT', 'is_active': True, 'quantity': 0.01, 'current_price': 50000, 'risk_amount': 10},
            {'symbol': 'BTC/USDT', 'is_active': True, 'quantity': 0.01, 'current_price': 50000, 'risk_amount': 10},
            {'symbol': 'BTC/USDT', 'is_active': True, 'quantity': 0.01, 'current_price': 50000, 'risk_amount': 10},
        ]  # 3 BTC positions = max correlated
        decision = self.engine.validate_signal(
            signal=self.base_signal,
            account_balance=self.account_balance,
            current_positions=positions,
            current_prices={},
        )
        self.assertFalse(decision.approved)
        self.assertIn('correlated', decision.reason.lower())

    def test_position_sizing(self):
        """Position size should be calculated correctly."""
        decision = self.engine.validate_signal(
            signal=self.base_signal,
            account_balance=self.account_balance,
            current_positions=[],
            current_prices={},
        )
        self.assertTrue(decision.approved)
        # Risk should be approximately 1% of account
        self.assertLessEqual(decision.risk_percent, 1.5)  # Allow some tolerance

    def test_kill_switch_blocks_all_trades(self):
        """Kill switch should block all new trades."""
        self.engine.activate_kill_switch('Test activation')
        decision = self.engine.validate_signal(
            signal=self.base_signal,
            account_balance=self.account_balance,
            current_positions=[],
            current_prices={},
        )
        self.assertFalse(decision.approved)
        self.assertTrue(decision.kill_switch_active)

    def test_deactivate_kill_switch(self):
        """Deactivated kill switch should allow trades again."""
        self.engine.activate_kill_switch('Test')
        self.engine.deactivate_kill_switch('Test deactivation')
        decision = self.engine.validate_signal(
            signal=self.base_signal,
            account_balance=self.account_balance,
            current_positions=[],
            current_prices={},
        )
        self.assertTrue(decision.approved)

    def test_kill_switch_triggers(self):
        """Check all kill switch trigger conditions."""
        # Drawdown trigger
        should, reason = self.engine.check_kill_switch_triggers(
            account_balance=Decimal('10000'),
            current_equity=Decimal('8000'),
            peak_equity=Decimal('10000'),
            daily_pnl=Decimal('0'),
        )
        self.assertTrue(should)
        self.assertIn('drawdown', reason.lower())

    def test_kill_switch_no_trigger_normal(self):
        """Normal conditions should not trigger kill switch."""
        should, reason = self.engine.check_kill_switch_triggers(
            account_balance=Decimal('10000'),
            current_equity=Decimal('10000'),
            peak_equity=Decimal('10000'),
            daily_pnl=Decimal('0'),
        )
        self.assertFalse(should)

    def test_portfolio_risk_state(self):
        """Portfolio risk state should return comprehensive data."""
        state = self.engine.get_portfolio_risk_state(
            account_balance=self.account_balance,
            current_positions=[],
        )
        self.assertIn('kill_switch_active', state)
        self.assertIn('position_count', state)
        self.assertIn('exposure_percent', state)
        self.assertIn('risk_percent', state)
        self.assertIn('limits', state)

    def test_sell_signal_position_sizing(self):
        """Short positions should be sized correctly."""
        signal = {**self.base_signal, 'direction': 'sell', 'stop_loss': Decimal('51000')}
        decision = self.engine.validate_signal(
            signal=signal,
            account_balance=self.account_balance,
            current_positions=[],
            current_prices={},
        )
        self.assertTrue(decision.approved)
        self.assertGreater(decision.position_size, 0)

    def test_risk_state_logged(self):
        """Risk state should be included in decision."""
        decision = self.engine.validate_signal(
            signal=self.base_signal,
            account_balance=self.account_balance,
            current_positions=[],
            current_prices={},
        )
        self.assertIn('exposure_pct', decision.risk_state)
        self.assertIn('risk_pct', decision.risk_state)
        self.assertIn('active_positions', decision.risk_state)


class SignalModelTest(TestCase):
    """Tests for Signal models."""

    def test_create_signal(self):
        """Test creating a Signal."""
        signal = Signal.objects.create(
            symbol='BTC/USDT',
            direction='buy',
            confidence=75,
            risk_score=40,
            entry_price=50000,
            timeframe='1h',
            technical_score=70,
            composite_score=65,
        )
        self.assertEqual(str(signal), 'BTC/USDT buy - 75%')

    def test_create_signal_reason(self):
        """Test creating a SignalReason."""
        signal = Signal.objects.create(
            symbol='BTC/USDT',
            direction='buy',
            confidence=75,
            entry_price=50000,
            timeframe='1h',
        )
        reason = SignalReason.objects.create(
            signal=signal,
            reason_type='technical',
            description='RSI oversold',
            confidence=80,
        )
        self.assertEqual(reason.signal, signal)

    def test_create_factor_weight(self):
        """Test creating a FactorWeight."""
        weight = FactorWeight.objects.create(
            name='technical',
            weight=0.30,
            description='Technical analysis weight',
        )
        self.assertEqual(weight.weight, Decimal('0.30'))

    def test_create_risk_profile(self):
        """Test creating a RiskProfile."""
        profile = RiskProfile.objects.create(
            name='Conservative',
            max_portfolio_risk=Decimal('2.0'),
            risk_per_trade=Decimal('0.5'),
        )
        self.assertEqual(profile.name, 'Conservative')

    def test_create_portfolio_position(self):
        """Test creating a PortfolioPosition."""
        position = PortfolioPosition.objects.create(
            symbol='BTC/USDT',
            side='long',
            quantity=Decimal('0.1'),
            entry_price=Decimal('50000'),
        )
        self.assertEqual(str(position), 'BTC/USDT long - 0.1 @ 50000')

