"""Social media sentiment analysis service."""
import re
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SocialSentimentAnalyzer:
    """Analyze social media sentiment for crypto assets."""

    BULLISH_KEYWORDS = [
        'moon', 'bullish', 'buy', 'hodl', 'accumulate', 'breakout', 'pump',
        'ath', 'all time high', 'undervalued', 'gem', 'long', 'uptrend',
        'support holding', 'bounce', 'recovery', 'rally', 'surge', 'soar',
        'institutional adoption', 'etf approved', 'bull run', 'parabolic',
    ]

    BEARISH_KEYWORDS = [
        'dump', 'crash', 'bearish', 'sell', 'short', 'breakdown', 'reject',
        'overvalued', 'scam', 'rug', 'fraud', 'ponzi', 'bubble', 'downtrend',
        'resistance holding', 'decline', 'correction', 'capitulation', 'liquidation',
        'ban', 'regulation', 'sec', 'hack', 'exploit', 'vulnerability',
    ]

    @staticmethod
    def analyze_text_sentiment(text: str) -> Dict:
        """Analyze sentiment of a single text."""
        text_lower = text.lower()

        bullish_count = sum(1 for word in SocialSentimentAnalyzer.BULLISH_KEYWORDS if word in text_lower)
        bearish_count = sum(1 for word in SocialSentimentAnalyzer.BEARISH_KEYWORDS if word in text_lower)

        total = bullish_count + bearish_count
        if total == 0:
            score = 0
            label = 'neutral'
        else:
            score = (bullish_count - bearish_count) / total
            if score > 0.5:
                label = 'very_bullish'
            elif score > 0.2:
                label = 'bullish'
            elif score < -0.5:
                label = 'very_bearish'
            elif score < -0.2:
                label = 'bearish'
            else:
                label = 'neutral'

        return {
            'score': round(score, 4),
            'label': label,
            'bullish_signals': bullish_count,
            'bearish_signals': bearish_count,
        }

    @staticmethod
    def aggregate_social_sentiment(posts: List[Dict]) -> Dict:
        """Aggregate sentiment from multiple social media posts."""
        if not posts:
            return {
                'sentiment_score': 0,
                'sentiment_label': 'neutral',
                'volume': 0,
                'engagement': 0,
                'bullish_ratio': 0.5,
                'bearish_ratio': 0.5,
            }

        sentiments = []
        total_engagement = 0

        for post in posts:
            text = post.get('text', '') or post.get('content', '')
            engagement = post.get('engagement', 0) or post.get('likes', 0)

            result = SocialSentimentAnalyzer.analyze_text_sentiment(text)
            sentiments.append({
                'score': result['score'],
                'weight': max(1, engagement),
            })
            total_engagement += engagement

        total_weight = sum(s['weight'] for s in sentiments)
        if total_weight > 0:
            weighted_score = sum(s['score'] * s['weight'] for s in sentiments) / total_weight
        else:
            weighted_score = sum(s['score'] for s in sentiments) / len(sentiments)

        if weighted_score > 0.5:
            label = 'very_bullish'
        elif weighted_score > 0.2:
            label = 'bullish'
        elif weighted_score < -0.5:
            label = 'very_bearish'
        elif weighted_score < -0.2:
            label = 'bearish'
        else:
            label = 'neutral'

        bullish_count = sum(1 for s in sentiments if s['score'] > 0.2)
        bearish_count = sum(1 for s in sentiments if s['score'] < -0.2)

        return {
            'sentiment_score': round(weighted_score, 4),
            'sentiment_label': label,
            'volume': len(posts),
            'engagement': total_engagement,
            'bullish_ratio': round(bullish_count / len(posts), 4) if posts else 0.5,
            'bearish_ratio': round(bearish_count / len(posts), 4) if posts else 0.5,
        }

    @staticmethod
    def extract_keywords(texts: List[str], top_n: int = 10) -> List[str]:
        """Extract trending keywords from texts."""
        word_freq = {}
        for text in texts:
            words = re.findall(r'\b\w+\b', text.lower())
            for word in words:
                if len(word) > 3:
                    word_freq[word] = word_freq.get(word, 0) + 1

        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:top_n]]

    @staticmethod
    def detect_sentiment_shift(current: float, historical: List[float]) -> Optional[Dict]:
        """Detect significant sentiment shifts by comparing current vs historical."""
        if not historical:
            return None

        import numpy as np
        avg = np.mean(historical)
        std = np.std(historical) if len(historical) > 1 else 0.1

        if std == 0:
            std = 0.1

        z_score = (current - avg) / std

        if abs(z_score) > 1.5:
            direction = 'positive' if current > avg else 'negative'
            return {
                'is_significant': True,
                'direction': direction,
                'z_score': round(float(z_score), 2),
                'current': current,
                'historical_avg': round(float(avg), 4),
                'shift_magnitude': round(float(abs(current - avg)), 4),
            }

        return None
