"""Journal serializers."""
from rest_framework import serializers
from .models import JournalEntry, JournalInsight, MarketContext


class JournalInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalInsight
        fields = '__all__'


class MarketContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketContext
        fields = '__all__'


class JournalEntrySerializer(serializers.ModelSerializer):
    insights = JournalInsightSerializer(many=True, read_only=True)
    market_context = MarketContextSerializer(read_only=True)

    class Meta:
        model = JournalEntry
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


class JournalEntryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalEntry
        fields = ['entry_type', 'title', 'content', 'summary', 'symbols_analyzed',
                  'market_sentiment', 'composite_score', 'data_sources', 'news_count',
                  'indicators_used', 'ai_model', 'ai_confidence', 'ai_reasoning',
                  'key_findings', 'risks_identified', 'opportunities', 'tags']
