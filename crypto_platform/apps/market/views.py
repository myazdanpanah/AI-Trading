"""Market API views."""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from .models import Candle, OrderBook, DerivativesData, TradingPair
from .serializers import CandleSerializer, OrderBookSerializer, DerivativesDataSerializer


class CandleViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for candle data."""
    queryset = Candle.objects.all()
    serializer_class = CandleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['symbol', 'timeframe']

    def get_queryset(self):
        queryset = Candle.objects.all()
        symbol = self.request.query_params.get('symbol')
        timeframe = self.request.query_params.get('timeframe')
        if symbol:
            queryset = queryset.filter(symbol=symbol)
        if timeframe:
            queryset = queryset.filter(timeframe=timeframe)
        return queryset.order_by('-timestamp')[:500]


class OrderBookViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for order book data."""
    queryset = OrderBook.objects.all()
    serializer_class = OrderBookSerializer
    permission_classes = [permissions.IsAuthenticated]


class DerivativesDataViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for derivatives data."""
    queryset = DerivativesData.objects.all()
    serializer_class = DerivativesDataSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def data_source_status(request):
    """Get status of data sources (Binance vs CoinGecko)."""
    from .services.unified_data import get_data_source_info
    return Response(get_data_source_info())


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def quick_ticker(request):
    """Get quick ticker for a symbol using unified data service."""
    symbol = request.query_params.get('symbol', 'BTC')
    try:
        from .services.unified_data import fetch_ticker
        ticker = fetch_ticker(symbol)
        return Response(ticker)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
