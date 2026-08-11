"""Market views."""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Exchange, TradingPair, Candle, OrderBook, DerivativesData, WhaleAlert
from .serializers import (
    ExchangeSerializer, TradingPairSerializer, CandleSerializer,
    OrderBookSerializer, DerivativesDataSerializer, WhaleAlertSerializer
)


class ExchangeViewSet(viewsets.ModelViewSet):
    """Manage exchanges."""
    queryset = Exchange.objects.all()
    serializer_class = ExchangeSerializer
    filterset_fields = ['api_status']
    search_fields = ['name']


class TradingPairViewSet(viewsets.ModelViewSet):
    """Manage trading pairs."""
    queryset = TradingPair.objects.select_related('exchange').all()
    serializer_class = TradingPairSerializer
    filterset_fields = ['exchange', 'is_active']
    search_fields = ['symbol', 'base_asset']


class CandleViewSet(viewsets.ModelViewSet):
    """Manage candle data."""
    queryset = Candle.objects.all()
    serializer_class = CandleSerializer
    filterset_fields = ['symbol', 'timeframe']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest candles for a symbol."""
        symbol = request.query_params.get('symbol', 'BTCUSDT')
        timeframe = request.query_params.get('timeframe', '1h')
        limit = int(request.query_params.get('limit', 100))
        
        candles = Candle.objects.filter(
            symbol=symbol, timeframe=timeframe
        ).order_by('-timestamp')[:limit]
        
        serializer = self.get_serializer(candles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def symbols(self, request):
        """Get available symbols."""
        symbols = Candle.objects.values_list('symbol', flat=True).distinct()
        return Response(list(symbols))

    @action(detail=False, methods=['get'])
    def timeframes(self, request):
        """Get available timeframes."""
        timeframes = Candle.objects.values_list('timeframe', flat=True).distinct()
        return Response(list(timeframes))


class OrderBookViewSet(viewsets.ModelViewSet):
    """Manage order book data."""
    queryset = OrderBook.objects.all()
    serializer_class = OrderBookSerializer
    filterset_fields = ['symbol']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest order book for a symbol."""
        symbol = request.query_params.get('symbol', 'BTCUSDT')
        orderbook = OrderBook.objects.filter(symbol=symbol).order_by('-timestamp').first()
        if orderbook:
            serializer = self.get_serializer(orderbook)
            return Response(serializer.data)
        return Response({'error': 'No order book data found'}, status=status.HTTP_404_NOT_FOUND)


class DerivativesDataViewSet(viewsets.ModelViewSet):
    """Manage derivatives data."""
    queryset = DerivativesData.objects.all()
    serializer_class = DerivativesDataSerializer
    filterset_fields = ['symbol']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def funding_rates(self, request):
        """Get current funding rates."""
        symbol = request.query_params.get('symbol')
        queryset = DerivativesData.objects.all()
        if symbol:
            queryset = queryset.filter(symbol=symbol)
        
        # Get latest for each symbol
        from django.db.models import Max
        latest_ids = queryset.values('symbol').annotate(
            latest=Max('id')
        ).values_list('latest', flat=True)
        
        data = DerivativesData.objects.filter(id__in=latest_ids)
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)


class WhaleAlertViewSet(viewsets.ModelViewSet):
    """Manage whale alerts."""
    queryset = WhaleAlert.objects.all()
    serializer_class = WhaleAlertSerializer
    filterset_fields = ['symbol', 'transaction_type']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent whale alerts."""
        limit = int(request.query_params.get('limit', 10))
        alerts = WhaleAlert.objects.order_by('-timestamp')[:limit]
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)
