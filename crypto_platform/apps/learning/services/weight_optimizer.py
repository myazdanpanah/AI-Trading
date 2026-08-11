"""Weight Optimizer - Adaptive weight optimization based on signal performance."""
import logging
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Q

logger = logging.getLogger(__name__)


class WeightOptimizer:
    """
    Optimizes signal component weights based on historical performance.
    Uses adaptive algorithms to improve signal accuracy over time.
    """
    
    MIN_WEIGHT = Decimal('0.05')
    MAX_WEIGHT = Decimal('0.50')
    LEARNING_RATE = Decimal('0.1')
    DECAY_FACTOR = Decimal('0.95')
    
    def __init__(self):
        self.components = ['technical', 'sentiment', 'news', 'ai', 'macro']
    
    def optimize_weights(
        self,
        performance_window_days: int = 30,
        min_signals: int = 10,
    ) -> Dict:
        """
        Optimize weights based on recent signal performance.
        
        Returns:
            Dict with optimized weights and metadata
        """
        from ..models import StrategyWeight, SignalResult
        from signals.models import Signal
        
        # Get current weights
        current_weights = {}
        for sw in StrategyWeight.objects.all():
            current_weights[sw.component] = {
                'weight': sw.weight,
                'performance_score': sw.performance_score,
            }
        
        # Calculate performance for each component
        start_date = datetime.now() - timedelta(days=performance_window_days)
        performance_scores = self._calculate_component_performance(
            start_date, min_signals
        )
        
        # Optimize weights using gradient-like approach
        optimized_weights = {}
        weight_changes = {}
        
        for component in self.components:
            current = current_weights.get(component, {'weight': Decimal('10'), 'performance_score': Decimal('50')})
            current_weight = current['weight']
            performance = performance_scores.get(component, Decimal('50'))
            
            # Calculate weight adjustment based on performance
            performance_delta = performance - Decimal('50')  # Baseline is 50
            adjustment = performance_delta * self.LEARNING_RATE
            
            # Apply adjustment
            new_weight = current_weight + adjustment
            
            # Apply constraints
            new_weight = max(self.MIN_WEIGHT * 100, min(self.MAX_WEIGHT * 100, new_weight))
            
            optimized_weights[component] = float(new_weight)
            weight_changes[component] = float(adjustment)
            
            # Update database
            StrategyWeight.objects.update_or_create(
                component=component,
                defaults={
                    'weight': new_weight,
                    'performance_score': performance,
                }
            )
        
        logger.info(f"Optimized weights: {optimized_weights}")
        
        return {
            'optimized_weights': optimized_weights,
            'weight_changes': weight_changes,
            'performance_scores': {k: float(v) for k, v in performance_scores.items()},
            'window_days': performance_window_days,
            'optimized_at': datetime.now().isoformat(),
        }
    
    def _calculate_component_performance(
        self,
        start_date: datetime,
        min_signals: int,
    ) -> Dict[str, Decimal]:
        """
        Calculate performance score for each component based on signal outcomes.
        
        Returns:
            Dict mapping component names to performance scores (0-100)
        """
        from ..models import SignalResult
        
        performance = {}
        
        # Get all results in the window
        all_results = list(SignalResult.objects.filter(
            evaluated_at__gte=start_date
        ).select_related('signal'))
        
        total = len(all_results)
        if total < min_signals:
            # Default neutral scores for all components
            for component in self.components:
                performance[component] = Decimal('50')
            return performance
        
        # Calculate overall win rate as baseline
        wins = sum(1 for r in all_results if r.success)
        overall_win_rate = Decimal(str(wins / total * 100)) if total > 0 else Decimal('50')
        
        # Distribute performance based on component weight contribution
        # Each component gets a score based on how well signals performed
        # when that component's score was high vs low
        for component in self.components:
            # Use overall performance as base, with slight variation per component
            # In production, this would correlate component scores with outcomes
            performance[component] = overall_win_rate
        
        return performance
    
    def get_current_weights(self) -> Dict:
        """Get current optimized weights."""
        from ..models import StrategyWeight
        
        weights = {}
        for sw in StrategyWeight.objects.all():
            weights[sw.component] = {
                'weight': float(sw.weight),
                'performance_score': float(sw.performance_score),
                'last_updated': sw.last_updated.isoformat(),
            }
        
        return weights
    
    def get_weight_history(
        self,
        component: str = None,
        days: int = 30,
    ) -> List[Dict]:
        """
        Get weight change history for analysis.
        
        Returns:
            List of weight snapshots
        """
        # For now, return current state
        # In production, this would query a weight_history table
        current = self.get_current_weights()
        
        if component:
            return [{component: current.get(component, {})}]
        
        return [{'weights': current, 'timestamp': datetime.now().isoformat()}]
    
    def calculate_weight_effectiveness(
        self,
        component: str,
        start_date: datetime = None,
    ) -> Dict:
        """
        Calculate how effective a component's weight has been.
        
        Returns:
            Dict with effectiveness metrics
        """
        from ..models import StrategyWeight, SignalResult
        
        weight = StrategyWeight.objects.filter(component=component).first()
        if not weight:
            return {'component': component, 'effectiveness': 0}
        
        start_date = start_date or datetime.now() - timedelta(days=30)
        
        results = SignalResult.objects.filter(
            evaluated_at__gte=start_date
        )
        
        total = results.count()
        if total == 0:
            return {'component': component, 'effectiveness': 0}
        
        wins = results.filter(success=True).count()
        win_rate = Decimal(str(wins / total * 100))
        
        # Effectiveness is based on win rate relative to weight
        effectiveness = (win_rate / weight.weight * 10) if weight.weight > 0 else Decimal('0')
        
        return {
            'component': component,
            'current_weight': float(weight.weight),
            'performance_score': float(weight.performance_score),
            'actual_win_rate': float(win_rate),
            'effectiveness': float(min(100, effectiveness)),
            'period_days': (datetime.now() - start_date).days,
        }
