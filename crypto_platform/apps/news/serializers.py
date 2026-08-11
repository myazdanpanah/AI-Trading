"""News serializers."""
from rest_framework import serializers
from .models import NewsSource, NewsArticle, NewsEntity


class NewsSourceSerializer(serializers.ModelSerializer):
    article_count = serializers.SerializerMethodField()

    class Meta:
        model = NewsSource
        fields = '__all__'

    def get_article_count(self, obj):
        return obj.articles.count() if hasattr(obj, 'articles') else 0


class NewsEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsEntity
        fields = '__all__'


class NewsArticleSerializer(serializers.ModelSerializer):
    entities = NewsEntitySerializer(many=True, read_only=True)
    source_name = serializers.CharField(source='source.name', read_only=True)
    age_hours = serializers.SerializerMethodField()

    class Meta:
        model = NewsArticle
        fields = [
            'id', 'title', 'content', 'url', 'source', 'source_name',
            'author', 'language', 'published_at', 'sentiment',
            'impact_score', 'ai_summary', 'entities', 'age_hours',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_age_hours(self, obj):
        from datetime import datetime
        if obj.published_at:
            delta = datetime.now() - obj.published_at.replace(tzinfo=None)
            return round(delta.total_seconds() / 3600, 1)
        return None


class NewsAnalysisSerializer(serializers.Serializer):
    """Serializer for news analysis requests."""
    hours = serializers.IntegerField(default=24, min_value=1, max_value=168)
    sentiment = serializers.ChoiceField(
        choices=['bullish', 'bearish', 'neutral', 'all'],
        default='all'
    )
    min_impact = serializers.IntegerField(default=0, min_value=0, max_value=100)
