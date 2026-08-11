"""Learning views - Full CRUD + analysis endpoints."""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import SignalResult, ModelPerformance, StrategyWeight, BacktestResult
from .serializers import (
    SignalResultSerializer, ModelPerformanceSerializer,
    StrategyWeightSerializer, BacktestResultSerializer,
)
from .services import PerformanceTracker, WeightOptimizer, AccuracyImprover

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(tags=['Learning'], summary='List signal results'),
    create=extend_schema(tags=['Learning'], summary='Create signal result'),
    retrieve=extend_schema(tags=['Learning'], summary='Get signal result'),
    update=extend_schema(tags=['Learning'], summary='Update signal result'),
    partial_update=extend_schema(tags=['Learning'], summary='Partial update signal result'),
    destroy=extend_schema(tags=['Learning'], summary='Delete signal result'),
    record=extend_schema(tags=['Learning'], summary='Record a signal outcome'),
    performance=extend_schema(tags=['Learning'], summary='Get performance metrics'),
    daily=extend_schema(tags=['Learning'], summary='Get daily performance metrics'),
    by_factor=extend_schema(tags=['Learning'], summary='Get performance breakdown by factor'),
)
class SignalResultViewSet(viewsets.ModelViewSet):
    """ViewSet for SignalResult CRUD and analysis."""
    queryset = SignalResult.objects.all()
    serializer_class = SignalResultSerializer
    filterset_fields = ['success', 'market_condition']

    @action(detail=False, methods=['post'])
    def record(self, request):
        """Record a signal outcome."""
        try:
            tracker = PerformanceTracker()
            result = tracker.record_signal_outcome(
                signal_id=request.data.get('signal_id'),
                exit_price=request.data.get('exit_price'),
                profit_loss=request.data.get('profit_loss', 0),
                profit_loss_percent=request.data.get('profit_loss_percent', 0),
                success=request.data.get('success', False),
                duration_hours=request.data.get('duration_hours', 0),
                market_condition=request.data.get('market_condition', ''),
                notes=request.data.get('notes', ''),
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Failed to record signal outcome: {e}")
            return Response(
                {'error': 'Failed to record signal outcome'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def performance(self, request):
        """Get performance metrics."""
        try:
            tracker = PerformanceTracker()
            result = tracker.get_signal_performance(
                symbol=request.query_params.get('symbol'),
                timeframe=request.query_params.get('timeframe'),
            )
            return Response(result)
        except Exception as e:
            logger.error(f"Failed to get performance: {e}")
            return Response(
                {'error': 'Failed to calculate performance'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def daily(self, request):
        """Get daily performance metrics."""
        try:
            tracker = PerformanceTracker()
            days = int(request.query_params.get('days', 30))
            result = tracker.get_daily_performance(days=days)
            return Response(result)
        except Exception as e:
            logger.error(f"Failed to get daily performance: {e}")
            return Response(
                {'error': 'Failed to calculate daily performance'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def by_factor(self, request):
        """Get performance breakdown by factor."""
        try:
            tracker = PerformanceTracker()
            factor = request.query_params.get('factor', 'symbol')
            result = tracker.get_performance_by_factor(factor=factor)
            return Response(result)
        except Exception as e:
            logger.error(f"Failed to get factor performance: {e}")
            return Response(
                {'error': 'Failed to calculate factor performance'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema_view(
    list=extend_schema(tags=['Learning'], summary='List model performance records'),
    create=extend_schema(tags=['Learning'], summary='Create model performance record'),
    retrieve=extend_schema(tags=['Learning'], summary='Get model performance record'),
    update=extend_schema(tags=['Learning'], summary='Update model performance record'),
    partial_update=extend_schema(tags=['Learning'], summary='Partial update model performance record'),
    destroy=extend_schema(tags=['Learning'], summary='Delete model performance record'),
)
class ModelPerformanceViewSet(viewsets.ModelViewSet):
    """ViewSet for ModelPerformance CRUD."""
    queryset = ModelPerformance.objects.all()
    serializer_class = ModelPerformanceSerializer
    filterset_fields = ['model_name']


@extend_schema_view(
    list=extend_schema(tags=['Learning'], summary='List strategy weights'),
    create=extend_schema(tags=['Learning'], summary='Create strategy weight'),
    retrieve=extend_schema(tags=['Learning'], summary='Get strategy weight'),
    update=extend_schema(tags=['Learning'], summary='Update strategy weight'),
    partial_update=extend_schema(tags=['Learning'], summary='Partial update strategy weight'),
    destroy=extend_schema(tags=['Learning'], summary='Delete strategy weight'),
    optimize=extend_schema(tags=['Learning'], summary='Optimize weights based on recent performance'),
    current=extend_schema(tags=['Learning'], summary='Get current optimized weights'),
    effectiveness=extend_schema(tags=['Learning'], summary='Get weight effectiveness analysis'),
)
class StrategyWeightViewSet(viewsets.ModelViewSet):
    """ViewSet for StrategyWeight CRUD and optimization."""
    queryset = StrategyWeight.objects.all()
    serializer_class = StrategyWeightSerializer

    @action(detail=False, methods=['post'])
    def optimize(self, request):
        """Optimize weights based on recent performance."""
        try:
            optimizer = WeightOptimizer()
            window_days = int(request.data.get('window_days', 30))
            result = optimizer.optimize_weights(performance_window_days=window_days)
            return Response(result)
        except Exception as e:
            logger.error(f"Failed to optimize weights: {e}")
            return Response(
                {'error': 'Failed to optimize weights'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current optimized weights."""
        try:
            optimizer = WeightOptimizer()
            result = optimizer.get_current_weights()
            return Response(result)
        except Exception as e:
            logger.error(f"Failed to get weights: {e}")
            return Response(
                {'error': 'Failed to get weights'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def effectiveness(self, request):
        """Get weight effectiveness analysis."""
        try:
            optimizer = WeightOptimizer()
            component = request.query_params.get('component', 'technical')
            result = optimizer.calculate_weight_effectiveness(component=component)
            return Response(result)
        except Exception as e:
            logger.error(f"Failed to calculate effectiveness: {e}")
            return Response(
                {'error': 'Failed to calculate effectiveness'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BacktestResultViewSet(viewsets.ModelViewSet):
    """ViewSet for BacktestResult CRUD."""
    queryset = BacktestResult.objects.all()
    serializer_class = BacktestResultSerializer


class AccuracyAnalysisViewSet(viewsets.ViewSet):
    """ViewSet for accuracy analysis and recommendations."""

    @action(detail=False, methods=['get'])
    def patterns(self, request):
        """Analyze accuracy patterns."""
        try:
            improver = AccuracyImprover()
            lookback_days = int(request.query_params.get('lookback_days', 90))
            result = improver.analyze_accuracy_patterns(lookback_days=lookback_days)
            return Response(result)
        except Exception as e:
            logger.error(f"Failed to analyze patterns: {e}")
            return Response(
                {'error': 'Failed to analyze patterns'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """Get accuracy improvement recommendations."""
        try:
            improver = AccuracyImprover()
            result = improver.get_accuracy_recommendations()
            return Response(result)
        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return Response(
                {'error': 'Failed to get recommendations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def predict(self, request):
        """Predict signal quality."""
        try:
            improver = AccuracyImprover()
            result = improver.predict_signal_quality(signal_data=request.data)
            return Response(result)
        except Exception as e:
            logger.error(f"Failed to predict quality: {e}")
            return Response(
                {'error': 'Failed to predict quality'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
