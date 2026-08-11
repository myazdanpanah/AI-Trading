"""Sentiment Intelligence serializers."""
from rest_framework import serializers
from .models import (
    SocialSentiment, FearGreedIndex, WhaleActivity,
    InfluencerSentiment, MarketSentimentAggregated, SentimentAlert
)


class SocialSentimentSerializer(serializers.ModelSerializer):
    """Serializer for Social Sentiment."""
    class Meta:
        model = SocialSentiment
        fields = '__all__'


class FearGreedIndexSerializer(serializers.ModelSerializer):
    """Serializer for Fear & Greed Index."""
    class Meta:
        model = FearGreedIndex
        fields = '__all__'


class WhaleActivitySerializer(serializers.ModelSerializer):
    """Serializer for Whale Activity."""
    class Meta:
        model = WhaleActivity
        fields = '__all__'


class InfluencerSentimentSerializer(serializers.ModelSerializer):
    """Serializer for Influencer Sentiment."""
    class Meta:
        model = InfluencerSentiment
        fields = '__all__'


class MarketSentimentAggregatedSerializer(serializers.ModelSerializer):
    """Serializer for Aggregated Market Sentiment."""
    class Meta:
        model = MarketSentimentAggregated
        fields = '__all__'


class SentimentAlertSerializer(serializers.ModelSerializer):
    """Serializer for Sentiment Alert."""
    class Meta:
        model = SentimentAlert
        fields = '__all__'


class SentimentAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for sentiment analysis request."""
    symbol = serializers.CharField(max_length=20)
    include_social = serializers.BooleanField(default=True)
    include_fear_greed = serializers.BooleanField(default=True)
    include_whale = serializers.BooleanField(default=True)
    include_influencer = serializers.BooleanField(default=True)
    time_range = serializers.ChoiceField(
        choices=['1h', '4h', '24h', '7d', '30d'],
        default='24h'
    )
