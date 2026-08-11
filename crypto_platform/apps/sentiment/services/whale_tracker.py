"""Whale activity tracking service."""
from typing import Dict, List, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class WhaleActivityTracker:
    """Track and analyze whale wallet activity."""

    # Thresholds for whale classification (in USD)
    WHALE_THRESHOLDS = {
        'small_whale': 100_000,
        'medium_whale': 1_000_000,
        'large_whale': 10_000_000,
        'mega_whale': 100_000_000,
    }

    @staticmethod
    def classify_whale(usd_value: float) -> str:
        """Classify whale size based on USD value."""
        if usd_value >= 100_000_000:
            return 'mega_whale'
        elif usd_value >= 10_000_000:
            return 'large_whale'
        elif usd_value >= 1_000_000:
            return 'medium_whale'
        elif usd_value >= 100_000:
            return 'small_whale'
        else:
            return 'retail'

    @staticmethod
    def analyze_whale_movement(
        balance_change: Decimal,
        balance_before: Decimal,
        transaction_type: str,
    ) -> Dict:
        """Analyze whale movement and predict sentiment impact."""
        if balance_before == 0:
            percent_change = 100
        else:
            percent_change = float(balance_change / balance_before * 100)

        # Determine sentiment impact
        if transaction_type == 'exchange_deposit':
            # Whale depositing to exchange = potential sell
            sentiment = 'bearish'
            confidence = min(0.9, 0.5 + abs(percent_change) * 0.05)
        elif transaction_type == 'exchange_withdrawal':
            # Whale withdrawing from exchange = holding
            sentiment = 'bullish'
            confidence = min(0.9, 0.5 + abs(percent_change) * 0.05)
        elif transaction_type == 'accumulation':
            sentiment = 'bullish'
            confidence = 0.7
        elif transaction_type == 'distribution':
            sentiment = 'bearish'
            confidence = 0.7
        else:
            sentiment = 'neutral'
            confidence = 0.5

        return {
            'sentiment': sentiment,
            'confidence': round(confidence, 2),
            'percent_change': round(percent_change, 2),
            'is_significant': abs(percent_change) > 10,
        }

    @staticmethod
    def calculate_whale_score(activities: List[Dict]) -> Dict:
        """Calculate overall whale sentiment score."""
        if not activities:
            return {'score': 0, 'label': 'neutral', 'confidence': 0}

        bullish_count = sum(1 for a in activities if a.get('sentiment') == 'bullish')
        bearish_count = sum(1 for a in activities if a.get('sentiment') == 'bearish')
        total = len(activities)

        score = (bullish_count - bearish_count) / total if total > 0 else 0

        if score > 0.3:
            label = 'bullish'
        elif score < -0.3:
            label = 'bearish'
        else:
            label = 'neutral'

        confidence = min(0.9, 0.5 + abs(score) * 0.5)

        return {
            'score': round(score, 4),
            'label': label,
            'confidence': round(confidence, 2),
            'total_activities': total,
            'bullish_activities': bullish_count,
            'bearish_activities': bearish_count,
        }

    @staticmethod
    def detect_accumulation_pattern(activities: List[Dict]) -> Optional[Dict]:
        """Detect whale accumulation pattern."""
        if len(activities) < 5:
            return None

        # Check for consistent buying pattern
        deposits = [a for a in activities if a.get('transaction_type') == 'exchange_withdrawal']
        if len(deposits) >= 3:
            total_volume = sum(float(a.get('usd_value', 0)) for a in deposits)
            avg_volume = total_volume / len(deposits)

            return {
                'pattern': 'accumulation',
                'signal': 'bullish',
                'confidence': min(0.85, 0.6 + len(deposits) * 0.05),
                'total_volume': total_volume,
                'activity_count': len(deposits),
                'avg_volume': avg_volume,
            }

        return None

    @staticmethod
    def detect_distribution_pattern(activities: List[Dict]) -> Optional[Dict]:
        """Detect whale distribution pattern."""
        if len(activities) < 5:
            return None

        # Check for consistent selling pattern
        withdrawals = [a for a in activities if a.get('transaction_type') == 'exchange_deposit']
        if len(withdrawals) >= 3:
            total_volume = sum(float(a.get('usd_value', 0)) for a in withdrawals)
            avg_volume = total_volume / len(withdrawals)

            return {
                'pattern': 'distribution',
                'signal': 'bearish',
                'confidence': min(0.85, 0.6 + len(withdrawals) * 0.05),
                'total_volume': total_volume,
                'activity_count': len(withdrawals),
                'avg_volume': avg_volume,
            }

        return None
