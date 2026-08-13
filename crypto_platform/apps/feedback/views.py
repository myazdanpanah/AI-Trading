"""Feedback Loop views - API endpoints for AI memory, similarity search, and self-improvement."""
import logging
from rest_framework import viewsets, status
from datetime import datetime
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import MarketMemory, SignalMemory, PatternMemory, LearningInsight, FeedbackCycle
from .serializers import (
    MarketMemorySerializer, SignalMemorySerializer, PatternMemorySerializer,
    LearningInsightSerializer, FeedbackCycleSerializer,
    SimilaritySearchInputSerializer, SignalPredictionInputSerializer,
    PerformanceAnalysisInputSerializer, FeedbackCycleInputSerializer,
    RecordSignalOutcomeInputSerializer,
)
from .services import SimilaritySearchService, LearningAgent, FeedbackOrchestrator

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(tags=['Feedback'], summary='List market memories'),
    create=extend_schema(tags=['Feedback'], summary='Create market memory'),
    retrieve=extend_schema(tags=['Feedback'], summary='Get market memory'),
    update=extend_schema(tags=['Feedback'], summary='Update market memory'),
    partial_update=extend_schema(tags=['Feedback'], summary='Partial update market memory'),
    destroy=extend_schema(tags=['Feedback'], summary='Delete market memory'),
    search_similar=extend_schema(tags=['Feedback'], summary='Find similar historical market situations'),
    record_state=extend_schema(tags=['Feedback'], summary='Record current market state'),
)
class MarketMemoryViewSet(viewsets.ModelViewSet):
    """ViewSet for MarketMemory CRUD and similarity search."""
    queryset = MarketMemory.objects.all()
    serializer_class = MarketMemorySerializer
    filterset_fields = ['symbol', 'timeframe', 'market_condition']
    
    @action(detail=False, methods=['post'])
    def search_similar(self, request):
        """Find similar historical market situations."""
        serializer = SimilaritySearchInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            results = SimilaritySearchService.find_similar_memories(
                current_market_data=data,
                symbol=data.get('symbol'),
                limit=data.get('limit', 5),
                min_similarity=data.get('min_similarity', 0.7),
            )
            
            return Response({
                'similar_memories': results,
                'count': len(results),
                'query': {
                    'symbol': data['symbol'],
                    'timeframe': data.get('timeframe', '1h'),
                }
            })
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return Response(
                {'error': 'Similarity search failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def record_state(self, request):
        """Record current market state for future similarity search."""
        try:
            data = request.data
            
            # Calculate embedding
            embedding = SimilaritySearchService.calculate_embedding(data)
            
            memory = MarketMemory.objects.create(
                symbol=data['symbol'],
                timeframe=data.get('timeframe', '1h'),
                price=data['price'],
                volume=data.get('volume', 0),
                technical_indicators=data.get('technical_indicators', {}),
                sentiment_data=data.get('sentiment_data', {}),
                news_summary=data.get('news_summary', ''),
                embedding=embedding,
                market_condition=data.get('market_condition', ''),
                dominant_factor=data.get('dominant_factor', ''),
                confidence_at_time=data.get('confidence', 0.5),
            )
            
            return Response(
                MarketMemorySerializer(memory).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Failed to record market state: {e}")
            return Response(
                {'error': 'Failed to record market state'},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema_view(
    list=extend_schema(tags=['Feedback'], summary='List signal memories'),
    create=extend_schema(tags=['Feedback'], summary='Create signal memory'),
    retrieve=extend_schema(tags=['Feedback'], summary='Get signal memory'),
    update=extend_schema(tags=['Feedback'], summary='Update signal memory'),
    partial_update=extend_schema(tags=['Feedback'], summary='Partial update signal memory'),
    destroy=extend_schema(tags=['Feedback'], summary='Delete signal memory'),
    record_outcome=extend_schema(tags=['Feedback'], summary='Record signal outcome for learning'),
    prediction=extend_schema(tags=['Feedback'], summary='Get prediction for a signal'),
)
class SignalMemoryViewSet(viewsets.ModelViewSet):
    """ViewSet for SignalMemory - tracking signal outcomes for learning."""
    queryset = SignalMemory.objects.select_related('signal', 'market_memory').all()
    serializer_class = SignalMemorySerializer
    filterset_fields = ['was_correct', 'signal_direction']
    
    @action(detail=False, methods=['post'])
    def record_outcome(self, request):
        """Record signal outcome for learning."""
        serializer = RecordSignalOutcomeInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            from signals.models import Signal
            
            signal = Signal.objects.get(id=data['signal_id'])
            
            # Find associated market memory
            market_memory = MarketMemory.objects.filter(
                symbol=signal.symbol,
                timeframe=signal.timeframe,
            ).order_by('-created_at').first()
            
            # Create signal memory
            signal_memory = SignalMemory.objects.create(
                signal=signal,
                market_memory=market_memory,
                signal_direction=signal.direction,
                signal_confidence=signal.confidence,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                exit_price=data['exit_price'],
                actual_return=0,
                actual_return_percent=data['profit_loss_percent'],
                was_correct=data['profit_loss_percent'] > 0,
                holding_period_hours=data.get('holding_period_hours', 0),
                factors_at_creation={
                    'technical_score': float(signal.technical_score),
                    'sentiment_score': float(signal.sentiment_score),
                    'news_score': float(signal.news_score),
                    'ai_score': float(signal.ai_score),
                    'macro_score': float(signal.macro_score),
                    'composite_score': float(signal.composite_score),
                },
                evaluated_at=datetime.now(),
            )
            
            return Response(
                SignalMemorySerializer(signal_memory).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Failed to record signal outcome: {e}")
            return Response(
                {'error': f'Failed to record outcome: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def prediction(self, request):
        """Get prediction for a signal based on historical similarity."""
        serializer = SignalPredictionInputSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            prediction = SimilaritySearchService.get_signal_prediction(
                current_market_data=data,
                signal_direction=data['signal_direction'],
            )
            
            return Response(prediction)
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return Response(
                {'error': 'Prediction failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema_view(
    list=extend_schema(tags=['Feedback'], summary='List pattern memories'),
    create=extend_schema(tags=['Feedback'], summary='Create pattern memory'),
    retrieve=extend_schema(tags=['Feedback'], summary='Get pattern memory'),
    update=extend_schema(tags=['Feedback'], summary='Update pattern memory'),
    partial_update=extend_schema(tags=['Feedback'], summary='Partial update pattern memory'),
    destroy=extend_schema(tags=['Feedback'], summary='Delete pattern memory'),
    find_similar=extend_schema(tags=['Feedback'], summary='Find similar historical patterns'),
)
class PatternMemoryViewSet(viewsets.ModelViewSet):
    """ViewSet for PatternMemory - successful and failed patterns."""
    queryset = PatternMemory.objects.all()
    serializer_class = PatternMemorySerializer
    filterset_fields = ['pattern_type', 'symbol', 'timeframe']
    
    @action(detail=False, methods=['post'])
    def find_similar(self, request):
        """Find similar historical patterns."""
        try:
            data = request.data
            
            results = SimilaritySearchService.find_similar_patterns(
                current_indicators=data.get('indicators', {}),
                pattern_type=data.get('pattern_type'),
                symbol=data.get('symbol'),
                limit=data.get('limit', 5),
            )
            
            return Response({
                'similar_patterns': results,
                'count': len(results),
            })
        except Exception as e:
            logger.error(f"Pattern search failed: {e}")
            return Response(
                {'error': 'Pattern search failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema_view(
    list=extend_schema(tags=['Feedback'], summary='List learning insights'),
    create=extend_schema(tags=['Feedback'], summary='Create learning insight'),
    retrieve=extend_schema(tags=['Feedback'], summary='Get learning insight'),
    update=extend_schema(tags=['Feedback'], summary='Update learning insight'),
    partial_update=extend_schema(tags=['Feedback'], summary='Partial update learning insight'),
    destroy=extend_schema(tags=['Feedback'], summary='Delete learning insight'),
    implement=extend_schema(tags=['Feedback'], summary='Mark an insight as implemented'),
    active=extend_schema(tags=['Feedback'], summary='Get all active insights'),
)
class LearningInsightViewSet(viewsets.ModelViewSet):
    """ViewSet for LearningInsight - AI-generated insights and recommendations."""
    queryset = LearningInsight.objects.all()
    serializer_class = LearningInsightSerializer
    filterset_fields = ['insight_type', 'is_active', 'was_implemented']
    
    @action(detail=True, methods=['post'])
    def implement(self, request, pk=None):
        """Mark an insight as implemented."""
        insight = self.get_object()
        insight.was_implemented = True
        insight.implementation_result = request.data.get('result', 'Implemented')
        insight.save()
        
        return Response(LearningInsightSerializer(insight).data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active insights."""
        insights = LearningInsight.objects.filter(
            is_active=True,
            was_implemented=False,
        ).order_by('-confidence', '-impact_score')[:20]
        
        return Response(LearningInsightSerializer(insights, many=True).data)


@extend_schema_view(
    list=extend_schema(tags=['Feedback'], summary='List feedback cycles'),
    create=extend_schema(tags=['Feedback'], summary='Create feedback cycle'),
    retrieve=extend_schema(tags=['Feedback'], summary='Get feedback cycle'),
    update=extend_schema(tags=['Feedback'], summary='Update feedback cycle'),
    partial_update=extend_schema(tags=['Feedback'], summary='Partial update feedback cycle'),
    destroy=extend_schema(tags=['Feedback'], summary='Delete feedback cycle'),
    run_cycle=extend_schema(tags=['Feedback'], summary='Execute a feedback cycle'),
    history=extend_schema(tags=['Feedback'], summary='Get feedback cycle history'),
)
class FeedbackCycleViewSet(viewsets.ModelViewSet):
    """ViewSet for FeedbackCycle - tracking feedback loop cycles."""
    serializer_class = FeedbackCycleSerializer
    filterset_fields = ['cycle_type', 'status']

    def get_queryset(self):
        qs = FeedbackCycle.objects.all()
        cycle_type = self.request.query_params.get('cycle_type')
        if cycle_type:
            qs = qs.filter(cycle_type=cycle_type)
        return qs.order_by('-started_at')
    
    @action(detail=False, methods=['post'])
    def run_cycle(self, request):
        """Execute a feedback cycle."""
        cycle_type = request.data.get('cycle_type', 'daily')
        
        try:
            if cycle_type == '6hour_btc':
                from .services.btc_feedback_loop import BTCFeedbackLoop
                result = BTCFeedbackLoop.run()
            else:
                result = FeedbackOrchestrator.run_feedback_cycle(
                    cycle_type=cycle_type,
                    lookback_days=request.data.get('lookback_days', 1),
                    symbol=request.data.get('symbol'),
                )
            
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Feedback cycle failed: {e}")
            return Response(
                {'error': f'Feedback cycle failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get feedback cycle history."""
        limit = int(request.query_params.get('limit', 10))
        cycle_type = request.query_params.get('cycle_type')
        
        cycles = FeedbackOrchestrator.get_historical_cycles(
            limit=limit,
            cycle_type=cycle_type,
        )
        
        return Response(cycles)


class PerformanceAnalysisViewSet(viewsets.ViewSet):
    """ViewSet for performance analysis and recommendations."""
    
    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """Run comprehensive performance analysis."""
        serializer = PerformanceAnalysisInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            analysis = LearningAgent.analyze_performance(
                lookback_days=data.get('lookback_days', 30),
                symbol=data.get('symbol'),
                min_signals=data.get('min_signals', 10),
            )
            
            return Response(analysis)
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return Response(
                {'error': f'Analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """Get improvement recommendations."""
        lookback_days = int(request.query_params.get('lookback_days', 30))
        symbol = request.query_params.get('symbol')
        
        try:
            analysis = LearningAgent.analyze_performance(
                lookback_days=lookback_days,
                symbol=symbol,
                min_signals=5,
            )
            
            recommendations = LearningAgent.generate_improvement_recommendations(analysis)
            
            return Response({
                'recommendations': recommendations,
                'analysis_status': analysis.get('status'),
                'overall_metrics': analysis.get('overall'),
            })
        except Exception as e:
            logger.error(f"Recommendations failed: {e}")
            return Response(
                {'error': 'Failed to generate recommendations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def insights(self, request):
        """Get all learning insights."""
        limit = int(request.query_params.get('limit', 20))
        insight_type = request.query_params.get('type')
        
        insights = FeedbackOrchestrator.get_learning_insights(
            limit=limit,
            insight_type=insight_type,
        )
        
        return Response(insights)
    
    @action(detail=False, methods=['get'])
    def memories(self, request):
        """Get market memories."""
        symbol = request.query_params.get('symbol')
        limit = int(request.query_params.get('limit', 50))
        
        memories = FeedbackOrchestrator.get_market_memories(
            symbol=symbol,
            limit=limit,
        )
        
        return Response(memories)

    @action(detail=False, methods=['get'], url_path='results/performance')
    def results_performance(self, request):
        """Get performance metrics for a given lookback period."""
        days = int(request.query_params.get('days', 30))
        symbol = request.query_params.get('symbol')

        try:
            analysis = LearningAgent.analyze_performance(
                lookback_days=days,
                symbol=symbol,
                min_signals=1,
            )

            if analysis.get('status') == 'complete':
                overall = analysis.get('overall', {})
                return Response({
                    'win_rate': overall.get('win_rate', 0),
                    'total_signals': overall.get('total_signals', 0),
                    'avg_return': overall.get('avg_return', 0),
                    'profit_factor': overall.get('profit_factor', 0),
                    'sharpe_ratio': overall.get('sharpe_ratio', 0),
                    'factor_analysis': analysis.get('factor_analysis', {}),
                    'insights': analysis.get('insights', []),
                    'days': days,
                })
            else:
                # Return default metrics when no signal data exists
                return Response({
                    'win_rate': 0,
                    'total_signals': 0,
                    'avg_return': 0,
                    'profit_factor': 0,
                    'sharpe_ratio': 0,
                    'factor_analysis': {},
                    'insights': [],
                    'days': days,
                    'status': 'no_data',
                })
        except Exception as e:
            logger.error(f"Performance metrics failed: {e}")
            return Response({
                'win_rate': 0,
                'total_signals': 0,
                'avg_return': 0,
                'profit_factor': 0,
                'sharpe_ratio': 0,
                'factor_analysis': {},
                'insights': [],
                'days': days,
                'status': 'error',
                'error': str(e),
            })
