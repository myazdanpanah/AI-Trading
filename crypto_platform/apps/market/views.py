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


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def candles(request):
    """Get OHLCV candle data for a symbol."""
    symbol = request.query_params.get('symbol', 'BTC')
    days = int(request.query_params.get('days', 60))
    try:
        from .services.unified_data import fetch_market_data
        data = fetch_market_data(symbol)
        closes = data['closes']
        highs = data['highs']
        lows = data['lows']
        volumes = data['volumes']
        # Limit to requested days
        n = min(days, len(closes))
        candle_list = []
        from datetime import datetime, timedelta
        now = datetime.now()
        for i in range(n):
            idx = len(closes) - n + i
            dt = now - timedelta(days=n - i - 1)
            candle_list.append({
                'date': dt.strftime('%b %d'),
                'timestamp': dt.isoformat(),
                'open': closes[idx] if idx > 0 else closes[idx],
                'high': highs[idx],
                'low': lows[idx],
                'close': closes[idx],
                'volume': volumes[idx] if idx < len(volumes) else 0,
            })
        return Response({
            'symbol': symbol,
            'source': data.get('source', 'unknown'),
            'candles': candle_list,
            'current_price': closes[-1] if closes else 0,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
