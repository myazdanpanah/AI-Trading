"""Journal models - AI-written analysis entries based on market interactions."""
import uuid
from django.db import models
from django.conf import settings


class NewsSource(models.Model):
    """Configurable news source for the AI to read."""
    SOURCE_TYPES = [
        ('rss', 'RSS Feed'),
        ('api', 'API'),
        ('web', 'Website'),
        ('twitter', 'Twitter/X'),
        ('reddit', 'Reddit'),
        ('telegram', 'Telegram'),
    ]

    CATEGORIES = [
        ('crypto_news', 'Crypto News'),
        ('market_data', 'Market Data'),
        ('defi', 'DeFi'),
        ('nft', 'NFT'),
        ('regulation', 'Regulation'),
        ('macro', 'Macro Economics'),
        ('on_chain', 'On-Chain Data'),
        ('social', 'Social Media'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='news_sources', null=True, blank=True)
    name = models.CharField(max_length=100)
    url = models.URLField(max_length=500)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES, default='rss')
    category = models.CharField(max_length=20, choices=CATEGORIES, default='crypto_news')
    icon = models.CharField(max_length=10, default='📰')
    reliability_score = models.IntegerField(default=50, help_text='Source reliability 0-100')
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False, help_text='Primary sources always included')
    tags = models.JSONField(default=list, help_text='Topics covered by this source')
    last_fetched = models.DateTimeField(null=True, blank=True)
    fetch_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'news source'
        verbose_name_plural = 'news sources'
        db_table = 'journal_news_sources'
        ordering = ['-reliability_score', 'name']

    def __str__(self):
        return f"{self.icon} {self.name} ({self.source_type})"


class JournalEntry(models.Model):
    """AI-generated journal entry analyzing market conditions."""
    ENTRY_TYPES = [
        ('market_analysis', 'Market Analysis'),
        ('signal_review', 'Signal Review'),
        ('news_digest', 'News Digest'),
        ('sentiment_report', 'Sentiment Report'),
        ('technical_review', 'Technical Review'),
        ('macro_outlook', 'Macro Outlook'),
        ('daily_summary', 'Daily Summary'),
        ('weekly_summary', 'Weekly Summary'),
        ('lessons_learned', 'Lessons Learned'),
    ]

    SENTIMENT_CHOICES = [
        ('very_bullish', 'Very Bullish'),
        ('bullish', 'Bullish'),
        ('neutral', 'Neutral'),
        ('bearish', 'Bearish'),
        ('very_bearish', 'Very Bearish'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='journal_entries', null=True, blank=True)
    entry_type = models.CharField(max_length=30, choices=ENTRY_TYPES, default='market_analysis')
    title = models.CharField(max_length=200)
    content = models.TextField()
    summary = models.TextField(blank=True, help_text='Brief AI summary of the entry')

    # Market context
    symbols_analyzed = models.JSONField(default=list, help_text='List of symbols discussed')
    market_sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES, default='neutral')
    composite_score = models.FloatField(default=50, help_text='Overall market score 0-100')

    # Data sources used
    data_sources = models.JSONField(default=list, help_text='Sources: news, technical, sentiment, etc.')
    sources_used = models.JSONField(default=list, help_text='Specific news sources used in this entry')
    news_count = models.IntegerField(default=0, help_text='Number of news articles analyzed')
    indicators_used = models.JSONField(default=list, help_text='Technical indicators referenced')

    # AI metadata
    ai_model = models.CharField(max_length=50, default='gemma4:latest')
    ai_confidence = models.FloatField(default=0.5, help_text='AI confidence in its analysis 0-1')
    ai_reasoning = models.TextField(blank=True, help_text='Step-by-step AI reasoning')

    # Key findings
    key_findings = models.JSONField(default=list, help_text='List of key findings')
    risks_identified = models.JSONField(default=list, help_text='List of risks')
    opportunities = models.JSONField(default=list, help_text='List of opportunities')

    # Metadata
    tags = models.JSONField(default=list)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'journal entry'
        verbose_name_plural = 'journal entries'
        db_table = 'journal_entries'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.entry_type}: {self.title[:50]}"


class JournalInsight(models.Model):
    """Extracted insights from journal entries for pattern recognition."""
    INSIGHT_TYPES = [
        ('pattern', 'Pattern Detected'),
        ('correlation', 'Correlation Found'),
        ('anomaly', 'Anomaly Detected'),
        ('trend', 'Trend Identified'),
        ('risk_alert', 'Risk Alert'),
        ('opportunity', 'Opportunity Found'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='insights')
    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPES)
    description = models.TextField()
    confidence = models.FloatField(default=0.5)
    symbol = models.CharField(max_length=20, blank=True)
    data = models.JSONField(default=dict, help_text='Structured insight data')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'journal insight'
        verbose_name_plural = 'journal insights'
        db_table = 'journal_insights'

    def __str__(self):
        return f"{self.insight_type}: {self.description[:50]}"


class MarketContext(models.Model):
    """Snapshot of market context at time of journal entry."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entry = models.OneToOneField(JournalEntry, on_delete=models.CASCADE, related_name='market_context')

    # Price data
    btc_price = models.FloatField(default=0)
    eth_price = models.FloatField(default=0)
    btc_dominance = models.FloatField(default=0)

    # Market indicators
    fear_greed_index = models.IntegerField(default=50)
    fear_greed_label = models.CharField(max_length=20, default='Neutral')
    total_market_cap = models.FloatField(default=0)
    total_volume_24h = models.FloatField(default=0)

    # Technical snapshot
    btc_trend = models.CharField(max_length=20, default='neutral')
    btc_rsi = models.FloatField(default=50)
    btc_macd_signal = models.CharField(max_length=20, default='neutral')

    # News snapshot
    news_sentiment_score = models.FloatField(default=50)
    breaking_news_count = models.IntegerField(default=0)
    top_news_headlines = models.JSONField(default=list)

    # Sentiment snapshot
    social_sentiment_score = models.FloatField(default=50)
    funding_rate_avg = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'market context'
        verbose_name_plural = 'market contexts'
        db_table = 'journal_market_contexts'

    def __str__(self):
        return f"Context: BTC=${self.btc_price:,.0f} F&G={self.fear_greed_index}"
