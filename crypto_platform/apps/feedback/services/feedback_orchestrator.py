"""Feedback Orchestrator Service - Manage the complete feedback loop cycle."""
import logging
from typing import Dict, List
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class FeedbackOrchestrator:
    """Orchestrate the complete feedback loop: observe → analyze → learn → improve."""
    
    @classmethod
    def run_feedback_cycle(
        cls,
        cycle_type: str = 'daily',
        lookback_days: int = 1,
        symbol: str = None,
    ) -> Dict:
        """Execute a complete feedback cycle.
        
        Steps:
        1. Collect recent signal outcomes
        2. Analyze performance patterns
        3. Generate learning insights
        4. Update memory embeddings
        5. Adjust weights if needed
        6. Generate improvement recommendations
        
        Returns:
            Comprehensive feedback cycle results
        """
        from ..models import FeedbackCycle, SignalMemory, LearningInsight
        from .learning_agent import LearningAgent
        from .similarity_search import SimilaritySearchService
        
        # Create cycle record
        cycle = FeedbackCycle.objects.create(
            cycle_type=cycle_type,
            status='running',
        )
        
        try:
            results = {
                'cycle_id': str(cycle.id),
                'cycle_type': cycle_type,
                'started_at': cycle.started_at.isoformat(),
                'steps': {},
            }
            
            # Step 1: Collect recent signals
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            signals = SignalMemory.objects.filter(
                created_at__gte=cutoff_date,
                evaluated_at__isnull=False,
            )
            if symbol:
                signals = signals.filter(signal__symbol=symbol)
            
            signals_list = list(signals)
            cycle.signals_evaluated = len(signals_list)
            cycle.signals_correct = sum(1 for s in signals_list if s.was_correct)
            
            results['steps']['collection'] = {
                'signals_found': len(signals_list),
                'correct_signals': cycle.signals_correct,
                'win_rate': round(cycle.signals_correct / len(signals_list) * 100, 2) if signals_list else 0,
            }
            
            # Step 2: Analyze performance
            analysis = LearningAgent.analyze_performance(
                lookback_days=lookback_days * 3,  # Look back further for context
                symbol=symbol,
                min_signals=5,
            )
            results['steps']['analysis'] = {
                'status': analysis.get('status'),
                'overall_metrics': analysis.get('overall'),
            }
            
            # Step 3: Generate insights
            insights = []
            if analysis.get('status') == 'complete':
                recommendations = LearningAgent.generate_improvement_recommendations(analysis)
                
                for rec in recommendations:
                    insight = LearningInsight.objects.create(
                        insight_type=rec.get('type', 'performance_analysis'),
                        title=rec.get('title', 'Performance Insight'),
                        description=rec.get('description', ''),
                        confidence=0.7,
                        impact_score=0.5,
                        related_symbols=[symbol] if symbol else [],
                        supporting_evidence=[rec],
                    )
                    insights.append(str(insight.id))
                
                cycle.insights_generated = len(insights)
            
            results['steps']['insights'] = {
                'insights_generated': len(insights),
                'insight_ids': insights,
            }
            
            # Step 4: Update memory embeddings for recent signals
            embeddings_updated = cls._update_memory_embeddings(signals_list)
            results['steps']['embeddings'] = {
                'updated': embeddings_updated,
            }
            
            # Step 5: Adjust weights based on performance
            weight_adjustment = {}
            try:
                from apps.signals.services.weight_adjuster import WeightAdjuster
                weight_result = WeightAdjuster.adjust_weights(lookback_days=lookback_days * 3)
                weight_adjustment = weight_result
                cycle.weights_adjusted = weight_result.get('weights_changed', False)
                results['steps']['weights'] = {
                    'status': weight_result.get('status'),
                    'weights_changed': weight_result.get('weights_changed', False),
                    'summary': weight_result.get('summary', ''),
                    'new_weights': weight_result.get('new_weights', {}),
                }
            except Exception as e:
                logger.warning(f"Weight adjustment failed: {e}")
                results['steps']['weights'] = {'status': 'skipped', 'error': str(e)}
            
            # Step 6: Calculate pre/post accuracy
            pre_accuracy = cycle.signals_correct / cycle.signals_evaluated * 100 if cycle.signals_evaluated > 0 else 0
            cycle.pre_cycle_accuracy = Decimal(str(round(pre_accuracy, 2)))
            cycle.post_cycle_accuracy = cycle.pre_cycle_accuracy  # Will be updated after next cycle
            
            # Step 6: Generate summary
            cycle.summary = cls._generate_cycle_summary(analysis, results)
            cycle.recommendations = analysis.get('insights', [])
            
            # Complete the cycle
            cycle.status = 'completed'
            cycle.completed_at = datetime.now()
            cycle.save()
            
            results['completed_at'] = cycle.completed_at.isoformat()
            results['summary'] = cycle.summary
            results['recommendations'] = cycle.recommendations
            
            logger.info(f"Feedback cycle {cycle.id} completed successfully")
            return results
            
        except Exception as e:
            cycle.status = 'failed'
            cycle.error_message = str(e)
            cycle.save()
            
            logger.error(f"Feedback cycle {cycle.id} failed: {e}")
            raise
    
    @staticmethod
    def _update_memory_embeddings(signals: List) -> int:
        """Update memory embeddings for analyzed signals."""
        from ..models import MarketMemory
        from .similarity_search import SimilaritySearchService
        
        updated = 0
        for signal_memory in signals:
            if signal_memory.market_memory and not signal_memory.market_memory.embedding:
                # Generate embedding from market data
                market_data = {
                    'price_change_1h': 0,  # Would be calculated from actual data
                    'rsi': signal_memory.factors_at_creation.get('technical_score', 50),
                    'fear_greed_index': signal_memory.factors_at_creation.get('sentiment_score', 50),
                    'volume_ratio': 1.0,
                    'macd_signal': 0,
                    'ema_trend': 0,
                    'adx': 25,
                    'social_sentiment': 0,
                    'atr_percent': 2.0,
                }
                
                embedding = SimilaritySearchService.calculate_embedding(market_data)
                signal_memory.market_memory.embedding = embedding
                signal_memory.market_memory.save(update_fields=['embedding'])
                updated += 1
        
        return updated
    
    @staticmethod
    def _generate_cycle_summary(analysis: Dict, results: Dict) -> str:
        """Generate a human-readable summary of the feedback cycle."""
        if analysis.get('status') != 'complete':
            return "Insufficient data for meaningful analysis."
        
        overall = analysis.get('overall', {})
        collection = results.get('steps', {}).get('collection', {})
        
        parts = []
        
        # Performance summary
        win_rate = overall.get('win_rate', 0)
        if win_rate >= 65:
            parts.append(f"Excellent performance with {win_rate}% win rate.")
        elif win_rate >= 55:
            parts.append(f"Good performance with {win_rate}% win rate.")
        elif win_rate >= 45:
            parts.append(f"Average performance with {win_rate}% win rate.")
        else:
            parts.append(f"Below average performance with {win_rate}% win rate - review needed.")
        
        # Return summary
        avg_return = overall.get('avg_return', 0)
        if avg_return > 0:
            parts.append(f"Average return per signal: +{avg_return:.2f}%")
        else:
            parts.append(f"Average return per signal: {avg_return:.2f}%")
        
        # Insights count
        insights_count = results.get('steps', {}).get('insights', {}).get('insights_generated', 0)
        if insights_count > 0:
            parts.append(f"Generated {insights_count} actionable insights.")
        
        return " ".join(parts)
    
    @classmethod
    def get_historical_cycles(
        cls,
        limit: int = 10,
        cycle_type: str = None,
    ) -> List[Dict]:
        """Get recent feedback cycles."""
        from ..models import FeedbackCycle
        
        queryset = FeedbackCycle.objects.all()
        if cycle_type:
            queryset = queryset.filter(cycle_type=cycle_type)
        
        cycles = queryset.order_by('-started_at')[:limit]
        
        return [
            {
                'id': str(c.id),
                'cycle_type': c.cycle_type,
                'status': c.status,
                'signals_evaluated': c.signals_evaluated,
                'signals_correct': c.signals_correct,
                'win_rate': round(c.signals_correct / c.signals_evaluated * 100, 2) if c.signals_evaluated > 0 else 0,
                'insights_generated': c.insights_generated,
                'summary': c.summary,
                'started_at': c.started_at.isoformat(),
                'completed_at': c.completed_at.isoformat() if c.completed_at else None,
            }
            for c in cycles
        ]
    
    @classmethod
    def get_learning_insights(
        cls,
        limit: int = 20,
        insight_type: str = None,
        active_only: bool = True,
    ) -> List[Dict]:
        """Get learning insights."""
        from ..models import LearningInsight
        
        queryset = LearningInsight.objects.all()
        if insight_type:
            queryset = queryset.filter(insight_type=insight_type)
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        insights = queryset.order_by('-created_at')[:limit]
        
        return [
            {
                'id': str(i.id),
                'type': i.insight_type,
                'title': i.title,
                'description': i.description,
                'confidence': i.confidence,
                'impact_score': i.impact_score,
                'related_symbols': i.related_symbols,
                'was_implemented': i.was_implemented,
                'created_at': i.created_at.isoformat(),
            }
            for i in insights
        ]
    
    @classmethod
    def get_market_memories(
        cls,
        symbol: str = None,
        limit: int = 50,
        has_embedding: bool = True,
    ) -> List[Dict]:
        """Get market memories."""
        from ..models import MarketMemory
        
        queryset = MarketMemory.objects.all()
        if symbol:
            queryset = queryset.filter(symbol=symbol)
        if has_embedding:
            queryset = queryset.filter(embedding__isnull=False).exclude(embedding=[])
        
        memories = queryset.order_by('-created_at')[:limit]
        
        return [
            {
                'id': str(m.id),
                'symbol': m.symbol,
                'timeframe': m.timeframe,
                'price': float(m.price),
                'market_condition': m.market_condition,
                'dominant_factor': m.dominant_factor,
                'has_embedding': bool(m.embedding),
                'created_at': m.created_at.isoformat(),
            }
            for m in memories
        ]
