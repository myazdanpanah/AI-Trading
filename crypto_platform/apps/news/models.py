"""News intelligence models."""
import uuid
from django.db import models


class NewsSource(models.Model):
    """News source configuration."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    url = models.URLField()
    source_type = models.CharField(
        max_length=20,
        choices=[
            ('rss', 'RSS Feed'),
            ('twitter', 'Twitter/X'),
            ('reddit', 'Reddit'),
            ('telegram', 'Telegram'),
            ('blog', 'Official Blog'),
            ('government', 'Government'),
        ]
    )
    is_active = models.BooleanField(default=True)
    fetch_interval = models.IntegerField(default=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'news source'
        verbose_name_plural = 'news sources'
        db_table = 'news_sources'

    def __str__(self):
        return self.name


class NewsArticle(models.Model):
    """News article with AI analysis."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=500)
    content = models.TextField()
    url = models.URLField(unique=True)
    author = models.CharField(max_length=200, blank=True)
    language = models.CharField(max_length=10, default='en')
    published_at = models.DateTimeField(db_index=True)
    sentiment = models.CharField(
        max_length=20,
        choices=[
            ('bullish', 'Bullish'),
            ('neutral', 'Neutral'),
            ('bearish', 'Bearish'),
        ],
        default='neutral'
    )
    impact_score = models.IntegerField(default=50)
    ai_summary = models.TextField(blank=True)
    embedding = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'news article'
        verbose_name_plural = 'news articles'
        db_table = 'news_articles'
        ordering = ['-published_at']

    def __str__(self):
        return self.title[:100]


class NewsEntity(models.Model):
    """Entities extracted from news."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, related_name='entities')
    entity_type = models.CharField(
        max_length=20,
        choices=[
            ('crypto', 'Cryptocurrency'),
            ('company', 'Company'),
            ('person', 'Person'),
            ('event', 'Event'),
            ('regulation', 'Regulation'),
        ]
    )
    name = models.CharField(max_length=200)
    sentiment = models.CharField(max_length=20, default='neutral')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'news entity'
        verbose_name_plural = 'news entities'
        db_table = 'news_entities'
        unique_together = ['article', 'name']

    def __str__(self):
        return f"{self.entity_type}: {self.name}"
