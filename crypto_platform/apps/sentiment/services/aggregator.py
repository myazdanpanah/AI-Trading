"""Sentiment aggregation service."""
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class SentimentAggregator:
    """Aggregate sentiment from multiple sources into a unified score."""

    @staticmethod
    def aggregate_sentiment(
        social_sentiment: float = 0,
        news_sentiment: float = 0,
        whale_sentiment: float = 0,
        influencer_sentiment: float = 0,
        fear_greed_value: int = 50,
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict:
        """Aggregate sentiment from all sources."""
        default_weights = {
            'social': 0.25,
            'news': 0.25,
            'whale': 0.20,
            'influencer': 0.15,
            'fear_greed': 0.15,
        }
        w = weights or default_weights

        # Normalize fear_greed to -1 to 1 scale
        fear_greed_normalized = (fear_greed_value - 50) / 50

        overall_score = (
            social_sentiment * w['social'] +
            news_sentiment * w['news'] +
            whale_sentiment * w['whale'] +
            influencer_sentiment * w['influencer'] +
            fear_greed_normalized * w['fear_greed']
        )

        overall_score = max(-1, min(1, overall_score))

        # Determine label
        if overall_score > 0.5:
            label = 'very_bullish'
        elif overall_score > 0.2:
            label = 'bullish'
        elif overall_score < -0.5:
            label = 'very_bearish'
        elif overall_score < -0.2:
            label = 'bearish'
        else:
            label = 'neutral'

        # Calculate confidence based on source agreement
        scores = [social_sentiment, news_sentiment, whale_sentiment, influencer_sentiment, fear_greed_normalized]
        non_zero_scores = [s for s in scores if s != 0]

        if len(non_zero_scores) >= 3:
            import numpy as np
            std = np.std(non_zero_scores)
            confidence = max(0.3, min(0.9, 0.9 - std * 0.5))
        else:
            confidence = 0.4

        return {
            'overall_score': round(overall_score, 4),
            'overall_label': label,
            'confidence': round(confidence, 2),
            'source_scores': {
                'social': round(social_sentiment, 4),
                'news': round(news_sentiment, 4),
                'whale': round(whale_sentiment, 4),
                'influencer': round(influencer_sentiment, 4),
                'fear_greed': round(fear_greed_normalized, 4),
            },
            'weights_used': w,
        }

    @staticmethod
    def detect_sentiment_divergence(source_scores: Dict[str, float]) -> Optional[Dict]:
        """Detect when sentiment sources diverge significantly."""
        scores = list(source_scores.values())
        if len(scores) < 3:
            return None

        import numpy as np
        mean_score = np.mean(scores)
        std_score = np.std(scores)

        if std_score > 0.4:
            # Find which sources diverge
            divergent = []
            for source, score in source_scores.items():
                if abs(score - mean_score) > std_score:
                    divergent.append({
                        'source': source,
                        'score': round(score, 4),
                        'deviation': round(score - mean_score, 4),
                    })

            return {
                'is_divergent': True,
                'mean_score': round(float(mean_score), 4),
                'std_score': round(float(std_score), 4),
                'divergent_sources': divergent,
                'interpretation': 'Mixed signals - some sources bullish, others bearish',
            }

        return {'is_divergent': False}

    @staticmethod
    def calculate_sentiment_momentum(
        historical_scores: List[float],
        window: int = 5,
    ) -> Dict:
        """Calculate sentiment momentum (rate of change)."""
        if len(historical_scores) < window + 1:
            return {'momentum': 0, 'trend': 'stable'}

        recent_avg = sum(historical_scores[-window:]) / window
        previous_avg = sum(historical_scores[-window*2:-window]) / window if len(historical_scores) >= window * 2 else sum(historical_scores[:-window]) / max(1, len(historical_scores) - window)

        momentum = recent_avg - previous_avg

        if momentum > 0.1:
            trend = 'improving'
        elif momentum < -0.1:
            trend = 'declining'
        else:
            trend = 'stable'

        return {
            'momentum': round(momentum, 4),
            'trend': trend,
            'recent_avg': round(recent_avg, 4),
            'previous_avg': round(previous_avg, 4),
            'is_significant': abs(momentum) > 0.2,
        }

    @staticmethod
    def generate_sentiment_summary(
        aggregated: Dict,
        momentum: Dict,
        divergence: Optional[Dict],
    ) -> str:
        """Generate human-readable sentiment summary."""
        label = aggregated.get('overall_label', 'neutral')
        score = aggregated.get('overall_score', 0)
        confidence = aggregated.get('confidence', 0)
        trend = momentum.get('trend', 'stable')

        summary_parts = [
            f"Overall sentiment is {label.replace('_', ' ')} with a score of {score:.2f}.",
        ]

        if confidence > 0.7:
            summary_parts.append("High confidence in this assessment.")
        elif confidence < 0.4:
            summary_parts.append("Low confidence - mixed signals from sources.")

        if trend == 'improving':
            summary_parts.append("Sentiment is trending upward.")
        elif trend == 'declining':
            summary_parts.append("Sentiment is trending downward.")

        if divergence and divergence.get('is_divergent'):
            sources = [d['source'] for d in divergence.get('divergent_sources', [])]
            summary_parts.append(f"Notable divergence detected in: {', '.join(sources)}.")

        return " ".join(summary_parts)
