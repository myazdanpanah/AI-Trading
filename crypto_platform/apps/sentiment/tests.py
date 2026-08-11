"""Tests for Sentiment Intelligence services."""
from django.test import TestCase
from datetime import datetime

from .services.social_analyzer import SocialSentimentAnalyzer
from .services.fear_greed import FearGreedAnalyzer
from .services.whale_tracker import WhaleActivityTracker
from .services.influencer_monitor import InfluencerSentimentMonitor
from .services.aggregator import SentimentAggregator
from .models import (
    SocialSentiment, FearGreedIndex, WhaleActivity,
    InfluencerSentiment, MarketSentimentAggregated, SentimentAlert
)


class SocialSentimentAnalyzerTest(TestCase):
    """Test SocialSentimentAnalyzer calculations."""

    def test_analyze_text_sentiment_bullish(self):
        """Test bullish text sentiment analysis."""
        text = "Bitcoin is going to moon! Buy now, huge breakout coming!"
        result = SocialSentimentAnalyzer.analyze_text_sentiment(text)

        self.assertIn('score', result)
        self.assertIn('label', result)
        self.assertGreater(result['score'], 0)
        self.assertIn(result['label'], ['bullish', 'very_bullish'])

    def test_analyze_text_sentiment_bearish(self):
        """Test bearish text sentiment analysis."""
        text = "Bitcoin crash incoming! Sell everything, it's a scam!"
        result = SocialSentimentAnalyzer.analyze_text_sentiment(text)

        self.assertLess(result['score'], 0)
        self.assertIn(result['label'], ['bearish', 'very_bearish'])

    def test_analyze_text_sentiment_neutral(self):
        """Test neutral text sentiment analysis."""
        text = "Bitcoin is trading at 50000 dollars today."
        result = SocialSentimentAnalyzer.analyze_text_sentiment(text)

        self.assertEqual(result['score'], 0)
        self.assertEqual(result['label'], 'neutral')

    def test_aggregate_social_sentiment(self):
        """Test aggregating multiple posts."""
        posts = [
            {'text': 'Bitcoin moon! Buy!', 'engagement': 100},
            {'text': 'Bitcoin crash! Sell!', 'engagement': 50},
            {'text': 'Bitcoin is neutral', 'engagement': 25},
        ]

        result = SocialSentimentAnalyzer.aggregate_social_sentiment(posts)

        self.assertIn('sentiment_score', result)
        self.assertIn('sentiment_label', result)
        self.assertEqual(result['volume'], 3)

    def test_aggregate_empty_posts(self):
        """Test aggregating empty posts."""
        result = SocialSentimentAnalyzer.aggregate_social_sentiment([])

        self.assertEqual(result['sentiment_score'], 0)
        self.assertEqual(result['volume'], 0)

    def test_extract_keywords(self):
        """Test keyword extraction."""
        texts = [
            "Bitcoin is bullish and moon",
            "Bitcoin breakout coming soon",
            "Ethereum also bullish",
        ]

        keywords = SocialSentimentAnalyzer.extract_keywords(texts, top_n=5)

        self.assertIsInstance(keywords, list)
        self.assertLessEqual(len(keywords), 5)

    def test_detect_sentiment_shift(self):
        """Test sentiment shift detection."""
        historical = [0.1, 0.2, 0.15, 0.1, 0.2, 0.15, 0.1, 0.2]
        current = 0.8

        result = SocialSentimentAnalyzer.detect_sentiment_shift(current, historical)

        self.assertIsNotNone(result)
        self.assertTrue(result['is_significant'])
        self.assertEqual(result['direction'], 'positive')

    def test_detect_no_sentiment_shift(self):
        """Test no sentiment shift detected."""
        historical = [0.1, 0.2, 0.15, 0.1, 0.2, 0.15, 0.1, 0.2]
        current = 0.15

        result = SocialSentimentAnalyzer.detect_sentiment_shift(current, historical)

        self.assertIsNone(result)


class FearGreedAnalyzerTest(TestCase):
    """Test FearGreedAnalyzer calculations."""

    def test_calculate_fear_greed(self):
        """Test Fear & Greed calculation."""
        result = FearGreedAnalyzer.calculate_fear_greed(
            volatility=30,
            momentum=60,
            social_media=70,
            dominance=50,
            trends=65,
        )

        self.assertIn('value', result)
        self.assertIn('label', result)
        self.assertIn('components', result)
        self.assertGreaterEqual(result['value'], 0)
        self.assertLessEqual(result['value'], 100)

    def test_calculate_volatility_score(self):
        """Test volatility score calculation."""
        import random
        random.seed(42)
        prices = [100 + random.uniform(-5, 5) for _ in range(100)]

        score = FearGreedAnalyzer.calculate_volatility_score(prices)

        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_calculate_momentum_score(self):
        """Test momentum score calculation."""
        prices = [100 + i for i in range(50)]  # Uptrend

        score = FearGreedAnalyzer.calculate_momentum_score(prices)

        self.assertGreater(score, 50)  # Should be bullish

    def test_calculate_momentum_downtrend(self):
        """Test momentum score in downtrend."""
        prices = [200 - i for i in range(50)]  # Downtrend

        score = FearGreedAnalyzer.calculate_momentum_score(prices)

        self.assertLess(score, 50)  # Should be bearish

    def test_calculate_social_score(self):
        """Test social score calculation."""
        score = FearGreedAnalyzer.calculate_social_score(0.5)
        self.assertEqual(score, 75)

        score = FearGreedAnalyzer.calculate_social_score(-0.5)
        self.assertEqual(score, 25)

    def test_calculate_dominance_score(self):
        """Test dominance score calculation."""
        score = FearGreedAnalyzer.calculate_dominance_score(70)
        self.assertEqual(score, 30)

    def test_analyze_fear_greed(self):
        """Test comprehensive Fear & Greed analysis."""
        import random
        random.seed(42)
        prices = [100 + random.uniform(-5, 5) for _ in range(100)]

        result = FearGreedAnalyzer.analyze_fear_greed(
            prices=prices,
            social_sentiment=0.3,
            btc_dominance=50,
        )

        self.assertIn('value', result)
        self.assertIn('label', result)

    def test_detect_extreme_signals(self):
        """Test extreme signal detection."""
        history = [50, 55, 60, 55, 50, 45, 40, 35, 30, 25]

        result = FearGreedAnalyzer.detect_extreme_signals(10, history)

        self.assertIsNotNone(result)
        self.assertTrue(result['is_extreme'])
        self.assertEqual(result['signal'], 'contrarian_buy')


class WhaleActivityTrackerTest(TestCase):
    """Test WhaleActivityTracker calculations."""

    def test_classify_whale(self):
        """Test whale classification."""
        self.assertEqual(WhaleActivityTracker.classify_whale(50_000), 'retail')
        self.assertEqual(WhaleActivityTracker.classify_whale(150_000), 'small_whale')
        self.assertEqual(WhaleActivityTracker.classify_whale(5_000_000), 'medium_whale')
        self.assertEqual(WhaleActivityTracker.classify_whale(50_000_000), 'large_whale')
        self.assertEqual(WhaleActivityTracker.classify_whale(150_000_000), 'mega_whale')

    def test_analyze_whale_movement_bullish(self):
        """Test bullish whale movement analysis."""
        from decimal import Decimal

        result = WhaleActivityTracker.analyze_whale_movement(
            balance_change=Decimal('1000'),
            balance_before=Decimal('10000'),
            transaction_type='exchange_withdrawal',
        )

        self.assertEqual(result['sentiment'], 'bullish')
        self.assertGreater(result['confidence'], 0)

    def test_analyze_whale_movement_bearish(self):
        """Test bearish whale movement analysis."""
        from decimal import Decimal

        result = WhaleActivityTracker.analyze_whale_movement(
            balance_change=Decimal('-1000'),
            balance_before=Decimal('10000'),
            transaction_type='exchange_deposit',
        )

        self.assertEqual(result['sentiment'], 'bearish')

    def test_calculate_whale_score(self):
        """Test whale score calculation."""
        activities = [
            {'sentiment': 'bullish'},
            {'sentiment': 'bullish'},
            {'sentiment': 'bearish'},
            {'sentiment': 'neutral'},
        ]

        result = WhaleActivityTracker.calculate_whale_score(activities)

        self.assertIn('score', result)
        self.assertIn('label', result)
        self.assertEqual(result['total_activities'], 4)

    def test_calculate_whale_score_empty(self):
        """Test whale score with empty activities."""
        result = WhaleActivityTracker.calculate_whale_score([])

        self.assertEqual(result['score'], 0)
        self.assertEqual(result['label'], 'neutral')

    def test_detect_accumulation_pattern(self):
        """Test accumulation pattern detection."""
        activities = [
            {'transaction_type': 'exchange_withdrawal', 'usd_value': 100000},
            {'transaction_type': 'exchange_withdrawal', 'usd_value': 150000},
            {'transaction_type': 'exchange_withdrawal', 'usd_value': 120000},
            {'transaction_type': 'exchange_withdrawal', 'usd_value': 180000},
            {'transaction_type': 'exchange_withdrawal', 'usd_value': 200000},
        ]

        result = WhaleActivityTracker.detect_accumulation_pattern(activities)

        self.assertIsNotNone(result)
        self.assertEqual(result['pattern'], 'accumulation')
        self.assertEqual(result['signal'], 'bullish')

    def test_detect_distribution_pattern(self):
        """Test distribution pattern detection."""
        activities = [
            {'transaction_type': 'exchange_deposit', 'usd_value': 100000},
            {'transaction_type': 'exchange_deposit', 'usd_value': 150000},
            {'transaction_type': 'exchange_deposit', 'usd_value': 120000},
            {'transaction_type': 'exchange_deposit', 'usd_value': 180000},
            {'transaction_type': 'exchange_deposit', 'usd_value': 200000},
        ]

        result = WhaleActivityTracker.detect_distribution_pattern(activities)

        self.assertIsNotNone(result)
        self.assertEqual(result['pattern'], 'distribution')
        self.assertEqual(result['signal'], 'bearish')


class InfluencerSentimentMonitorTest(TestCase):
    """Test InfluencerSentimentMonitor calculations."""

    def test_calculate_credibility_score(self):
        """Test credibility score calculation."""
        score = InfluencerSentimentMonitor.calculate_credibility_score(
            follower_count=100000,
            engagement_rate=5.0,
            historical_accuracy=0.7,
            account_age_days=365,
        )

        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 1)

    def test_analyze_influencer_post(self):
        """Test influencer post analysis."""
        content = "Bitcoin is going to moon! Bullish breakout incoming!"
        sentiment_keywords = {
            'bullish': ['moon', 'bullish', 'breakout', 'buy'],
            'bearish': ['crash', 'dump', 'sell', 'scam'],
        }

        result = InfluencerSentimentMonitor.analyze_influencer_post(content, sentiment_keywords)

        self.assertIn('score', result)
        self.assertIn('label', result)
        self.assertGreater(result['score'], 0)

    def test_aggregate_influencer_sentiment(self):
        """Test aggregating influencer sentiment."""
        posts = [
            {'sentiment_score': 0.8, 'credibility_score': 0.9, 'followers': 100000},
            {'sentiment_score': 0.5, 'credibility_score': 0.7, 'followers': 50000},
            {'sentiment_score': 0.3, 'credibility_score': 0.6, 'followers': 25000},
        ]

        result = InfluencerSentimentMonitor.aggregate_influencer_sentiment(posts)

        self.assertIn('score', result)
        self.assertIn('label', result)
        self.assertEqual(result['post_count'], 3)

    def test_aggregate_empty_posts(self):
        """Test aggregating empty posts."""
        result = InfluencerSentimentMonitor.aggregate_influencer_sentiment([])

        self.assertEqual(result['score'], 0)
        self.assertEqual(result['post_count'], 0)

    def test_detect_influencer_consensus(self):
        """Test influencer consensus detection."""
        posts = [
            {'sentiment_score': 0.8},
            {'sentiment_score': 0.7},
            {'sentiment_score': 0.9},
            {'sentiment_score': 0.6},
        ]

        result = InfluencerSentimentMonitor.detect_influencer_consensus(posts)

        self.assertIsNotNone(result)
        self.assertEqual(result['consensus'], 'bullish')
        self.assertGreater(result['ratio'], 0.7)


class SentimentAggregatorTest(TestCase):
    """Test SentimentAggregator calculations."""

    def test_aggregate_sentiment(self):
        """Test sentiment aggregation."""
        result = SentimentAggregator.aggregate_sentiment(
            social_sentiment=0.5,
            news_sentiment=0.3,
            whale_sentiment=0.4,
            influencer_sentiment=0.6,
            fear_greed_value=65,
        )

        self.assertIn('overall_score', result)
        self.assertIn('overall_label', result)
        self.assertIn('confidence', result)
        self.assertIn('source_scores', result)

    def test_aggregate_neutral_sentiment(self):
        """Test neutral sentiment aggregation."""
        result = SentimentAggregator.aggregate_sentiment(
            social_sentiment=0,
            news_sentiment=0,
            whale_sentiment=0,
            influencer_sentiment=0,
            fear_greed_value=50,
        )

        self.assertEqual(result['overall_label'], 'neutral')

    def test_detect_sentiment_divergence(self):
        """Test sentiment divergence detection."""
        source_scores = {
            'social': 0.8,
            'news': -0.6,
            'whale': 0.5,
            'influencer': -0.4,
        }

        result = SentimentAggregator.detect_sentiment_divergence(source_scores)

        self.assertIsNotNone(result)
        self.assertTrue(result['is_divergent'])

    def test_detect_no_divergence(self):
        """Test no divergence detected."""
        source_scores = {
            'social': 0.5,
            'news': 0.4,
            'whale': 0.6,
            'influencer': 0.5,
        }

        result = SentimentAggregator.detect_sentiment_divergence(source_scores)

        self.assertIsNotNone(result)
        self.assertFalse(result['is_divergent'])

    def test_calculate_sentiment_momentum(self):
        """Test sentiment momentum calculation."""
        historical = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]

        result = SentimentAggregator.calculate_sentiment_momentum(historical)

        self.assertIn('momentum', result)
        self.assertIn('trend', result)
        self.assertEqual(result['trend'], 'improving')

    def test_calculate_sentiment_momentum_declining(self):
        """Test declining sentiment momentum."""
        historical = [0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]

        result = SentimentAggregator.calculate_sentiment_momentum(historical)

        self.assertEqual(result['trend'], 'declining')

    def test_generate_sentiment_summary(self):
        """Test sentiment summary generation."""
        aggregated = {
            'overall_label': 'bullish',
            'overall_score': 0.5,
            'confidence': 0.8,
        }
        momentum = {'trend': 'improving'}

        summary = SentimentAggregator.generate_sentiment_summary(aggregated, momentum, None)

        self.assertIsInstance(summary, str)
        self.assertIn('bullish', summary.lower())
        self.assertIn('improving', summary.lower())


class SocialSentimentModelTest(TestCase):
    """Test SocialSentiment model."""

    def test_create_social_sentiment(self):
        """Test creating social sentiment."""
        sentiment = SocialSentiment.objects.create(
            symbol='BTC-USDT',
            platform='twitter',
            sentiment_score=0.5,
            sentiment_label='bullish',
            volume=1000,
            engagement=5000,
            top_posts=[{'text': 'Bitcoin moon!', 'likes': 100}],
            keywords=['bitcoin', 'moon', 'bullish'],
            timestamp=datetime.now(),
        )

        self.assertEqual(sentiment.symbol, 'BTC-USDT')
        self.assertEqual(sentiment.platform, 'twitter')
        self.assertEqual(sentiment.sentiment_label, 'bullish')

    def test_social_sentiment_str(self):
        """Test social sentiment string representation."""
        sentiment = SocialSentiment.objects.create(
            symbol='BTC-USDT',
            platform='twitter',
            sentiment_score=0.5,
            sentiment_label='bullish',
            timestamp=datetime.now(),
        )

        self.assertIn('BTC-USDT', str(sentiment))
        self.assertIn('twitter', str(sentiment))


class FearGreedIndexModelTest(TestCase):
    """Test FearGreedIndex model."""

    def test_create_fear_greed_index(self):
        """Test creating Fear & Greed index."""
        index = FearGreedIndex.objects.create(
            value=75,
            label='greed',
            volatility=40,
            momentum=60,
            social_media=70,
            dominance=50,
            trends=65,
            timestamp=datetime.now(),
        )

        self.assertEqual(index.value, 75)
        self.assertEqual(index.label, 'greed')

    def test_fear_greed_str(self):
        """Test Fear & Greed string representation."""
        index = FearGreedIndex.objects.create(
            value=25,
            label='fear',
            timestamp=datetime.now(),
        )

        self.assertIn('25', str(index))
        self.assertIn('fear', str(index))


class WhaleActivityModelTest(TestCase):
    """Test WhaleActivity model."""

    def test_create_whale_activity(self):
        """Test creating whale activity."""
        activity = WhaleActivity.objects.create(
            symbol='BTC-USDT',
            whale_type='exchange_whale',
            wallet_address='0x1234567890abcdef',
            balance_change=1000,
            balance_before=5000,
            balance_after=6000,
            usd_value=50000000,
            sentiment_impact='bullish',
            confidence=0.8,
            timestamp=datetime.now(),
        )

        self.assertEqual(activity.symbol, 'BTC-USDT')
        self.assertEqual(activity.whale_type, 'exchange_whale')
        self.assertEqual(activity.sentiment_impact, 'bullish')

    def test_whale_activity_str(self):
        """Test whale activity string representation."""
        activity = WhaleActivity.objects.create(
            symbol='BTC-USDT',
            whale_type='mega_whale',
            wallet_address='0x1234567890abcdef',
            usd_value=150000000,
            timestamp=datetime.now(),
        )

        self.assertIn('BTC-USDT', str(activity))
        self.assertIn('mega_whale', str(activity))


class InfluencerSentimentModelTest(TestCase):
    """Test InfluencerSentiment model."""

    def test_create_influencer_sentiment(self):
        """Test creating influencer sentiment."""
        sentiment = InfluencerSentiment.objects.create(
            influencer_name='CryptoInfluencer',
            platform='twitter',
            followers=100000,
            credibility_score=0.8,
            sentiment_score=0.6,
            sentiment_label='bullish',
            mentioned_symbols=['BTC', 'ETH'],
            post_content='Bitcoin is going to moon!',
            engagement=5000,
            timestamp=datetime.now(),
        )

        self.assertEqual(sentiment.influencer_name, 'CryptoInfluencer')
        self.assertEqual(sentiment.sentiment_label, 'bullish')

    def test_influencer_sentiment_str(self):
        """Test influencer sentiment string representation."""
        sentiment = InfluencerSentiment.objects.create(
            influencer_name='CryptoInfluencer',
            platform='twitter',
            sentiment_label='bullish',
            timestamp=datetime.now(),
        )

        self.assertIn('CryptoInfluencer', str(sentiment))
        self.assertIn('bullish', str(sentiment))


class MarketSentimentAggregatedModelTest(TestCase):
    """Test MarketSentimentAggregated model."""

    def test_create_aggregated_sentiment(self):
        """Test creating aggregated sentiment."""
        sentiment = MarketSentimentAggregated.objects.create(
            symbol='BTC-USDT',
            overall_score=0.5,
            overall_label='bullish',
            social_score=0.6,
            news_score=0.4,
            whale_score=0.5,
            influencer_score=0.7,
            fear_greed_value=65,
            confidence=0.8,
            data_sources=['social', 'news', 'whale'],
            timestamp=datetime.now(),
        )

        self.assertEqual(sentiment.symbol, 'BTC-USDT')
        self.assertEqual(sentiment.overall_label, 'bullish')

    def test_aggregated_sentiment_str(self):
        """Test aggregated sentiment string representation."""
        sentiment = MarketSentimentAggregated.objects.create(
            symbol='BTC-USDT',
            overall_score=0.5,
            overall_label='bullish',
            timestamp=datetime.now(),
        )

        self.assertIn('BTC-USDT', str(sentiment))
        self.assertIn('bullish', str(sentiment))


class SentimentAlertModelTest(TestCase):
    """Test SentimentAlert model."""

    def test_create_sentiment_alert(self):
        """Test creating sentiment alert."""
        alert = SentimentAlert.objects.create(
            symbol='BTC-USDT',
            alert_type='sentiment_spike',
            severity='high',
            title='Sentiment Spike Detected',
            message='Social sentiment has increased significantly.',
            sentiment_score=0.8,
            timestamp=datetime.now(),
        )

        self.assertEqual(alert.symbol, 'BTC-USDT')
        self.assertEqual(alert.alert_type, 'sentiment_spike')
        self.assertFalse(alert.is_read)

    def test_sentiment_alert_str(self):
        """Test sentiment alert string representation."""
        alert = SentimentAlert.objects.create(
            symbol='BTC-USDT',
            alert_type='whale_movement',
            severity='critical',
            title='Whale Alert',
            message='Large whale movement detected.',
            timestamp=datetime.now(),
        )

        self.assertIn('BTC-USDT', str(alert))
        self.assertIn('whale_movement', str(alert))
