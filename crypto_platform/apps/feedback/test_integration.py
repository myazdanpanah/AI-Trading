"""Integration tests for the Feedback Loop - signal-to-memory workflow."""
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase

from .models import MarketMemory, SignalMemory, PatternMemory, LearningInsight
from .services.similarity_search import SimilaritySearchService
from .services.learning_agent import LearningAgent


class SignalToMemoryIntegrationTest(TestCase):
    """Test the complete signal-to-memory workflow."""

    def test_embedding_generation_from_market_conditions(self):
        """Test that market conditions generate valid embeddings."""
        market_conditions = {
            'price_change_1h': 2.5,
            'price_change_24h': -1.2,
            'price_change_7d': 15.0,
            'volume_ratio': 2.0,
            'rsi': 72,
            'macd_signal': 0.5,
            'ema_trend': 1.0,
            'adx': 45,
            'fear_greed_index': 75,
            'social_sentiment': 0.6,
            'atr_percent': 4.5,
        }
        embedding = SimilaritySearchService.calculate_embedding(market_conditions)
        self.assertEqual(len(embedding), 11)
        # Verify normalized
        magnitude = sum(x * x for x in embedding) ** 0.5
        self.assertAlmostEqual(magnitude, 1.0, places=4)

    def test_similarity_search_ranking(self):
        """Test that similarity search correctly ranks by cosine similarity."""
        base_vec = [0.5, 0.5, 0.5, 0.5]
        candidates = [
            ('similar', [0.5, 0.5, 0.5, 0.5]),
            ('orthogonal', [0.5, -0.5, 0.5, -0.5]),
            ('opposite', [-0.5, -0.5, -0.5, -0.5]),
        ]
        similarities = []
        for name, vec in candidates:
            sim = SimilaritySearchService.cosine_similarity(base_vec, vec)
            similarities.append((name, sim))

        # Similar should rank highest
        similarities.sort(key=lambda x: x[1], reverse=True)
        self.assertEqual(similarities[0][0], 'similar')
        self.assertAlmostEqual(similarities[0][1], 1.0, places=4)

    def test_cosine_similarity_mismatched_lengths(self):
        """Test cosine similarity with vectors of different lengths returns 0."""
        result = SimilaritySearchService.cosine_similarity([1, 0], [1, 0, 0])
        self.assertEqual(result, 0.0)

    def test_learning_agent_profit_factor_edge_cases(self):
        """Test profit factor with various edge cases."""
        # Empty returns
        self.assertEqual(LearningAgent._calculate_profit_factor([]), 0)

        # Single win
        self.assertEqual(LearningAgent._calculate_profit_factor([5.0]), float('inf'))

        # Single loss
        self.assertEqual(LearningAgent._calculate_profit_factor([-3.0]), 0)

        # Mixed returns: (10+20) / (5+10) = 30/15 = 2.0
        result = LearningAgent._calculate_profit_factor([10.0, -5.0, 20.0, -10.0])
        self.assertAlmostEqual(result, 2.0, places=4)

    def test_learning_agent_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        # Zero standard deviation (all same returns)
        result = LearningAgent._calculate_sharpe([0.05, 0.05, 0.05])
        self.assertEqual(result, 0)

        # Normal case
        returns = [0.1, -0.05, 0.08, -0.03, 0.06]
        result = LearningAgent._calculate_sharpe(returns)
        self.assertIsInstance(result, float)


class SimilaritySearchNormalizationTest(TestCase):
    """Test embedding normalization across different market conditions."""

    def test_extreme_values_normalized(self):
        """Test that extreme market values are properly normalized."""
        extreme_conditions = {
            'price_change_1h': 100.0,
            'price_change_24h': -50.0,
            'price_change_7d': 500.0,
            'volume_ratio': 100.0,
            'rsi': 100,
            'macd_signal': 5.0,
            'ema_trend': 10.0,
            'adx': 100,
            'fear_greed_index': 100,
            'social_sentiment': 1.0,
            'atr_percent': 50.0,
        }
        embedding = SimilaritySearchService.calculate_embedding(extreme_conditions)
        for val in embedding:
            self.assertGreaterEqual(val, 0.0)
            self.assertLessEqual(val, 1.0)

    def test_bearish_market_embedding(self):
        """Test embedding for bearish market conditions."""
        bearish = {
            'price_change_1h': -5.0,
            'price_change_24h': -15.0,
            'price_change_7d': -30.0,
            'volume_ratio': 3.0,
            'rsi': 20,
            'macd_signal': -1.0,
            'ema_trend': -2.0,
            'adx': 60,
            'fear_greed_index': 15,
            'social_sentiment': -0.5,
            'atr_percent': 8.0,
        }
        embedding = SimilaritySearchService.calculate_embedding(bearish)
        self.assertEqual(len(embedding), 11)

    def test_neutral_market_embedding(self):
        """Test embedding for neutral/consolidating market."""
        neutral = {
            'price_change_1h': 0.1,
            'price_change_24h': -0.5,
            'price_change_7d': 1.0,
            'volume_ratio': 1.0,
            'rsi': 50,
            'macd_signal': 0.0,
            'ema_trend': 0.0,
            'adx': 20,
            'fear_greed_index': 50,
            'social_sentiment': 0.0,
            'atr_percent': 2.0,
        }
        embedding = SimilaritySearchService.calculate_embedding(neutral)
        self.assertEqual(len(embedding), 11)


class LearningThresholdsTest(TestCase):
    """Test learning agent performance thresholds and categorization."""

    def test_excellent_performance_detection(self):
        """Test that excellent win rates are properly categorized."""
        self.assertGreater(LearningAgent.EXCELLENT_WIN_RATE, LearningAgent.GOOD_WIN_RATE)
        self.assertGreater(LearningAgent.GOOD_WIN_RATE, LearningAgent.POOR_WIN_RATE)


class DatabaseIntegrationTest(TestCase):
    """Test full flow with database interactions."""

    def test_market_memory_create_and_query(self):
        """Test creating MarketMemory and querying by symbol."""
        memory = MarketMemory.objects.create(
            symbol='BTC/USDT',
            timeframe='1h',
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            market_conditions={'rsi': 45, 'trend': 'neutral'},
        )
        self.assertIsNotNone(memory.id)
        self.assertEqual(MarketMemory.objects.filter(symbol='BTC/USDT').count(), 1)

    def test_signal_memory_lifecycle(self):
        """Test creating SignalMemory with outcome tracking."""
        memory = SignalMemory.objects.create(
            symbol='ETH/USDT',
            direction='buy',
            confidence=Decimal('75.0'),
            entry_price=Decimal('3000'),
            timeframe='4h',
            actual_return=Decimal('2.5'),
            actual_return_percent=Decimal('2.5'),
            success=True,
            evaluated_at=datetime.now(),
        )
        self.assertTrue(memory.success)
        self.assertEqual(SignalMemory.objects.filter(success=True).count(), 1)

    def test_pattern_memory_create(self):
        """Test creating PatternMemory with pattern data."""
        pattern = PatternMemory.objects.create(
            pattern_type='bullish_engulfing',
            symbol='BTC/USDT',
            success_rate=Decimal('68.5'),
            sample_size=45,
            avg_return=Decimal('1.8'),
            conditions={'rsi_range': '30-40', 'volume': 'above_avg'},
        )
        self.assertEqual(pattern.pattern_type, 'bullish_engulfing')

    def test_learning_insight_create(self):
        """Test creating LearningInsight with recommendation."""
        insight = LearningInsight.objects.create(
            insight_type='weight_adjustment',
            title='Increase technical weight',
            description='Technical analysis has 70% win rate in trending markets',
            recommendation='Increase technical weight from 0.3 to 0.35',
            confidence=Decimal('82.0'),
            supporting_data={'win_rate': 70, 'sample_size': 150},
        )
        self.assertEqual(insight.insight_type, 'weight_adjustment')
