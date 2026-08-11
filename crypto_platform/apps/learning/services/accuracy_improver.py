"""Accuracy Improver - Signal accuracy analysis and improvement recommendations."""
import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Q, StdDev
from collections import defaultdict

logger = logging.getLogger(__name__)


class AccuracyImprover:
    """
    Analyzes signal accuracy patterns and provides recommendations
    for improving signal quality over time.
    """
    
    # Minimum data thresholds for analysis
    MIN_SIGNALS_FOR_ANALYSIS = 20
    MIN_SIGNALS_FOR_PATTERN = 10
    
    def analyze_accuracy_patterns(
        self,
        lookback_days: int = 90,
    ) -> Dict:
        """
        Analyze signal accuracy patterns across different dimensions.
        
        Returns:
            Dict with pattern analysis and recommendations
        """
        from ..models import SignalResult
        from signals.models import Signal
        
        start_date = datetime.now() - timedelta(days=lookback_days)
        
        results = SignalResult.objects.filter(
            evaluated_at__gte=start_date
        ).select_related('signal')
        
        total = results.count()
        if total < self.MIN_SIGNALS_FOR_ANALYSIS:
            return {
                'status': 'insufficient_data',
                'total_signals': total,
                'required': self.MIN_SIGNALS_FOR_ANALYSIS,
                'message': f'Need at least {self.MIN_SIGNALS_FOR_ANALYSIS} signals for analysis',
            }
        
        # Analyze by different dimensions
        patterns = {
            'by_symbol': self._analyze_by_dimension(results, 'signal__symbol'),
            'by_timeframe': self._analyze_by_dimension(results, 'signal__timeframe'),
            'by_direction': self._analyze_by_dimension(results, 'signal__direction'),
            'by_confidence': self._analyze_by_confidence(results),
            'by_time_of_day': self._analyze_by_time(results),
            'by_market_condition': self._analyze_by_condition(results),
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(patterns, total)
        
        return {
            'status': 'analysis_complete',
            'total_signals': total,
            'lookback_days': lookback_days,
            'patterns': patterns,
            'recommendations': recommendations,
            'analyzed_at': datetime.now().isoformat(),
        }
    
    def get_accuracy_recommendations(
        self,
        min_signals: int = 5,
    ) -> List[Dict]:
        """
        Get specific recommendations for improving signal accuracy.
        
        Returns:
            List of actionable recommendations
        """
        from ..models import SignalResult
        
        recommendations = []
        
        # Analyze overall win rate
        overall = SignalResult.objects.aggregate(
            total=Count('id'),
            wins=Count('id', filter=Q(success=True))
        )
        
        if overall['total'] < min_signals:
            return [{'type': 'insufficient_data', 'message': 'Collect more signal data'}]
        
        win_rate = (overall['wins'] / overall['total'] * 100) if overall['total'] > 0 else 0
        
        # Win rate recommendations
        if win_rate < 45:
            recommendations.append({
                'type': 'low_win_rate',
                'severity': 'high',
                'message': f'Win rate ({win_rate:.1f}%) is below 45%. Consider tightening entry criteria.',
                'action': 'Reduce signal generation threshold or add confirmation filters.',
            })
        elif win_rate < 55:
            recommendations.append({
                'type': 'moderate_win_rate',
                'severity': 'medium',
                'message': f'Win rate ({win_rate:.1f}%) is moderate. Room for improvement.',
                'action': 'Analyze losing trades for common patterns.',
            })
        
        # Analyze confidence correlation
        confidence_analysis = self._analyze_confidence_correlation()
        if confidence_analysis.get('low_confidence_wins_high'):
            recommendations.append({
                'type': 'confidence_mismatch',
                'severity': 'medium',
                'message': 'Low confidence signals are performing better than high confidence ones.',
                'action': 'Review confidence scoring algorithm for potential recalibration.',
            })
        
        # Analyze holding period
        duration_analysis = self._analyze_duration_impact()
        if duration_analysis.get('optimal_duration'):
            recommendations.append({
                'type': 'duration_optimization',
                'severity': 'low',
                'message': f"Optimal holding period is {duration_analysis['optimal_duration']} hours.",
                'action': f'Consider targeting {duration_analysis["optimal_duration"]}-hour exits.',
            })
        
        # Analyze stop loss effectiveness
        stop_analysis = self._analyze_stop_loss_effectiveness()
        if stop_analysis.get('stop_loss_frequency', 0) > 0.3:
            recommendations.append({
                'type': 'stop_loss_too_tight',
                'severity': 'high',
                'message': f"{stop_analysis['stop_loss_frequency']*100:.1f}% of trades hit stop loss.",
                'action': 'Consider widening stop loss or adjusting entry timing.',
            })
        
        return recommendations
    
    def predict_signal_quality(
        self,
        signal_data: Dict,
    ) -> Dict:
        """
        Predict the expected quality of a signal based on historical patterns.
        
        Args:
            signal_data: Dict with symbol, timeframe, direction, confidence, etc.
            
        Returns:
            Dict with quality prediction and confidence
        """
        from ..models import SignalResult
        
        symbol = signal_data.get('symbol')
        timeframe = signal_data.get('timeframe')
        direction = signal_data.get('direction')
        confidence = signal_data.get('confidence', 50)
        
        # Get historical performance for similar signals
        query = Q()
        if symbol:
            query &= Q(signal__symbol=symbol)
        if timeframe:
            query &= Q(signal__timeframe=timeframe)
        if direction:
            query &= Q(signal__direction=direction)
        
        results = SignalResult.objects.filter(query)
        total = results.count()
        
        if total < 5:
            return {
                'predicted_quality': 'unknown',
                'confidence': 0,
                'message': 'Insufficient historical data for prediction',
            }
        
        # Calculate historical win rate for similar signals
        wins = results.filter(success=True).count()
        historical_win_rate = Decimal(str(wins / total * 100))
        
        # Adjust prediction based on confidence
        confidence_factor = Decimal(str(confidence)) / Decimal('100')
        predicted_win_rate = historical_win_rate * (Decimal('0.7') + confidence_factor * Decimal('0.3'))
        
        # Determine quality rating
        if predicted_win_rate >= 65:
            quality = 'high'
        elif predicted_win_rate >= 50:
            quality = 'medium'
        else:
            quality = 'low'
        
        return {
            'predicted_quality': quality,
            'predicted_win_rate': float(predicted_win_rate),
            'historical_win_rate': float(historical_win_rate),
            'confidence': float(min(95, max(10, predicted_win_rate))),
            'sample_size': total,
            'message': f'Based on {total} similar signals',
        }
    
    def _analyze_by_dimension(self, results, field: str) -> Dict:
        """Analyze performance by a specific dimension."""
        breakdown = defaultdict(lambda: {'total': 0, 'wins': 0})
        
        for result in results:
            value = self._get_field_value(result, field)
            breakdown[value]['total'] += 1
            if result.success:
                breakdown[value]['wins'] += 1
        
        analysis = {}
        for value, data in breakdown.items():
            win_rate = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            analysis[str(value)] = {
                'total': data['total'],
                'wins': data['wins'],
                'win_rate': round(win_rate, 1),
            }
        
        return analysis
    
    def _analyze_by_confidence(self, results) -> Dict:
        """Analyze performance by confidence level."""
        ranges = [
            ('low', 0, 40),
            ('medium', 40, 60),
            ('high', 60, 80),
            ('very_high', 80, 100),
        ]
        
        analysis = {}
        for label, low, high in ranges:
            range_results = results.filter(
                signal__confidence__gte=low,
                signal__confidence__lt=high
            )
            total = range_results.count()
            if total > 0:
                wins = range_results.filter(success=True).count()
                analysis[label] = {
                    'total': total,
                    'wins': wins,
                    'win_rate': round(wins / total * 100, 1),
                }
        
        return analysis
    
    def _analyze_by_time(self, results) -> Dict:
        """Analyze performance by time of day."""
        hourly = defaultdict(lambda: {'total': 0, 'wins': 0})
        
        for result in results:
            hour = result.evaluated_at.hour
            hourly[hour]['total'] += 1
            if result.success:
                hourly[hour]['wins'] += 1
        
        analysis = {}
        for hour, data in sorted(hourly.items()):
            win_rate = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            analysis[f'{hour:02d}:00'] = {
                'total': data['total'],
                'wins': data['wins'],
                'win_rate': round(win_rate, 1),
            }
        
        return analysis
    
    def _analyze_by_condition(self, results) -> Dict:
        """Analyze performance by market condition."""
        conditions = defaultdict(lambda: {'total': 0, 'wins': 0})
        
        for result in results:
            condition = result.market_condition or 'unknown'
            conditions[condition]['total'] += 1
            if result.success:
                conditions[condition]['wins'] += 1
        
        analysis = {}
        for condition, data in conditions.items():
            win_rate = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            analysis[condition] = {
                'total': data['total'],
                'wins': data['wins'],
                'win_rate': round(win_rate, 1),
            }
        
        return analysis
    
    def _analyze_confidence_correlation(self) -> Dict:
        """Analyze correlation between confidence and actual performance."""
        from ..models import SignalResult
        
        results = SignalResult.objects.select_related('signal').all()
        
        if results.count() < 10:
            return {}
        
        high_conf = results.filter(signal__confidence__gte=70)
        low_conf = results.filter(signal__confidence__lt=40)
        
        high_win_rate = 0
        low_win_rate = 0
        
        if high_conf.count() > 0:
            high_win_rate = high_conf.filter(success=True).count() / high_conf.count() * 100
        if low_conf.count() > 0:
            low_win_rate = low_conf.filter(success=True).count() / low_conf.count() * 100
        
        return {
            'high_confidence_win_rate': high_win_rate,
            'low_confidence_win_rate': low_win_rate,
            'low_confidence_wins_high': low_win_rate > high_win_rate,
        }
    
    def _analyze_duration_impact(self) -> Dict:
        """Analyze how holding duration affects performance."""
        from ..models import SignalResult
        
        results = SignalResult.objects.all()
        
        if results.count() < 10:
            return {}
        
        # Group by duration ranges
        ranges = [
            ('short', 0, 4),
            ('medium', 4, 24),
            ('long', 24, 168),
            ('very_long', 168, float('inf')),
        ]
        
        best_rate = 0
        optimal_duration = None
        
        for label, low, high in ranges:
            range_results = results.filter(
                duration_hours__gte=low,
                duration_hours__lt=high
            )
            if range_results.count() >= 5:
                win_rate = range_results.filter(success=True).count() / range_results.count() * 100
                if win_rate > best_rate:
                    best_rate = win_rate
                    optimal_duration = f'{low}-{high}'
        
        return {'optimal_duration': optimal_duration}
    
    def _analyze_stop_loss_effectiveness(self) -> Dict:
        """Analyze stop loss trigger frequency."""
        from ..models import SignalResult
        
        total = SignalResult.objects.count()
        if total == 0:
            return {}
        
        stopped = SignalResult.objects.filter(
            notes__icontains='stop_loss'
        ).count()
        
        return {
            'stop_loss_frequency': stopped / total if total > 0 else 0,
            'total_stopped': stopped,
            'total_signals': total,
        }
    
    def _generate_recommendations(self, patterns: Dict, total: int) -> List[Dict]:
        """Generate recommendations based on pattern analysis."""
        recommendations = []
        
        # Check symbol performance
        by_symbol = patterns.get('by_symbol', {})
        for symbol, data in by_symbol.items():
            if data['total'] >= self.MIN_SIGNALS_FOR_PATTERN:
                if data['win_rate'] < 40:
                    recommendations.append({
                        'type': 'symbol_performance',
                        'severity': 'medium',
                        'symbol': symbol,
                        'message': f'{symbol} has low win rate ({data["win_rate"]}%)',
                        'action': f'Review signal criteria for {symbol} or reduce exposure.',
                    })
        
        # Check timeframe performance
        by_timeframe = patterns.get('by_timeframe', {})
        for tf, data in by_timeframe.items():
            if data['total'] >= self.MIN_SIGNALS_FOR_PATTERN:
                if data['win_rate'] > 60:
                    recommendations.append({
                        'type': 'timeframe_strength',
                        'severity': 'low',
                        'timeframe': tf,
                        'message': f'{tf} timeframe shows strong performance ({data["win_rate"]}%)',
                        'action': f'Consider increasing weight for {tf} signals.',
                    })
        
        return recommendations
    
    def _get_field_value(self, obj, field_path: str):
        """Get nested field value using dot notation."""
        parts = field_path.split('__')
        value = obj
        for part in parts:
            value = getattr(value, part, None)
            if value is None:
                return None
        return value
