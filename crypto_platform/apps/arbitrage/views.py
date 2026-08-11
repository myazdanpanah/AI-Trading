"""Arbitrage views."""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ArbitrageOpportunity, ArbitrageConfig, ArbitrageExecution
from .serializers import ArbitrageOpportunitySerializer, ArbitrageConfigSerializer, ArbitrageExecutionSerializer
from .services.detector import ArbitrageDetector


class ArbitrageOpportunityViewSet(viewsets.ModelViewSet):
    """API endpoint for arbitrage opportunities."""
    serializer_class = ArbitrageOpportunitySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ArbitrageOpportunity.objects.all()
    
    def get_queryset(self):
        queryset = ArbitrageOpportunity.objects.all()
        
        # Filter by symbol
        symbol = self.request.query_params.get('symbol')
        if symbol:
            queryset = queryset.filter(symbol=symbol)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by minimum spread
        min_spread = self.request.query_params.get('min_spread')
        if min_spread:
            queryset = queryset.filter(spread_percent__gte=min_spread)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active arbitrage opportunities."""
        opportunities = ArbitrageOpportunity.objects.filter(status='active')
        serializer = self.get_serializer(opportunities, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def scan(self, request):
        """Trigger a scan for new arbitrage opportunities."""
        # In production, this would fetch real prices from exchanges
        detector = ArbitrageDetector()
        
        # Mock prices for demonstration
        mock_prices = {
            'binance': {
                'BTC/USDT': {'bid': 67450, 'ask': 67460, 'volume': 50000},
                'ETH/USDT': {'bid': 3440, 'ask': 3445, 'volume': 100000},
            },
            'bybit': {
                'BTC/USDT': {'bid': 67500, 'ask': 67510, 'volume': 30000},
                'ETH/USDT': {'bid': 3455, 'ask': 3460, 'volume': 80000},
            },
            'okx': {
                'BTC/USDT': {'bid': 67480, 'ask': 67490, 'volume': 40000},
                'ETH/USDT': {'bid': 3450, 'ask': 3455, 'volume': 90000},
            },
        }
        
        opportunities = detector.find_opportunities(mock_prices)
        
        # Save opportunities
        saved = []
        for opp in opportunities:
            opp_obj, _ = ArbitrageOpportunity.objects.update_or_create(
                symbol=opp['symbol'],
                buy_exchange=opp['buy_exchange'],
                sell_exchange=opp['sell_exchange'],
                defaults={
                    'buy_price': opp['buy_price'],
                    'sell_price': opp['sell_price'],
                    'spread_percent': opp['spread_percent'],
                    'estimated_profit_usd': opp['estimated_profit_usd'],
                    'volume_available': opp['volume_available'],
                    'net_profit_percent': opp['net_profit_percent'],
                    'risk_score': opp['risk_score'],
                    'status': 'active',
                }
            )
            saved.append(opp_obj)
        
        serializer = self.get_serializer(saved, many=True)
        return Response(serializer.data)


class ArbitrageConfigViewSet(viewsets.ModelViewSet):
    """API endpoint for arbitrage configuration."""
    serializer_class = ArbitrageConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ArbitrageConfig.objects.all()


class ArbitrageExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for arbitrage execution history."""
    serializer_class = ArbitrageExecutionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ArbitrageExecution.objects.all()
