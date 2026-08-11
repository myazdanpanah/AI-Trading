"""Support and Resistance level analysis service."""
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class SRAnalyzer:
    """Analyze support and resistance levels."""

    @staticmethod
    def find_support_resistance_levels(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        window: int = 20,
        num_levels: int = 5,
    ) -> Dict:
        """Find support and resistance levels using multiple methods."""
        all_prices = []
        for i in range(len(highs)):
            all_prices.append(highs[i])
            all_prices.append(lows[i])
            all_prices.append(closes[i])

        # Method 1: Pivot points
        pivot_levels = SRAnalyzer._find_pivot_levels(highs, lows, closes)

        # Method 2: Price clustering
        cluster_levels = SRAnalyzer._find_cluster_levels(all_prices)

        # Method 3: Historical S/R
        historical_levels = SRAnalyzer._find_historical_sr(highs, lows, closes, window)

        # Combine and rank levels
        all_levels = {}
        for level in pivot_levels + cluster_levels + historical_levels:
            price = round(level['price'], 8)
            if price in all_levels:
                all_levels[price]['touch_count'] += level.get('touch_count', 1)
                all_levels[price]['methods'].append(level['method'])
            else:
                all_levels[price] = {
                    'price': price,
                    'touch_count': level.get('touch_count', 1),
                    'methods': [level['method']],
                }

        # Sort by touch count and method diversity
        sorted_levels = sorted(
            all_levels.values(),
            key=lambda x: (x['touch_count'], len(x['methods'])),
            reverse=True
        )[:num_levels * 2]

        current_price = closes[-1]
        support_levels = []
        resistance_levels = []

        for level in sorted_levels:
            strength = min(100, level['touch_count'] * 15 + len(level['methods']) * 10)
            level_data = {
                'price': level['price'],
                'strength': strength,
                'touch_count': level['touch_count'],
                'methods': level['methods'],
            }
            if level['price'] < current_price:
                support_levels.append(level_data)
            else:
                resistance_levels.append(level_data)

        return {
            'support': sorted(support_levels, key=lambda x: x['price'], reverse=True)[:num_levels],
            'resistance': sorted(resistance_levels, key=lambda x: x['price'])[:num_levels],
            'current_price': current_price,
        }

    @staticmethod
    def _find_pivot_points(
        highs: List[float],
        lows: List[float],
        closes: List[float],
    ) -> Dict:
        """Calculate pivot points."""
        if not highs or not lows or not closes:
            return {}

        high = max(highs[-24:]) if len(highs) >= 24 else max(highs)
        low = min(lows[-24:]) if len(lows) >= 24 else min(lows)
        close = closes[-1]

        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)

        return {
            'pivot': pivot,
            'r1': r1, 'r2': r2, 'r3': r3,
            's1': s1, 's2': s2, 's3': s3,
        }

    @staticmethod
    def _find_pivot_levels(
        highs: List[float],
        lows: List[float],
        closes: List[float],
    ) -> List[Dict]:
        """Find S/R levels using pivot points."""
        pivots = SRAnalyzer._find_pivot_points(highs, lows, closes)
        levels = []

        for key, price in pivots.items():
            if key.startswith('r'):
                levels.append({'price': price, 'method': 'pivot_point', 'touch_count': 1})
            elif key.startswith('s'):
                levels.append({'price': price, 'method': 'pivot_point', 'touch_count': 1})

        return levels

    @staticmethod
    def _find_cluster_levels(prices: List[float], num_clusters: int = 10) -> List[Dict]:
        """Find S/R levels using price clustering."""
        if not prices:
            return []

        prices_arr = np.array(prices)

        # Simple k-means-like clustering
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price

        if price_range == 0:
            return [{'price': min_price, 'method': 'cluster', 'touch_count': len(prices)}]

        cluster_size = price_range / num_clusters
        clusters = []

        for i in range(num_clusters):
            cluster_min = min_price + i * cluster_size
            cluster_max = cluster_min + cluster_size
            cluster_prices = [p for p in prices if cluster_min <= p < cluster_max]

            if cluster_prices:
                cluster_center = np.mean(cluster_prices)
                clusters.append({
                    'price': float(cluster_center),
                    'method': 'cluster',
                    'touch_count': len(cluster_prices),
                })

        return clusters

    @staticmethod
    def _find_historical_sr(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        window: int = 20,
    ) -> List[Dict]:
        """Find historical support/resistance levels."""
        levels = []

        # Find local maxima (resistance) and minima (support)
        for i in range(window, len(highs) - window):
            # Local maximum
            if highs[i] == max(highs[i-window:i+window+1]):
                levels.append({
                    'price': highs[i],
                    'method': 'historical_high',
                    'touch_count': 1,
                })

            # Local minimum
            if lows[i] == min(lows[i-window:i+window+1]):
                levels.append({
                    'price': lows[i],
                    'method': 'historical_low',
                    'touch_count': 1,
                })

        return levels

    @staticmethod
    def calculate_distance_to_levels(
        current_price: float,
        support_levels: List[Dict],
        resistance_levels: List[Dict],
    ) -> Dict:
        """Calculate distance to nearest support/resistance."""
        nearest_support = None
        nearest_resistance = None
        min_support_distance = float('inf')
        min_resistance_distance = float('inf')

        for level in support_levels:
            distance = current_price - level['price']
            if 0 < distance < min_support_distance:
                min_support_distance = distance
                nearest_support = level

        for level in resistance_levels:
            distance = level['price'] - current_price
            if 0 < distance < min_resistance_distance:
                min_resistance_distance = distance
                nearest_resistance = level

        return {
            'nearest_support': nearest_support,
            'nearest_resistance': nearest_resistance,
            'support_distance_percent': round(min_support_distance / current_price * 100, 2) if nearest_support else None,
            'resistance_distance_percent': round(min_resistance_distance / current_price * 100, 2) if nearest_resistance else None,
        }
