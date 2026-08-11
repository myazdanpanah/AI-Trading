"""Tests for news app."""
from django.test import TestCase
from datetime import datetime, timedelta
from decimal import Decimal
from .models import NewsSource, NewsArticle, NewsEntity
from .services.analyzer import NewsAnalyzer
from .services.pipeline import NewsProcessingPipeline
from .crawlers.base import CrawledArticle


class NewsModelsTest(TestCase):
    def setUp(self):
        self.source = NewsSource.objects.create(
            name='CoinDesk',
            url='https://coindesk.com',
            source_type='rss'
        )

    def test_news_source_creation(self):
        self.assertEqual(self.source.name, 'CoinDesk')
        self.assertTrue(self.source.is_active)

    def test_news_article_creation(self):
        article = NewsArticle.objects.create(
            source=self.source,
            title='Bitcoin News',
            content='Bitcoin is going up',
            url='https://coindesk.com/bitcoin-news',
            sentiment='bullish',
            impact_score=80,
            published_at=datetime.now()
        )
        self.assertEqual(article.title, 'Bitcoin News')
        self.assertEqual(article.sentiment, 'bullish')
        self.assertEqual(article.impact_score, 80)

    def test_news_entity_creation(self):
        article = NewsArticle.objects.create(
            source=self.source,
            title='ETH Update',
            content='Ethereum upgrades',
            url='https://coindesk.com/eth-update',
            published_at=datetime.now()
        )
        entity = NewsEntity.objects.create(
            article=article,
            entity_type='crypto',
            name='ETH',
            sentiment='bullish'
        )
        self.assertEqual(entity.article, article)
        self.assertEqual(entity.name, 'ETH')


class NewsAnalyzerTest(TestCase):
    def setUp(self):
        self.analyzer = NewsAnalyzer()

    def test_sentiment_bullish(self):
        sentiment = self.analyzer._analyze_sentiment(
            'Bitcoin Surges to New All-Time High',
            'Bitcoin rallies as institutional adoption grows and ETF approved'
        )
        self.assertEqual(sentiment, 'bullish')

    def test_sentiment_bearish(self):
        sentiment = self.analyzer._analyze_sentiment(
            'Major Exchange Hacked',
            'Crypto crash as hack exploit causes massive losses and fear'
        )
        self.assertEqual(sentiment, 'bearish')

    def test_sentiment_neutral(self):
        sentiment = self.analyzer._analyze_sentiment(
            'Crypto Market Update',
            'Markets trading sideways today'
        )
        self.assertEqual(sentiment, 'neutral')

    def test_detect_assets(self):
        assets = self.analyzer._detect_assets(
            'Bitcoin and Ethereum See Growth',
            'BTC and ETH prices rise as SOL also gains'
        )
        self.assertIn('BTC', assets)
        self.assertIn('ETH', assets)
        self.assertIn('SOL', assets)

    def test_impact_score(self):
        score = self.analyzer._calculate_impact(
            'SEC Approves Bitcoin ETF',
            'Institutional adoption continues with ETF approval'
        )
        self.assertGreater(score, 50)

    def test_generate_summary(self):
        summary = self.analyzer._generate_summary(
            'Test Title',
            'This is a test content that should be summarized'
        )
        self.assertEqual(summary, 'This is a test content that should be summarized')


class NewsPipelineTest(TestCase):
    def setUp(self):
        self.pipeline = NewsProcessingPipeline()

    def test_content_hash(self):
        hash1 = self.pipeline.generate_content_hash('Test Title', 'https://example.com')
        hash2 = self.pipeline.generate_content_hash('Test Title', 'https://example.com')
        hash3 = self.pipeline.generate_content_hash('Different Title', 'https://example.com')
        
        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, hash3)

    def test_stats(self):
        stats = self.pipeline.get_stats()
        self.assertIn('total_fetched', stats)
        self.assertIn('total_new', stats)
        self.assertIn('total_duplicates', stats)
