"""Chart pattern detection service."""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PatternDetector:
    """Detect chart patterns from OHLCV data."""

    @staticmethod
    def detect_double_top(highs: List[float], closes: List[float], window: int = 20) -> Optional[Dict]:
        """Detect double top pattern."""
        if len(highs) < window * 2:
            return None

        # Find two peaks
        peaks = []
        for i in range(window, len(highs) - window):
            if highs[i] == max(highs[i-window:i+window+1]):
                peaks.append(i)

        if len(peaks) < 2:
            return None

        # Check if peaks are similar in price
        peak1_idx, peak2_idx = peaks[-2], peaks[-1]
        peak1_price = highs[peak1_idx]
        peak2_price = highs[peak2_idx]

        price_diff_percent = abs(peak1_price - peak2_price) / peak1_price * 100

        if price_diff_percent < 3:  # Peaks within 3% of each other
            # Find the trough between peaks
            trough_idx = peak1_idx + np.argmin(closes[peak1_idx:peak2_idx+1])
            trough_price = closes[trough_idx]

            # Neckline is at the trough level
            neckline = trough_price

            return {
                'pattern_type': 'double_top',
                'direction': 'bearish',
                'peak1_price': peak1_price,
                'peak2_price': peak2_price,
                'neckline': neckline,
                'target': neckline - (peak1_price - neckline),
                'confidence': max(0.5, 1 - price_diff_percent / 5),
            }

        return None

    @staticmethod
    def detect_double_bottom(lows: List[float], closes: List[float], window: int = 20) -> Optional[Dict]:
        """Detect double bottom pattern."""
        if len(lows) < window * 2:
            return None

        # Find two troughs
        troughs = []
        for i in range(window, len(lows) - window):
            if lows[i] == min(lows[i-window:i+window+1]):
                troughs.append(i)

        if len(troughs) < 2:
            return None

        # Check if troughs are similar in price
        trough1_idx, trough2_idx = troughs[-2], troughs[-1]
        trough1_price = lows[trough1_idx]
        trough2_price = lows[trough2_idx]

        price_diff_percent = abs(trough1_price - trough2_price) / trough1_price * 100

        if price_diff_percent < 3:
            # Find the peak between troughs
            peak_idx = trough1_idx + np.argmax(closes[trough1_idx:trough2_idx+1])
            peak_price = closes[peak_idx]

            neckline = peak_price

            return {
                'pattern_type': 'double_bottom',
                'direction': 'bullish',
                'trough1_price': trough1_price,
                'trough2_price': trough2_price,
                'neckline': neckline,
                'target': neckline + (neckline - trough1_price),
                'confidence': max(0.5, 1 - price_diff_percent / 5),
            }

        return None

    @staticmethod
    def detect_head_shoulders(highs: List[float], closes: List[float], window: int = 15) -> Optional[Dict]:
        """Detect head and shoulders pattern."""
        if len(highs) < window * 3:
            return None

        # Find peaks
        peaks = []
        for i in range(window, len(highs) - window):
            if highs[i] == max(highs[i-window:i+window+1]):
                peaks.append(i)

        if len(peaks) < 3:
            return None

        # Check last three peaks
        left_idx, head_idx, right_idx = peaks[-3], peaks[-2], peaks[-1]
        left_price = highs[left_idx]
        head_price = highs[head_idx]
        right_price = highs[right_idx]

        # Head should be higher than shoulders
        if head_price > left_price and head_price > right_price:
            # Shoulders should be similar
            shoulder_diff = abs(left_price - right_price) / left_price * 100
            if shoulder_diff < 5:
                # Find neckline (troughs between peaks)
                trough1 = min(closes[left_idx:head_idx+1])
                trough2 = min(closes[head_idx:right_idx+1])
                neckline = max(trough1, trough2)

                return {
                    'pattern_type': 'head_shoulders',
                    'direction': 'bearish',
                    'left_shoulder': left_price,
                    'head': head_price,
                    'right_shoulder': right_price,
                    'neckline': neckline,
                    'target': neckline - (head_price - neckline),
                    'confidence': max(0.5, 1 - shoulder_diff / 10),
                }

        return None

    @staticmethod
    def detect_triangle(highs: List[float], lows: List[float], window: int = 20) -> Optional[Dict]:
        """Detect triangle patterns (ascending, descending, symmetrical)."""
        if len(highs) < window * 2:
            return None

        # Get recent highs and lows
        recent_highs = highs[-window:]
        recent_lows = lows[-window:]

        # Calculate trend lines
        high_slope = np.polyfit(range(window), recent_highs, 1)[0]
        low_slope = np.polyfit(range(window), recent_lows, 1)[0]

        # Determine pattern type
        if high_slope < 0 and low_slope > 0:
            pattern_type = 'symmetrical_triangle'
            direction = 'neutral'
        elif high_slope < 0 and abs(low_slope) < abs(high_slope) * 0.3:
            pattern_type = 'descending_triangle'
            direction = 'bearish'
        elif low_slope > 0 and abs(high_slope) < abs(low_slope) * 0.3:
            pattern_type = 'ascending_triangle'
            direction = 'bullish'
        else:
            return None

        # Calculate convergence point
        if high_slope != low_slope:
            convergence_idx = (low_slope * window - high_slope * 0 - recent_lows[0] + recent_highs[0]) / (high_slope - low_slope)
        else:
            convergence_idx = window

        return {
            'pattern_type': pattern_type,
            'direction': direction,
            'high_slope': round(float(high_slope), 6),
            'low_slope': round(float(low_slope), 6),
            'convergence_distance': int(convergence_idx),
            'confidence': 0.6,
        }

    @staticmethod
    def detect_flag(
        closes: List[float],
        volumes: List[float],
        window: int = 20,
        flag_window: int = 10,
    ) -> Optional[Dict]:
        """Detect bull/bear flag patterns."""
        if len(closes) < window + flag_window:
            return None

        # Check for flagpole (strong move)
        pole_start = closes[-(window + flag_window)]
        pole_end = closes[-flag_window]
        pole_move_percent = (pole_end - pole_start) / pole_start * 100

        if abs(pole_move_percent) < 5:
            return None

        # Check for flag (consolidation)
        flag_closes = closes[-flag_window:]
        flag_high = max(flag_closes)
        flag_low = min(flag_closes)
        flag_range = (flag_high - flag_low) / flag_low * 100

        if flag_range > 5:  # Flag too wide
            return None

        # Determine pattern
        if pole_move_percent > 0:
            pattern_type = 'bull_flag'
            direction = 'bullish'
            target = pole_end + (pole_end - pole_start)
        else:
            pattern_type = 'bear_flag'
            direction = 'bearish'
            target = pole_end - (pole_start - pole_end)

        return {
            'pattern_type': pattern_type,
            'direction': direction,
            'pole_move_percent': round(pole_move_percent, 2),
            'flag_range_percent': round(flag_range, 2),
            'target': round(target, 8),
            'confidence': max(0.5, 1 - flag_range / 10),
        }

    @classmethod
    def detect_all_patterns(
        cls,
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float] = None,
    ) -> List[Dict]:
        """Detect all patterns in the data."""
        patterns = []

        # Double top/bottom
        double_top = cls.detect_double_top(highs, closes)
        if double_top:
            patterns.append(double_top)

        double_bottom = cls.detect_double_bottom(lows, closes)
        if double_bottom:
            patterns.append(double_bottom)

        # Head and shoulders
        hs = cls.detect_head_shoulders(highs, closes)
        if hs:
            patterns.append(hs)

        # Triangles
        triangle = cls.detect_triangle(highs, lows)
        if triangle:
            patterns.append(triangle)

        # Flags
        if volumes:
            flag = cls.detect_flag(closes, volumes)
            if flag:
                patterns.append(flag)

        return patterns
