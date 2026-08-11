"""Sentiment Intelligence models."""
import uuid
from django.db import models


class SocialSentiment(models.Model):
    """Social media sentiment data."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    platform = models.CharField(
        max_length=20,
        choices=[
            ('twitter', 'Twitter/X'),
            ('reddit', 'Reddit'),
            ('telegram', 'Telegram'),
            ('discord', 'Discord'),
            ('youtube', 'YouTube'),
            ('tiktok', 'TikTok'),
        ]
    )
    sentiment_score = models.FloatField(default=0, help_text='Sentiment score -1 to 1')
    sentiment_label = models.CharField(
        max_length=20,
        choices=[
            ('very_bearish', 'Very Bearish'),
            ('bearish', 'Bearish'),
            ('neutral', 'Neutral'),
            ('bullish', 'Bullish'),
            ('very_bullish', 'Very Bullish'),
        ]
    )
    volume = models.IntegerField(default=0, help_text='Number of mentions')
    engagement = models.IntegerField(default=0, help_text='Total engagement (likes, shares, comments)')
    top_posts = models.JSONField(default=list, help_text='Top posts by engagement')
    keywords = models.JSONField(default=list, help_text='Trending keywords')
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Social sentiment'
        verbose_name_plural = 'Social sentiments'
        db_table = 'social_sentiments'
        unique_together = ['symbol', 'platform', 'timestamp']
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.symbol} {self.platform} - {self.sentiment_label}"


class FearGreedIndex(models.Model):
    """Crypto Fear & Greed Index."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    value = models.IntegerField(default=50, help_text='Index value 0-100')
    label = models.CharField(
        max_length=20,
        choices=[
            ('extreme_fear', 'Extreme Fear'),
            ('fear', 'Fear'),
            ('neutral', 'Neutral'),
            ('greed', 'Greed'),
            ('extreme_greed', 'Extreme Greed'),
        ]
    )
    volatility = models.FloatField(default=0, help_text='Market volatility component')
    momentum = models.FloatField(default=0, help_text='Market momentum component')
    social_media = models.FloatField(default=0, help_text='Social media component')
    dominance = models.FloatField(default=0, help_text='BTC dominance component')
    trends = models.FloatField(default=0, help_text='Google Trends component')
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Fear & Greed Index'
        verbose_name_plural = 'Fear & Greed Indices'
        db_table = 'fear_greed_index'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Fear & Greed: {self.value} - {self.label}"


class WhaleActivity(models.Model):
    """Whale transaction tracking."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    whale_type = models.CharField(
        max_length=20,
        choices=[
            ('exchange_whale', 'Exchange Whale'),
            ('accumulation_whale', 'Accumulation Whale'),
            ('distribution_whale', 'Distribution Whale'),
            ('mining_whale', 'Mining Whale'),
            ('institutional', 'Institutional'),
        ]
    )
    wallet_address = models.CharField(max_length=100)
    balance_change = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    balance_before = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    balance_after = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    transaction_count = models.IntegerField(default=1)
    usd_value = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    sentiment_impact = models.CharField(
        max_length=20,
        choices=[
            ('bullish', 'Bullish'),
            ('bearish', 'Bearish'),
            ('neutral', 'Neutral'),
        ],
        default='neutral'
    )
    confidence = models.FloatField(default=0.5, help_text='Confidence score 0-1')
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Whale activity'
        verbose_name_plural = 'Whale activities'
        db_table = 'whale_activities'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.symbol} {self.whale_type} - {self.usd_value}"


class InfluencerSentiment(models.Model):
    """Crypto influencer sentiment tracking."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    influencer_name = models.CharField(max_length=100)
    platform = models.CharField(
        max_length=20,
        choices=[
            ('twitter', 'Twitter/X'),
            ('youtube', 'YouTube'),
            ('telegram', 'Telegram'),
            ('discord', 'Discord'),
        ]
    )
    followers = models.IntegerField(default=0)
    credibility_score = models.FloatField(default=0.5, help_text='Credibility score 0-1')
    sentiment_score = models.FloatField(default=0, help_text='Sentiment score -1 to 1')
    sentiment_label = models.CharField(
        max_length=20,
        choices=[
            ('very_bearish', 'Very Bearish'),
            ('bearish', 'Bearish'),
            ('neutral', 'Neutral'),
            ('bullish', 'Bullish'),
            ('very_bullish', 'Very Bullish'),
        ]
    )
    mentioned_symbols = models.JSONField(default=list, help_text='Symbols mentioned')
    post_content = models.TextField(blank=True)
    engagement = models.IntegerField(default=0)
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Influencer sentiment'
        verbose_name_plural = 'Influencer sentiments'
        db_table = 'influencer_sentiments'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.influencer_name} - {self.sentiment_label}"


class MarketSentimentAggregated(models.Model):
    """Aggregated market sentiment across all sources."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    overall_score = models.FloatField(default=0, help_text='Overall sentiment -1 to 1')
    overall_label = models.CharField(
        max_length=20,
        choices=[
            ('very_bearish', 'Very Bearish'),
            ('bearish', 'Bearish'),
            ('neutral', 'Neutral'),
            ('bullish', 'Bullish'),
            ('very_bullish', 'Very Bullish'),
        ]
    )
    social_score = models.FloatField(default=0, help_text='Social media sentiment')
    news_score = models.FloatField(default=0, help_text='News sentiment')
    whale_score = models.FloatField(default=0, help_text='Whale activity sentiment')
    influencer_score = models.FloatField(default=0, help_text='Influencer sentiment')
    fear_greed_value = models.IntegerField(default=50, help_text='Fear & Greed index')
    confidence = models.FloatField(default=0.5, help_text='Confidence in aggregated score')
    data_sources = models.JSONField(default=list, help_text='Sources used for aggregation')
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Aggregated market sentiment'
        verbose_name_plural = 'Aggregated market sentiments'
        db_table = 'market_sentiment_aggregated'
        unique_together = ['symbol', 'timestamp']
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.symbol} - {self.overall_label} ({self.overall_score})"


class SentimentAlert(models.Model):
    """Sentiment-based alerts."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    alert_type = models.CharField(
        max_length=30,
        choices=[
            ('sentiment_spike', 'Sentiment Spike'),
            ('sentiment_drop', 'Sentiment Drop'),
            ('whale_movement', 'Whale Movement'),
            ('influencer_signal', 'Influencer Signal'),
            ('fear_greed_extreme', 'Fear & Greed Extreme'),
            ('volume_anomaly', 'Volume Anomaly'),
        ]
    )
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ]
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    sentiment_score = models.FloatField(default=0)
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sentiment alert'
        verbose_name_plural = 'Sentiment alerts'
        db_table = 'sentiment_alerts'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.symbol} {self.alert_type} - {self.severity}"
