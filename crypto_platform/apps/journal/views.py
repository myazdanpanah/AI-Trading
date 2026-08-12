"""Journal API views."""
import time
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from .models import JournalEntry, JournalInsight, MarketContext, NewsSource
from .serializers import (
    JournalEntrySerializer, JournalEntryCreateSerializer,
    JournalInsightSerializer, MarketContextSerializer,
    NewsSourceSerializer,
)
from .services.journal_writer import (
    generate_journal_entry,
    fetch_fear_greed_index,
    fetch_news_headlines,
    get_user_news_sources,
)


class NewsSourceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing news sources."""
    serializer_class = NewsSourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NewsSource.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def seed_defaults(self, request):
        """Seed default news sources for the user."""
        from .services.journal_writer import DEFAULT_NEWS_FEEDS

        created = 0
        for key, source_data in DEFAULT_NEWS_FEEDS.items():
            obj, was_created = NewsSource.objects.get_or_create(
                user=request.user,
                name=source_data['name'],
                defaults={
                    'url': source_data['url'],
                    'source_type': 'rss',
                    'category': source_data.get('category', 'crypto_news'),
                    'icon': source_data.get('icon', '📰'),
                    'reliability_score': 70,
                    'is_active': True,
                    'tags': [source_data.get('category', 'crypto_news')],
                }
            )
            if was_created:
                created += 1

        return Response({
            'message': f'Created {created} default news sources',
            'total': NewsSource.objects.filter(user=request.user).count(),
        })

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get available source categories."""
        from .models import NewsSource
        categories = dict(NewsSource.CATEGORIES)
        return Response(categories)


class JournalEntryViewSet(viewsets.ModelViewSet):
    """ViewSet for Journal entries with AI generation."""
    queryset = JournalEntry.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return JournalEntryCreateSerializer
        return JournalEntrySerializer

    def get_queryset(self):
        queryset = JournalEntry.objects.filter(user=self.request.user)
        entry_type = self.request.query_params.get('type')
        symbol = self.request.query_params.get('symbol')
        if entry_type:
            queryset = queryset.filter(entry_type=entry_type)
        if symbol:
            queryset = queryset.filter(symbols_analyzed__contains=[symbol])
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a new journal entry using AI analysis."""
        start = time.time()

        # Get analysis data from request or fetch fresh
        analysis_data = request.data.get('analysis_data')
        entry_type = request.data.get('entry_type', 'market_analysis')
        symbol = request.data.get('symbol', 'BTC')

        if not analysis_data:
            # Fetch fresh analysis
            from apps.trading_skills.services.skills_engine import (
                calculate_btc_trend, calculate_alt_breadth,
                calculate_dominance_regime, calculate_funding_regime,
                calculate_drawdown_vol, calculate_momentum_thrust,
                calculate_composite_score, calculate_exposure_posture,
                analyze_technical, calculate_position_size,
            )
            from apps.market.services.unified_data import fetch_market_data
            from apps.technical_analysis.services.indicator_engine import IndicatorEngine

            try:
                market = fetch_market_data(symbol.upper())
                closes = market['closes']
                highs = market['highs']
                lows = market['lows']
                volumes = market['volumes']

                btc_trend = calculate_btc_trend(closes)
                components = {
                    'btc_trend': btc_trend,
                    'alt_breadth': calculate_alt_breadth({}),
                    'dominance': calculate_dominance_regime([54]*31, btc_trend.get('score', 50) >= 60),
                    'funding': calculate_funding_regime({f'{symbol.upper()}USDT': 0.0001}),
                    'drawdown_vol': calculate_drawdown_vol(closes),
                    'momentum_thrust': calculate_momentum_thrust({symbol: closes}),
                }
                composite = calculate_composite_score(components)
                exposure = calculate_exposure_posture({'composite': composite})
                technical = analyze_technical(closes, highs, lows)
                all_ind = IndicatorEngine.calculate_all_indicators(
                    [{'close': c, 'high': h, 'low': l, 'volume': v}
                     for c, h, l, v in zip(closes, highs, lows, volumes)]
                )

                entry = 64000
                sl = entry * 0.98
                position = calculate_position_size(10000, 0.02, entry, sl)

                regime_score = composite.get('score', 50) or 50
                tech_score = technical.get('overall_score', 50)
                final = regime_score * 0.5 + tech_score * 0.5
                verdict = 'HOLD' if 40 <= final < 60 else 'BUY' if final >= 60 else 'SELL' if final < 40 else 'HOLD'

                analysis_data = {
                    'symbol': symbol.upper(),
                    'current_price': closes[-1],
                    'data_points': len(closes),
                    'regime': {'components': {}, 'composite': composite, 'exposure': exposure},
                    'technical': {**technical, 'vwap': all_ind.get('vwap', {}), 'ichimoku': all_ind.get('ichimoku', {})},
                    'position': {**position, 'stop_loss': sl, 'take_profits': [{'level': 'TP1', 'price': entry * 1.02, 'pct': 2.0}]},
                    'verdict': {
                        'signal': verdict,
                        'regime_score': regime_score,
                        'technical_score': tech_score,
                        'combined_score': final,
                        'posture': exposure['posture'],
                        'max_exposure': exposure['max_exposure'],
                    },
                }
            except Exception as e:
                return Response({'error': f'Failed to generate analysis: {str(e)}'},
                              status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Generate journal entry (with user's configured sources)
        result = generate_journal_entry(analysis_data, entry_type, user=request.user)

        # Save to database
        entry_data = result['entry']
        entry = JournalEntry.objects.create(
            user=request.user,
            **entry_data
        )

        # Save market context
        MarketContext.objects.create(entry=entry, **result['context'])

        return Response({
            'entry': JournalEntrySerializer(entry).data,
            'sources_used': result['sources_used'],
            'execution_time_ms': result['execution_time_ms'],
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest journal entries."""
        limit = int(request.query_params.get('limit', 10))
        entries = JournalEntry.objects.filter(user=request.user)[:limit]
        return Response(JournalEntrySerializer(entries, many=True).data)

    @action(detail=False, methods=['get'])
    def sentiment_trend(self, request):
        """Get sentiment trend over time."""
        entries = JournalEntry.objects.filter(
            user=request.user,
            market_sentiment__in=['very_bullish', 'bullish', 'neutral', 'bearish', 'very_bearish']
        )[:30]

        sentiment_map = {
            'very_bullish': 100, 'bullish': 75,
            'neutral': 50, 'bearish': 25, 'very_bearish': 0,
        }

        trend = []
        for entry in entries:
            trend.append({
                'date': entry.created_at.isoformat(),
                'sentiment': sentiment_map.get(entry.market_sentiment, 50),
                'score': entry.composite_score,
                'title': entry.title,
                'sources': entry.sources_used,
            })

        return Response(trend)


class JournalInsightViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Journal insights."""
    queryset = JournalInsight.objects.all()
    serializer_class = JournalInsightSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def market_context_current(request):
    """Get current market context for journal."""
    fear_greed = fetch_fear_greed_index()
    news = fetch_news_headlines(user=request.user, limit=8)

    return Response({
        'fear_greed': fear_greed,
        'recent_news': news,
        'sources_used': list(set([n['source'] for n in news])),
        'timestamp': time.time(),
    })
