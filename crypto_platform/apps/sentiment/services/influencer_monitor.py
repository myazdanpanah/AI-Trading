"""Influencer sentiment monitoring service."""
import math
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class InfluencerSentimentMonitor:
    """Monitor crypto influencer sentiment and credibility."""

    @staticmethod
    def calculate_credibility_score(
        follower_count: int,
        engagement_rate: float,
        historical_accuracy: float,
        account_age_days: int,
    ) -> float:
        """Calculate influencer credibility score (0-1)."""
        follower_score = min(1.0, math.log10(max(1, follower_count)) / 8)
        engagement_score = min(1.0, engagement_rate / 10)
        accuracy_score = max(0, min(1, historical_accuracy))
        age_score = min(1.0, account_age_days / 365)

        credibility = (
            follower_score * 0.2 +
            engagement_score * 0.2 +
            accuracy_score * 0.4 +
            age_score * 0.2
        )
        return round(credibility, 4)

    @staticmethod
    def analyze_influencer_post(
        content: str,
        sentiment_keywords: Dict[str, List[str]],
    ) -> Dict:
        """Analyze sentiment of an influencer post."""
        content_lower = content.lower()

        scores = {}
        for sentiment, keywords in sentiment_keywords.items():
            count = sum(1 for kw in keywords if kw in content_lower)
            scores[sentiment] = count

        total = sum(scores.values())
        if total == 0:
            return {'score': 0, 'label': 'neutral', 'confidence': 0.3}

        bullish = scores.get('bullish', 0)
        bearish = scores.get('bearish', 0)

        score = (bullish - bearish) / total

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

        confidence = min(0.9, 0.3 + total * 0.1)

        return {
            'score': round(score, 4),
            'label': label,
            'confidence': round(confidence, 2),
            'keyword_hits': total,
        }

    @staticmethod
    def aggregate_influencer_sentiment(posts: List[Dict]) -> Dict:
        """Aggregate sentiment from multiple influencer posts."""
        if not posts:
            return {
                'score': 0,
                'label': 'neutral',
                'confidence': 0,
                'post_count': 0,
            }

        weighted_scores = []
        total_weight = 0

        for post in posts:
            score = post.get('sentiment_score', 0)
            credibility = post.get('credibility_score', 0.5)
            followers = post.get('followers', 0)

            follower_weight = math.log10(max(1, followers)) / 8
            weight = credibility * 0.6 + follower_weight * 0.4

            weighted_scores.append(score * weight)
            total_weight += weight

        avg_score = sum(weighted_scores) / total_weight if total_weight > 0 else 0

        if avg_score > 0.5:
            label = 'very_bullish'
        elif avg_score > 0.2:
            label = 'bullish'
        elif avg_score < -0.5:
            label = 'very_bearish'
        elif avg_score < -0.2:
            label = 'bearish'
        else:
            label = 'neutral'

        confidence = min(0.9, 0.3 + len(posts) * 0.05)

        return {
            'score': round(avg_score, 4),
            'label': label,
            'confidence': round(confidence, 2),
            'post_count': len(posts),
            'total_weight': round(total_weight, 4),
        }

    @staticmethod
    def detect_influencer_consensus(posts: List[Dict]) -> Optional[Dict]:
        """Detect if influencers are reaching a consensus sentiment."""
        if len(posts) < 3:
            return None

        scores = [p.get('sentiment_score', 0) for p in posts]
        bullish_count = sum(1 for s in scores if s > 0.2)
        bearish_count = sum(1 for s in scores if s < -0.2)
        total = len(scores)

        bullish_ratio = bullish_count / total
        bearish_ratio = bearish_count / total

        if bullish_ratio > 0.7:
            return {
                'consensus': 'bullish',
                'ratio': round(bullish_ratio, 2),
                'post_count': total,
                'confidence': min(0.9, 0.5 + bullish_ratio * 0.4),
            }
        elif bearish_ratio > 0.7:
            return {
                'consensus': 'bearish',
                'ratio': round(bearish_ratio, 2),
                'post_count': total,
                'confidence': min(0.9, 0.5 + bearish_ratio * 0.4),
            }

        return {
            'consensus': 'mixed',
            'ratio': round(max(bullish_ratio, bearish_ratio), 2),
            'post_count': total,
            'confidence': 0.3,
        }
