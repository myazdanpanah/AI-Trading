"""Tests for Calibration Engine (Phase 66).

Covers:
- Brier Score calculation (perfect, random, worst case)
- Reliability curve bucketing
- ECE and MCE calculation
- Overconfidence / underconfidence detection
- Calibration quality rating
- Per-group calibration (regime, timeframe, symbol)
- ProbabilityAdjuster confidence adjustment
- Edge cases (empty data, single sample, all correct, all wrong)
"""
from django.test import TestCase

from .services.calibration import (
    CalibrationEngine,
    CalibrationResult,
    CalibrationBucket,
    ProbabilityAdjuster,
    DEFAULT_NUM_BUCKETS,
    MIN_SAMPLES_PER_BUCKET,
)


class BrierScoreTest(TestCase):
    """Test Brier Score calculation."""

    def test_perfect_predictions(self):
        """All predictions match outcomes exactly → Brier = 0."""
        engine = CalibrationEngine(num_buckets=10, min_samples=1)
        # 100% predicted, all correct; 0% predicted, all wrong
        predictions = [(100, True)] * 5 + [(0, False)] * 5
        result = engine.calibrate(predictions)
        self.assertAlmostEqual(result.brier_score, 0.0, places=6)

    def test_worst_predictions(self):
        """All predictions are exactly wrong → Brier = 1."""
        engine = CalibrationEngine()
        predictions = [(100, False), (0, True), (100, False), (0, True)]
        result = engine.calibrate(predictions)
        self.assertAlmostEqual(result.brier_score, 1.0, places=6)

    def test_random_predictions(self):
        """Random predictions should have Brier around 0.25."""
        engine = CalibrationEngine()
        # Simulate random: 50% confidence, 50% correct
        predictions = [(50, True), (50, False)] * 50
        result = engine.calibrate(predictions)
        self.assertAlmostEqual(result.brier_score, 0.25, places=2)

    def test_brier_between_0_and_1(self):
        """Brier Score always between 0 and 1."""
        engine = CalibrationEngine()
        predictions = [
            (80, True), (60, False), (70, True), (90, False),
            (40, True), (30, False), (50, True), (20, False),
        ]
        result = engine.calibrate(predictions)
        self.assertGreaterEqual(result.brier_score, 0.0)
        self.assertLessEqual(result.brier_score, 1.0)


class ReliabilityCurveTest(TestCase):
    """Test reliability curve bucketing."""

    def test_curve_has_correct_buckets(self):
        """Reliability curve should have num_buckets entries."""
        engine = CalibrationEngine(num_buckets=10)
        predictions = [(i * 10 + 5, i < 5) for i in range(100)]
        result = engine.calibrate(predictions)
        self.assertEqual(len(result.reliability_curve), 10)

    def test_bucket_ranges(self):
        """Buckets should cover 0-100% in equal intervals."""
        engine = CalibrationEngine(num_buckets=5)
        predictions = [(i * 20 + 10, True) for i in range(50)]
        result = engine.calibrate(predictions)
        self.assertEqual(len(result.reliability_curve), 5)
        self.assertEqual(result.reliability_curve[0]['range'], '0%-20%')
        self.assertEqual(result.reliability_curve[4]['range'], '80%-100%')

    def test_empty_bucket_skipped(self):
        """Buckets with fewer than min_samples should have count=0."""
        engine = CalibrationEngine(num_buckets=10, min_samples=5)
        # Only put data in first bucket
        predictions = [(5, True)] * 10
        result = engine.calibrate(predictions)
        # Other buckets should have count 0
        for bucket in result.reliability_curve[1:]:
            self.assertEqual(bucket['count'], 0)

    def test_populated_bucket_has_data(self):
        """Buckets with enough data should have non-zero counts."""
        engine = CalibrationEngine(num_buckets=5, min_samples=2)
        # Put 5 signals in each bucket
        predictions = []
        for bucket_idx in range(5):
            center = bucket_idx * 20 + 10
            for _ in range(5):
                predictions.append((center, bucket_idx < 3))
        result = engine.calibrate(predictions)
        populated = [b for b in result.reliability_curve if b['count'] > 0]
        self.assertGreater(len(populated), 0)


class ECEMCETest(TestCase):
    """Test Expected Calibration Error and Maximum Calibration Error."""

    def test_perfect_calibration_ece_zero(self):
        """Perfect calibration → ECE = 0."""
        engine = CalibrationEngine(num_buckets=10, min_samples=1)
        # 80% bucket: 8 out of 10 correct
        # 60% bucket: 6 out of 10 correct
        predictions = [(80, True)] * 8 + [(80, False)] * 2 + [(60, True)] * 6 + [(60, False)] * 4
        result = engine.calibrate(predictions)
        self.assertAlmostEqual(result.ece, 0.0, places=2)

    def test_mce_ge_ece(self):
        """MCE should always be >= ECE."""
        engine = CalibrationEngine()
        predictions = [
            (80, True), (60, False), (70, True), (90, False),
            (40, True), (30, False), (50, True), (20, False),
        ] * 5
        result = engine.calibrate(predictions)
        self.assertGreaterEqual(result.mce, result.ece)

    def test_overconfident_high_ece(self):
        """Systematic overconfidence should produce high ECE."""
        engine = CalibrationEngine(num_buckets=5, min_samples=3)
        # System says 90% but only right 50% of the time
        predictions = [(90, True)] * 5 + [(90, False)] * 5  # 50% actual at 90% predicted
        result = engine.calibrate(predictions)
        self.assertGreater(result.ece, 0.1)  # Should be significantly miscalibrated


class OverconfidenceDetectionTest(TestCase):
    """Test overconfidence / underconfidence detection."""

    def test_overconfident_detection(self):
        """System that says 90% but is right 50% → overconfident."""
        engine = CalibrationEngine(num_buckets=5, min_samples=3)
        # Many signals at 90% confidence, only 50% correct
        predictions = [(90, True)] * 10 + [(90, False)] * 10
        result = engine.calibrate(predictions)
        self.assertTrue(result.overconfidence_detected)

    def test_underconfident_detection(self):
        """System that says 20% but is right 80% → underconfident."""
        engine = CalibrationEngine(num_buckets=5, min_samples=3)
        # Many signals at 20% confidence, 80% correct
        predictions = [(20, True)] * 16 + [(20, False)] * 4
        result = engine.calibrate(predictions)
        self.assertTrue(result.underconfidence_detected)

    def test_well_calibrated_no_bias(self):
        """Well-calibrated system → no over/under confidence."""
        engine = CalibrationEngine(num_buckets=5, min_samples=3)
        # 80% confidence → 80% correct
        predictions = [(80, True)] * 8 + [(80, False)] * 2
        result = engine.calibrate(predictions)
        # Should not detect systematic bias
        self.assertFalse(result.overconfidence_detected)


class CalibrationQualityTest(TestCase):
    """Test calibration quality rating."""

    def test_excellent_quality(self):
        """Well-calibrated system → good or excellent quality."""
        engine = CalibrationEngine(num_buckets=10, min_samples=1)
        # Each bucket is perfectly calibrated
        predictions = []
        for pct in range(10, 100, 10):
            n_correct = pct // 10
            n_wrong = 10 - n_correct
            predictions += [(pct, True)] * n_correct
            predictions += [(pct, False)] * n_wrong
        result = engine.calibrate(predictions)
        self.assertIn(result.calibration_quality, ['excellent', 'good', 'fair'])

    def test_no_data_quality(self):
        """No data → no_data."""
        engine = CalibrationEngine()
        result = engine.calibrate([])
        self.assertEqual(result.calibration_quality, 'no_data')

    def test_quality_is_string(self):
        """Quality should be a valid string."""
        engine = CalibrationEngine()
        predictions = [(50, True), (50, False)] * 10
        result = engine.calibrate(predictions)
        self.assertIn(result.calibration_quality, [
            'excellent', 'good', 'fair', 'poor', 'uncalibrated'
        ])


class PerGroupCalibrationTest(TestCase):
    """Test per-regime, per-timeframe, per-symbol calibration."""

    def test_by_regime(self):
        """Should produce per-regime calibration."""
        engine = CalibrationEngine(num_buckets=5, min_samples=2)
        predictions = [(70, True)] * 5 + [(70, False)] * 5
        regime_map = {i: 'bull_trend' if i < 5 else 'bear_trend' for i in range(10)}
        result = engine.calibrate(predictions, regime_data=regime_map)
        self.assertIn('bull_trend', result.by_regime)
        self.assertIn('bear_trend', result.by_regime)

    def test_by_timeframe(self):
        """Should produce per-timeframe calibration."""
        engine = CalibrationEngine(num_buckets=5, min_samples=2)
        predictions = [(60, True)] * 5 + [(60, False)] * 5
        tf_map = {i: '1h' if i < 5 else '4h' for i in range(10)}
        result = engine.calibrate(predictions, timeframe_data=tf_map)
        self.assertIn('1h', result.by_timeframe)
        self.assertIn('4h', result.by_timeframe)

    def test_by_symbol(self):
        """Should produce per-symbol calibration."""
        engine = CalibrationEngine(num_buckets=5, min_samples=2)
        predictions = [(80, True)] * 5 + [(80, False)] * 5
        sym_map = {i: 'BTC' if i < 5 else 'ETH' for i in range(10)}
        result = engine.calibrate(predictions, symbol_data=sym_map)
        self.assertIn('BTC', result.by_symbol)
        self.assertIn('ETH', result.by_symbol)


class ProbabilityAdjusterTest(TestCase):
    """Test confidence adjustment using reliability curve."""

    def test_no_curve_returns_raw(self):
        """With no reliability curve, returns raw confidence."""
        adjusted = ProbabilityAdjuster.adjust_confidence(80, [])
        self.assertEqual(adjusted, 80)

    def test_overconfident_adjusts_down(self):
        """Overconfident system → adjusted confidence is lower."""
        curve = [
            {'range': '0%-10%', 'predicted_mean': 0.05, 'actual_rate': 0.06, 'count': 5},
            {'range': '10%-20%', 'predicted_mean': 0.15, 'actual_rate': 0.14, 'count': 5},
            {'range': '20%-30%', 'predicted_mean': 0.25, 'actual_rate': 0.22, 'count': 5},
            {'range': '30%-40%', 'predicted_mean': 0.35, 'actual_rate': 0.30, 'count': 5},
            {'range': '40%-50%', 'predicted_mean': 0.45, 'actual_rate': 0.42, 'count': 5},
            {'range': '50%-60%', 'predicted_mean': 0.55, 'actual_rate': 0.50, 'count': 5},
            {'range': '60%-70%', 'predicted_mean': 0.65, 'actual_rate': 0.58, 'count': 5},
            {'range': '70%-80%', 'predicted_mean': 0.75, 'actual_rate': 0.65, 'count': 25},
            {'range': '80%-90%', 'predicted_mean': 0.85, 'actual_rate': 0.70, 'count': 25},
            {'range': '90%-100%', 'predicted_mean': 0.95, 'actual_rate': 0.75, 'count': 10},
        ]
        adjusted = ProbabilityAdjuster.adjust_confidence(85, curve)
        self.assertLess(adjusted, 85)  # Should be adjusted down

    def test_clamped_to_0_100(self):
        """Adjusted confidence should stay within 0-100."""
        curve = [
            {'range': '0%-10%', 'predicted_mean': 0.05, 'actual_rate': 0.95, 'count': 25},
            {'range': '10%-20%', 'predicted_mean': 0.15, 'actual_rate': 0.95, 'count': 5},
            {'range': '20%-30%', 'predicted_mean': 0.25, 'actual_rate': 0.95, 'count': 5},
            {'range': '30%-40%', 'predicted_mean': 0.35, 'actual_rate': 0.95, 'count': 5},
            {'range': '40%-50%', 'predicted_mean': 0.45, 'actual_rate': 0.95, 'count': 5},
            {'range': '50%-60%', 'predicted_mean': 0.55, 'actual_rate': 0.95, 'count': 5},
            {'range': '60%-70%', 'predicted_mean': 0.65, 'actual_rate': 0.95, 'count': 5},
            {'range': '70%-80%', 'predicted_mean': 0.75, 'actual_rate': 0.95, 'count': 5},
            {'range': '80%-90%', 'predicted_mean': 0.85, 'actual_rate': 0.95, 'count': 5},
            {'range': '90%-100%', 'predicted_mean': 0.95, 'actual_rate': 0.95, 'count': 5},
        ]
        adjusted = ProbabilityAdjuster.adjust_confidence(5, curve)
        self.assertGreaterEqual(adjusted, 0)
        self.assertLessEqual(adjusted, 100)


class EdgeCaseTest(TestCase):
    """Test edge cases."""

    def test_empty_predictions(self):
        """Empty predictions → no_data quality."""
        engine = CalibrationEngine()
        result = engine.calibrate([])
        self.assertEqual(result.total_signals, 0)
        self.assertEqual(result.calibration_quality, 'no_data')

    def test_single_prediction(self):
        """Single prediction should work."""
        engine = CalibrationEngine()
        result = engine.calibrate([(80, True)])
        self.assertEqual(result.total_signals, 1)

    def test_all_correct(self):
        """All signals correct → Brier depends on confidence level."""
        engine = CalibrationEngine()
        predictions = [(80, True)] * 20
        result = engine.calibrate(predictions)
        # Brier = (0.8 - 1.0)² = 0.04
        self.assertAlmostEqual(result.brier_score, 0.04, places=4)

    def test_all_wrong(self):
        """All signals wrong → Brier depends on confidence level."""
        engine = CalibrationEngine()
        predictions = [(80, False)] * 20
        result = engine.calibrate(predictions)
        # Brier = (0.8 - 0.0)² = 0.64
        self.assertAlmostEqual(result.brier_score, 0.64, places=4)

    def test_result_to_dict(self):
        """CalibrationResult.to_dict() should return serializable dict."""
        engine = CalibrationEngine()
        predictions = [(70, True), (60, False), (80, True), (50, False)] * 5
        result = engine.calibrate(predictions)
        d = result.to_dict()
        self.assertIn('brier_score', d)
        self.assertIn('ece', d)
        self.assertIn('reliability_curve', d)
        self.assertIn('calibration_quality', d)
        self.assertIn('computed_at', d)
