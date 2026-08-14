"""Calibration Engine — measures and improves probability calibration.

Calibration answers: "When the system says 80% confidence, is it right 80% of the time?"

Metrics Implemented:
    1. Brier Score — mean squared error of probability predictions (0=perfect, 1=worst)
    2. Reliability Curve — predicted probability vs actual success rate per bucket
    3. Expected Calibration Error (ECE) — weighted average of per-bucket calibration error
    4. Maximum Calibration Error (MCE) — worst single bucket
    5. Overconfidence / Underconfidence detection
    6. Calibration by regime, timeframe, and symbol

Architecture:
    SignalMemory (signal_confidence, was_correct)
        ↓
    CalibrationEngine
        ↓
    CalibrationRun (stored result)
        ↓
    API → Frontend → Reliability Curve Chart

Usage:
    engine = CalibrationEngine()
    result = engine.calibrate(
        predictions=[(80, True), (60, False), (70, True), ...]
    )
    # result.brier_score = 0.12
    # result.reliability_curve = [{'bucket': 0.1, 'predicted': 0.55, 'actual': 0.52, 'count': 15}, ...]
    # result.ece = 0.03
"""
import logging
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


# ── Configuration ─────────────────────────────────────────────────────

DEFAULT_NUM_BUCKETS = 10  # 0-10%, 10-20%, ..., 90-100%
MIN_SAMPLES_PER_BUCKET = 3  # Need at least 3 signals for a reliable bucket


@dataclass
class CalibrationBucket:
    """A single bucket in the reliability diagram."""
    bucket_index: int
    lower: float  # e.g. 0.0
    upper: float  # e.g. 0.1
    predicted_mean: float  # Average predicted confidence in this bucket
    actual_rate: float  # Actual success rate (was_correct %)
    count: int  # Number of signals in this bucket
    brier_contribution: float = 0.0  # This bucket's contribution to total Brier

    def to_dict(self) -> Dict:
        return {
            'bucket_index': self.bucket_index,
            'range': f"{self.lower:.0%}-{self.upper:.0%}",
            'predicted_mean': round(self.predicted_mean, 4),
            'actual_rate': round(self.actual_rate, 4),
            'count': self.count,
            'calibration_error': round(abs(self.predicted_mean - self.actual_rate), 4),
            'brier_contribution': round(self.brier_contribution, 4),
        }


@dataclass
class CalibrationResult:
    """Complete calibration analysis result."""
    # Core metrics
    brier_score: float = 0.0  # 0=perfect, 1=worst
    ece: float = 0.0  # Expected Calibration Error (0=perfect)
    mce: float = 0.0  # Maximum Calibration Error

    # Reliability curve data
    reliability_curve: List[Dict] = field(default_factory=list)

    # Diagnostics
    total_signals: int = 0
    overall_accuracy: float = 0.0
    overconfidence_detected: bool = False
    underconfidence_detected: bool = False
    calibration_quality: str = 'unknown'  # excellent, good, fair, poor, uncalibrated

    # Per-group breakdowns
    by_regime: Dict[str, Dict] = field(default_factory=dict)
    by_timeframe: Dict[str, Dict] = field(default_factory=dict)
    by_symbol: Dict[str, Dict] = field(default_factory=dict)

    # Metadata
    num_buckets: int = 0
    min_samples_per_bucket: int = 0
    computed_at: str = ''

    def __post_init__(self):
        if not self.computed_at:
            self.computed_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            'brier_score': round(self.brier_score, 6),
            'ece': round(self.ece, 6),
            'mce': round(self.mce, 6),
            'reliability_curve': self.reliability_curve,
            'total_signals': self.total_signals,
            'overall_accuracy': round(self.overall_accuracy, 4),
            'overconfidence_detected': self.overconfidence_detected,
            'underconfidence_detected': self.underconfidence_detected,
            'calibration_quality': self.calibration_quality,
            'by_regime': self.by_regime,
            'by_timeframe': self.by_timeframe,
            'by_symbol': self.by_symbol,
            'num_buckets': self.num_buckets,
            'computed_at': self.computed_at,
        }


# ── Calibration Engine ────────────────────────────────────────────────

class CalibrationEngine:
    """Measures and improves probability calibration.

    The engine takes pairs of (predicted_confidence, actual_outcome)
    and computes calibration metrics.

    predicted_confidence: 0-100 (system's confidence in its signal)
    actual_outcome: True/False (was the signal correct?)
    """

    def __init__(self, num_buckets: int = DEFAULT_NUM_BUCKETS, min_samples: int = MIN_SAMPLES_PER_BUCKET):
        self.num_buckets = num_buckets
        self.min_samples = min_samples

    def calibrate(
        self,
        predictions: List[Tuple[float, bool]],
        regime_data: Optional[Dict[float, str]] = None,
        timeframe_data: Optional[Dict[float, str]] = None,
        symbol_data: Optional[Dict[float, str]] = None,
    ) -> CalibrationResult:
        """Run full calibration analysis on prediction/outcome pairs.

        Args:
            predictions: List of (confidence_0_100, was_correct) tuples
            regime_data: Optional {index: regime_name} for per-regime analysis
            timeframe_data: Optional {index: timeframe} for per-timeframe analysis
            symbol_data: Optional {index: symbol} for per-symbol analysis

        Returns:
            CalibrationResult with all metrics
        """
        if not predictions:
            return CalibrationResult(
                calibration_quality='no_data',
                num_buckets=self.num_buckets,
            )

        # Normalize to 0-1 scale
        normalized = [(p / 100.0, 1.0 if o else 0.0) for p, o in predictions]

        # ── Brier Score ──────────────────────────────────────────────
        brier_score = self._brier_score(normalized)

        # ── Reliability Curve ─────────────────────────────────────────
        buckets = self._compute_reliability_curve(normalized)
        reliability_curve = [b.to_dict() for b in buckets]

        # ── ECE and MCE ──────────────────────────────────────────────
        ece, mce = self._compute_ece_mce(buckets)

        # ── Overall accuracy ──────────────────────────────────────────
        total = len(predictions)
        correct = sum(1 for _, o in predictions if o)
        overall_accuracy = correct / total if total > 0 else 0.0

        # ── Overconfidence / Underconfidence ──────────────────────────
        overconf, underconf = self._detect_calibration_bias(buckets)

        # ── Calibration quality rating ────────────────────────────────
        quality = self._rate_calibration_quality(ece, brier_score)

        # ── Per-group breakdowns ──────────────────────────────────────
        by_regime = {}
        by_timeframe = {}
        by_symbol = {}

        if regime_data:
            by_regime = self._calibrate_by_group(normalized, regime_data, 'regime')
        if timeframe_data:
            by_timeframe = self._calibrate_by_group(normalized, timeframe_data, 'timeframe')
        if symbol_data:
            by_symbol = self._calibrate_by_group(normalized, symbol_data, 'symbol')

        result = CalibrationResult(
            brier_score=brier_score,
            ece=ece,
            mce=mce,
            reliability_curve=reliability_curve,
            total_signals=total,
            overall_accuracy=overall_accuracy,
            overconfidence_detected=overconf,
            underconfidence_detected=underconf,
            calibration_quality=quality,
            by_regime=by_regime,
            by_timeframe=by_timeframe,
            by_symbol=by_symbol,
            num_buckets=self.num_buckets,
            min_samples_per_bucket=self.min_samples,
        )

        logger.info(
            f"Calibration: Brier={brier_score:.4f} | ECE={ece:.4f} | "
            f"Quality={quality} | Signals={total}"
        )

        return result

    def calibrate_from_database(self, symbol: str = None, limit: int = 500) -> CalibrationResult:
        """Calibrate using actual SignalMemory data from the database.

        Args:
            symbol: Optional filter by symbol
            limit: Max signals to analyze

        Returns:
            CalibrationResult
        """
        try:
            from ..models import Signal
            from apps.feedback.models import SignalMemory

            # Get evaluated signals with confidence and outcome
            query = SignalMemory.objects.filter(
                evaluated_at__isnull=False,
            ).select_related('signal')

            if symbol:
                query = query.filter(signal__symbol=symbol.upper())

            memories = query.order_by('-created_at')[:limit]

            predictions = []
            regime_map = {}
            timeframe_map = {}
            symbol_map = {}

            for i, mem in enumerate(memories):
                confidence = float(mem.signal_confidence)
                outcome = mem.was_correct

                predictions.append((confidence, outcome))

                # Collect grouping data
                factors = mem.factors_at_creation or {}
                regime = factors.get('regime', 'unknown')
                regime_map[i] = regime
                timeframe_map[i] = mem.signal.timeframe if hasattr(mem, 'signal') else 'unknown'
                symbol_map[i] = mem.signal.symbol if hasattr(mem, 'signal') else 'unknown'

            return self.calibrate(
                predictions,
                regime_data=regime_map if regime_map else None,
                timeframe_data=timeframe_map if timeframe_map else None,
                symbol_data=symbol_map if symbol_map else None,
            )

        except Exception as e:
            logger.error(f"Database calibration failed: {e}")
            return CalibrationResult(calibration_quality='error')

    # ── Core Metrics ──────────────────────────────────────────────────

    def _brier_score(self, normalized: List[Tuple[float, float]]) -> float:
        """Calculate Brier Score: mean((predicted - actual)²).

        Lower is better: 0 = perfect, 1 = worst possible.
        """
        if not normalized:
            return 0.0

        total = 0.0
        for predicted, actual in normalized:
            total += (predicted - actual) ** 2

        return total / len(normalized)

    def _compute_reliability_curve(self, normalized: List[Tuple[float, float]]) -> List[CalibrationBucket]:
        """Compute reliability curve: predicted vs actual per bucket."""
        buckets = []

        for i in range(self.num_buckets):
            lower = i / self.num_buckets
            upper = (i + 1) / self.num_buckets

            # Get predictions in this bucket
            bucket_predictions = [
                (p, o) for p, o in normalized
                if lower <= p < upper or (i == self.num_buckets - 1 and p == upper)
            ]

            if len(bucket_predictions) >= self.min_samples:
                predicted_mean = sum(p for p, _ in bucket_predictions) / len(bucket_predictions)
                actual_rate = sum(o for _, o in bucket_predictions) / len(bucket_predictions)
                count = len(bucket_predictions)

                # Brier contribution from this bucket
                brier_contribution = sum(
                    (p - o) ** 2 for p, o in bucket_predictions
                ) / len(normalized)
            else:
                predicted_mean = (lower + upper) / 2
                actual_rate = 0.0
                count = 0
                brier_contribution = 0.0

            buckets.append(CalibrationBucket(
                bucket_index=i,
                lower=lower,
                upper=upper,
                predicted_mean=predicted_mean,
                actual_rate=actual_rate,
                count=count,
                brier_contribution=brier_contribution,
            ))

        return buckets

    def _compute_ece_mce(self, buckets: List[CalibrationBucket]) -> Tuple[float, float]:
        """Compute Expected Calibration Error and Maximum Calibration Error."""
        total_samples = sum(b.count for b in buckets)
        if total_samples == 0:
            return 0.0, 0.0

        ece = 0.0
        mce = 0.0

        for bucket in buckets:
            if bucket.count == 0:
                continue

            weight = bucket.count / total_samples
            error = abs(bucket.predicted_mean - bucket.actual_rate)

            ece += weight * error
            mce = max(mce, error)

        return ece, mce

    def _detect_calibration_bias(self, buckets: List[CalibrationBucket]) -> Tuple[bool, bool]:
        """Detect systematic overconfidence or underconfidence.

        Overconfidence: predicted > actual consistently (system says 80% but only right 60%)
        Underconfidence: predicted < actual consistently (system says 60% but right 80%)
        """
        weighted_over = 0.0
        weighted_under = 0.0
        total_weight = 0.0

        for bucket in buckets:
            if bucket.count < self.min_samples:
                continue

            weight = bucket.count
            diff = bucket.predicted_mean - bucket.actual_rate

            if diff > 0:
                weighted_over += diff * weight
            else:
                weighted_under += abs(diff) * weight

            total_weight += weight

        if total_weight == 0:
            return False, False

        avg_over = weighted_over / total_weight
        avg_under = weighted_under / total_weight

        # Threshold: 5% systematic bias
        overconfidence = avg_over > 0.05
        underconfidence = avg_under > 0.05

        return overconfidence, underconfidence

    def _rate_calibration_quality(self, ece: float, brier: float) -> str:
        """Rate overall calibration quality."""
        if ece < 0.03 and brier < 0.15:
            return 'excellent'
        elif ece < 0.05 and brier < 0.20:
            return 'good'
        elif ece < 0.10 and brier < 0.25:
            return 'fair'
        elif ece < 0.20:
            return 'poor'
        else:
            return 'uncalibrated'

    def _calibrate_by_group(
        self,
        normalized: List[Tuple[float, float]],
        group_map: Dict[int, str],
        group_name: str,
    ) -> Dict[str, Dict]:
        """Run calibration for each subgroup (regime, timeframe, symbol)."""
        # Group predictions
        groups: Dict[str, List[Tuple[float, float]]] = {}
        for i, (predicted, actual) in enumerate(normalized):
            group = group_map.get(i, 'unknown')
            if group not in groups:
                groups[group] = []
            groups[group].append((predicted, actual))

        results = {}
        for group, preds in groups.items():
            if len(preds) < self.min_samples:
                continue

            brier = self._brier_score(preds)
            buckets = self._compute_reliability_curve(preds)
            ece, mce = self._compute_ece_mce(buckets)

            correct = sum(1 for _, o in preds if o)
            accuracy = correct / len(preds)

            results[group] = {
                'brier_score': round(brier, 6),
                'ece': round(ece, 6),
                'accuracy': round(accuracy, 4),
                'count': len(preds),
                'quality': self._rate_calibration_quality(ece, brier),
            }

        return results


# ── Probability Adjuster ──────────────────────────────────────────────

class ProbabilityAdjuster:
    """Adjusts raw confidence scores based on calibration data.

    If the system is overconfident (says 80% but is right 60%),
    the adjuster maps 80% → ~60% based on the reliability curve.
    """

    @staticmethod
    def adjust_confidence(
        raw_confidence: float,
        reliability_curve: List[Dict],
    ) -> float:
        """Adjust confidence using the reliability curve.

        Args:
            raw_confidence: System's raw confidence (0-100)
            reliability_curve: From CalibrationResult.reliability_curve

        Returns:
            Adjusted confidence (0-100)
        """
        if not reliability_curve:
            return raw_confidence

        raw_01 = raw_confidence / 100.0

        # Find the bucket this confidence falls into
        for bucket in reliability_curve:
            bucket_range = bucket.get('range', '0%-10%')
            lower_str, upper_str = bucket_range.split('-')
            lower = float(lower_str.strip('%')) / 100.0
            upper = float(upper_str.strip('%')) / 100.0

            if lower <= raw_01 < upper or (bucket == reliability_curve[-1] and raw_01 == upper):
                actual_rate = bucket.get('actual_rate', raw_01)
                count = bucket.get('count', 0)

                if count >= 3:
                    # Blend: more data → more adjustment
                    blend = min(1.0, count / 20.0)  # Full adjustment at 20+ samples
                    adjusted = raw_01 * (1 - blend) + actual_rate * blend
                    return max(0, min(100, adjusted * 100))

        return raw_confidence
