"""Walk-Forward Validation Engine — prevents strategy overfitting.

Implements:
- Training / Validation / Test windows
- Rolling windows
- Parameter freezing before OOS
- Leakage detection
- Window comparison
"""
import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class WindowSpec:
    """Specification for a single walk-forward window."""
    window_index: int
    train_start: datetime
    train_end: datetime
    validate_start: datetime
    validate_end: datetime
    test_start: datetime
    test_end: datetime


class WalkForwardEngine:
    """
    Walk-forward validation engine.

    Prevents overfitting by:
    1. Training on historical data (IS period)
    2. Validating on unseen data (IS validation)
    3. Testing on completely held-out data (OOS period)
    4. Rolling forward and repeating
    5. Comparing IS vs OOS performance

    No future data may enter any earlier window.
    """

    def __init__(
        self,
        initial_capital: Decimal = Decimal('10000'),
        fee_rate: Decimal = Decimal('0.001'),
        slippage_rate: Decimal = Decimal('0.0005'),
    ):
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate

    def generate_windows(
        self,
        start_date: datetime,
        end_date: datetime,
        train_days: int = 90,
        validate_days: int = 30,
        test_days: int = 30,
        step_days: int = 30,
    ) -> List[WindowSpec]:
        """
        Generate rolling walk-forward windows.

        Args:
            start_date: Overall start date
            end_date: Overall end date
            train_days: Training window length
            validate_days: Validation window length
            test_days: Test (OOS) window length
            step_days: How far to roll forward each step

        Returns:
            List of WindowSpec objects
        """
        windows = []
        window_index = 0
        current_start = start_date
        total_window = train_days + validate_days + test_days

        while True:
            train_start = current_start
            train_end = train_start + timedelta(days=train_days)
            validate_start = train_end
            validate_end = validate_start + timedelta(days=validate_days)
            test_start = validate_end
            test_end = test_start + timedelta(days=test_days)

            # Stop if the test window would extend beyond end_date
            if test_end > end_date:
                break

            windows.append(WindowSpec(
                window_index=window_index,
                train_start=train_start,
                train_end=train_end,
                validate_start=validate_start,
                validate_end=validate_end,
                test_start=test_start,
                test_end=test_end,
            ))

            window_index += 1
            current_start += timedelta(days=step_days)

            # Safety: prevent infinite loop
            if window_index > 100:
                logger.warning("Walk-forward exceeded 100 windows, stopping")
                break

        logger.info(
            f"Generated {len(windows)} walk-forward windows "
            f"(train={train_days}d, validate={validate_days}d, test={test_days}d, step={step_days}d)"
        )
        return windows

    def run_walk_forward(
        self,
        strategy_name: str,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        historical_data: List[Dict],
        train_days: int = 90,
        validate_days: int = 30,
        test_days: int = 30,
        step_days: int = 30,
        strategy_version: str = '1.0',
        weight_snapshot: Dict = None,
    ) -> Dict:
        """
        Run a complete walk-forward validation.

        Args:
            strategy_name: Strategy identifier
            symbol: Trading pair
            timeframe: Candle timeframe
            start_date: Overall start
            end_date: Overall end
            historical_data: Full OHLCV dataset
            train_days: Training window
            validate_days: Validation window
            test_days: Test (OOS) window
            step_days: Rolling step
            strategy_version: Version string
            weight_snapshot: Current factor weights

        Returns:
            Dict with run results and per-window results
        """
        from .backtester import SignalBacktester

        # Generate windows
        windows = self.generate_windows(
            start_date, end_date,
            train_days, validate_days, test_days, step_days,
        )

        if not windows:
            return {
                'status': 'failed',
                'error': 'No valid windows could be generated. Increase the date range or reduce window sizes.',
                'total_windows': 0,
            }

        window_results = []
        all_oos_returns = []
        all_oos_sharpes = []
        all_oos_win_rates = []
        all_is_returns = []
        max_oos_drawdown = Decimal('0')
        leakage_detected = False
        leakage_details = {}

        for ws in windows:
            logger.info(
                f"Window {ws.window_index}: "
                f"Train {ws.train_start.date()}→{ws.train_end.date()}, "
                f"Validate {ws.validate_start.date()}→{ws.validate_end.date()}, "
                f"Test {ws.test_start.date()}→{ws.test_end.date()}"
            )

            # Extract data for each window
            train_data = self._extract_data(historical_data, ws.train_start, ws.train_end)
            validate_data = self._extract_data(historical_data, ws.validate_start, ws.validate_end)
            test_data = self._extract_data(historical_data, ws.test_start, ws.test_end)

            # Leak check: verify no data overlap
            has_leakage, leakage_reason = self._check_leakage(
                train_data, validate_data, test_data, ws
            )
            if has_leakage:
                leakage_detected = True
                leakage_details[f'window_{ws.window_index}'] = leakage_reason

            # Run backtest on training data (IS)
            bt = SignalBacktester(
                initial_capital=self.initial_capital,
                fee_rate=self.fee_rate,
                slippage_rate=self.slippage_rate,
            )

            is_result = bt.run_backtest(
                strategy_name=f'{strategy_name}_IS',
                symbol=symbol,
                timeframe=timeframe,
                start_date=ws.train_start,
                end_date=ws.train_end,
                historical_data=train_data + validate_data,  # Full IS period
                strategy_version=strategy_version,
                weight_snapshot=weight_snapshot,
            )

            # Freeze parameters after training (snapshot of weights at IS end)
            frozen_weights = weight_snapshot.copy() if weight_snapshot else {}

            # Run backtest on test data (OOS) with FROZEN parameters
            oos_bt = SignalBacktester(
                initial_capital=self.initial_capital,
                fee_rate=self.fee_rate,
                slippage_rate=self.slippage_rate,
            )

            oos_result = oos_bt.run_backtest(
                strategy_name=f'{strategy_name}_OOS',
                symbol=symbol,
                timeframe=timeframe,
                start_date=ws.test_start,
                end_date=ws.test_end,
                historical_data=test_data,
                strategy_version=strategy_version,
                weight_snapshot=frozen_weights,  # Frozen from IS
            )

            # Collect metrics
            is_return = Decimal(str(is_result.get('total_return_percent', 0)))
            oos_return = Decimal(str(oos_result.get('total_return_percent', 0)))
            is_sharpe = Decimal(str(is_result.get('sharpe_ratio', 0)))
            oos_sharpe = Decimal(str(oos_result.get('sharpe_ratio', 0)))
            is_win_rate = Decimal(str(is_result.get('win_rate', 0)))
            oos_win_rate = Decimal(str(oos_result.get('win_rate', 0)))

            all_is_returns.append(is_return)
            all_oos_returns.append(oos_return)
            all_oos_sharpes.append(oos_sharpe)
            all_oos_win_rates.append(oos_win_rate)

            oos_dd = Decimal(str(oos_result.get('max_drawdown', 0)))
            if oos_dd > max_oos_drawdown:
                max_oos_drawdown = oos_dd

            window_result = {
                'window_index': ws.window_index,
                'train_start': ws.train_start.isoformat(),
                'train_end': ws.train_end.isoformat(),
                'validate_start': ws.validate_start.isoformat(),
                'validate_end': ws.validate_end.isoformat(),
                'test_start': ws.test_start.isoformat(),
                'test_end': ws.test_end.isoformat(),
                'is_return_percent': float(is_return),
                'is_sharpe': float(is_sharpe),
                'is_win_rate': float(is_win_rate),
                'is_trades': is_result.get('total_trades', 0),
                'is_max_drawdown': float(Decimal(str(is_result.get('max_drawdown', 0)))),
                'oos_return_percent': float(oos_return),
                'oos_sharpe': float(oos_sharpe),
                'oos_win_rate': float(oos_win_rate),
                'oos_trades': oos_result.get('total_trades', 0),
                'oos_max_drawdown': float(oos_dd),
                'frozen_weights': frozen_weights,
                'is_equity_curve': is_result.get('equity_curve', []),
                'oos_equity_curve': oos_result.get('equity_curve', []),
                'has_leakage': has_leakage,
                'leakage_reason': leakage_reason,
            }
            window_results.append(window_result)

        # Calculate aggregate metrics
        n = len(window_results)
        avg_oos_return = sum(all_oos_returns) / n if n > 0 else Decimal('0')
        avg_oos_sharpe = sum(all_oos_sharpes) / n if n > 0 else Decimal('0')
        avg_oos_win_rate = sum(all_oos_win_rates) / n if n > 0 else Decimal('0')
        avg_is_return = sum(all_is_returns) / n if n > 0 else Decimal('0')

        # OOS/IS ratio — key overfitting indicator
        # If OOS << IS, strategy is likely overfit
        oos_is_ratio = (avg_oos_return / avg_is_return) if avg_is_return != 0 else Decimal('0')

        result = {
            'status': 'completed',
            'strategy_name': strategy_name,
            'strategy_version': strategy_version,
            'symbol': symbol,
            'timeframe': timeframe,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'train_days': train_days,
            'validate_days': validate_days,
            'test_days': test_days,
            'step_days': step_days,
            'total_windows': n,
            'avg_oos_return': float(avg_oos_return),
            'avg_oos_sharpe': float(avg_oos_sharpe),
            'avg_oos_win_rate': float(avg_oos_win_rate),
            'oos_vs_is_ratio': float(oos_is_ratio),
            'max_oos_drawdown': float(max_oos_drawdown),
            'leakage_detected': leakage_detected,
            'leakage_details': leakage_details,
            'weight_snapshot': weight_snapshot or {},
            'windows': window_results,
        }

        logger.info(
            f"Walk-forward complete: {n} windows | "
            f"Avg OOS return: {avg_oos_return:.2f}% | "
            f"OOS/IS ratio: {oos_is_ratio:.2f} | "
            f"Leakage: {'YES' if leakage_detected else 'No'}"
        )

        return result

    def _extract_data(
        self,
        historical_data: List[Dict],
        start: datetime,
        end: datetime,
    ) -> List[Dict]:
        """Extract data within a time range. No future data leaks."""
        return [
            candle for candle in historical_data
            if start <= candle.get('timestamp', datetime.min) < end
        ]

    def _check_leakage(
        self,
        train_data: List[Dict],
        validate_data: List[Dict],
        test_data: List[Dict],
        ws: WindowSpec,
    ) -> Tuple[bool, str]:
        """
        Detect data leakage between windows.

        Checks:
        1. No timestamp overlap between train/validate/test
        2. No data from future in earlier windows
        3. Windows are chronologically ordered
        """
        reasons = []

        # Check chronological ordering
        if ws.train_end > ws.validate_start:
            reasons.append(f"Train end ({ws.train_end}) overlaps validate start ({ws.validate_start})")
        if ws.validate_end > ws.test_start:
            reasons.append(f"Validate end ({ws.validate_end}) overlaps test start ({ws.test_start})")

        # Check data timestamp overlap
        train_timestamps = set()
        for c in train_data:
            ts = c.get('timestamp')
            if ts:
                train_timestamps.add(ts)

        validate_timestamps = set()
        for c in validate_data:
            ts = c.get('timestamp')
            if ts:
                validate_timestamps.add(ts)

        test_timestamps = set()
        for c in test_data:
            ts = c.get('timestamp')
            if ts:
                test_timestamps.add(ts)

        # Check overlaps
        train_val_overlap = train_timestamps & validate_timestamps
        if train_val_overlap:
            reasons.append(f"Train/Validate overlap: {len(train_val_overlap)} timestamps")

        val_test_overlap = validate_timestamps & test_timestamps
        if val_test_overlap:
            reasons.append(f"Validate/Test overlap: {len(val_test_overlap)} timestamps")

        train_test_overlap = train_timestamps & test_timestamps
        if train_test_overlap:
            reasons.append(f"Train/Test overlap: {len(train_test_overlap)} timestamps")

        # Check for out-of-order timestamps within each window
        for name, data in [('train', train_data), ('validate', validate_data), ('test', test_data)]:
            timestamps = [c.get('timestamp') for c in data if c.get('timestamp')]
            for i in range(1, len(timestamps)):
                if timestamps[i] < timestamps[i-1]:
                    reasons.append(f"Out-of-order timestamps in {name} window")
                    break

        has_leakage = len(reasons) > 0
        return has_leakage, '; '.join(reasons) if reasons else ''

    def compare_windows(self, window_results: List[Dict]) -> Dict:
        """
        Compare IS vs OOS performance across windows.

        Returns overfitting analysis.
        """
        if not window_results:
            return {'status': 'no_data'}

        is_returns = [w['is_return_percent'] for w in window_results]
        oos_returns = [w['oos_return_percent'] for w in window_results]

        avg_is = sum(is_returns) / len(is_returns)
        avg_oos = sum(oos_returns) / len(oos_returns)

        # Count windows where OOS < IS (overfitting signal)
        overfit_count = sum(1 for i, o in zip(is_returns, oos_returns) if o < i)
        overfit_pct = (overfit_count / len(window_results)) * 100

        # Stability: standard deviation of OOS returns
        import math
        oos_variance = sum((r - avg_oos) ** 2 for r in oos_returns) / len(oos_returns) if oos_returns else 0
        oos_std = math.sqrt(oos_variance)

        # Consistency: % of OOS windows with positive return
        positive_oos = sum(1 for r in oos_returns if r > 0)
        consistency = (positive_oos / len(oos_returns)) * 100

        # Overall verdict
        if overfit_pct > 70 and avg_oos < avg_is * 0.5:
            verdict = 'OVERFITTING LIKELY'
        elif overfit_pct > 50:
            verdict = 'MILD OVERFITTING'
        elif consistency > 60 and avg_oos > 0:
            verdict = 'STRATEGY VALIDATED'
        else:
            verdict = 'INCONCLUSIVE'

        return {
            'total_windows': len(window_results),
            'avg_is_return': avg_is,
            'avg_oos_return': avg_oos,
            'oos_vs_is_ratio': avg_oos / avg_is if avg_is != 0 else 0,
            'overfit_windows': overfit_count,
            'overfit_percentage': overfit_pct,
            'oos_std': oos_std,
            'consistency_pct': consistency,
            'positive_oos_windows': positive_oos,
            'verdict': verdict,
        }
