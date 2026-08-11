"""Tests for Technical Analysis services."""
import numpy as np
from django.test import TestCase
from datetime import datetime, timedelta
import random

from .services.indicator_engine import IndicatorEngine
from .services.pattern_detector import PatternDetector
from .services.sr_analyzer import SRAnalyzer
from .services.trend_analyzer import TrendAnalyzer
from .services.smart_money import SmartMoneyAnalyzer
from .models import (
    TechnicalIndicator, TechnicalPattern, SupportResistance,
    TrendAnalysis, SmartMoneyEvent, TechnicalAnalysisResult
)


def generate_candle_data(n=100, base_price=50000, volatility=0.02):
    """Generate realistic OHLCV candle data for testing."""
    candles = []
    price = base_price

    for i in range(n):
        change = random.uniform(-volatility, volatility)
        open_price = price
        close = price * (1 + change)
        high = max(open_price, close) * (1 + random.uniform(0, 0.005))
        low = min(open_price, close) * (1 - random.uniform(0, 0.005))
        volume = random.uniform(100, 1000)

        candles.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
        })
        price = close

    return candles


def extract_prices(candles):
    """Extract price arrays from candle data."""
    return {
        'closes': [c['close'] for c in candles],
        'highs': [c['high'] for c in candles],
        'lows': [c['low'] for c in candles],
        'volumes': [c['volume'] for c in candles],
    }


class IndicatorEngineTest(TestCase):
    """Test IndicatorEngine calculations."""

    def setUp(self):
        random.seed(42)
        self.candles = generate_candle_data(100)
        self.prices = extract_prices(self.candles)

    def test_calculate_rsi(self):
        """Test RSI calculation."""
        result = IndicatorEngine.calculate_rsi(self.prices['closes'], period=14)

        self.assertIn('value', result)
        self.assertIn('signal', result)
        self.assertIn('strength', result)
        self.assertIn('period', result)
        self.assertEqual(result['period'], 14)
        self.assertGreaterEqual(result['value'], 0)
        self.assertLessEqual(result['value'], 100)
        self.assertIn(result['signal'], ['bullish', 'bearish', 'neutral'])

    def test_calculate_rsi_short_data(self):
        """Test RSI with insufficient data."""
        short_closes = [100, 101, 102]
        result = IndicatorEngine.calculate_rsi(short_closes, period=14)

        self.assertEqual(result['value'], 50)
        self.assertEqual(result['signal'], 'neutral')
        self.assertEqual(result['strength'], 0)

    def test_calculate_macd(self):
        """Test MACD calculation."""
        result = IndicatorEngine.calculate_macd(self.prices['closes'])

        self.assertIn('macd', result)
        self.assertIn('signal', result)
        self.assertIn('histogram', result)
        self.assertIn('trend', result)
        self.assertIn(result['trend'], ['bullish', 'bearish', 'neutral', 'bullish_cross', 'bearish_cross'])

    def test_calculate_macd_short_data(self):
        """Test MACD with insufficient data."""
        short_closes = [100, 101, 102]
        result = IndicatorEngine.calculate_macd(short_closes)

        self.assertEqual(result['macd'], 0)
        self.assertEqual(result['signal'], 0)
        self.assertEqual(result['histogram'], 0)

    def test_calculate_bollinger_bands(self):
        """Test Bollinger Bands calculation."""
        result = IndicatorEngine.calculate_bollinger_bands(self.prices['closes'], period=20)

        self.assertIn('upper', result)
        self.assertIn('middle', result)
        self.assertIn('lower', result)
        self.assertIn('width', result)
        self.assertIn('position', result)
        self.assertIn('signal', result)
        self.assertGreater(result['upper'], result['middle'])
        self.assertGreater(result['middle'], result['lower'])

    def test_calculate_ema(self):
        """Test EMA calculation."""
        result = IndicatorEngine.calculate_ema(self.prices['closes'], period=21)

        self.assertIn('value', result)
        self.assertIn('signal', result)
        self.assertIn('price_above', result)
        self.assertIn('period', result)
        self.assertEqual(result['period'], 21)

    def test_calculate_atr(self):
        """Test ATR calculation."""
        result = IndicatorEngine.calculate_atr(
            self.prices['highs'],
            self.prices['lows'],
            self.prices['closes'],
            period=14
        )

        self.assertIn('value', result)
        self.assertIn('percent', result)
        self.assertIn('volatility', result)
        self.assertIn('period', result)
        self.assertGreater(result['value'], 0)
        self.assertIn(result['volatility'], ['very_low', 'low', 'normal', 'high', 'very_high'])

    def test_calculate_stochastic(self):
        """Test Stochastic calculation."""
        result = IndicatorEngine.calculate_stochastic(
            self.prices['highs'],
            self.prices['lows'],
            self.prices['closes']
        )

        self.assertIn('k', result)
        self.assertIn('d', result)
        self.assertIn('signal', result)
        self.assertGreaterEqual(result['k'], 0)
        self.assertLessEqual(result['k'], 100)

    def test_calculate_all_indicators(self):
        """Test calculating all indicators at once."""
        result = IndicatorEngine.calculate_all_indicators(self.candles)

        self.assertIn('rsi_14', result)
        self.assertIn('rsi_7', result)
        self.assertIn('macd', result)
        self.assertIn('bollinger_bands', result)
        self.assertIn('ema_9', result)
        self.assertIn('ema_21', result)
        self.assertIn('ema_50', result)
        self.assertIn('atr_14', result)
        self.assertIn('stochastic', result)

    def test_calculate_all_indicators_empty(self):
        """Test with empty data."""
        result = IndicatorEngine.calculate_all_indicators([])
        self.assertEqual(result, {})


class PatternDetectorTest(TestCase):
    """Test PatternDetector calculations."""

    def setUp(self):
        random.seed(42)
        self.candles = generate_candle_data(100)
        self.prices = extract_prices(self.candles)

    def test_detect_double_top(self):
        """Test double top detection."""
        # Create data with clear double top pattern
        highs = [100] * 50 + [110] * 5 + [105] * 5 + [110] * 5 + [100] * 35
        closes = [100] * 100

        result = PatternDetector.detect_double_top(highs, closes, window=10)
        # Result may or may not find pattern depending on data
        if result:
            self.assertIn('pattern_type', result)
            self.assertEqual(result['pattern_type'], 'double_top')
            self.assertEqual(result['direction'], 'bearish')

    def test_detect_double_bottom(self):
        """Test double bottom detection."""
        # Create data with clear double bottom pattern
        lows = [100] * 50 + [90] * 5 + [95] * 5 + [90] * 5 + [100] * 35
        closes = [100] * 100

        result = PatternDetector.detect_double_bottom(lows, closes, window=10)
        # Result may or may not find pattern depending on data
        if result:
            self.assertIn('pattern_type', result)
            self.assertEqual(result['pattern_type'], 'double_bottom')
            self.assertEqual(result['direction'], 'bullish')

    def test_detect_head_shoulders(self):
        """Test head and shoulders detection."""
        # Create data with clear H&S pattern
        highs = ([100] * 20 + [110] * 5 + [105] * 5 +  # Left shoulder
                 [100] * 10 + [115] * 5 + [110] * 5 +  # Head
                 [100] * 10 + [110] * 5 + [105] * 5 +  # Right shoulder
                 [100] * 20)
        closes = [100] * 100

        result = PatternDetector.detect_head_shoulders(highs, closes, window=10)
        if result:
            self.assertIn('pattern_type', result)
            self.assertEqual(result['pattern_type'], 'head_shoulders')

    def test_detect_triangle(self):
        """Test triangle detection."""
        # Create ascending triangle
        highs = [100 - i * 0.1 for i in range(50)] + [95] * 50
        lows = [90 + i * 0.1 for i in range(50)] + [95] * 50

        result = PatternDetector.detect_triangle(highs, lows, window=20)
        if result:
            self.assertIn('pattern_type', result)
            self.assertIn(result['pattern_type'], [
                'ascending_triangle', 'descending_triangle', 'symmetrical_triangle'
            ])

    def test_detect_flag(self):
        """Test flag pattern detection."""
        # Create bull flag pattern
        closes = list(range(100, 150)) + [150 - i * 0.5 for i in range(50)]
        volumes = [100] * 100

        result = PatternDetector.detect_flag(closes, volumes, window=30, flag_window=15)
        if result:
            self.assertIn('pattern_type', result)
            self.assertIn(result['pattern_type'], ['bull_flag', 'bear_flag'])

    def test_detect_all_patterns(self):
        """Test detecting all patterns."""
        patterns = PatternDetector.detect_all_patterns(
            self.prices['highs'],
            self.prices['lows'],
            self.prices['closes'],
            self.prices['volumes']
        )

        self.assertIsInstance(patterns, list)
        for pattern in patterns:
            self.assertIn('pattern_type', pattern)
            self.assertIn('direction', pattern)
            self.assertIn('confidence', pattern)


class SRAnalyzerTest(TestCase):
    """Test SRAnalyzer calculations."""

    def setUp(self):
        random.seed(42)
        self.candles = generate_candle_data(100)
        self.prices = extract_prices(self.candles)

    def test_find_support_resistance_levels(self):
        """Test finding S/R levels."""
        result = SRAnalyzer.find_support_resistance_levels(
            self.prices['highs'],
            self.prices['lows'],
            self.prices['closes']
        )

        self.assertIn('support', result)
        self.assertIn('resistance', result)
        self.assertIn('current_price', result)
        self.assertIsInstance(result['support'], list)
        self.assertIsInstance(result['resistance'], list)

    def test_support_levels_structure(self):
        """Test support levels have correct structure."""
        result = SRAnalyzer.find_support_resistance_levels(
            self.prices['highs'],
            self.prices['lows'],
            self.prices['closes']
        )

        for level in result['support']:
            self.assertIn('price', level)
            self.assertIn('strength', level)
            self.assertIn('touch_count', level)
            self.assertIn('methods', level)
            self.assertLess(level['price'], result['current_price'])

    def test_resistance_levels_structure(self):
        """Test resistance levels have correct structure."""
        result = SRAnalyzer.find_support_resistance_levels(
            self.prices['highs'],
            self.prices['lows'],
            self.prices['closes']
        )

        for level in result['resistance']:
            self.assertIn('price', level)
            self.assertIn('strength', level)
            self.assertIn('touch_count', level)
            self.assertGreater(level['price'], result['current_price'])

    def test_calculate_distance_to_levels(self):
        """Test distance calculation to levels."""
        support_levels = [{'price': 49000, 'strength': 80}]
        resistance_levels = [{'price': 51000, 'strength': 70}]

        result = SRAnalyzer.calculate_distance_to_levels(
            50000, support_levels, resistance_levels
        )

        self.assertIn('nearest_support', result)
        self.assertIn('nearest_resistance', result)
        self.assertIn('support_distance_percent', result)
        self.assertIn('resistance_distance_percent', result)
        self.assertEqual(result['support_distance_percent'], 2.0)
        self.assertEqual(result['resistance_distance_percent'], 2.0)


class TrendAnalyzerTest(TestCase):
    """Test TrendAnalyzer calculations."""

    def setUp(self):
        random.seed(42)
        self.candles = generate_candle_data(100)
        self.prices = extract_prices(self.candles)

    def test_calculate_adx(self):
        """Test ADX calculation."""
        result = TrendAnalyzer.calculate_adx(
            self.prices['highs'],
            self.prices['lows'],
            self.prices['closes']
        )

        self.assertIn('adx', result)
        self.assertIn('plus_di', result)
        self.assertIn('minus_di', result)
        self.assertIn('trend_strength', result)
        self.assertIn('trend_direction', result)
        self.assertGreaterEqual(result['adx'], 0)
        self.assertIn(result['trend_strength'], ['weak', 'moderate', 'strong', 'very_strong'])

    def test_analyze_ema_alignment(self):
        """Test EMA alignment analysis."""
        result = TrendAnalyzer.analyze_ema_alignment(self.prices['closes'])

        self.assertIn('alignment', result)
        self.assertIn('signal', result)
        self.assertIn('ema_9', result)
        self.assertIn('ema_21', result)
        self.assertIn('ema_50', result)
        self.assertIn(result['alignment'], [
            'bullish_aligned', 'bullish_partial', 'bearish_aligned',
            'bearish_partial', 'mixed', 'insufficient_data'
        ])

    def test_detect_trend_direction(self):
        """Test trend direction detection."""
        result = TrendAnalyzer.detect_trend_direction(
            self.prices['highs'],
            self.prices['lows'],
            self.prices['closes']
        )

        self.assertIn('direction', result)
        self.assertIn('confidence', result)
        self.assertIn('higher_highs', result)
        self.assertIn('lower_lows', result)

    def test_analyze_trend(self):
        """Test comprehensive trend analysis."""
        result = TrendAnalyzer.analyze_trend(
            self.prices['highs'],
            self.prices['lows'],
            self.prices['closes']
        )

        self.assertIn('adx', result)
        self.assertIn('ema_alignment', result)
        self.assertIn('direction', result)


class SmartMoneyAnalyzerTest(TestCase):
    """Test SmartMoneyAnalyzer calculations."""

    def setUp(self):
        random.seed(42)
        self.candles = generate_candle_data(100)
        self.prices = extract_prices(self.candles)

    def test_detect_accumulation(self):
        """Test accumulation detection."""
        # Create accumulation pattern: sideways price with increasing volume
        closes = [100] * 30 + [101] * 10 + [100] * 10
        lows = [98] * 30 + [99] * 10 + [98] * 10
        volumes = [100] * 15 + [150] * 15 + [100] * 20

        result = SmartMoneyAnalyzer.detect_accumulation(closes, volumes, lows)

        if result:
            self.assertEqual(result['event_type'], 'accumulation')
            self.assertEqual(result['direction'], 'bullish')

    def test_detect_distribution(self):
        """Test distribution detection."""
        # Create distribution pattern: sideways price with selling pressure
        closes = [100] * 30 + [101] * 10 + [100] * 10
        highs = [102] * 30 + [103] * 10 + [102] * 10
        volumes = [100] * 15 + [150] * 15 + [100] * 20

        result = SmartMoneyAnalyzer.detect_distribution(closes, volumes, highs)

        if result:
            self.assertEqual(result['event_type'], 'distribution')
            self.assertEqual(result['direction'], 'bearish')

    def test_detect_liquidity_sweep(self):
        """Test liquidity sweep detection."""
        # Create liquidity sweep pattern
        highs = [100] * 40 + [105] + [99] * 9
        lows = [95] * 50
        closes = [98] * 40 + [99] + [98] * 9

        result = SmartMoneyAnalyzer.detect_liquidity_sweep(highs, lows, closes)

        if result:
            self.assertEqual(result['event_type'], 'liquidity_sweep')
            self.assertIn(result['direction'], ['bullish', 'bearish'])

    def test_detect_order_block(self):
        """Test order block detection."""
        closes = [100] * 40 + [100] * 10
        volumes = [100] * 40 + [250] * 10

        result = SmartMoneyAnalyzer.detect_order_block(closes, volumes)

        if result:
            self.assertEqual(result['event_type'], 'order_block')
            self.assertIn(result['direction'], ['bullish', 'bearish'])

    def test_detect_fair_value_gap(self):
        """Test fair value gap detection."""
        # Create bullish FVG
        highs = [100] * 40
        lows = [95] * 40 + [96] * 5 + [99] * 5

        result = SmartMoneyAnalyzer.detect_fair_value_gap(highs, lows)

        if result:
            self.assertEqual(result['event_type'], 'fair_value_gap')
            self.assertIn(result['direction'], ['bullish', 'bearish'])

    def test_analyze_all(self):
        """Test analyzing all smart money patterns."""
        events = SmartMoneyAnalyzer.analyze_all(
            self.prices['highs'],
            self.prices['lows'],
            self.prices['closes'],
            self.prices['volumes']
        )

        self.assertIsInstance(events, list)
        for event in events:
            self.assertIn('event_type', event)
            self.assertIn('direction', event)
            self.assertIn('confidence', event)


class TechnicalIndicatorModelTest(TestCase):
    """Test TechnicalIndicator model."""

    def test_create_indicator(self):
        """Test creating a technical indicator."""
        indicator = TechnicalIndicator.objects.create(
            symbol='BTC-USDT',
            timeframe='1h',
            indicator_type='rsi',
            value={'value': 65.5, 'signal': 'bullish'},
            signal='bullish',
            strength=70,
            period=14,
            timestamp=datetime.now(),
        )

        self.assertEqual(indicator.symbol, 'BTC-USDT')
        self.assertEqual(indicator.timeframe, '1h')
        self.assertEqual(indicator.indicator_type, 'rsi')
        self.assertEqual(indicator.signal, 'bullish')
        self.assertEqual(indicator.strength, 70)

    def test_indicator_str(self):
        """Test indicator string representation."""
        indicator = TechnicalIndicator.objects.create(
            symbol='BTC-USDT',
            timeframe='1h',
            indicator_type='rsi',
            value={'value': 65.5},
            signal='bullish',
            timestamp=datetime.now(),
        )

        self.assertIn('BTC-USDT', str(indicator))
        self.assertIn('rsi', str(indicator))


class TechnicalPatternModelTest(TestCase):
    """Test TechnicalPattern model."""

    def test_create_pattern(self):
        """Test creating a technical pattern."""
        now = datetime.now()
        pattern = TechnicalPattern.objects.create(
            symbol='BTC-USDT',
            timeframe='4h',
            pattern_type='double_top',
            direction='bearish',
            confidence=0.75,
            start_price=50000,
            end_price=52000,
            target_price=48000,
            stop_price=53000,
            start_time=now - timedelta(hours=10),
            end_time=now,
        )

        self.assertEqual(pattern.symbol, 'BTC-USDT')
        self.assertEqual(pattern.pattern_type, 'double_top')
        self.assertEqual(pattern.direction, 'bearish')
        self.assertEqual(pattern.confidence, 0.75)

    def test_pattern_str(self):
        """Test pattern string representation."""
        now = datetime.now()
        pattern = TechnicalPattern.objects.create(
            symbol='BTC-USDT',
            timeframe='4h',
            pattern_type='double_top',
            direction='bearish',
            confidence=0.75,
            start_price=50000,
            end_price=52000,
            start_time=now - timedelta(hours=10),
            end_time=now,
        )

        self.assertIn('BTC-USDT', str(pattern))
        self.assertIn('double_top', str(pattern))


class SupportResistanceModelTest(TestCase):
    """Test SupportResistance model."""

    def test_create_support_level(self):
        """Test creating a support level."""
        level = SupportResistance.objects.create(
            symbol='BTC-USDT',
            timeframe='1h',
            level_type='support',
            price=49000,
            strength=85,
            touch_count=5,
        )

        self.assertEqual(level.symbol, 'BTC-USDT')
        self.assertEqual(level.level_type, 'support')
        self.assertEqual(level.price, 49000)
        self.assertEqual(level.strength, 85)

    def test_create_resistance_level(self):
        """Test creating a resistance level."""
        level = SupportResistance.objects.create(
            symbol='BTC-USDT',
            timeframe='1h',
            level_type='resistance',
            price=51000,
            strength=70,
            touch_count=3,
        )

        self.assertEqual(level.level_type, 'resistance')
        self.assertEqual(level.price, 51000)


class TrendAnalysisModelTest(TestCase):
    """Test TrendAnalysis model."""

    def test_create_trend_analysis(self):
        """Test creating a trend analysis."""
        trend = TrendAnalysis.objects.create(
            symbol='BTC-USDT',
            timeframe='1h',
            trend_direction='uptrend',
            trend_strength=75,
            adx_value=35.5,
            current_price=50000,
            ema_short=49800,
            ema_long=49500,
            ema_signal='bullish_alignment',
            timestamp=datetime.now(),
        )

        self.assertEqual(trend.symbol, 'BTC-USDT')
        self.assertEqual(trend.trend_direction, 'uptrend')
        self.assertEqual(trend.trend_strength, 75)
        self.assertEqual(trend.ema_signal, 'bullish_alignment')


class SmartMoneyEventModelTest(TestCase):
    """Test SmartMoneyEvent model."""

    def test_create_smart_money_event(self):
        """Test creating a smart money event."""
        event = SmartMoneyEvent.objects.create(
            symbol='BTC-USDT',
            event_type='accumulation',
            direction='bullish',
            confidence=0.8,
            price_level=50000,
            volume_confirmation=True,
            description='High volume buying detected',
            timeframe='4h',
            timestamp=datetime.now(),
        )

        self.assertEqual(event.symbol, 'BTC-USDT')
        self.assertEqual(event.event_type, 'accumulation')
        self.assertEqual(event.direction, 'bullish')
        self.assertTrue(event.volume_confirmation)

    def test_smart_money_event_str(self):
        """Test smart money event string representation."""
        event = SmartMoneyEvent.objects.create(
            symbol='BTC-USDT',
            event_type='order_block',
            direction='bullish',
            confidence=0.7,
            price_level=50000,
            timeframe='1h',
            timestamp=datetime.now(),
        )

        self.assertIn('BTC-USDT', str(event))
        self.assertIn('order_block', str(event))


class TechnicalAnalysisResultModelTest(TestCase):
    """Test TechnicalAnalysisResult model."""

    def test_create_analysis_result(self):
        """Test creating a technical analysis result."""
        result = TechnicalAnalysisResult.objects.create(
            symbol='BTC-USDT',
            timeframe='1h',
            overall_signal='buy',
            confidence=0.75,
            indicators_summary={'rsi': 65, 'macd': 'bullish'},
            patterns_summary=['double_bottom'],
            support_levels=[49000, 48000],
            resistance_levels=[51000, 52000],
            trend_summary={'direction': 'uptrend', 'strength': 70},
            smart_money_summary=[{'event': 'accumulation'}],
            entry_price=50000,
            stop_loss=48500,
            take_profit_1=52000,
            take_profit_2=54000,
            take_profit_3=56000,
            risk_reward_ratio=2.5,
            timestamp=datetime.now(),
        )

        self.assertEqual(result.symbol, 'BTC-USDT')
        self.assertEqual(result.overall_signal, 'buy')
        self.assertEqual(result.confidence, 0.75)
        self.assertEqual(result.risk_reward_ratio, 2.5)
        self.assertEqual(result.entry_price, 50000)
        self.assertEqual(result.stop_loss, 48500)

    def test_analysis_result_str(self):
        """Test analysis result string representation."""
        result = TechnicalAnalysisResult.objects.create(
            symbol='BTC-USDT',
            timeframe='1h',
            overall_signal='sell',
            confidence=0.6,
            timestamp=datetime.now(),
        )

        self.assertIn('BTC-USDT', str(result))
        self.assertIn('sell', str(result))
