"""
Candlestick Pattern Skill - Based on Rayner Teo's Ultimate Candlestick Patterns Trading Course

T.A.E. Framework:
- T: Trend (200 MA bias)
- A: Area of Value (Support/Resistance, MA, Trendlines, Channels)
- E: Entry Trigger (5 powerful candlestick patterns)

5 Powerful Candlestick Patterns:
1. Engulfing Pattern (Bullish & Bearish)
2. Hammer & Shooting Star
3. Dragonfly & Gravestone Doji
4. Morning Star & Evening Star
5. Tweezer Top & Bottom

This skill is designed to be used by the LLM module for short-term trading decisions.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class Candle:
    """Represents a single candlestick."""
    open: float
    high: float
    low: float
    close: float
    volume: float = 0
    timestamp: str = ""
    
    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)
    
    @property
    def total_range(self) -> float:
        return self.high - self.low
    
    @property
    def upper_shadow(self) -> float:
        return self.high - max(self.open, self.close)
    
    @property
    def lower_shadow(self) -> float:
        return min(self.open, self.close) - self.low
    
    @property
    def is_bullish(self) -> bool:
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        return self.close < self.open
    
    @property
    def is_doji(self) -> bool:
        return self.body_size < self.total_range * 0.1


@dataclass
class PatternResult:
    """Result of a candlestick pattern detection."""
    pattern_name: str
    direction: str  # 'bullish', 'bearish', 'neutral'
    confidence: float  # 0-1
    description: str
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    candle_indices: List[int]  # Which candles form the pattern


class CandlestickSkill:
    """
    Candlestick Pattern Analysis Skill
    
    Implements Rayner Teo's T.A.E. Framework:
    - Trend: 200-period moving average for bias
    - Area of Value: Support/Resistance levels
    - Entry Trigger: 5 powerful candlestick patterns
    """
    
    # Pattern detection thresholds
    BODY_RATIO_THRESHOLD = 0.3  # Body must be < 30% of range for doji
    SHADOW_RATIO_THRESHOLD = 2.0  # Shadow must be 2x body for hammer/shooting star
    ENGULFING_MARGIN = 1.02  # Engulfing must be 2% larger
    
    @classmethod
    def analyze(cls, closes: List[float], highs: List[float], lows: List[float], 
                opens: List[float] = None, volumes: List[float] = None) -> Dict:
        """
        Complete candlestick analysis using T.A.E. framework.
        
        Returns comprehensive analysis including:
        - Trend bias (from 200 MA)
        - Area of value (support/resistance)
        - Detected patterns with entry signals
        - Trading recommendations
        """
        if len(closes) < 20:
            return {'error': 'Need at least 20 candles for analysis'}
        
        # Create candle objects
        candles = cls._create_candles(closes, highs, lows, opens, volumes)
        
        # T.A.E. Analysis
        trend = cls._analyze_trend(closes)
        area_of_value = cls._analyze_area_of_value(closes, highs, lows)
        patterns = cls._detect_all_patterns(candles)
        
        # Generate trading signals
        signals = cls._generate_signals(trend, area_of_value, patterns)
        
        # Calculate overall score
        overall_score = cls._calculate_score(trend, area_of_value, patterns)
        
        return {
            'trend': trend,
            'area_of_value': area_of_value,
            'patterns': [cls._pattern_to_dict(p) for p in patterns],
            'signals': signals,
            'overall_score': overall_score,
            'bias': trend.get('bias', 'neutral'),
            'summary': cls._generate_summary(trend, area_of_value, patterns, signals),
        }
    
    @classmethod
    def _create_candles(cls, closes, highs, lows, opens=None, volumes=None) -> List[Candle]:
        """Create Candle objects from price data."""
        if opens is None:
            opens = [closes[i-1] if i > 0 else closes[i] for i in range(len(closes))]
        if volumes is None:
            volumes = [0] * len(closes)
        
        return [
            Candle(
                open=opens[i], high=highs[i], low=lows[i], 
                close=closes[i], volume=volumes[i]
            )
            for i in range(len(closes))
        ]
    
    @classmethod
    def _analyze_trend(cls, closes: List[float]) -> Dict:
        """
        Analyze trend using 200-period moving average.
        
        Rules from Rayner Teo:
        - Price above 200 MA → Long bias
        - Price below 200 MA → Short bias
        """
        if len(closes) < 200:
            # Use shorter MA if not enough data
            ma_period = min(50, len(closes))
        else:
            ma_period = 200
        
        ma = np.mean(closes[-ma_period:])
        current_price = closes[-1]
        price_vs_ma = ((current_price - ma) / ma) * 100
        
        if current_price > ma:
            bias = 'bullish'
            strength = min(100, abs(price_vs_ma) * 10)
        elif current_price < ma:
            bias = 'bearish'
            strength = min(100, abs(price_vs_ma) * 10)
        else:
            bias = 'neutral'
            strength = 0
        
        # Additional trend indicators
        sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else current_price
        sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else current_price
        
        # EMA alignment
        ema_9 = cls._ema(closes, 9)
        ema_21 = cls._ema(closes, 21)
        
        aligned_bullish = ema_9 > ema_21 > ma if len(closes) >= 21 else False
        aligned_bearish = ema_9 < ema_21 < ma if len(closes) >= 21 else False
        
        return {
            'ma_period': ma_period,
            'ma_value': round(ma, 2),
            'current_price': current_price,
            'price_vs_ma_pct': round(price_vs_ma, 2),
            'bias': bias,
            'strength': round(strength, 1),
            'sma_20': round(sma_20, 2),
            'sma_50': round(sma_50, 2),
            'ema_9': round(ema_9, 2),
            'ema_21': round(ema_21, 2),
            'aligned_bullish': aligned_bullish,
            'aligned_bearish': aligned_bearish,
        }
    
    @classmethod
    def _ema(cls, data: List[float], period: int) -> float:
        """Calculate EMA."""
        if len(data) < period:
            return data[-1]
        multiplier = 2 / (period + 1)
        ema = np.mean(data[:period])
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        return ema
    
    @classmethod
    def _analyze_area_of_value(cls, closes, highs, lows) -> Dict:
        """
        Identify areas of value (support/resistance).
        
        From Rayner Teo:
        - Support and Resistance
        - Moving Averages
        - Trendlines
        - Channels
        """
        current_price = closes[-1]
        
        # Find support and resistance levels
        lookback = min(50, len(closes))
        recent_highs = highs[-lookback:]
        recent_lows = lows[-lookback:]
        
        # Simple pivot point method
        resistance_levels = []
        support_levels = []
        
        for i in range(2, len(recent_highs) - 2):
            if recent_highs[i] > recent_highs[i-1] and recent_highs[i] > recent_highs[i+1]:
                resistance_levels.append(recent_highs[i])
            if recent_lows[i] < recent_lows[i-1] and recent_lows[i] < recent_lows[i+1]:
                support_levels.append(recent_lows[i])
        
        # Remove duplicates and sort
        resistance_levels = sorted(set([round(r, 2) for r in resistance_levels]), reverse=True)
        support_levels = sorted(set([round(s, 2) for s in support_levels]))
        
        # Find nearest support and resistance
        nearest_resistance = next((r for r in resistance_levels if r > current_price), None)
        nearest_support = next((s for s in support_levels if s < current_price), None)
        
        # Calculate distance to nearest levels
        dist_to_resistance = ((nearest_resistance - current_price) / current_price * 100) if nearest_resistance else None
        dist_to_support = ((current_price - nearest_support) / current_price * 100) if nearest_support else None
        
        # Determine if price is near a level (within 2%)
        near_resistance = dist_to_resistance is not None and dist_to_resistance < 2
        near_support = dist_to_support is not None and dist_to_support < 2
        
        return {
            'current_price': current_price,
            'nearest_resistance': nearest_resistance,
            'nearest_support': nearest_support,
            'dist_to_resistance_pct': round(dist_to_resistance, 2) if dist_to_resistance else None,
            'dist_to_support_pct': round(dist_to_support, 2) if dist_to_support else None,
            'near_resistance': near_resistance,
            'near_support': near_support,
            'resistance_levels': resistance_levels[:5],
            'support_levels': support_levels[:5],
            'in_value_zone': near_resistance or near_support,
        }
    
    @classmethod
    def _detect_all_patterns(cls, candles: List[Candle]) -> List[PatternResult]:
        """Detect all 5 powerful candlestick patterns."""
        patterns = []
        
        for i in range(2, len(candles)):
            # 1. Engulfing Pattern
            pattern = cls._detect_engulfing(candles, i)
            if pattern:
                patterns.append(pattern)
            
            # 2. Hammer / Shooting Star
            pattern = cls._detect_hammer_shooting_star(candles, i)
            if pattern:
                patterns.append(pattern)
            
            # 3. Dragonfly / Gravestone Doji
            pattern = cls._detect_doji_patterns(candles, i)
            if pattern:
                patterns.append(pattern)
            
            # 4. Morning Star / Evening Star (3-candle pattern)
            if i >= 2:
                pattern = cls._detect_morning_evening_star(candles, i)
                if pattern:
                    patterns.append(pattern)
            
            # 5. Tweezer Top / Bottom
            if i >= 1:
                pattern = cls._detect_tweezer(candles, i)
                if pattern:
                    patterns.append(pattern)
        
        return patterns
    
    @classmethod
    def _detect_engulfing(cls, candles: List[Candle], i: int) -> Optional[PatternResult]:
        """Detect Bullish/Bearish Engulfing pattern."""
        if i < 1:
            return None
        
        prev = candles[i-1]
        curr = candles[i]
        
        # Bullish Engulfing
        if (prev.is_bearish and curr.is_bullish and
            curr.body_size > prev.body_size * cls.ENGULFING_MARGIN and
            curr.close >= prev.open and curr.open <= prev.close):
            
            entry = curr.close
            stop_loss = curr.low - (curr.body_size * 0.1)
            take_profit = entry + (entry - stop_loss) * 2
            
            return PatternResult(
                pattern_name='Bullish Engulfing',
                direction='bullish',
                confidence=0.75,
                description='Bearish candle engulfed by bullish candle - reversal signal',
                entry_price=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward_ratio=round((take_profit - entry) / (entry - stop_loss), 2) if entry > stop_loss else 0,
                candle_indices=[i-1, i],
            )
        
        # Bearish Engulfing
        if (prev.is_bullish and curr.is_bearish and
            curr.body_size > prev.body_size * cls.ENGULFING_MARGIN and
            curr.close <= prev.open and curr.open >= prev.close):
            
            entry = curr.close
            stop_loss = curr.high + (curr.body_size * 0.1)
            take_profit = entry - (stop_loss - entry) * 2
            
            return PatternResult(
                pattern_name='Bearish Engulfing',
                direction='bearish',
                confidence=0.75,
                description='Bullish candle engulfed by bearish candle - reversal signal',
                entry_price=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward_ratio=round((entry - take_profit) / (stop_loss - entry), 2) if stop_loss > entry else 0,
                candle_indices=[i-1, i],
            )
        
        return None
    
    @classmethod
    def _detect_hammer_shooting_star(cls, candles: List[Candle], i: int) -> Optional[PatternResult]:
        """Detect Hammer (bullish) or Shooting Star (bearish)."""
        candle = candles[i]
        
        if candle.total_range == 0:
            return None
        
        body_ratio = candle.body_size / candle.total_range
        lower_shadow_ratio = candle.lower_shadow / candle.body_size if candle.body_size > 0 else 0
        upper_shadow_ratio = candle.upper_shadow / candle.body_size if candle.body_size > 0 else 0
        
        # Hammer: Small body, long lower shadow, little/no upper shadow
        if (body_ratio < 0.35 and 
            candle.lower_shadow > candle.body_size * 2 and
            candle.upper_shadow < candle.body_size * 0.5):
            
            entry = candle.close
            stop_loss = candle.low - (candle.body_size * 0.1)
            take_profit = entry + (entry - stop_loss) * 2
            
            return PatternResult(
                pattern_name='Hammer',
                direction='bullish',
                confidence=0.70,
                description='Rejection of lower prices - buyers stepped in',
                entry_price=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward_ratio=round((take_profit - entry) / (entry - stop_loss), 2) if entry > stop_loss else 0,
                candle_indices=[i],
            )
        
        # Shooting Star: Small body, long upper shadow, little/no lower shadow
        if (body_ratio < 0.35 and
            candle.upper_shadow > candle.body_size * 2 and
            candle.lower_shadow < candle.body_size * 0.5):
            
            entry = candle.close
            stop_loss = candle.high + (candle.body_size * 0.1)
            take_profit = entry - (stop_loss - entry) * 2
            
            return PatternResult(
                pattern_name='Shooting Star',
                direction='bearish',
                confidence=0.70,
                description='Rejection of higher prices - sellers stepped in',
                entry_price=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward_ratio=round((entry - take_profit) / (stop_loss - entry), 2) if stop_loss > entry else 0,
                candle_indices=[i],
            )
        
        return None
    
    @classmethod
    def _detect_doji_patterns(cls, candles: List[Candle], i: int) -> Optional[PatternResult]:
        """Detect Dragonfly Doji (bullish) or Gravestone Doji (bearish)."""
        candle = candles[i]
        
        if not candle.is_doji:
            return None
        
        # Dragonfly Doji: Long lower shadow, no upper shadow
        if (candle.lower_shadow > candle.total_range * 0.6 and
            candle.upper_shadow < candle.total_range * 0.1):
            
            entry = candle.close
            stop_loss = candle.low - (candle.total_range * 0.05)
            take_profit = entry + (entry - stop_loss) * 2
            
            return PatternResult(
                pattern_name='Dragonfly Doji',
                direction='bullish',
                confidence=0.65,
                description='Indecision with rejection of lower prices',
                entry_price=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward_ratio=round((take_profit - entry) / (entry - stop_loss), 2) if entry > stop_loss else 0,
                candle_indices=[i],
            )
        
        # Gravestone Doji: Long upper shadow, no lower shadow
        if (candle.upper_shadow > candle.total_range * 0.6 and
            candle.lower_shadow < candle.total_range * 0.1):
            
            entry = candle.close
            stop_loss = candle.high + (candle.total_range * 0.05)
            take_profit = entry - (stop_loss - entry) * 2
            
            return PatternResult(
                pattern_name='Gravestone Doji',
                direction='bearish',
                confidence=0.65,
                description='Indecision with rejection of higher prices',
                entry_price=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward_ratio=round((entry - take_profit) / (stop_loss - entry), 2) if stop_loss > entry else 0,
                candle_indices=[i],
            )
        
        return None
    
    @classmethod
    def _detect_morning_evening_star(cls, candles: List[Candle], i: int) -> Optional[PatternResult]:
        """Detect Morning Star (bullish) or Evening Star (bearish) - 3-candle pattern."""
        if i < 2:
            return None
        
        first = candles[i-2]
        second = candles[i-1]
        third = candles[i]
        
        # Morning Star: Bearish -> Doji/Small -> Bullish
        if (first.is_bearish and 
            second.body_size < first.body_size * 0.3 and
            third.is_bullish and
            third.close > (first.open + first.close) / 2):
            
            entry = third.close
            stop_loss = second.low - (second.body_size * 0.1)
            take_profit = entry + (entry - stop_loss) * 2
            
            return PatternResult(
                pattern_name='Morning Star',
                direction='bullish',
                confidence=0.80,
                description='3-candle bullish reversal: sellers → indecision → buyers',
                entry_price=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward_ratio=round((take_profit - entry) / (entry - stop_loss), 2) if entry > stop_loss else 0,
                candle_indices=[i-2, i-1, i],
            )
        
        # Evening Star: Bullish -> Doji/Small -> Bearish
        if (first.is_bullish and
            second.body_size < first.body_size * 0.3 and
            third.is_bearish and
            third.close < (first.open + first.close) / 2):
            
            entry = third.close
            stop_loss = second.high + (second.body_size * 0.1)
            take_profit = entry - (stop_loss - entry) * 2
            
            return PatternResult(
                pattern_name='Evening Star',
                direction='bearish',
                confidence=0.80,
                description='3-candle bearish reversal: buyers → indecision → sellers',
                entry_price=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward_ratio=round((entry - take_profit) / (stop_loss - entry), 2) if stop_loss > entry else 0,
                candle_indices=[i-2, i-1, i],
            )
        
        return None
    
    @classmethod
    def _detect_tweezer(cls, candles: List[Candle], i: int) -> Optional[PatternResult]:
        """Detect Tweezer Bottom (bullish) or Tweezer Top (bearish)."""
        if i < 1:
            return None
        
        prev = candles[i-1]
        curr = candles[i]
        
        tolerance = 0.001  # 0.1% tolerance
        
        # Tweezer Bottom: Both candles have similar lows
        if (abs(prev.low - curr.low) / prev.low < tolerance and
            prev.is_bearish and curr.is_bullish):
            
            entry = curr.close
            stop_loss = curr.low - (curr.body_size * 0.1)
            take_profit = entry + (entry - stop_loss) * 2
            
            return PatternResult(
                pattern_name='Tweezer Bottom',
                direction='bullish',
                confidence=0.72,
                description='Double rejection of lower prices - strong support',
                entry_price=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward_ratio=round((take_profit - entry) / (entry - stop_loss), 2) if entry > stop_loss else 0,
                candle_indices=[i-1, i],
            )
        
        # Tweezer Top: Both candles have similar highs
        if (abs(prev.high - curr.high) / prev.high < tolerance and
            prev.is_bullish and curr.is_bearish):
            
            entry = curr.close
            stop_loss = curr.high + (curr.body_size * 0.1)
            take_profit = entry - (stop_loss - entry) * 2
            
            return PatternResult(
                pattern_name='Tweezer Top',
                direction='bearish',
                confidence=0.72,
                description='Double rejection of higher prices - strong resistance',
                entry_price=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward_ratio=round((entry - take_profit) / (stop_loss - entry), 2) if stop_loss > entry else 0,
                candle_indices=[i-1, i],
            )
        
        return None
    
    @classmethod
    def _generate_signals(cls, trend: Dict, aov: Dict, patterns: List[PatternResult]) -> List[Dict]:
        """Generate trading signals by combining T.A.E. framework."""
        signals = []
        
        for pattern in patterns[-5:]:  # Last 5 patterns
            # Check if pattern aligns with trend
            trend_aligned = (
                (pattern.direction == 'bullish' and trend['bias'] == 'bullish') or
                (pattern.direction == 'bearish' and trend['bias'] == 'bearish')
            )
            
            # Check if pattern is at area of value
            at_value = aov.get('in_value_zone', False)
            
            # Calculate signal strength
            strength = pattern.confidence
            if trend_aligned:
                strength += 0.15
            if at_value:
                strength += 0.10
            strength = min(1.0, strength)
            
            signal_type = 'BUY' if pattern.direction == 'bullish' else 'SELL'
            
            signals.append({
                'type': signal_type,
                'pattern': pattern.pattern_name,
                'direction': pattern.direction,
                'strength': round(strength, 2),
                'entry': pattern.entry_price,
                'stop_loss': pattern.stop_loss,
                'take_profit': pattern.take_profit,
                'risk_reward': pattern.risk_reward_ratio,
                'trend_aligned': trend_aligned,
                'at_area_of_value': at_value,
                'description': pattern.description,
            })
        
        return signals
    
    @classmethod
    def _calculate_score(cls, trend: Dict, aov: Dict, patterns: List[PatternResult]) -> Dict:
        """Calculate overall candlestick analysis score."""
        # Trend score
        trend_score = 50 + trend['strength'] * 0.5 if trend['bias'] == 'bullish' else \
                      50 - trend['strength'] * 0.5 if trend['bias'] == 'bearish' else 50
        
        # Area of value score
        aov_score = 70 if aov.get('in_value_zone') else 50
        
        # Pattern score (based on recent patterns)
        if patterns:
            bullish_patterns = sum(1 for p in patterns[-5:] if p.direction == 'bullish')
            bearish_patterns = sum(1 for p in patterns[-5:] if p.direction == 'bearish')
            pattern_score = 50 + (bullish_patterns - bearish_patterns) * 10
        else:
            pattern_score = 50
        
        # Overall score
        overall = (trend_score * 0.4 + aov_score * 0.3 + pattern_score * 0.3)
        
        return {
            'trend_score': round(trend_score, 1),
            'aov_score': round(aov_score, 1),
            'pattern_score': round(pattern_score, 1),
            'overall': round(overall, 1),
        }
    
    @classmethod
    def _generate_summary(cls, trend: Dict, aov: Dict, patterns: List[PatternResult], signals: List[Dict]) -> str:
        """Generate human-readable summary of the analysis."""
        trend_bias = trend['bias'].upper()
        ma_value = trend['ma_value']
        current = trend['current_price']
        
        summary_parts = [
            f"Trend: {trend_bias} (Price {'above' if trend['bias'] == 'bullish' else 'below'} {trend['ma_period']}-period MA at ${ma_value:,.2f})",
        ]
        
        if aov.get('near_support'):
            summary_parts.append(f"Near support at ${aov['nearest_support']:,.2f} ({aov['dist_to_support_pct']:.1f}% away)")
        elif aov.get('near_resistance'):
            summary_parts.append(f"Near resistance at ${aov['nearest_resistance']:,.2f} ({aov['dist_to_resistance_pct']:.1f}% away)")
        
        if patterns:
            recent = patterns[-1]
            summary_parts.append(f"Latest pattern: {recent.pattern_name} ({recent.direction})")
        
        if signals:
            best = max(signals, key=lambda s: s['strength'])
            summary_parts.append(f"Best signal: {best['type']} {best['pattern']} (strength: {best['strength']:.0%})")
        
        return " | ".join(summary_parts)
    
    @classmethod
    def _pattern_to_dict(cls, pattern: PatternResult) -> Dict:
        """Convert PatternResult to dictionary."""
        return {
            'name': pattern.pattern_name,
            'direction': pattern.direction,
            'confidence': pattern.confidence,
            'description': pattern.description,
            'entry': pattern.entry_price,
            'stop_loss': pattern.stop_loss,
            'take_profit': pattern.take_profit,
            'risk_reward': pattern.risk_reward_ratio,
            'candles': pattern.candle_indices,
        }
