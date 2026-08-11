"""News views."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import NewsSource, NewsArticle, NewsEntity
from .serializers import (
    NewsSourceSerializer, NewsArticleSerializer,
    NewsEntitySerializer
)
from .tasks import crawl_news_sources, analyze_news_batch


class NewsSourceViewSet(viewsets.ModelViewSet):
    """Manage news sources."""
    queryset = NewsSource.objects.all()
    serializer_class = NewsSourceSerializer
    filterset_fields = ['source_type', 'is_active']
    search_fields = ['name']

    @action(detail=False, methods=['post'])
    def trigger_crawl(self, request):
        """Trigger news crawl."""
        task = crawl_news_sources.delay()
        return Response({
            'task_id': task.id,
            'message': 'News crawl started'
        }, status=status.HTTP_202_ACCEPTED)


class NewsArticleViewSet(viewsets.ModelViewSet):
    """Manage news articles."""
    queryset = NewsArticle.objects.select_related('source').prefetch_related('entities').all()
    serializer_class = NewsArticleSerializer
    filterset_fields = ['sentiment', 'language', 'source']
    search_fields = ['title', 'content']
    ordering_fields = ['published_at', 'impact_score']
    ordering = ['-published_at']

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest news articles."""
        limit = int(request.query_params.get('limit', 20))
        articles = NewsArticle.objects.select_related('source').order_by('-published_at')[:limit]
        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_sentiment(self, request):
        """Get articles filtered by sentiment."""
        sentiment = request.query_params.get('sentiment', 'all')
        limit = int(request.query_params.get('limit', 20))

        queryset = NewsArticle.objects.select_related('source')
        if sentiment != 'all':
            queryset = queryset.filter(sentiment=sentiment)

        articles = queryset.order_by('-impact_score')[:limit]
        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def high_impact(self, request):
        """Get high impact news."""
        min_impact = int(request.query_params.get('min_impact', 70))
        limit = int(request.query_params.get('limit', 20))

        articles = NewsArticle.objects.select_related('source').filter(
            impact_score__gte=min_impact
        ).order_by('-impact_score')[:limit]

        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """Trigger analysis for articles."""
        article_ids = request.data.get('article_ids')
        task = analyze_news_batch.delay(article_ids)
        return Response({
            'task_id': task.id,
            'message': 'Analysis started'
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['get'])
    def sentiment_summary(self, request):
        """Get sentiment summary."""
        from .services.analyzer import NewsAnalyzer
        import asyncio

        hours = int(request.query_params.get('hours', 24))
        analyzer = NewsAnalyzer()
        result = asyncio.run(analyzer.get_sentiment_summary(hours))
        return Response(result)


class NewsEntityViewSet(viewsets.ModelViewSet):
    """Manage news entities."""
    queryset = NewsEntity.objects.select_related('article').all()
    serializer_class = NewsEntitySerializer
    filterset_fields = ['entity_type', 'sentiment']
    search_fields = ['name']
