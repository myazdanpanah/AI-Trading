"""Learning Loop - Adjusts model weights based on forecast accuracy feedback."""
import time
import logging
from typing import Dict, List
from django.utils import timezone
from django.db import transaction
from django.db import models
from django.db.models import Avg, Count

from ..models import PriceForecast, ModelWeight, ForecastCycle

logger = logging.getLogger(__name__)


class LearningLoop:
    """
    Adjusts model weights based on forecast accuracy.
    
    Learning Rules:
    1. If a factor was consistently correct → increase its weight
    2. If a factor was consistently wrong → decrease its weight
    3. Weights are normalized to sum to 1.0
    4. Adjustments are small (0.01-0.05) to prevent overfitting
    5. Minimum weight per factor: 0.05 (never fully ignore a factor)
    """
    
    # Learning parameters
    LEARNING_RATE = 0.02  # Small adjustments per cycle
    MIN_WEIGHT = 0.05     # Minimum weight for any factor
    MAX_WEIGHT = 0.60     # Maximum weight for any factor
    MIN_SAMPLES = 5       # Minimum verified forecasts to adjust
    
    @classmethod
    def run_learning_cycle(cls) -> Dict:
        """
        Run a complete learning cycle after forecast verification.
        Analyzes recent accuracy and adjusts model weights.
        """
        start = time.time()
        
        try:
            adjustments = []
            
            # Get all symbols with model weights
            weights = ModelWeight.objects.all()
            
            for weight in weights:
                adj = cls._adjust_weights_for_symbol(weight)
                if adj:
                    adjustments.extend(adj)
            
            # Create a cycle record
            cycle = ForecastCycle.objects.create(
                cycle_time=timezone.now(),
                status='COMPLETED',
                adjustments_made=adjustments,
                execution_time_ms=int((time.time() - start) * 1000),
            )
            
            return {
                'status': 'success',
                'adjustments_made': len(adjustments),
                'adjustments': adjustments,
                'execution_time_ms': cycle.execution_time_ms,
            }
            
        except Exception as e:
            logger.error(f"Learning cycle failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    @classmethod
    def _adjust_weights_for_symbol(cls, model_weight: ModelWeight) -> List[Dict]:
        """Adjust weights for a single symbol based on recent accuracy."""
        adjustments = []
        
        # Get recent verified forecasts for this symbol
        recent_forecasts = PriceForecast.objects.filter(
            symbol=model_weight.symbol,
            status='VERIFIED',
            verified_at__gte=timezone.now() - timezone.timedelta(days=7),
        )
        
        if recent_forecasts.count() < cls.MIN_SAMPLES:
            return adjustments  # Not enough data
        
        # Analyze each factor's contribution to correct vs incorrect predictions
        factors = {
            'technical': ('technical_score', 'technical_weight'),
            'sentiment': ('momentum_score', 'sentiment_weight'),  # Using momentum as proxy
            'news': ('volatility_score', 'news_weight'),  # Using volatility as proxy
            'ai': ('regime_score', 'ai_weight'),
            'macro': ('volatility_score', 'macro_weight'),
        }
        
        factor_performance = {}
        
        for factor_name, (score_field, weight_field) in factors.items():
            # Get average score for correct vs incorrect predictions
            correct_avg = recent_forecasts.filter(
                direction_correct=True
            ).aggregate(avg=Avg(score_field))['avg'] or 50
            
            incorrect_avg = recent_forecasts.filter(
                direction_correct=False
            ).aggregate(avg=Avg(score_field))['avg'] or 50
            
            # Calculate discrimination power
            # How well does this factor distinguish correct from incorrect?
            discrimination = abs(correct_avg - incorrect_avg)
            
            # Calculate adjustment
            current_weight = getattr(model_weight, weight_field)
            
            if discrimination > 10:
                # Factor is discriminative - boost if it correlates with correctness
                if correct_avg > incorrect_avg:
                    # Higher score = more correct → boost weight
                    adjustment = min(cls.LEARNING_RATE, discrimination / 500)
                else:
                    # Higher score = more wrong → decrease weight
                    adjustment = -min(cls.LEARNING_RATE, discrimination / 500)
            else:
                # Factor is not discriminative - slight regression toward mean
                target_weight = 0.20  # Equal weight target
                adjustment = (target_weight - current_weight) * 0.01
            
            # Apply adjustment with bounds
            new_weight = current_weight + adjustment
            new_weight = max(cls.MIN_WEIGHT, min(cls.MAX_WEIGHT, new_weight))
            
            if abs(new_weight - current_weight) > 0.001:
                setattr(model_weight, weight_field, new_weight)
                adjustments.append({
                    'symbol': model_weight.symbol,
                    'factor': factor_name,
                    'old_weight': round(current_weight, 4),
                    'new_weight': round(new_weight, 4),
                    'discrimination': round(discrimination, 2),
                    'correct_avg': round(correct_avg, 2),
                    'incorrect_avg': round(incorrect_avg, 2),
                })
        
        # Normalize weights to sum to 1.0
        total = (
            model_weight.technical_weight +
            model_weight.sentiment_weight +
            model_weight.news_weight +
            model_weight.ai_weight +
            model_weight.macro_weight
        )
        
        if total > 0:
            model_weight.technical_weight /= total
            model_weight.sentiment_weight /= total
            model_weight.news_weight /= total
            model_weight.ai_weight /= total
            model_weight.macro_weight /= total
        
        # Update tracking
        model_weight.adjustment_count += 1
        model_weight.last_adjustment = timezone.now()
        
        # Update accuracy stats
        stats = recent_forecasts.aggregate(
            total=Count('id'),
            correct=Count('id', filter=models.Q(direction_correct=True)),
        )
        model_weight.total_predictions = stats['total']
        model_weight.correct_predictions = stats['correct']
        model_weight.accuracy_rate = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        model_weight.save()
        
        return adjustments
    
    @classmethod
    def get_learning_stats(cls, symbol: str = None) -> Dict:
        """Get learning statistics and weight history."""
        query = ModelWeight.objects.all()
        if symbol:
            query = query.filter(symbol=symbol)
        
        weights = query.first()
        if not weights:
            return {'error': 'No weights found'}
        
        # Get recent adjustments
        recent_cycles = ForecastCycle.objects.filter(
            adjustments_made__isnull=False
        ).order_by('-cycle_time')[:10]
        
        adjustment_history = []
        for cycle in recent_cycles:
            if cycle.adjustments_made:
                for adj in cycle.adjustments_made:
                    if symbol is None or adj.get('symbol') == symbol:
                        adjustment_history.append({
                            'time': cycle.cycle_time.isoformat(),
                            **adj,
                        })
        
        return {
            'symbol': weights.symbol,
            'current_weights': weights.get_weights_dict(),
            'accuracy_rate': weights.accuracy_rate,
            'total_predictions': weights.total_predictions,
            'adjustment_count': weights.adjustment_count,
            'last_adjustment': weights.last_adjustment.isoformat() if weights.last_adjustment else None,
            'recent_adjustments': adjustment_history[:20],
        }
    
    @classmethod
    def reset_weights(cls, symbol: str = None):
        """Reset model weights to defaults."""
        defaults = {
            'technical_weight': 0.35,
            'sentiment_weight': 0.15,
            'news_weight': 0.10,
            'ai_weight': 0.25,
            'macro_weight': 0.15,
        }
        
        query = ModelWeight.objects.all()
        if symbol:
            query = query.filter(symbol=symbol)
        
        for weight in query:
            for field, value in defaults.items():
                setattr(weight, field, value)
            weight.total_predictions = 0
            weight.correct_predictions = 0
            weight.accuracy_rate = 0
            weight.adjustment_count = 0
            weight.save()
