"""Forecast API views."""
import logging
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .models import PriceForecast, ForecastCycle, ModelWeight
from .serializers import (
    PriceForecastSerializer, ForecastCycleSerializer, ModelWeightSerializer,
    RunForecastInputSerializer, AccuracyStatsSerializer,
)
from .services.forecaster import PriceForecaster
from .services.verifier import ForecastVerifier
from .services.learning_loop import LearningLoop

logger = logging.getLogger(__name__)


class PriceForecastViewSet(viewsets.ReadOnlyModelViewSet):
    """View price forecasts."""
    queryset = PriceForecast.objects.all()
    serializer_class = PriceForecastSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = PriceForecast.objects.all()
        symbol = self.request.query_params.get('symbol')
        status_filter = self.request.query_params.get('status')
        
        if symbol:
            queryset = queryset.filter(symbol=symbol)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset[:100]


class ForecastCycleViewSet(viewsets.ReadOnlyModelViewSet):
    """View forecast cycles."""
    queryset = ForecastCycle.objects.all()
    serializer_class = ForecastCycleSerializer
    permission_classes = [permissions.IsAuthenticated]


class ModelWeightViewSet(viewsets.ReadOnlyModelViewSet):
    """View model weights."""
    queryset = ModelWeight.objects.all()
    serializer_class = ModelWeightSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def run_forecast(request):
    """Trigger a new forecast cycle."""
    serializer = RunForecastInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    symbols = serializer.validated_data.get('symbols', ['BTC', 'ETH', 'SOL', 'BNB', 'XRP'])
    
    result = PriceForecaster.run_forecast_cycle(symbols)
    
    if result['status'] == 'success':
        return Response(result, status=status.HTTP_201_CREATED)
    else:
        return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_forecasts(request):
    """Verify pending forecasts against real data."""
    result = ForecastVerifier.verify_pending_forecasts()
    return Response(result)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def run_learning_cycle(request):
    """Run a learning cycle to adjust model weights."""
    result = LearningLoop.run_learning_cycle()
    return Response(result)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def accuracy_stats(request):
    """Get accuracy statistics for forecasts."""
    symbol = request.query_params.get('symbol')
    days = int(request.query_params.get('days', 30))
    
    stats = ForecastVerifier.get_accuracy_stats(symbol=symbol, days=days)
    return Response(stats)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def learning_stats(request):
    """Get learning statistics and weight history."""
    symbol = request.query_params.get('symbol')
    stats = LearningLoop.get_learning_stats(symbol=symbol)
    return Response(stats)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reset_weights(request):
    """Reset model weights to defaults."""
    symbol = request.data.get('symbol')
    LearningLoop.reset_weights(symbol=symbol)
    return Response({'status': 'success', 'message': 'Weights reset to defaults'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def run_full_cycle(request):
    """
    Run complete forecast-verify-learn cycle.
    This is the main endpoint called every 6 hours.
    """
    import time
    start = time.time()
    
    # 1. Run forecasts
    forecast_result = PriceForecaster.run_forecast_cycle()
    
    # 2. Verify old forecasts
    verify_result = ForecastVerifier.verify_pending_forecasts()
    
    # 3. Run learning
    learn_result = LearningLoop.run_learning_cycle()
    
    return Response({
        'status': 'success',
        'forecast': forecast_result,
        'verification': verify_result,
        'learning': learn_result,
        'total_time_ms': int((time.time() - start) * 1000),
    })
