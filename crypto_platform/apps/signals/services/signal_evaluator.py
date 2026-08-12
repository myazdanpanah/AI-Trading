"""Signal Evaluator - Automatically evaluates signal outcomes for the feedback loop."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SignalEvaluator:
    """
    Evaluates trading signals by checking what happened to the price
    after the signal was created. Records outcomes for the AI feedback loop.
    """

    @staticmethod
    def evaluate_signal(signal) -> Optional[Dict]:
        """
        Evaluate a single signal by fetching current price and comparing.

        Returns:
            Dict with evaluation results or None if not ready to evaluate
        """
        from apps.market.services.unified_data import fetch_market_data

        try:
            # Get current price
            market = fetch_market_data(signal.symbol)
            current_price = market['current_price']

            if not current_price or current_price <= 0:
                return None

            entry_price = float(signal.entry_price) if signal.entry_price else 0
            if entry_price <= 0:
                return None

            # Calculate return
            if signal.direction in ('buy', 'strong_buy'):
                return_pct = ((current_price - entry_price) / entry_price) * 100
            elif signal.direction in ('sell', 'strong_sell'):
                return_pct = ((entry_price - current_price) / entry_price) * 100
            else:
                # HOLD - check if price moved significantly
                return_pct = ((current_price - entry_price) / entry_price) * 100

            # Determine if signal was correct
            was_correct = return_pct > 0

            # Calculate max favorable and adverse excursion
            stop_loss = float(signal.stop_loss) if signal.stop_loss else entry_price * 0.97
            take_profit = signal.take_profit[0] if signal.take_profit and isinstance(signal.take_profit, list) and len(signal.take_profit) > 0 else entry_price * 1.03

            max_favorable = max(0, return_pct) if was_correct else 0
            max_adverse = abs(min(0, return_pct)) if not was_correct else 0

            # Check if stop loss was hit
            stopped_out = False
            if signal.direction in ('buy', 'strong_buy') and current_price <= stop_loss:
                stopped_out = True
            elif signal.direction in ('sell', 'strong_sell') and current_price >= stop_loss:
                stopped_out = True

            # Check if take profit was hit
            tp_hit = False
            if signal.direction in ('buy', 'strong_buy') and current_price >= take_profit:
                tp_hit = True
            elif signal.direction in ('sell', 'strong_sell') and current_price <= take_profit:
                tp_hit = True

            # Calculate holding period
            from django.utils import timezone
            created = signal.created_at
            now = timezone.now()
            # Make both offset-aware or both offset-naive
            if hasattr(created, 'tzinfo') and created.tzinfo is not None and hasattr(now, 'tzinfo') and now.tzinfo is None:
                now = now.replace(tzinfo=created.tzinfo)
            elif hasattr(created, 'tzinfo') and created.tzinfo is None and hasattr(now, 'tzinfo') and now.tzinfo is not None:
                created = created.replace(tzinfo=now.tzinfo)
            holding_hours = (now - created).total_seconds() / 3600

            return {
                'signal_id': str(signal.id),
                'symbol': signal.symbol,
                'direction': signal.direction,
                'entry_price': entry_price,
                'current_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'return_percent': round(return_pct, 4),
                'was_correct': was_correct,
                'stopped_out': stopped_out,
                'tp_hit': tp_hit,
                'max_favorable': round(max_favorable, 4),
                'max_adverse': round(max_adverse, 4),
                'holding_hours': round(holding_hours, 1),
                'confidence': signal.confidence,
                'composite_score': float(signal.composite_score),
                'factor_scores': {
                    'technical': float(signal.technical_score),
                    'sentiment': float(signal.sentiment_score),
                    'news': float(signal.news_score),
                    'ai': float(signal.ai_score),
                    'macro': float(signal.macro_score),
                },
            }

        except Exception as e:
            logger.error(f"Failed to evaluate signal {signal.id}: {e}")
            return None

    @staticmethod
    def record_outcome(signal, evaluation: Dict) -> bool:
        """Record the evaluation outcome in SignalMemory for the feedback loop."""
        try:
            from django.utils import timezone
            from apps.feedback.models import SignalMemory, MarketMemory

            # Create or get market memory
            market_memory = None
            try:
                market_memory = MarketMemory.objects.filter(
                    symbol=signal.symbol,
                    timeframe=signal.timeframe,
                ).order_by('-created_at').first()
            except Exception:
                pass

            # Create signal memory
            signal_memory = SignalMemory.objects.create(
                signal=signal,
                market_memory=market_memory,
                signal_direction=signal.direction,
                signal_confidence=signal.confidence,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                exit_price=evaluation['current_price'],
                actual_return=evaluation['return_percent'],
                actual_return_percent=evaluation['return_percent'],
                was_correct=evaluation['was_correct'],
                max_favorable=evaluation['max_favorable'],
                max_adverse=evaluation['max_adverse'],
                holding_period_hours=int(evaluation['holding_hours']),
                factors_at_creation=evaluation['factor_scores'],
                lesson_learned=SignalEvaluator._generate_lesson(evaluation),
                evaluated_at=timezone.now(),
            )

            # Create training sample with candle data
            try:
                from apps.feedback.services.candle_collector import candle_collector
                training_result = candle_collector.create_training_sample(signal_memory)
                logger.info(f"Created training sample for signal {signal.id}: {training_result}")
            except Exception as e:
                logger.warning(f"Failed to create training sample: {e}")

            logger.info(f"Recorded outcome for signal {signal.id}: {'WIN' if evaluation['was_correct'] else 'LOSS'} ({evaluation['return_percent']:.2f}%)")
            return True

        except Exception as e:
            logger.error(f"Failed to record outcome for signal {signal.id}: {e}")
            return False

    @staticmethod
    def _generate_lesson(evaluation: Dict) -> str:
        """Generate a lesson learned from the signal outcome."""
        direction = evaluation['direction']
        return_pct = evaluation['return_percent']
        was_correct = evaluation['was_correct']
        scores = evaluation['factor_scores']

        if was_correct:
            # Find which factors were most accurate
            best_factor = max(scores.items(), key=lambda x: x[1])
            return f"WINNING {direction} signal. {best_factor[0]} was strongest indicator ({best_factor[1]:.0f}). Returned {return_pct:.2f}%."

        else:
            # Find which factors were misleading
            worst_factor = max(scores.items(), key=lambda x: x[1] if direction in ('buy', 'strong_buy') else 100 - x[1])
            return f"LOSING {direction} signal. {worst_factor[0]} was misleading ({worst_factor[1]:.0f}). Lost {abs(return_pct):.2f}%."

    @staticmethod
    def evaluate_pending_signals(min_age_hours: int = 4) -> Dict:
        """
        Evaluate all signals that are old enough to have meaningful outcomes.

        Args:
            min_age_hours: Minimum age before evaluating (default 4 hours)

        Returns:
            Dict with evaluation summary
        """
        from apps.signals.models import Signal
        from django.utils import timezone

        cutoff = timezone.now() - timedelta(hours=min_age_hours)

        # Get unevaluated signals
        evaluated_ids = set()
        try:
            from apps.feedback.models import SignalMemory
            evaluated_ids = set(SignalMemory.objects.values_list('signal_id', flat=True))
        except Exception:
            pass

        signals = Signal.objects.filter(
            created_at__lt=cutoff,
            is_active=True,
        ).exclude(id__in=evaluated_ids)

        results = {
            'evaluated': 0,
            'wins': 0,
            'losses': 0,
            'total_return': 0,
            'details': [],
        }

        for signal in signals:
            evaluation = SignalEvaluator.evaluate_signal(signal)
            if evaluation:
                success = SignalEvaluator.record_outcome(signal, evaluation)
                if success:
                    results['evaluated'] += 1
                    if evaluation['was_correct']:
                        results['wins'] += 1
                    else:
                        results['losses'] += 1
                    results['total_return'] += evaluation['return_percent']
                    results['details'].append({
                        'symbol': signal.symbol,
                        'direction': signal.direction,
                        'return': evaluation['return_percent'],
                        'correct': evaluation['was_correct'],
                    })

        results['win_rate'] = (results['wins'] / results['evaluated'] * 100) if results['evaluated'] > 0 else 0
        results['avg_return'] = (results['total_return'] / results['evaluated']) if results['evaluated'] > 0 else 0

        logger.info(f"Evaluated {results['evaluated']} signals: {results['wins']} wins, {results['losses']} losses ({results['win_rate']:.1f}%)")
        return results

    @staticmethod
    def get_performance_metrics(days: int = 30, symbol: str = None) -> Dict:
        """Get comprehensive performance metrics for the feedback loop."""
        try:
            from apps.feedback.models import SignalMemory
            from django.utils import timezone

            cutoff = timezone.now() - timedelta(days=days)
            memories = SignalMemory.objects.filter(evaluated_at__gte=cutoff)

            if symbol:
                memories = memories.filter(signal__symbol=symbol)

            total = memories.count()
            if total == 0:
                return {
                    'status': 'no_data',
                    'total_signals': 0,
                    'win_rate': 0,
                    'avg_return': 0,
                    'profit_factor': 0,
                    'sharpe_ratio': 0,
                }

            correct = memories.filter(was_correct=True).count()
            returns = list(memories.values_list('actual_return_percent', flat=True))
            wins = [r for r in returns if r > 0]
            losses = [abs(r) for r in returns if r < 0]

            avg_return = sum(returns) / len(returns) if returns else 0
            win_rate = (correct / total) * 100

            avg_win = sum(wins) / len(wins) if wins else 0
            avg_loss = sum(losses) / len(losses) if losses else 1
            profit_factor = avg_win / avg_loss if avg_loss > 0 else avg_win

            # Sharpe ratio (simplified)
            import statistics
            sharpe = (statistics.stdev(returns) > 0 and avg_return / statistics.stdev(returns)) or 0

            # Factor analysis
            factor_analysis = {}
            for factor in ['technical', 'sentiment', 'news', 'ai', 'macro']:
                factor_signals = memories.filter(factors_at_creation__has_key=factor)
                if factor_signals.exists():
                    factor_returns = list(factor_signals.values_list('actual_return_percent', flat=True))
                    factor_wins = sum(1 for r in factor_returns if r > 0)
                    factor_analysis[factor] = {
                        'total_signals': factor_signals.count(),
                        'win_rate': (factor_wins / factor_signals.count()) * 100 if factor_signals.count() > 0 else 0,
                        'avg_return': sum(factor_returns) / len(factor_returns) if factor_returns else 0,
                    }

            return {
                'status': 'complete',
                'total_signals': total,
                'wins': correct,
                'losses': total - correct,
                'win_rate': round(win_rate, 1),
                'avg_return': round(avg_return, 2),
                'profit_factor': round(profit_factor, 2),
                'sharpe_ratio': round(sharpe, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'factor_analysis': factor_analysis,
                'days': days,
            }

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {'status': 'error', 'error': str(e)}
