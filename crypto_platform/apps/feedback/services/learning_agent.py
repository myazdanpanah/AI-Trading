"""Learning Agent Service - Analyze mistakes, compare predictions, recommend improvements."""
import logging
from typing import Dict, List
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

logger = logging.getLogger(__name__)


class LearningAgent:
    """AI-powered learning agent that analyzes signal performance and recommends improvements."""
    
    # Performance thresholds
    EXCELLENT_WIN_RATE = 0.70
    GOOD_WIN_RATE = 0.55
    POOR_WIN_RATE = 0.40
    
    # Factor importance thresholds
    FACTOR_IMPROVEMENT_THRESHOLD = 0.10
    FACTOR_DECLINE_THRESHOLD = -0.10
    
    @classmethod
    def analyze_performance(
        cls,
        lookback_days: int = 30,
        symbol: str = None,
        min_signals: int = 10,
    ) -> Dict:
        """Comprehensive performance analysis of signals.
        
        Returns detailed analysis of:
        - Overall accuracy and trends
        - Performance by factor (technical, sentiment, news, AI, macro)
        - Performance by market condition
        - Time-based patterns
        - Specific mistakes and successes
        """
        from ..models import SignalMemory, LearningInsight
        
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        
        # Query signals
        queryset = SignalMemory.objects.filter(
            created_at__gte=cutoff_date,
            evaluated_at__isnull=False,
        )
        if symbol:
            queryset = queryset.filter(signal__symbol=symbol)
        
        signals = list(queryset.select_related('signal').order_by('created_at'))
        
        if len(signals) < min_signals:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least {min_signals} signals, found {len(signals)}',
                'signals_found': len(signals),
            }
        
        # Overall metrics
        total = len(signals)
        correct = sum(1 for s in signals if s.was_correct)
        win_rate = correct / total
        
        returns = [float(s.actual_return_percent) for s in signals]
        avg_return = sum(returns) / total if total > 0 else 0
        max_return = max(returns) if returns else 0
        max_loss = min(returns) if returns else 0
        
        # Performance by direction
        long_signals = [s for s in signals if s.signal_direction in ('buy', 'strong_buy')]
        short_signals = [s for s in signals if s.signal_direction in ('sell', 'strong_sell')]
        
        long_win_rate = (
            sum(1 for s in long_signals if s.was_correct) / len(long_signals)
            if long_signals else 0
        )
        short_win_rate = (
            sum(1 for s in short_signals if s.was_correct) / len(short_signals)
            if short_signals else 0
        )
        
        # Performance by confidence level
        high_confidence = [s for s in signals if s.signal_confidence >= 70]
        medium_confidence = [s for s in signals if 40 <= s.signal_confidence < 70]
        low_confidence = [s for s in signals if s.signal_confidence < 40]
        
        # Performance by market condition
        condition_performance = defaultdict(lambda: {'total': 0, 'correct': 0})
        for s in signals:
            if s.market_memory and s.market_memory.market_condition:
                condition = s.market_memory.market_condition
                condition_performance[condition]['total'] += 1
                if s.was_correct:
                    condition_performance[condition]['correct'] += 1
        
        # Factor analysis
        factor_analysis = cls._analyze_factors(signals)
        
        # Identify patterns in mistakes
        mistakes = [s for s in signals if not s.was_correct]
        successes = [s for s in signals if s.was_correct]
        
        mistake_patterns = cls._identify_mistake_patterns(mistakes)
        success_patterns = cls._identify_success_patterns(successes)
        
        # Generate insights
        insights = cls._generate_insights(
            win_rate, long_win_rate, short_win_rate,
            factor_analysis, mistake_patterns, success_patterns
        )
        
        return {
            'status': 'complete',
            'period_days': lookback_days,
            'total_signals': total,
            'overall': {
                'win_rate': round(win_rate * 100, 2),
                'avg_return': round(avg_return, 4),
                'max_return': round(max_return, 4),
                'max_loss': round(max_loss, 4),
                'profit_factor': cls._calculate_profit_factor(returns),
                'sharpe_ratio': cls._calculate_sharpe(returns),
            },
            'by_direction': {
                'long': {
                    'count': len(long_signals),
                    'win_rate': round(long_win_rate * 100, 2),
                },
                'short': {
                    'count': len(short_signals),
                    'win_rate': round(short_win_rate * 100, 2),
                },
            },
            'by_confidence': {
                'high': {
                    'count': len(high_confidence),
                    'win_rate': round(
                        sum(1 for s in high_confidence if s.was_correct) / len(high_confidence) * 100, 2
                    ) if high_confidence else 0,
                },
                'medium': {
                    'count': len(medium_confidence),
                    'win_rate': round(
                        sum(1 for s in medium_confidence if s.was_correct) / len(medium_confidence) * 100, 2
                    ) if medium_confidence else 0,
                },
                'low': {
                    'count': len(low_confidence),
                    'win_rate': round(
                        sum(1 for s in low_confidence if s.was_correct) / len(low_confidence) * 100, 2
                    ) if low_confidence else 0,
                },
            },
            'by_market_condition': dict(condition_performance),
            'factor_analysis': factor_analysis,
            'mistake_patterns': mistake_patterns,
            'success_patterns': success_patterns,
            'insights': insights,
        }
    
    @staticmethod
    def _analyze_factors(signals: List) -> Dict:
        """Analyze how each factor contributed to signal success/failure."""
        factors = ['technical', 'sentiment', 'news', 'ai', 'macro']
        
        factor_analysis = {}
        for factor in factors:
            correct_scores = []
            incorrect_scores = []
            
            for s in signals:
                factors_data = s.factors_at_creation or {}
                score = factors_data.get(f'{factor}_score')
                if score is not None:
                    if s.was_correct:
                        correct_scores.append(float(score))
                    else:
                        incorrect_scores.append(float(score))
            
            avg_correct = sum(correct_scores) / len(correct_scores) if correct_scores else 0
            avg_incorrect = sum(incorrect_scores) / len(incorrect_scores) if incorrect_scores else 0
            
            factor_analysis[factor] = {
                'avg_score_correct': round(avg_correct, 4),
                'avg_score_incorrect': round(avg_incorrect, 4),
                'discrimination_power': round(avg_correct - avg_incorrect, 4),
                'sample_size': len(correct_scores) + len(incorrect_scores),
            }
        
        return factor_analysis
    
    @staticmethod
    def _identify_mistake_patterns(mistakes: List) -> Dict:
        """Identify common patterns in incorrect signals."""
        if not mistakes:
            return {'patterns': [], 'count': 0}
        
        patterns = []
        
        # Check for overconfidence
        high_conf_mistakes = [m for m in mistakes if m.signal_confidence >= 70]
        if len(high_conf_mistakes) > len(mistakes) * 0.3:
            patterns.append({
                'type': 'overconfidence',
                'description': f'{len(high_conf_mistakes)} high-confidence signals failed',
                'severity': 'high',
                'recommendation': 'Reduce confidence threshold or add confirmation filters',
            })
        
        # Check for direction bias
        buy_mistakes = [m for m in mistakes if m.signal_direction in ('buy', 'strong_buy')]
        sell_mistakes = [m for m in mistakes if m.signal_direction in ('sell', 'strong_sell')]
        
        if len(buy_mistakes) > len(sell_mistakes) * 2:
            patterns.append({
                'type': 'bullish_bias',
                'description': 'Buy signals failing more often than sell signals',
                'severity': 'medium',
                'recommendation': 'Review bullish signal criteria',
            })
        elif len(sell_mistakes) > len(buy_mistakes) * 2:
            patterns.append({
                'type': 'bearish_bias',
                'description': 'Sell signals failing more often than buy signals',
                'severity': 'medium',
                'recommendation': 'Review bearish signal criteria',
            })
        
        # Check for market condition issues
        condition_counts = defaultdict(int)
        for m in mistakes:
            if m.market_memory:
                condition_counts[m.market_memory.market_condition] += 1
        
        for condition, count in condition_counts.items():
            if count > len(mistakes) * 0.4 and condition:
                patterns.append({
                    'type': 'condition_specific',
                    'description': f'Many failures in {condition} market',
                    'severity': 'high',
                    'recommendation': f'Add filters for {condition} market conditions',
                })
        
        return {
            'patterns': patterns,
            'count': len(patterns),
            'total_mistakes': len(mistakes),
        }
    
    @staticmethod
    def _identify_success_patterns(successes: List) -> Dict:
        """Identify patterns in successful signals."""
        if not successes:
            return {'patterns': [], 'count': 0}
        
        patterns = []
        
        # Check for high-confidence winners
        high_conf_wins = [s for s in successes if s.signal_confidence >= 70]
        if len(high_conf_wins) > len(successes) * 0.5:
            patterns.append({
                'type': 'confidence_correlation',
                'description': 'High confidence signals perform well',
                'recommendation': 'Trust confidence scoring',
            })
        
        # Check best market conditions
        condition_wins = defaultdict(int)
        for s in successes:
            if s.market_memory:
                condition_wins[s.market_memory.market_condition] += 1
        
        best_conditions = sorted(condition_wins.items(), key=lambda x: x[1], reverse=True)
        for condition, count in best_conditions[:2]:
            if condition:
                patterns.append({
                    'type': 'best_condition',
                    'description': f'Signals perform best in {condition} markets',
                    'recommendation': f'Focus on {condition} market opportunities',
                })
        
        return {
            'patterns': patterns,
            'count': len(patterns),
            'total_successes': len(successes),
        }
    
    @classmethod
    def _generate_insights(
        cls,
        win_rate: float,
        long_win_rate: float,
        short_win_rate: float,
        factor_analysis: Dict,
        mistake_patterns: Dict,
        success_patterns: Dict,
    ) -> List[Dict]:
        """Generate actionable insights from analysis."""
        insights = []
        
        # Overall performance insight
        if win_rate >= cls.EXCELLENT_WIN_RATE:
            insights.append({
                'type': 'performance',
                'priority': 'low',
                'title': 'Excellent Performance',
                'description': f'Win rate of {win_rate*100:.1f}% is excellent',
                'action': 'Consider slightly increasing position sizes',
            })
        elif win_rate <= cls.POOR_WIN_RATE:
            insights.append({
                'type': 'performance',
                'priority': 'high',
                'title': 'Poor Performance Alert',
                'description': f'Win rate of {win_rate*100:.1f}% needs improvement',
                'action': 'Review and tighten signal criteria',
            })
        
        # Direction bias insight
        if abs(long_win_rate - short_win_rate) > 0.15:
            weaker = 'long' if long_win_rate < short_win_rate else 'short'
            insights.append({
                'type': 'direction_bias',
                'priority': 'medium',
                'title': f'{weaker.title()} signals underperforming',
                'description': f'{weaker.title()} win rate: {long_win_rate*100 if weaker == "long" else short_win_rate*100:.1f}%',
                'action': f'Review {weaker} signal criteria and filters',
            })
        
        # Factor insights
        best_factor = max(factor_analysis.items(), key=lambda x: x[1]['discrimination_power'])
        worst_factor = min(factor_analysis.items(), key=lambda x: x[1]['discrimination_power'])
        
        if best_factor[1]['discrimination_power'] > 0.1:
            insights.append({
                'type': 'factor_strength',
                'priority': 'medium',
                'title': f'{best_factor[0].title()} is strongest predictor',
                'description': f'Discrimination power: {best_factor[1]["discrimination_power"]:.3f}',
                'action': f'Consider increasing {best_factor[0]} weight',
            })
        
        if worst_factor[1]['discrimination_power'] < -0.05:
            insights.append({
                'type': 'factor_weakness',
                'priority': 'high',
                'title': f'{worst_factor[0].title()} is counterproductive',
                'description': f'Discrimination power: {worst_factor[1]["discrimination_power"]:.3f}',
                'action': f'Consider reducing {worst_factor[0]} weight or retraining',
            })
        
        # Pattern insights
        for pattern in mistake_patterns.get('patterns', []):
            insights.append({
                'type': 'mistake_pattern',
                'priority': pattern['severity'],
                'title': f"Mistake Pattern: {pattern['type']}",
                'description': pattern['description'],
                'action': pattern['recommendation'],
            })
        
        return insights
    
    @staticmethod
    def _calculate_profit_factor(returns: List[float]) -> float:
        """Calculate profit factor (sum of wins / sum of losses)."""
        wins = [r for r in returns if r > 0]
        losses = [abs(r) for r in returns if r < 0]
        
        total_wins = sum(wins)
        total_losses = sum(losses)
        
        if total_losses == 0:
            return float('inf') if total_wins > 0 else 0
        
        return round(total_wins / total_losses, 4)
    
    @staticmethod
    def _calculate_sharpe(returns: List[float], risk_free_rate: float = 0.0) -> float:
        """Calculate simplified Sharpe ratio."""
        if not returns:
            return 0
        
        avg_return = sum(returns) / len(returns)
        
        if len(returns) < 2:
            return 0
        
        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0
        
        return round((avg_return - risk_free_rate) / std_dev, 4)
    
    @classmethod
    def generate_improvement_recommendations(cls, analysis: Dict) -> List[Dict]:
        """Generate specific recommendations based on performance analysis."""
        recommendations = []
        
        if analysis.get('status') != 'complete':
            return [{'type': 'data_needed', 'message': 'Insufficient data for recommendations'}]
        
        overall = analysis.get('overall', {})
        win_rate = overall.get('win_rate', 50) / 100
        
        # Confidence calibration
        by_confidence = analysis.get('by_confidence', {})
        high_conf_wr = by_confidence.get('high', {}).get('win_rate', 50) / 100
        low_conf_wr = by_confidence.get('low', {}).get('win_rate', 50) / 100
        
        if high_conf_wr < 0.5:
            recommendations.append({
                'type': 'confidence_calibration',
                'priority': 'high',
                'title': 'Confidence scores need recalibration',
                'description': f'High confidence signals only win {high_conf_wr*100:.1f}%',
                'action': 'Reduce confidence weights or add confirmation criteria',
            })
        
        if low_conf_wr > 0.55:
            recommendations.append({
                'type': 'confidence_calibration',
                'priority': 'medium',
                'title': 'Low confidence signals performing well',
                'description': f'Low confidence signals win {low_conf_wr*100:.1f}%',
                'action': 'Consider lowering confidence threshold for signal generation',
            })
        
        # Factor weight adjustments
        factor_analysis = analysis.get('factor_analysis', {})
        for factor, data in factor_analysis.items():
            if data.get('discrimination_power', 0) > 0.15:
                recommendations.append({
                    'type': 'weight_adjustment',
                    'priority': 'medium',
                    'title': f'Increase {factor} weight',
                    'description': f'{factor} has strong discrimination power ({data["discrimination_power"]:.3f})',
                    'action': f'Increase {factor} weight by 5-10%',
                })
            elif data.get('discrimination_power', 0) < -0.1:
                recommendations.append({
                    'type': 'weight_adjustment',
                    'priority': 'high',
                    'title': f'Decrease {factor} weight',
                    'description': f'{factor} is counterproductive ({data["discrimination_power"]:.3f})',
                    'action': f'Decrease {factor} weight by 5-10% or investigate',
                })
        
        # Risk management
        if overall.get('max_loss', 0) < -10:
            recommendations.append({
                'type': 'risk_management',
                'priority': 'high',
                'title': 'Large losses detected',
                'description': f'Max loss: {overall["max_loss"]:.2f}%',
                'action': 'Tighten stop losses or reduce position sizes',
            })
        
        return recommendations
