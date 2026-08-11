"""Sentiment Intelligence views."""
import asyncio
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (
    SocialSentiment, FearGreedIndex, WhaleActivity,
    InfluencerSentiment, MarketSentimentAggregated, SentimentAlert
)
from .serializers import (
    SocialSentimentSerializer, FearGreedIndexSerializer,
    WhaleActivitySerializer, InfluencerSentimentSerializer,
    MarketSentimentAggregatedSerializer, SentimentAlertSerializer,
    SentimentAnalysisRequestSerializer
)
from .services.social_analyzer import SocialSentimentAnalyzer
from .services.fear_greed import FearGreedAnalyzer
from .services.whale_tracker import WhaleActivityTracker
from .services.influencer_monitor import InfluencerSentimentMonitor
from .services.aggregator import SentimentAggregator

logger = logging.getLogger(__name__)


class SocialSentimentViewSet(viewsets.ModelViewSet):
    """Manage Social Sentiment data."""
    queryset = SocialSentiment.objects.all()
    serializer_class = SocialSentimentSerializer
    filterset_fields = ['symbol', 'platform', 'sentiment_label']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest sentiment for a symbol."""
        symbol = request.query_params.get('symbol')
        platform = request.query_params.get('platform')

        if not symbol:
            return Response(
                {'error': 'symbol parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        qs = SocialSentiment.objects.filter(symbol=symbol)
        if platform:
            qs = qs.filter(platform=platform)

        sentiment = qs.order_by('-timestamp').first()

        if sentiment:
            serializer = self.get_serializer(sentiment)
            return Response(serializer.data)
        return Response({'message': 'No sentiment data found'})


class FearGreedIndexViewSet(viewsets.ModelViewSet):
    """Manage Fear & Greed Index data."""
    queryset = FearGreedIndex.objects.all()
    serializer_class = FearGreedIndexSerializer
    filterset_fields = ['label']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current Fear & Greed Index."""
        index = FearGreedIndex.objects.order_by('-timestamp').first()

        if index:
            serializer = self.get_serializer(index)
            return Response(serializer.data)
        return Response({'message': 'No Fear & Greed data found'})

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get Fear & Greed history."""
        days = int(request.query_params.get('days', 30))
        limit = days * 24  # Hourly data

        indices = FearGreedIndex.objects.order_by('-timestamp')[:limit]
        serializer = self.get_serializer(indices, many=True)
        return Response(serializer.data)


class WhaleActivityViewSet(viewsets.ModelViewSet):
    """Manage Whale Activity data."""
    queryset = WhaleActivity.objects.all()
    serializer_class = WhaleActivitySerializer
    filterset_fields = ['symbol', 'whale_type', 'sentiment_impact']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest whale activities for a symbol."""
        symbol = request.query_params.get('symbol')
        limit = int(request.query_params.get('limit', 10))

        if not symbol:
            return Response(
                {'error': 'symbol parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        activities = WhaleActivity.objects.filter(
            symbol=symbol
        ).order_by('-timestamp')[:limit]

        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)


class InfluencerSentimentViewSet(viewsets.ModelViewSet):
    """Manage Influencer Sentiment data."""
    queryset = InfluencerSentiment.objects.all()
    serializer_class = InfluencerSentimentSerializer
    filterset_fields = ['platform', 'sentiment_label']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest influencer sentiments."""
        limit = int(request.query_params.get('limit', 10))

        sentiments = InfluencerSentiment.objects.order_by('-timestamp')[:limit]
        serializer = self.get_serializer(sentiments, many=True)
        return Response(serializer.data)


class MarketSentimentAggregatedViewSet(viewsets.ModelViewSet):
    """Manage Aggregated Market Sentiment."""
    queryset = MarketSentimentAggregated.objects.all()
    serializer_class = MarketSentimentAggregatedSerializer
    filterset_fields = ['symbol', 'overall_label']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest aggregated sentiment for a symbol."""
        symbol = request.query_params.get('symbol')

        if not symbol:
            return Response(
                {'error': 'symbol parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        sentiment = MarketSentimentAggregated.objects.filter(
            symbol=symbol
        ).order_by('-timestamp').first()

        if sentiment:
            serializer = self.get_serializer(sentiment)
            return Response(serializer.data)
        return Response({'message': 'No aggregated sentiment found'})


class SentimentAlertViewSet(viewsets.ModelViewSet):
    """Manage Sentiment Alerts."""
    queryset = SentimentAlert.objects.all()
    serializer_class = SentimentAlertSerializer
    filterset_fields = ['symbol', 'alert_type', 'severity', 'is_read']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread alerts."""
        symbol = request.query_params.get('symbol')

        qs = SentimentAlert.objects.filter(is_read=False)
        if symbol:
            qs = qs.filter(symbol=symbol)

        alerts = qs.order_by('-created_at')[:20]
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark an alert as read."""
        alert = self.get_object()
        alert.is_read = True
        alert.save()
        return Response({'status': 'marked as read'})


class SentimentAnalysisViewSet(viewsets.ViewSet):
    """Run comprehensive sentiment analysis."""

    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """Run full sentiment analysis."""
        serializer = SentimentAnalysisRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        symbol = data['symbol']
        results = {}

        try:
            # Analyze social sentiment
            if data.get('include_social'):
                social_data = SocialSentiment.objects.filter(
                    symbol=symbol
                ).order_by('-timestamp')[:100]

                if social_data.exists():
                    posts = [
                        {'text': s.top_posts[0].get('text', '') if s.top_posts else '',
                         'engagement': s.engagement}
                        for s in social_data
                    ]
                    social_result = SocialSentimentAnalyzer.aggregate_social_sentiment(posts)
                    results['social'] = social_result
                else:
                    results['social'] = SocialSentimentAnalyzer.aggregate_social_sentiment([])

            # Analyze Fear & Greed
            if data.get('include_fear_greed'):
                fg_index = FearGreedIndex.objects.order_by('-timestamp').first()
                if fg_index:
                    results['fear_greed'] = {
                        'value': fg_index.value,
                        'label': fg_index.label,
                    }
                else:
                    results['fear_greed'] = {'value': 50, 'label': 'neutral'}

            # Analyze whale activity
            if data.get('include_whale'):
                whale_data = WhaleActivity.objects.filter(
                    symbol=symbol
                ).order_by('-timestamp')[:20]

                whale_activities = [
                    {
                        'sentiment': w.sentiment_impact,
                        'usd_value': float(w.usd_value),
                        'transaction_type': w.whale_type,
                    }
                    for w in whale_data
                ]

                whale_result = WhaleActivityTracker.calculate_whale_score(whale_activities)
                results['whale'] = whale_result

            # Analyze influencer sentiment
            if data.get('include_influencer'):
                influencer_data = InfluencerSentiment.objects.order_by('-timestamp')[:20]

                influencer_posts = [
                    {
                        'sentiment_score': inf.sentiment_score,
                        'credibility_score': inf.credibility_score,
                        'followers': inf.followers,
                    }
                    for inf in influencer_data
                ]

                influencer_result = InfluencerSentimentMonitor.aggregate_influencer_sentiment(influencer_posts)
                results['influencer'] = influencer_result

            # Aggregate all sentiment
            aggregated = SentimentAggregator.aggregate_sentiment(
                social_sentiment=results.get('social', {}).get('sentiment_score', 0),
                news_sentiment=0,  # Would come from news app
                whale_sentiment=results.get('whale', {}).get('score', 0),
                influencer_sentiment=results.get('influencer', {}).get('score', 0),
                fear_greed_value=results.get('fear_greed', {}).get('value', 50),
            )

            results['aggregated'] = aggregated
            results['summary'] = SentimentAggregator.generate_sentiment_summary(
                aggregated,
                {'trend': 'stable'},
                None,
            )

            return Response({
                'symbol': symbol,
                'analysis': results,
            })

        except Exception as e:
            logger.error(f"Sentiment analysis failed for {symbol}: {e}", exc_info=True)
            return Response(
                {'error': 'An error occurred during sentiment analysis. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
