"""Technical indicator calculation engine."""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class IndicatorEngine:
    """Calculate technical indicators from OHLCV data."""

    @staticmethod
    def calculate_rsi(closes: List[float], period: int = 14) -> Dict:
        """Calculate RSI (Relative Strength Index)."""
        if len(closes) < period + 1:
            return {'value': 50, 'signal': 'neutral', 'strength': 0}

        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        # Calculate smoothed RSI
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

        # Determine signal
        if rsi >= 70:
            signal = 'bearish'
            strength = min(100, int((rsi - 70) * 5))
        elif rsi <= 30:
            signal = 'bullish'
            strength = min(100, int((30 - rsi) * 5))
        else:
            signal = 'neutral'
            strength = 0

        return {
            'value': round(rsi, 2),
            'signal': signal,
            'strength': strength,
            'period': period,
        }

    @staticmethod
    def calculate_macd(
        closes: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> Dict:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        if len(closes) < slow_period + signal_period:
            return {'macd': 0, 'signal': 0, 'histogram': 0, 'trend': 'neutral'}

        closes_arr = np.array(closes)

        # Calculate EMAs
        def ema(data, period):
            multiplier = 2 / (period + 1)
            ema_arr = np.zeros(len(data))
            ema_arr[0] = data[0]
            for i in range(1, len(data)):
                ema_arr[i] = (data[i] - ema_arr[i-1]) * multiplier + ema_arr[i-1]
            return ema_arr

        ema_fast = ema(closes_arr, fast_period)
        ema_slow = ema(closes_arr, slow_period)

        macd_line = ema_fast - ema_slow
        signal_line = ema(macd_line, signal_period)
        histogram = macd_line - signal_line

        current_macd = macd_line[-1]
        current_signal = signal_line[-1]
        current_histogram = histogram[-1]

        # Determine trend
        if current_histogram > 0 and current_macd > current_signal:
            trend = 'bullish'
        elif current_histogram < 0 and current_macd < current_signal:
            trend = 'bearish'
        else:
            trend = 'neutral'

        # Check for crossover
        if len(histogram) >= 2:
            if histogram[-2] <= 0 and histogram[-1] > 0:
                trend = 'bullish_cross'
            elif histogram[-2] >= 0 and histogram[-1] < 0:
                trend = 'bearish_cross'

        return {
            'macd': round(float(current_macd), 6),
            'signal': round(float(current_signal), 6),
            'histogram': round(float(current_histogram), 6),
            'trend': trend,
        }

    @staticmethod
    def calculate_bollinger_bands(
        closes: List[float],
        period: int = 20,
        std_dev: float = 2.0,
    ) -> Dict:
        """Calculate Bollinger Bands."""
        if len(closes) < period:
            return {'upper': 0, 'middle': 0, 'lower': 0, 'width': 0, 'position': 0.5}

        closes_arr = np.array(closes[-period:])
        middle = np.mean(closes_arr)
        std = np.std(closes_arr)

        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        current_price = closes[-1]
        width = (upper - lower) / middle * 100
        position = (current_price - lower) / (upper - lower) if upper != lower else 0.5

        # Determine signal
        if current_price <= lower:
            signal = 'bullish'
            strength = min(100, int((lower - current_price) / std * 50))
        elif current_price >= upper:
            signal = 'bearish'
            strength = min(100, int((current_price - upper) / std * 50))
        else:
            signal = 'neutral'
            strength = 0

        return {
            'upper': round(upper, 8),
            'middle': round(middle, 8),
            'lower': round(lower, 8),
            'width': round(width, 2),
            'position': round(position, 4),
            'signal': signal,
            'strength': strength,
            'period': period,
        }

    @staticmethod
    def calculate_ema(closes: List[float], period: int) -> Dict:
        """Calculate EMA (Exponential Moving Average)."""
        if len(closes) < period:
            return {'value': closes[-1] if closes else 0, 'signal': 'neutral'}

        closes_arr = np.array(closes)
        multiplier = 2 / (period + 1)
        ema_arr = np.zeros(len(closes_arr))
        ema_arr[0] = closes_arr[0]

        for i in range(1, len(closes_arr)):
            ema_arr[i] = (closes_arr[i] - ema_arr[i-1]) * multiplier + ema_arr[i-1]

        current_ema = ema_arr[-1]
        current_price = closes[-1]

        if current_price > current_ema:
            signal = 'bullish'
        elif current_price < current_ema:
            signal = 'bearish'
        else:
            signal = 'neutral'

        return {
            'value': round(float(current_ema), 8),
            'price_above': current_price > current_ema,
            'signal': signal,
            'period': period,
        }

    @staticmethod
    def calculate_atr(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        period: int = 14,
    ) -> Dict:
        """Calculate ATR (Average True Range)."""
        if len(closes) < period + 1:
            return {'value': 0, 'volatility': 'normal'}

        true_ranges = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            true_ranges.append(tr)

        if len(true_ranges) < period:
            return {'value': 0, 'volatility': 'normal'}

        atr = np.mean(true_ranges[-period:])
        current_price = closes[-1]
        atr_percent = (atr / current_price) * 100

        # Determine volatility level
        if atr_percent > 5:
            volatility = 'very_high'
        elif atr_percent > 3:
            volatility = 'high'
        elif atr_percent > 1:
            volatility = 'normal'
        elif atr_percent > 0.5:
            volatility = 'low'
        else:
            volatility = 'very_low'

        return {
            'value': round(float(atr), 8),
            'percent': round(atr_percent, 2),
            'volatility': volatility,
            'period': period,
        }

    @staticmethod
    def calculate_stochastic(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        k_period: int = 14,
        d_period: int = 3,
    ) -> Dict:
        """Calculate Stochastic Oscillator."""
        if len(closes) < k_period:
            return {'k': 50, 'd': 50, 'signal': 'neutral'}

        # Calculate %K
        highest_high = max(highs[-k_period:])
        lowest_low = min(lows[-k_period:])
        current_close = closes[-1]

        if highest_high == lowest_low:
            k = 50
        else:
            k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100

        # Calculate %D (SMA of %K)
        k_values = []
        for i in range(k_period, len(closes)):
            hh = max(highs[i-k_period:i+1])
            ll = min(lows[i-k_period:i+1])
            if hh == ll:
                k_values.append(50)
            else:
                k_values.append(((closes[i] - ll) / (hh - ll)) * 100)

        d = np.mean(k_values[-d_period:]) if len(k_values) >= d_period else k

        # Determine signal
        if k > 80 and d > 80:
            signal = 'bearish'
        elif k < 20 and d < 20:
            signal = 'bullish'
        elif k > d and len(k_values) >= 2 and k_values[-2] <= np.mean(k_values[-d_period-1:-1]):
            signal = 'bullish_cross'
        elif k < d and len(k_values) >= 2 and k_values[-2] >= np.mean(k_values[-d_period-1:-1]):
            signal = 'bearish_cross'
        else:
            signal = 'neutral'

        return {
            'k': round(float(k), 2),
            'd': round(float(d), 2),
            'signal': signal,
            'k_period': k_period,
            'd_period': d_period,
        }

    @staticmethod
    def calculate_vwap(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
        period: int = 20,
    ) -> Dict:
        """Calculate VWAP (Volume Weighted Average Price)."""
        if len(closes) < period:
            return {'value': closes[-1] if closes else 0, 'signal': 'neutral', 'deviation': 0}

        # Calculate typical price * volume for each bar
        typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs[-period:], lows[-period:], closes[-period:])]
        recent_volumes = volumes[-period:]

        cum_tp_vol = sum(tp * v for tp, v in zip(typical_prices, recent_volumes))
        cum_vol = sum(recent_volumes)

        if cum_vol == 0:
            vwap = closes[-1]
        else:
            vwap = cum_tp_vol / cum_vol

        current_price = closes[-1]
        deviation = ((current_price - vwap) / vwap) * 100 if vwap > 0 else 0

        # Calculate upper/lower VWAP bands (1 std dev)
        variance = sum(((tp - vwap) ** 2) * v for tp, v in zip(typical_prices, recent_volumes)) / cum_vol if cum_vol > 0 else 0
        std_dev = variance ** 0.5
        upper_band = vwap + std_dev
        lower_band = vwap - std_dev

        # Determine signal
        if current_price > vwap and deviation > 1:
            signal = 'bearish'  # Extended above VWAP
        elif current_price < vwap and deviation < -1:
            signal = 'bullish'  # Extended below VWAP
        elif current_price > vwap:
            signal = 'bullish'  # Above VWAP
        elif current_price < vwap:
            signal = 'bearish'  # Below VWAP
        else:
            signal = 'neutral'

        return {
            'value': round(float(vwap), 8),
            'upper_band': round(float(upper_band), 8),
            'lower_band': round(float(lower_band), 8),
            'deviation': round(float(deviation), 2),
            'signal': signal,
            'period': period,
        }

    @staticmethod
    def calculate_ichimoku(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        tenkan_period: int = 9,
        kijun_period: int = 26,
        senkou_b_period: int = 52,
    ) -> Dict:
        """Calculate Ichimoku Cloud indicators."""
        if len(closes) < senkou_b_period:
            return {
                'tenkan_sen': closes[-1] if closes else 0,
                'kijun_sen': closes[-1] if closes else 0,
                'senkou_a': closes[-1] if closes else 0,
                'senkou_b': closes[-1] if closes else 0,
                'chikou_span': closes[-1] if closes else 0,
                'signal': 'neutral',
                'cloud_color': 'neutral',
            }

        # Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
        tenkan_high = max(highs[-tenkan_period:])
        tenkan_low = min(lows[-tenkan_period:])
        tenkan_sen = (tenkan_high + tenkan_low) / 2

        # Kijun-sen (Base Line): (26-period high + 26-period low) / 2
        kijun_high = max(highs[-kijun_period:])
        kijun_low = min(lows[-kijun_period:])
        kijun_sen = (kijun_high + kijun_low) / 2

        # Senkou Span A (Leading Span 1): (Tenkan + Kijun) / 2
        senkou_a = (tenkan_sen + kijun_sen) / 2

        # Senkou Span B (Leading Span 2): (52-period high + 52-period low) / 2
        senkou_b_high = max(highs[-senkou_b_period:])
        senkou_b_low = min(lows[-senkou_b_period:])
        senkou_b = (senkou_b_high + senkou_b_low) / 2

        # Chikou Span (Lagging Span): current close, shifted back 26 periods
        chikou_span = closes[-1]

        current_price = closes[-1]

        # Determine cloud color
        if senkou_a > senkou_b:
            cloud_color = 'bullish'  # Green cloud
        elif senkou_a < senkou_b:
            cloud_color = 'bearish'  # Red cloud
        else:
            cloud_color = 'neutral'

        # Determine overall signal
        above_cloud = current_price > max(senkou_a, senkou_b)
        below_cloud = current_price < min(senkou_a, senkou_b)
        tk_cross_bullish = tenkan_sen > kijun_sen

        if above_cloud and tk_cross_bullish and cloud_color == 'bullish':
            signal = 'strong_bullish'
        elif above_cloud:
            signal = 'bullish'
        elif below_cloud and not tk_cross_bullish and cloud_color == 'bearish':
            signal = 'strong_bearish'
        elif below_cloud:
            signal = 'bearish'
        else:
            signal = 'neutral'  # In the cloud

        return {
            'tenkan_sen': round(float(tenkan_sen), 8),
            'kijun_sen': round(float(kijun_sen), 8),
            'senkou_a': round(float(senkou_a), 8),
            'senkou_b': round(float(senkou_b), 8),
            'chikou_span': round(float(chikou_span), 8),
            'cloud_color': cloud_color,
            'above_cloud': above_cloud,
            'below_cloud': below_cloud,
            'tk_cross': 'bullish' if tk_cross_bullish else 'bearish',
            'signal': signal,
        }

    @classmethod
    def calculate_all_indicators(cls, candle_data: List[Dict]) -> Dict:
        """Calculate all indicators from candle data."""
        if not candle_data:
            return {}

        closes = [float(c['close']) for c in candle_data]
        highs = [float(c['high']) for c in candle_data]
        lows = [float(c['low']) for c in candle_data]
        volumes = [float(c['volume']) for c in candle_data]

        return {
            'rsi_14': cls.calculate_rsi(closes, 14),
            'rsi_7': cls.calculate_rsi(closes, 7),
            'macd': cls.calculate_macd(closes),
            'bollinger_bands': cls.calculate_bollinger_bands(closes),
            'ema_9': cls.calculate_ema(closes, 9),
            'ema_21': cls.calculate_ema(closes, 21),
            'ema_50': cls.calculate_ema(closes, 50),
            'atr_14': cls.calculate_atr(highs, lows, closes, 14),
            'stochastic': cls.calculate_stochastic(highs, lows, closes),
            'vwap': cls.calculate_vwap(highs, lows, closes, volumes),
            'ichimoku': cls.calculate_ichimoku(highs, lows, closes),
        }
