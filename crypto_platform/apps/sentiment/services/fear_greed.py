"""Fear & Greed Index analysis service."""
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class FearGreedAnalyzer:
    """Analyze crypto market Fear & Greed Index."""

    @staticmethod
    def calculate_fear_greed(
        volatility: float,
        momentum: float,
        social_media: float,
        dominance: float,
        trends: float,
    ) -> Dict:
        """Calculate Fear & Greed index from components."""
        # Weighted average of components
        weights = {
            'volatility': 0.25,
            'momentum': 0.25,
            'social_media': 0.20,
            'dominance': 0.15,
            'trends': 0.15,
        }

        raw_score = (
            volatility * weights['volatility'] +
            momentum * weights['momentum'] +
            social_media * weights['social_media'] +
            dominance * weights['dominance'] +
            trends * weights['trends']
        )

        # Normalize to 0-100
        value = max(0, min(100, raw_score))

        # Determine label
        if value <= 20:
            label = 'extreme_fear'
        elif value <= 40:
            label = 'fear'
        elif value <= 60:
            label = 'neutral'
        elif value <= 80:
            label = 'greed'
        else:
            label = 'extreme_greed'

        return {
            'value': round(value, 2),
            'label': label,
            'components': {
                'volatility': round(volatility, 2),
                'momentum': round(momentum, 2),
                'social_media': round(social_media, 2),
                'dominance': round(dominance, 2),
                'trends': round(trends, 2),
            },
        }

    @staticmethod
    def calculate_volatility_score(prices: List[float], period: int = 20) -> float:
        """Calculate volatility score (0-100, higher = more volatile)."""
        if len(prices) < period:
            return 50.0

        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns[-period:]) * 100

        # Normalize: 0% vol = 0, 5% vol = 100
        score = min(100, volatility * 20)
        return float(score)

    @staticmethod
    def calculate_momentum_score(prices: List[float], period: int = 20) -> float:
        """Calculate momentum score (0-100, higher = more bullish momentum)."""
        if len(prices) < period:
            return 50.0

        # Price momentum
        momentum = (prices[-1] - prices[-period]) / prices[-period] * 100

        # Normalize: -20% = 0, 0% = 50, +20% = 100
        score = 50 + (momentum * 2.5)
        return float(max(0, min(100, score)))

    @staticmethod
    def calculate_social_score(social_sentiment: float) -> float:
        """Calculate social media score from sentiment (-1 to 1 -> 0 to 100)."""
        return float(max(0, min(100, (social_sentiment + 1) * 50)))

    @staticmethod
    def calculate_dominance_score(btc_dominance: float, eth_dominance: float = 0) -> float:
        """Calculate dominance score from BTC/ETH dominance."""
        # Higher BTC dominance often correlates with fear (altcoin sell-off)
        # Lower BTC dominance often correlates with greed (altcoin season)
        score = 100 - btc_dominance
        return float(max(0, min(100, score)))

    @staticmethod
    def calculate_trends_score(trend_data: Dict) -> float:
        """Calculate trends score from Google Trends data."""
        # Simplified trend scoring
        interest = trend_data.get('interest', 50)
        momentum = trend_data.get('momentum', 0)

        score = interest + (momentum * 10)
        return float(max(0, min(100, score)))

    @classmethod
    def analyze_fear_greed(
        cls,
        prices: List[float],
        social_sentiment: float = 0,
        btc_dominance: float = 50,
        trend_data: Optional[Dict] = None,
    ) -> Dict:
        """Comprehensive Fear & Greed analysis."""
        volatility = cls.calculate_volatility_score(prices)
        momentum = cls.calculate_momentum_score(prices)
        social = cls.calculate_social_score(social_sentiment)
        dominance = cls.calculate_dominance_score(btc_dominance)
        trends = cls.calculate_trends_score(trend_data or {})

        return cls.calculate_fear_greed(
            volatility=volatility,
            momentum=momentum,
            social_media=social,
            dominance=dominance,
            trends=trends,
        )

    @staticmethod
    def detect_extreme_signals(value: float, history: List[float]) -> Optional[Dict]:
        """Detect extreme Fear & Greed signals."""
        if not history:
            return None

        avg = np.mean(history[-30:]) if len(history) >= 30 else np.mean(history)
        std = np.std(history[-30:]) if len(history) >= 30 else np.std(history)

        if std == 0:
            return None

        z_score = (value - avg) / std

        if abs(z_score) > 2:
            return {
                'is_extreme': True,
                'z_score': round(float(z_score), 2),
                'signal': 'contrarian_buy' if value < 25 else 'contrarian_sell',
                'avg_value': round(float(avg), 2),
                'current_vs_avg': round(float(value - avg), 2),
            }

        return {'is_extreme': False}
