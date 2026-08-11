"""Smart money and institutional activity analysis service."""
import numpy as np
from typing import Dict, List, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class SmartMoneyAnalyzer:
    """Analyze smart money / institutional trading patterns."""

    @staticmethod
    def detect_accumulation(
        closes: List[float],
        volumes: List[float],
        lows: List[float],
        window: int = 20,
    ) -> Optional[Dict]:
        """Detect accumulation phase (smart money buying)."""
        if len(closes) < window:
            return None

        recent_closes = closes[-window:]
        recent_volumes = volumes[-window:]
        recent_lows = lows[-window:]

        # Price moving sideways or slightly down
        price_change = (recent_closes[-1] - recent_closes[0]) / recent_closes[0] * 100

        # Volume increasing on down days
        avg_volume = np.mean(recent_volumes)
        high_volume_days = sum(1 for v in recent_volumes if v > avg_volume * 1.2)

        # Higher lows forming
        low_trend = np.polyfit(range(window), recent_lows, 1)[0]

        if abs(price_change) < 5 and high_volume_days > window * 0.3 and low_trend > 0:
            return {
                'event_type': 'accumulation',
                'direction': 'bullish',
                'confidence': min(0.9, 0.5 + high_volume_days * 0.05),
                'volume_confirmation': high_volume_days > window * 0.4,
                'description': f'Sideways price action with increasing volume. {high_volume_days} high-volume days detected.',
            }

        return None

    @staticmethod
    def detect_distribution(
        closes: List[float],
        volumes: List[float],
        highs: List[float],
        window: int = 20,
    ) -> Optional[Dict]:
        """Detect distribution phase (smart money selling)."""
        if len(closes) < window:
            return None

        recent_closes = closes[-window:]
        recent_volumes = volumes[-window:]
        recent_highs = highs[-window:]

        # Price moving sideways or slightly up
        price_change = (recent_closes[-1] - recent_closes[0]) / recent_closes[0] * 100

        # Volume increasing on up days
        avg_volume = np.mean(recent_volumes)
        high_volume_days = sum(1 for v in recent_volumes if v > avg_volume * 1.2)

        # Lower highs forming
        high_trend = np.polyfit(range(window), recent_highs, 1)[0]

        if abs(price_change) < 5 and high_volume_days > window * 0.3 and high_trend < 0:
            return {
                'event_type': 'distribution',
                'direction': 'bearish',
                'confidence': min(0.9, 0.5 + high_volume_days * 0.05),
                'volume_confirmation': high_volume_days > window * 0.4,
                'description': f'Sideways price action with selling pressure. {high_volume_days} high-volume days detected.',
            }

        return None

    @staticmethod
    def detect_liquidity_sweep(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        window: int = 50,
    ) -> Optional[Dict]:
        """Detect liquidity sweep (stop hunt)."""
        if len(closes) < window:
            return None

        # Find recent swing high and low
        recent_high = max(highs[-window:])
        recent_low = min(lows[-window:])
        current_price = closes[-1]

        # Check if price swept above recent high then reversed
        if highs[-1] > recent_high and closes[-1] < recent_high:
            return {
                'event_type': 'liquidity_sweep',
                'direction': 'bearish',
                'price_level': float(recent_high),
                'confidence': 0.7,
                'description': f'Price swept above recent high ({recent_high}) then closed below.',
            }

        # Check if price swept below recent low then reversed
        if lows[-1] < recent_low and closes[-1] > recent_low:
            return {
                'event_type': 'liquidity_sweep',
                'direction': 'bullish',
                'price_level': float(recent_low),
                'confidence': 0.7,
                'description': f'Price swept below recent low ({recent_low}) then closed above.',
            }

        return None

    @staticmethod
    def detect_order_block(
        closes: List[float],
        volumes: List[float],
        window: int = 20,
    ) -> Optional[Dict]:
        """Detect order block (institutional order)."""
        if len(closes) < window + 5:
            return None

        # Look for large volume candle followed by price move
        recent_volumes = volumes[-window-5:-5]
        avg_volume = np.mean(recent_volumes)

        # Find the last significantly high volume candle
        for i in range(len(recent_volumes) - 1, -1, -1):
            if recent_volumes[i] > avg_volume * 2:
                # Check if price moved significantly after
                price_after = closes[-(window-5+i)]
                price_before = closes[-(window-5+i+1)]

                if abs(price_after - price_before) / price_before * 100 > 2:
                    direction = 'bullish' if price_after > price_before else 'bearish'
                    return {
                        'event_type': 'order_block',
                        'direction': direction,
                        'price_level': float(price_before),
                        'confidence': 0.65,
                        'volume_confirmation': True,
                        'description': f'High volume candle detected with significant price move.',
                    }

        return None

    @staticmethod
    def detect_fair_value_gap(
        highs: List[float],
        lows: List[float],
        window: int = 10,
    ) -> Optional[Dict]:
        """Detect fair value gap (imbalance)."""
        if len(highs) < window:
            return None

        # Check for gap between candle 1 high and candle 3 low (bullish gap)
        for i in range(-window, -2):
            gap = lows[i+2] - highs[i]
            if gap > 0:
                gap_percent = gap / highs[i] * 100
                if gap_percent > 0.1:
                    return {
                        'event_type': 'fair_value_gap',
                        'direction': 'bullish',
                        'price_level': float(highs[i]),
                        'gap_size': float(gap),
                        'confidence': min(0.8, 0.5 + gap_percent),
                        'description': f'Bullish FVG detected: {gap_percent:.2f}% gap.',
                    }

        # Check for gap between candle 1 low and candle 3 high (bearish gap)
        for i in range(-window, -2):
            gap = lows[i] - highs[i+2]
            if gap > 0:
                gap_percent = gap / lows[i] * 100
                if gap_percent > 0.1:
                    return {
                        'event_type': 'fair_value_gap',
                        'direction': 'bearish',
                        'price_level': float(lows[i]),
                        'gap_size': float(gap),
                        'confidence': min(0.8, 0.5 + gap_percent),
                        'description': f'Bearish FVG detected: {gap_percent:.2f}% gap.',
                    }

        return None

    @classmethod
    def analyze_all(
        cls,
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
    ) -> List[Dict]:
        """Analyze all smart money patterns."""
        events = []

        accumulation = cls.detect_accumulation(closes, volumes, lows)
        if accumulation:
            events.append(accumulation)

        distribution = cls.detect_distribution(closes, volumes, highs)
        if distribution:
            events.append(distribution)

        liquidity_sweep = cls.detect_liquidity_sweep(highs, lows, closes)
        if liquidity_sweep:
            events.append(liquidity_sweep)

        order_block = cls.detect_order_block(closes, volumes)
        if order_block:
            events.append(order_block)

        fvg = cls.detect_fair_value_gap(highs, lows)
        if fvg:
            events.append(fvg)

        return events
