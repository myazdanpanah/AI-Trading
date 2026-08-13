"""Weight Adjuster - Automatically adjusts signal generator weights based on performance."""
import logging
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WeightAdjuster:
    """
    Analyzes signal performance by factor and adjusts weights accordingly.
    
    Logic:
    - If a factor has high win rate → increase its weight
    - If a factor has low win rate → decrease its weight
    - Weights are normalized to sum to 1.0
    - Adjustments are gradual (max ±5% per cycle) to avoid wild swings
    """

    # Minimum and maximum weight bounds
    MIN_WEIGHT = Decimal('0.05')  # 5% minimum
    MAX_WEIGHT = Decimal('0.50')  # 50% maximum
    MAX_ADJUSTMENT = Decimal('0.05')  # Max 5% change per cycle
    MIN_SIGNALS_FOR_ADJUSTMENT = 5  # Need at least 5 signals to adjust

    FACTOR_NAMES = ['technical', 'sentiment', 'news', 'ai', 'macro']

    @classmethod
    def adjust_weights(cls, lookback_days: int = 30) -> Dict:
        """
        Analyze factor performance and adjust weights.
        
        Returns:
            Dict with adjustment results
        """
        from apps.signals.models import FactorWeight
        from apps.feedback.models import SignalMemory
        
        try:
            # Get current weights
            current_weights = {}
            for fw in FactorWeight.objects.filter(is_active=True):
                current_weights[fw.name] = fw.weight
            
            # If no weights in DB, use defaults
            if not current_weights:
                current_weights = {
                    'technical': Decimal('0.30'),
                    'sentiment': Decimal('0.20'),
                    'news': Decimal('0.15'),
                    'ai': Decimal('0.20'),
                    'macro': Decimal('0.15'),
                }
            
            # Get signal memories for analysis
            cutoff = datetime.now() - timedelta(days=lookback_days)
            memories = SignalMemory.objects.filter(
                evaluated_at__gte=cutoff,
                evaluated_at__isnull=False,
            )
            
            total_signals = memories.count()
            if total_signals < cls.MIN_SIGNALS_FOR_ADJUSTMENT:
                return {
                    'status': 'insufficient_data',
                    'total_signals': total_signals,
                    'min_required': cls.MIN_SIGNALS_FOR_ADJUSTMENT,
                    'weights_changed': False,
                }
            
            # Analyze each factor's performance
            factor_performance = {}
            for factor in cls.FACTOR_NAMES:
                factor_signals = memories.filter(factors_at_creation__has_key=factor)
                if factor_signals.count() == 0:
                    factor_performance[factor] = {
                        'win_rate': 50,  # Default neutral
                        'avg_return': 0,
                        'total_signals': 0,
                        'confidence': 0,
                    }
                    continue
                
                total = factor_signals.count()
                correct = factor_signals.filter(was_correct=True).count()
                win_rate = (correct / total) * 100
                
                returns = list(factor_signals.values_list('actual_return_percent', flat=True))
                avg_return = sum(float(r) for r in returns) / len(returns) if returns else 0
                
                # Confidence is based on sample size
                confidence = min(1.0, total / 20)  # Full confidence at 20+ signals
                
                factor_performance[factor] = {
                    'win_rate': win_rate,
                    'avg_return': avg_return,
                    'total_signals': total,
                    'confidence': confidence,
                }
            
            # Calculate adjustments
            adjustments = {}
            new_weights = {}
            
            for factor in cls.FACTOR_NAMES:
                current = current_weights.get(factor, Decimal('0.20'))
                perf = factor_performance[factor]
                
                # Calculate desired weight based on performance
                # Higher win rate → higher weight
                win_rate_factor = Decimal(str(perf['win_rate'])) / Decimal('100')
                confidence_decimal = Decimal(str(perf['confidence']))
                
                # Boost factors with high win rate, reduce those with low
                if perf['win_rate'] > 60:
                    # Good performer - increase weight
                    adjustment = cls.MAX_ADJUSTMENT * win_rate_factor * confidence_decimal
                elif perf['win_rate'] < 40:
                    # Poor performer - decrease weight
                    adjustment = -cls.MAX_ADJUSTMENT * (Decimal('1') - win_rate_factor) * confidence_decimal
                else:
                    # Neutral - small adjustment based on avg return
                    adjustment = Decimal(str(perf['avg_return'])) / Decimal('1000')  # Very small
                
                # Apply adjustment with bounds
                new_weight = current + adjustment
                new_weight = max(cls.MIN_WEIGHT, min(cls.MAX_WEIGHT, new_weight))
                
                adjustments[factor] = {
                    'old': float(current),
                    'new': float(new_weight),
                    'change': float(new_weight - current),
                    'win_rate': perf['win_rate'],
                    'signals': perf['total_signals'],
                }
                
                new_weights[factor] = new_weight
            
            # Normalize weights to sum to 1.0
            total_weight = sum(new_weights.values())
            if total_weight > 0:
                new_weights = {k: v / total_weight for k, v in new_weights.items()}
            
            # Save to database
            from apps.signals.models import WeightHistory
            weights_changed = False
            for factor, new_weight in new_weights.items():
                fw, created = FactorWeight.objects.get_or_create(
                    name=factor,
                    defaults={
                        'weight': new_weight,
                        'description': f'Auto-adjusted based on {factor_performance[factor]["total_signals"]} signals',
                        'is_active': True,
                    }
                )
                if not created:
                    old_weight = fw.weight
                    fw.weight = new_weight
                    fw.description = f'Auto-adjusted: {old_weight} -> {new_weight} ({factor_performance[factor]["win_rate"]:.1f}% win rate, {factor_performance[factor]["total_signals"]} signals)'
                    fw.save(update_fields=['weight', 'description', 'updated_at'])
                    weights_changed = True

                    # Save weight history
                    if old_weight != new_weight:
                        WeightHistory.objects.create(
                            factor_name=factor,
                            old_weight=old_weight,
                            new_weight=new_weight,
                            reason=f'Auto-adjustment: win_rate={factor_performance[factor]["win_rate"]:.1f}%, signals={factor_performance[factor]["total_signals"]}',
                            win_rate_before=factor_performance[factor]['win_rate'],
                            signals_evaluated=factor_performance[factor]['total_signals'],
                            adjustment_type='scheduled',
                        )
            
            # Generate summary
            summary = cls._generate_adjustment_summary(adjustments, factor_performance, total_signals)
            
            logger.info(f"Weight adjustment complete: {total_signals} signals analyzed, weights {'changed' if weights_changed else 'unchanged'}")
            
            return {
                'status': 'complete',
                'total_signals': total_signals,
                'factor_performance': {k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in factor_performance.items()},
                'adjustments': adjustments,
                'new_weights': {k: round(float(v), 4) for k, v in new_weights.items()},
                'weights_changed': weights_changed,
                'summary': summary,
            }
            
        except Exception as e:
            logger.error(f"Weight adjustment failed: {e}")
            return {'status': 'error', 'error': str(e)}

    @classmethod
    def _generate_adjustment_summary(cls, adjustments: Dict, performance: Dict, total_signals: int) -> str:
        """Generate human-readable summary of weight adjustments."""
        parts = [f"Analyzed {total_signals} signals."]
        
        # Find best and worst factors
        best_factor = max(performance.items(), key=lambda x: x[1]['win_rate'])
        worst_factor = min(performance.items(), key=lambda x: x[1]['win_rate'])
        
        parts.append(f"Best performer: {best_factor[0]} ({best_factor[1]['win_rate']:.1f}% win rate)")
        parts.append(f"Worst performer: {worst_factor[0]} ({worst_factor[1]['win_rate']:.1f}% win rate)")
        
        # List changes
        changes = []
        for factor, adj in adjustments.items():
            if abs(adj['change']) > 0.001:
                direction = 'increased' if adj['change'] > 0 else 'decreased'
                changes.append(f"{factor} {direction} to {adj['new']:.3f}")
        
        if changes:
            parts.append("Adjustments: " + ", ".join(changes))
        else:
            parts.append("No significant adjustments needed.")
        
        return " ".join(parts)

    @classmethod
    def get_current_weights(cls) -> Dict:
        """Get current factor weights."""
        from apps.signals.models import FactorWeight
        
        weights = {}
        for fw in FactorWeight.objects.filter(is_active=True):
            weights[fw.name] = {
                'weight': float(fw.weight),
                'description': fw.description,
                'updated_at': fw.updated_at.isoformat() if fw.updated_at else None,
            }
        
        return weights

    @classmethod
    def reset_weights(cls) -> Dict:
        """Reset weights to defaults."""
        from apps.signals.models import FactorWeight
        
        defaults = {
            'technical': Decimal('0.30'),
            'sentiment': Decimal('0.20'),
            'news': Decimal('0.15'),
            'ai': Decimal('0.20'),
            'macro': Decimal('0.15'),
        }
        
        for name, weight in defaults.items():
            fw, created = FactorWeight.objects.get_or_create(
                name=name,
                defaults={'weight': weight, 'is_active': True, 'description': 'Default weight'}
            )
            if not created:
                fw.weight = weight
                fw.description = 'Reset to default'
                fw.save(update_fields=['weight', 'description', 'updated_at'])
        
        return {'status': 'reset', 'weights': {k: float(v) for k, v in defaults.items()}}
