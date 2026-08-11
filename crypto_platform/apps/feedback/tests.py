"""Feedback Loop tests."""
from django.test import TestCase
from decimal import Decimal
from datetime import datetime, timedelta

from .services.similarity_search import SimilaritySearchService
from .services.learning_agent import LearningAgent


class SimilaritySearchServiceTest(TestCase):
    """Test SimilaritySearchService calculations."""

    def test_calculate_embedding(self):
        """Test embedding calculation from market data."""
        market_data = {
            'price_change_1h': 2.5,
            'price_change_24h': 5.0,
            'price_change_7d': 10.0,
            'volume_ratio': 1.5,
            'rsi': 65,
            'macd_signal': 0.3,
            'ema_trend': 0.5,
            'adx': 30,
            'fear_greed_index': 60,
            'social_sentiment': 0.3,
            'atr_percent': 3.0,
        }
        
        embedding = SimilaritySearchService.calculate_embedding(market_data)
        
        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), 11)  # 11 features
        
        # Check vector is normalized (magnitude ~1)
        magnitude = sum(f * f for f in embedding) ** 0.5
        self.assertAlmostEqual(magnitude, 1.0, places=5)

    def test_cosine_similarity_identical(self):
        """Test cosine similarity of identical vectors is 1.0."""
        vec = [0.5, 0.5, 0.5, 0.5]
        similarity = SimilaritySearchService.cosine_similarity(vec, vec)
        self.assertAlmostEqual(similarity, 1.0, places=5)

    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity of orthogonal vectors is 0.0."""
        vec_a = [1.0, 0.0]
        vec_b = [0.0, 1.0]
        similarity = SimilaritySearchService.cosine_similarity(vec_a, vec_b)
        self.assertAlmostEqual(similarity, 0.0, places=5)

    def test_cosine_similarity_empty_vectors(self):
        """Test cosine similarity with empty vectors returns 0."""
        similarity = SimilaritySearchService.cosine_similarity([], [])
        self.assertEqual(similarity, 0.0)

    def test_normalize(self):
        """Test value normalization to 0-1 range."""
        # Value at minimum
        result = SimilaritySearchService._normalize(0, 0, 100)
        self.assertEqual(result, 0.0)
        
        # Value at maximum
        result = SimilaritySearchService._normalize(100, 0, 100)
        self.assertEqual(result, 1.0)
        
        # Value in middle
        result = SimilaritySearchService._normalize(50, 0, 100)
        self.assertEqual(result, 0.5)
        
        # Value below minimum
        result = SimilaritySearchService._normalize(-10, 0, 100)
        self.assertEqual(result, 0.0)
        
        # Value above maximum
        result = SimilaritySearchService._normalize(150, 0, 100)
        self.assertEqual(result, 1.0)


class LearningAgentTest(TestCase):
    """Test LearningAgent calculations."""

    def test_calculate_profit_factor(self):
        """Test profit factor calculation."""
        # All wins
        returns = [1.0, 2.0, 3.0]
        result = LearningAgent._calculate_profit_factor(returns)
        self.assertEqual(result, float('inf'))
        
        # Mixed returns: (2+3) / (1+0.5) = 5/1.5 = 3.3333
        returns = [2.0, -1.0, 3.0, -0.5]
        result = LearningAgent._calculate_profit_factor(returns)
        self.assertAlmostEqual(result, 3.3333, places=4)
        
        # All losses
        returns = [-1.0, -2.0, -3.0]
        result = LearningAgent._calculate_profit_factor(returns)
        self.assertEqual(result, 0)

    def test_calculate_sharpe(self):
        """Test Sharpe ratio calculation."""
        # No returns
        result = LearningAgent._calculate_sharpe([])
        self.assertEqual(result, 0)
        
        # Single return
        result = LearningAgent._calculate_sharpe([1.0])
        self.assertEqual(result, 0)
        
        # Multiple returns
        returns = [0.05, 0.02, -0.01, 0.03, 0.04]
        result = LearningAgent._calculate_sharpe(returns)
        self.assertIsInstance(result, float)

    def test_performance_thresholds(self):
        """Test performance threshold constants."""
        self.assertEqual(LearningAgent.EXCELLENT_WIN_RATE, 0.70)
        self.assertEqual(LearningAgent.GOOD_WIN_RATE, 0.55)
        self.assertEqual(LearningAgent.POOR_WIN_RATE, 0.40)
