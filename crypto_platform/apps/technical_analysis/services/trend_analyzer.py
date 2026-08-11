"""Trend analysis service."""
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyze market trends using multiple methods."""

    @staticmethod
    def calculate_adx(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        period: int = 14,
    ) -> Dict:
        """Calculate ADX (Average Directional Index) for trend strength."""
        if len(closes) < period * 2:
            return {'adx': 25, 'plus_di': 0, 'minus_di': 0, 'trend_strength': 'weak'}

        # Calculate True Range, +DM, -DM
        tr_list = []
        plus_dm_list = []
        minus_dm_list = []

        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            tr_list.append(tr)

            up_move = highs[i] - highs[i-1]
            down_move = lows[i-1] - lows[i]

            if up_move > down_move and up_move > 0:
                plus_dm_list.append(up_move)
            else:
                plus_dm_list.append(0)

            if down_move > up_move and down_move > 0:
                minus_dm_list.append(down_move)
            else:
                minus_dm_list.append(0)

        # Smoothed averages
        atr = np.mean(tr_list[:period])
        plus_dm = np.mean(plus_dm_list[:period])
        minus_dm = np.mean(minus_dm_list[:period])

        dx_values = []
        for i in range(period, len(tr_list)):
            atr = (atr * (period - 1) + tr_list[i]) / period
            plus_dm = (plus_dm * (period - 1) + plus_dm_list[i]) / period
            minus_dm = (minus_dm * (period - 1) + minus_dm_list[i]) / period

            if atr != 0:
                plus_di = (plus_dm / atr) * 100
                minus_di = (minus_dm / atr) * 100
            else:
                plus_di = 0
                minus_di = 0

            di_sum = plus_di + minus_di
            if di_sum != 0:
                dx = abs(plus_di - minus_di) / di_sum * 100
            else:
                dx = 0
            dx_values.append(dx)

        # ADX is smoothed DX
        adx = np.mean(dx_values[-period:]) if dx_values else 25

        # Determine trend strength
        if adx >= 50:
            strength = 'very_strong'
        elif adx >= 25:
            strength = 'strong'
        elif adx >= 20:
            strength = 'moderate'
        else:
            strength = 'weak'

        return {
            'adx': round(float(adx), 2),
            'plus_di': round(float(plus_di), 2),
            'minus_di': round(float(minus_di), 2),
            'trend_strength': strength,
            'trend_direction': 'up' if plus_di > minus_di else 'down',
        }

    @staticmethod
    def analyze_ema_alignment(closes: List[float]) -> Dict:
        """Analyze EMA alignment for trend direction."""
        if len(closes) < 50:
            return {'alignment': 'insufficient_data', 'signal': 'neutral'}

        def ema(data, period):
            arr = np.array(data)
            multiplier = 2 / (period + 1)
            ema_arr = np.zeros(len(arr))
            ema_arr[0] = arr[0]
            for i in range(1, len(arr)):
                ema_arr[i] = (arr[i] - ema_arr[i-1]) * multiplier + ema_arr[i-1]
            return ema_arr

        ema_9 = ema(closes, 9)
        ema_21 = ema(closes, 21)
        ema_50 = ema(closes, 50)

        current_price = closes[-1]
        current_ema9 = ema_9[-1]
        current_ema21 = ema_21[-1]
        current_ema50 = ema_50[-1]

        # Check alignment
        if current_price > current_ema9 > current_ema21 > current_ema50:
            alignment = 'bullish_aligned'
            signal = 'strong_bullish'
        elif current_price > current_ema9 > current_ema21:
            alignment = 'bullish_partial'
            signal = 'bullish'
        elif current_price < current_ema9 < current_ema21 < current_ema50:
            alignment = 'bearish_aligned'
            signal = 'strong_bearish'
        elif current_price < current_ema9 < current_ema21:
            alignment = 'bearish_partial'
            signal = 'bearish'
        else:
            alignment = 'mixed'
            signal = 'neutral'

        # Check for crossover
        if len(ema_9) >= 2 and len(ema_21) >= 2:
            if ema_9[-2] < ema_21[-2] and ema_9[-1] > ema_21[-1]:
                signal = 'bullish_cross'
            elif ema_9[-2] > ema_21[-2] and ema_9[-1] < ema_21[-1]:
                signal = 'bearish_cross'

        return {
            'alignment': alignment,
            'signal': signal,
            'ema_9': round(float(current_ema9), 8),
            'ema_21': round(float(current_ema21), 8),
            'ema_50': round(float(current_ema50), 8),
        }

    @staticmethod
    def detect_trend_direction(
        highs: List[float],
        lows: List[float],
        closes: List[float],
    ) -> Dict:
        """Detect overall trend direction using multiple methods."""
        if len(closes) < 20:
            return {'direction': 'unknown', 'confidence': 0}

        closes_arr = np.array(closes)

        # Linear regression slope
        x = np.arange(len(closes_arr))
        slope = np.polyfit(x, closes_arr, 1)[0]
        slope_percent = (slope / closes_arr.mean()) * 100

        # Higher highs / lower lows
        recent_highs = highs[-10:]
        recent_lows = lows[-10:]

        hh_count = sum(1 for i in range(1, len(recent_highs)) if recent_highs[i] > recent_highs[i-1])
        ll_count = sum(1 for i in range(1, len(recent_lows)) if recent_lows[i] < recent_lows[i-1])

        # Determine direction
        if slope_percent > 0.1 and hh_count > ll_count:
            direction = 'uptrend'
            confidence = min(100, int(abs(slope_percent) * 10 + hh_count * 5))
        elif slope_percent < -0.1 and ll_count > hh_count:
            direction = 'downtrend'
            confidence = min(100, int(abs(slope_percent) * 10 + ll_count * 5))
        else:
            direction = 'sideways'
            confidence = min(100, int(50 - abs(slope_percent) * 10))

        # Strong trend if > 0.3% per bar
        if abs(slope_percent) > 0.3:
            direction = f'strong_{direction}' if direction != 'sideways' else direction

        return {
            'direction': direction,
            'slope_percent': round(float(slope_percent), 4),
            'higher_highs': hh_count,
            'lower_lows': ll_count,
            'confidence': confidence,
        }

    @classmethod
    def analyze_trend(
        cls,
        highs: List[float],
        lows: List[float],
        closes: List[float],
    ) -> Dict:
        """Comprehensive trend analysis."""
        adx_result = cls.calculate_adx(highs, lows, closes)
        ema_result = cls.analyze_ema_alignment(closes)
        direction_result = cls.detect_trend_direction(highs, lows, closes)

        return {
            'adx': adx_result,
            'ema_alignment': ema_result,
            'direction': direction_result,
        }
