"""Learning services tests - Comprehensive test suite."""
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase
from .models import SignalResult, ModelPerformance, StrategyWeight, BacktestResult
from .services import PerformanceTracker, WeightOptimizer, AccuracyImprover
from signals.models import Signal


class PerformanceTrackerTest(TestCase):
    """Tests for the PerformanceTracker service."""

    def setUp(self):
        self.tracker = PerformanceTracker()
        # Create test signal
        self.signal = Signal.objects.create(
            symbol='BTC/USDT',
            direction='buy',
            confidence=75,
            entry_price=Decimal('50000'),
            timeframe='1h',
        )

    def test_record_signal_outcome(self):
        """Test recording a signal outcome."""
        result = self.tracker.record_signal_outcome(
            signal_id=str(self.signal.id),
            exit_price=Decimal('51000'),
            profit_loss=Decimal('100'),
            profit_loss_percent=Decimal('2.0'),
            success=True,
            duration_hours=4,
        )
        self.assertEqual(result['signal_id'], str(self.signal.id))
        self.assertTrue(result['success'])
        self.assertEqual(SignalResult.objects.count(), 1)

    def test_get_signal_performance(self):
        """Test getting signal performance metrics."""
        # Create some results
        for i in range(10):
            SignalResult.objects.create(
                signal=self.signal,
                exit_price=Decimal('50000'),
                profit_loss=Decimal('100') if i % 3 != 0 else Decimal('-50'),
                profit_loss_percent=Decimal('2.0') if i % 3 != 0 else Decimal('-1.0'),
                success=i % 3 != 0,
                duration_hours=4,
            )
        
        result = self.tracker.get_signal_performance()
        self.assertIn('win_rate', result)
        self.assertIn('total_signals', result)
        self.assertEqual(result['total_signals'], 10)

    def test_get_daily_performance(self):
        """Test getting daily performance metrics."""
        # Create results across multiple days
        for i in range(5):
            SignalResult.objects.create(
                signal=self.signal,
                exit_price=Decimal('50000'),
                profit_loss=Decimal('100'),
                profit_loss_percent=Decimal('2.0'),
                success=True,
                duration_hours=4,
                evaluated_at=datetime.now() - timedelta(days=i),
            )
        
        result = self.tracker.get_daily_performance(days=7)
        self.assertGreater(len(result), 0)

    def test_empty_performance(self):
        """Test performance with no data."""
        result = self.tracker.get_signal_performance()
        self.assertEqual(result['total_signals'], 0)
        self.assertEqual(result['win_rate'], 0)


class WeightOptimizerTest(TestCase):
    """Tests for the WeightOptimizer service."""

    def setUp(self):
        self.optimizer = WeightOptimizer()
        # Create initial weights
        for component in ['technical', 'sentiment', 'news', 'ai', 'macro']:
            StrategyWeight.objects.create(
                component=component,
                weight=Decimal('10'),
                performance_score=Decimal('50'),
            )

    def test_optimize_weights(self):
        """Test weight optimization."""
        result = self.optimizer.optimize_weights()
        self.assertIn('optimized_weights', result)
        self.assertIn('weight_changes', result)
        self.assertEqual(len(result['optimized_weights']), 5)

    def test_get_current_weights(self):
        """Test getting current weights."""
        result = self.optimizer.get_current_weights()
        self.assertEqual(len(result), 5)
        self.assertIn('technical', result)

    def test_weight_constraints(self):
        """Test that weights stay within constraints."""
        result = self.optimizer.optimize_weights()
        for weight in result['optimized_weights'].values():
            self.assertGreaterEqual(weight, 5)  # MIN_WEIGHT * 100
            self.assertLessEqual(weight, 50)    # MAX_WEIGHT * 100


class AccuracyImproverTest(TestCase):
    """Tests for the AccuracyImprover service."""

    def setUp(self):
        self.improver = AccuracyImprover()
        # Create test signal
        self.signal = Signal.objects.create(
            symbol='BTC/USDT',
            direction='buy',
            confidence=75,
            entry_price=Decimal('50000'),
            timeframe='1h',
        )
        
        # Create enough results for analysis
        for i in range(25):
            SignalResult.objects.create(
                signal=self.signal,
                exit_price=Decimal('50000'),
                profit_loss=Decimal('100') if i % 2 == 0 else Decimal('-50'),
                profit_loss_percent=Decimal('2.0') if i % 2 == 0 else Decimal('-1.0'),
                success=i % 2 == 0,
                duration_hours=4,
                market_condition='trending',
            )

    def test_analyze_accuracy_patterns(self):
        """Test accuracy pattern analysis."""
        result = self.improver.analyze_accuracy_patterns()
        self.assertEqual(result['status'], 'analysis_complete')
        self.assertIn('patterns', result)
        self.assertIn('recommendations', result)

    def test_get_accuracy_recommendations(self):
        """Test getting accuracy recommendations."""
        result = self.improver.get_accuracy_recommendations()
        self.assertIsInstance(result, list)

    def test_predict_signal_quality(self):
        """Test signal quality prediction."""
        result = self.improver.predict_signal_quality({
            'symbol': 'BTC/USDT',
            'timeframe': '1h',
            'direction': 'buy',
            'confidence': 75,
        })
        self.assertIn('predicted_quality', result)
        self.assertIn('predicted_win_rate', result)

    def test_insufficient_data(self):
        """Test with insufficient data."""
        # Clear all results
        SignalResult.objects.all().delete()
        
        result = self.improver.analyze_accuracy_patterns()
        self.assertEqual(result['status'], 'insufficient_data')


class LearningModelTest(TestCase):
    """Tests for Learning models."""

    def test_create_signal_result(self):
        """Test creating a SignalResult."""
        signal = Signal.objects.create(
            symbol='BTC/USDT',
            direction='buy',
            confidence=75,
            entry_price=Decimal('50000'),
            timeframe='1h',
        )
        result = SignalResult.objects.create(
            signal=signal,
            exit_price=Decimal('51000'),
            profit_loss=Decimal('100'),
            profit_loss_percent=Decimal('2.0'),
            success=True,
            duration_hours=4,
        )
        self.assertTrue(result.success)

    def test_create_strategy_weight(self):
        """Test creating a StrategyWeight."""
        weight = StrategyWeight.objects.create(
            component='technical',
            weight=Decimal('10'),
            performance_score=Decimal('55'),
        )
        self.assertEqual(str(weight), 'technical: 10.00%')

    def test_create_model_performance(self):
        """Test creating a ModelPerformance."""
        perf = ModelPerformance.objects.create(
            model_name='gpt-4',
            accuracy=Decimal('75.5'),
            date=datetime.now().date(),
        )
        self.assertEqual(str(perf), 'gpt-4 - ' + datetime.now().date().isoformat())
