"""Technical Analysis views."""
import asyncio
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (
    TechnicalIndicator, TechnicalPattern, SupportResistance,
    TrendAnalysis, SmartMoneyEvent, TechnicalAnalysisResult
)
from .serializers import (
    TechnicalIndicatorSerializer, TechnicalPatternSerializer,
    SupportResistanceSerializer, TrendAnalysisSerializer,
    SmartMoneyEventSerializer, TechnicalAnalysisResultSerializer,
    AnalysisRequestSerializer
)
from .services.indicator_engine import IndicatorEngine
from .services.pattern_detector import PatternDetector
from .services.sr_analyzer import SRAnalyzer
from .services.trend_analyzer import TrendAnalyzer
from .services.smart_money import SmartMoneyAnalyzer

logger = logging.getLogger(__name__)


class TechnicalIndicatorViewSet(viewsets.ModelViewSet):
    """Manage Technical Indicators."""
    queryset = TechnicalIndicator.objects.all()
    serializer_class = TechnicalIndicatorSerializer
    filterset_fields = ['symbol', 'timeframe', 'indicator_type', 'signal']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest indicators for a symbol."""
        symbol = request.query_params.get('symbol')
        timeframe = request.query_params.get('timeframe', '1h')

        if not symbol:
            return Response(
                {'error': 'symbol parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        indicators = TechnicalIndicator.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by('-timestamp')[:20]

        serializer = self.get_serializer(indicators, many=True)
        return Response(serializer.data)


class TechnicalPatternViewSet(viewsets.ModelViewSet):
    """Manage Technical Patterns."""
    queryset = TechnicalPattern.objects.all()
    serializer_class = TechnicalPatternSerializer
    filterset_fields = ['symbol', 'timeframe', 'pattern_type', 'direction']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class SupportResistanceViewSet(viewsets.ModelViewSet):
    """Manage Support/Resistance levels."""
    queryset = SupportResistance.objects.all()
    serializer_class = SupportResistanceSerializer
    filterset_fields = ['symbol', 'timeframe', 'level_type']

    @action(detail=False, methods=['get'])
    def levels(self, request):
        """Get S/R levels for a symbol."""
        symbol = request.query_params.get('symbol')
        timeframe = request.query_params.get('timeframe', '1h')

        if not symbol:
            return Response(
                {'error': 'symbol parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        levels = SupportResistance.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by('price')

        serializer = self.get_serializer(levels, many=True)
        return Response(serializer.data)


class TrendAnalysisViewSet(viewsets.ModelViewSet):
    """Manage Trend Analysis."""
    queryset = TrendAnalysis.objects.all()
    serializer_class = TrendAnalysisSerializer
    filterset_fields = ['symbol', 'timeframe', 'trend_direction']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current trend for a symbol."""
        symbol = request.query_params.get('symbol')
        timeframe = request.query_params.get('timeframe', '1h')

        if not symbol:
            return Response(
                {'error': 'symbol parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        trend = TrendAnalysis.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by('-timestamp').first()

        if trend:
            serializer = self.get_serializer(trend)
            return Response(serializer.data)
        return Response({'message': 'No trend data found'})


class SmartMoneyEventViewSet(viewsets.ModelViewSet):
    """Manage Smart Money Events."""
    queryset = SmartMoneyEvent.objects.all()
    serializer_class = SmartMoneyEventSerializer
    filterset_fields = ['symbol', 'event_type', 'direction']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']


class TechnicalAnalysisResultViewSet(viewsets.ModelViewSet):
    """Manage Technical Analysis Results."""
    queryset = TechnicalAnalysisResult.objects.all()
    serializer_class = TechnicalAnalysisResultSerializer
    filterset_fields = ['symbol', 'timeframe', 'overall_signal']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest analysis result for a symbol."""
        symbol = request.query_params.get('symbol')
        timeframe = request.query_params.get('timeframe', '1h')

        if not symbol:
            return Response(
                {'error': 'symbol parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = TechnicalAnalysisResult.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by('-timestamp').first()

        if result:
            serializer = self.get_serializer(result)
            return Response(serializer.data)
        return Response({'message': 'No analysis result found'})


class AnalysisViewSet(viewsets.ViewSet):
    """Run technical analysis on market data."""

    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """Run full technical analysis."""
        serializer = AnalysisRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        symbol = data['symbol']
        timeframe = data['timeframe']

        # Get candle data (would come from market app in production)
        # For now, use placeholder data
        candle_data = self._get_candle_data(symbol, timeframe)

        if not candle_data:
            return Response(
                {'error': f'No candle data found for {symbol}'},
                status=status.HTTP_404_NOT_FOUND
            )

        results = {}

        # Calculate indicators
        if data.get('indicators'):
            closes = [float(c['close']) for c in candle_data]
            highs = [float(c['high']) for c in candle_data]
            lows = [float(c['low']) for c in candle_data]

            indicators = {}
            for indicator in data['indicators']:
                if indicator == 'rsi':
                    indicators['rsi'] = IndicatorEngine.calculate_rsi(closes)
                elif indicator == 'macd':
                    indicators['macd'] = IndicatorEngine.calculate_macd(closes)
                elif indicator == 'bollinger_bands':
                    indicators['bollinger_bands'] = IndicatorEngine.calculate_bollinger_bands(closes)
                elif indicator == 'ema':
                    indicators['ema_9'] = IndicatorEngine.calculate_ema(closes, 9)
                    indicators['ema_21'] = IndicatorEngine.calculate_ema(closes, 21)
                    indicators['ema_50'] = IndicatorEngine.calculate_ema(closes, 50)
                elif indicator == 'atr':
                    indicators['atr'] = IndicatorEngine.calculate_atr(highs, lows, closes)
                elif indicator == 'stochastic':
                    indicators['stochastic'] = IndicatorEngine.calculate_stochastic(highs, lows, closes)

            results['indicators'] = indicators

        # Detect patterns
        if data.get('include_patterns'):
            highs = [float(c['high']) for c in candle_data]
            lows = [float(c['low']) for c in candle_data]
            closes = [float(c['close']) for c in candle_data]
            volumes = [float(c['volume']) for c in candle_data]

            patterns = PatternDetector.detect_all_patterns(highs, lows, closes, volumes)
            results['patterns'] = patterns

        # Analyze S/R
        if data.get('include_sr'):
            highs = [float(c['high']) for c in candle_data]
            lows = [float(c['low']) for c in candle_data]
            closes = [float(c['close']) for c in candle_data]

            sr_levels = SRAnalyzer.find_support_resistance_levels(highs, lows, closes)
            results['support_resistance'] = sr_levels

        # Analyze trend
        if data.get('include_trend'):
            highs = [float(c['high']) for c in candle_data]
            lows = [float(c['low']) for c in candle_data]
            closes = [float(c['close']) for c in candle_data]

            trend = TrendAnalyzer.analyze_trend(highs, lows, closes)
            results['trend'] = trend

        # Analyze smart money
        if data.get('include_smart_money'):
            highs = [float(c['high']) for c in candle_data]
            lows = [float(c['low']) for c in candle_data]
            closes = [float(c['close']) for c in candle_data]
            volumes = [float(c['volume']) for c in candle_data]

            smart_money = SmartMoneyAnalyzer.analyze_all(highs, lows, closes, volumes)
            results['smart_money'] = smart_money

        return Response({
            'symbol': symbol,
            'timeframe': timeframe,
            'analysis': results,
        })

    def _get_candle_data(self, symbol: str, timeframe: str):
        """Get candle data from market app."""
        try:
            from apps.market.models import Candle
            
            candles = Candle.objects.filter(
                symbol=symbol,
                timeframe=timeframe
            ).order_by('timestamp')[:100]
            
            if not candles.exists():
                logger.info("Using mock candle data for %s (no candles found)", symbol)
                return self._get_mock_candle_data(symbol)
            
            return [
                {
                    'timestamp': c.timestamp.isoformat(),
                    'open': str(c.open),
                    'high': str(c.high),
                    'low': str(c.low),
                    'close': str(c.close),
                    'volume': str(c.volume),
                }
                for c in candles
            ]
        except ImportError:
            logger.warning("Could not import Candle model from market app")
            return self._get_mock_candle_data(symbol)
        except Exception as e:
            logger.warning(f"Failed to fetch candle data: {e}")
            return self._get_mock_candle_data(symbol)

    def _get_mock_candle_data(self, symbol: str):
        """Fallback mock data when no real data available."""
        logger.info("Generating mock candle data for %s", symbol)
        from datetime import datetime, timedelta
        import random

        base_price = 50000 if 'BTC' in symbol.upper() else 3000
        candle_data = []

        for i in range(100):
            timestamp = datetime.now() - timedelta(hours=i)
            change = random.uniform(-0.02, 0.02)
            close = base_price * (1 + change)
            open_price = close * (1 + random.uniform(-0.01, 0.01))
            high = max(open_price, close) * (1 + random.uniform(0, 0.005))
            low = min(open_price, close) * (1 - random.uniform(0, 0.005))
            volume = random.uniform(100, 1000)

            candle_data.append({
                'timestamp': timestamp.isoformat(),
                'open': str(open_price),
                'high': str(high),
                'low': str(low),
                'close': str(close),
                'volume': str(volume),
            })

        return list(reversed(candle_data))
