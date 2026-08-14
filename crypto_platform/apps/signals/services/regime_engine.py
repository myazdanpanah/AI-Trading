"""Market Regime Engine — classifies market conditions into 10 regimes.

Regimes:
1. Bull Trend        - Sustained upward price action
2. Bear Trend        - Sustained downward price action
3. Sideways          - Range-bound, no clear direction
4. High Volatility   - Large price swings, uncertain direction
5. Low Volatility    - Compressed range, potential breakout building
6. Breakout          - Price breaking out of established range
7. Accumulation      - Smart money buying, price stabilizing after decline
8. Distribution      - Smart money selling, price topping after rally
9. Capitulation      - Panic selling, extreme fear
10. Recovery         - Bouncing from bottom, improving sentiment

Each regime maps to a set of signal weights that optimize for that condition.
"""
import logging
import math
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RegimeState:
    """Current market regime state."""
    regime: str
    confidence: float  # 0-100
    sub_regimes: Dict[str, str]  # Individual component readings
    features: Dict[str, float]  # Raw feature values
    weights: Dict[str, float]  # Regime-conditioned weights


# ── Regime-Conditioned Weight Tables ──────────────────────────────────
# Maps each regime to optimal factor weights for that condition.
# Weights must sum to 1.0 for the quant composite (excluding AI).

REGIME_WEIGHTS = {
    'bull_trend': {
        'technical': 0.35,    # Technicals work well in trends
        'sentiment': 0.15,
        'news': 0.10,
        'macro': 0.15,
        'derivatives': 0.10,
        'market_structure': 0.15,
    },
    'bear_trend': {
        'technical': 0.30,    # Technicals still work but less reliable
        'sentiment': 0.15,
        'news': 0.15,         # News matters more in bear markets
        'macro': 0.20,        # Macro dominates in bear markets
        'derivatives': 0.10,
        'market_structure': 0.10,
    },
    'sideways': {
        'technical': 0.40,    # Range trading favors technicals
        'sentiment': 0.10,
        'news': 0.10,
        'macro': 0.10,
        'derivatives': 0.15,  # Funding/OI signal range boundaries
        'market_structure': 0.15,
    },
    'high_volatility': {
        'technical': 0.25,    # Technicals less reliable
        'sentiment': 0.10,
        'news': 0.15,
        'macro': 0.15,
        'derivatives': 0.20,  # Liquidation data crucial
        'market_structure': 0.15,
    },
    'low_volatility': {
        'technical': 0.35,    # Compression → technical setups
        'sentiment': 0.10,
        'news': 0.10,
        'macro': 0.10,
        'derivatives': 0.15,  # OI buildup signals breakout
        'market_structure': 0.20,
    },
    'breakout': {
        'technical': 0.30,    # Breakout confirmation
        'sentiment': 0.15,
        'news': 0.15,         # Catalyst drives breakout
        'macro': 0.10,
        'derivatives': 0.15,
        'market_structure': 0.15,
    },
    'accumulation': {
        'technical': 0.25,
        'sentiment': 0.15,    # Sentiment improving
        'news': 0.15,
        'macro': 0.15,
        'derivatives': 0.15,  # Short covering, OI changes
        'market_structure': 0.15,
    },
    'distribution': {
        'technical': 0.25,
        'sentiment': 0.15,
        'news': 0.20,         # Negative news at tops
        'macro': 0.15,
        'derivatives': 0.15,
        'market_structure': 0.10,
    },
    'capitulation': {
        'technical': 0.20,    # Technicals break down
        'sentiment': 0.20,    # Extreme fear = opportunity
        'news': 0.20,         # Panic headlines
        'macro': 0.15,
        'derivatives': 0.15,  # Liquidation cascades
        'market_structure': 0.10,
    },
    'recovery': {
        'technical': 0.30,    # Technical recovery signals
        'sentiment': 0.15,    # Sentiment improving from lows
        'news': 0.15,
        'macro': 0.15,
        'derivatives': 0.10,
        'market_structure': 0.15,
    },
}


class RegimeEngine:
    """
    Market Regime Engine — classifies market conditions and adjusts
    signal weights accordingly.

    The regime engine is INPUT to the signal fusion, not a separate signal.
    It determines HOW to weight the other factors.
    """

    def __init__(self):
        self.regimes = list(REGIME_WEIGHTS.keys())

    def detect_regime(
        self,
        price_data: List[Dict],
        volume_data: List[float] = None,
        dominance: float = None,
        funding_rate: float = None,
        open_interest_change: float = None,
    ) -> RegimeState:
        """
        Detect current market regime from market data.

        Args:
            price_data: List of OHLCV dicts with 'open', 'high', 'low', 'close', 'volume'
            volume_data: Optional volume series
            dominance: BTC dominance percentage
            funding_rate: Current funding rate
            open_interest_change: OI change percentage

        Returns:
            RegimeState with regime classification, confidence, features, and weights
        """
        if not price_data or len(price_data) < 20:
            return self._default_state()

        closes = [float(d.get('close', 0)) for d in price_data]
        highs = [float(d.get('high', 0)) for d in price_data]
        lows = [float(d.get('low', 0)) for d in price_data]
        volumes = volume_data or [float(d.get('volume', 0)) for d in price_data]

        # ── Feature Extraction ────────────────────────────────────────
        features = {}

        # Trend features
        features['sma_20'] = sum(closes[-20:]) / 20
        features['sma_50'] = sum(closes[-50:]) / 50 if len(closes) >= 50 else features['sma_20']
        features['ema_12'] = self._ema(closes, 12)
        features['ema_26'] = self._ema(closes, 26)
        current_price = closes[-1]

        # Trend strength: price vs SMAs
        trend_score = 0
        if current_price > features['sma_20']:
            trend_score += 25
        if current_price > features['sma_50']:
            trend_score += 25
        if features['sma_20'] > features['sma_50']:
            trend_score += 25
        if features['ema_12'] > features['ema_26']:
            trend_score += 25
        features['trend_score'] = trend_score  # 0-100

        # Volatility: ATR-based
        atr = self._calculate_atr(highs, lows, closes, 14)
        atr_pct = (atr / current_price * 100) if current_price > 0 else 0
        features['volatility_pct'] = atr_pct
        features['atr'] = atr

        # Historical volatility comparison
        if len(closes) >= 50:
            recent_vol = self._calculate_volatility(closes[-20:])
            historical_vol = self._calculate_volatility(closes[-50:])
            features['vol_ratio'] = recent_vol / historical_vol if historical_vol > 0 else 1.0
        else:
            features['vol_ratio'] = 1.0

        # Volume features
        avg_vol = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else sum(volumes) / len(volumes) if volumes else 0
        current_vol = volumes[-1] if volumes else 0
        features['volume_ratio'] = current_vol / avg_vol if avg_vol > 0 else 1.0

        # Momentum (RSI approximation)
        features['rsi'] = self._calculate_rsi(closes, 14)

        # Price position in range
        if len(highs) >= 20:
            range_high = max(highs[-20:])
            range_low = min(lows[-20:])
            range_size = range_high - range_low
            features['price_position'] = ((current_price - range_low) / range_size * 100) if range_size > 0 else 50
        else:
            features['price_position'] = 50

        # Breakout detection
        if len(highs) >= 20:
            prev_high = max(highs[-21:-1]) if len(highs) >= 21 else max(highs[:-1])
            prev_low = min(lows[-21:-1]) if len(lows) >= 21 else min(lows[:-1])
            features['breakout_up'] = 1 if current_price > prev_high else 0
            features['breakout_down'] = 1 if current_price < prev_low else 0
        else:
            features['breakout_up'] = 0
            features['breakout_down'] = 0

        # ── Regime Classification ─────────────────────────────────────
        regime_scores = {}

        # Bull Trend
        if features['trend_score'] >= 75 and features['vol_ratio'] < 1.5 and atr_pct < 4:
            regime_scores['bull_trend'] = features['trend_score']

        # Bear Trend
        if features['trend_score'] <= 25 and features['vol_ratio'] < 1.5 and atr_pct < 4:
            regime_scores['bear_trend'] = 100 - features['trend_score']

        # Sideways
        if 35 <= features['trend_score'] <= 65 and atr_pct < 3 and features['vol_ratio'] < 1.2:
            regime_scores['sideways'] = 100 - abs(features['trend_score'] - 50) * 2

        # High Volatility
        if features['vol_ratio'] > 1.5 or atr_pct > 5:
            vol_score = min(100, features['vol_ratio'] * 40 + atr_pct * 10)
            regime_scores['high_volatility'] = vol_score

        # Low Volatility
        if features['vol_ratio'] < 0.7 and atr_pct < 2:
            regime_scores['low_volatility'] = min(100, (1 - features['vol_ratio']) * 100 + (2 - atr_pct) * 20)

        # Breakout
        if features['breakout_up'] or features['breakout_down']:
            breakout_score = features['volume_ratio'] * 30 + 40
            if features['breakout_up']:
                regime_scores['breakout'] = breakout_score
            else:
                regime_scores['breakout'] = breakout_score * 0.8

        # Accumulation (low price position, improving volume, neutral trend)
        if features['price_position'] < 40 and features['volume_ratio'] > 1.1 and 40 <= features['trend_score'] <= 60:
            regime_scores['accumulation'] = 60 + features['volume_ratio'] * 10

        # Distribution (high price position, declining volume, neutral trend)
        if features['price_position'] > 60 and features['volume_ratio'] < 0.9 and 40 <= features['trend_score'] <= 60:
            regime_scores['distribution'] = 60 + (1 - features['volume_ratio']) * 20

        # Capitulation (extreme bearish + high volatility + high volume)
        if features['trend_score'] < 20 and features['vol_ratio'] > 1.8 and features['volume_ratio'] > 1.5:
            regime_scores['capitulation'] = 70 + features['vol_ratio'] * 10

        # Recovery (low price position but improving trend)
        if features['price_position'] < 35 and features['trend_score'] > 40 and features['trend_score'] < 65:
            regime_scores['recovery'] = 50 + (features['trend_score'] - 40) * 3

        # Select highest scoring regime
        if not regime_scores:
            regime = 'sideways'
            confidence = 30
        else:
            regime = max(regime_scores, key=regime_scores.get)
            confidence = min(100, regime_scores[regime])

        # Get regime-conditioned weights
        weights = REGIME_WEIGHTS.get(regime, REGIME_WEIGHTS['sideways'])

        # Sub-regimes (individual component readings)
        sub_regimes = {
            'trend': 'bullish' if features['trend_score'] > 60 else 'bearish' if features['trend_score'] < 40 else 'neutral',
            'volatility': 'high' if features['vol_ratio'] > 1.5 else 'low' if features['vol_ratio'] < 0.7 else 'normal',
            'momentum': 'overbought' if features['rsi'] > 70 else 'oversold' if features['rsi'] < 30 else 'neutral',
            'volume': 'high' if features['volume_ratio'] > 1.5 else 'low' if features['volume_ratio'] < 0.7 else 'normal',
        }

        logger.info(
            f"Regime detected: {regime} (confidence: {confidence:.0f}%) | "
            f"Trend: {sub_regimes['trend']} | Vol: {sub_regimes['volatility']} | "
            f"RSI: {features['rsi']:.1f}"
        )

        return RegimeState(
            regime=regime,
            confidence=confidence,
            sub_regimes=sub_regimes,
            features=features,
            weights=weights,
        )

    def get_regime_weights(self, regime: str) -> Dict[str, float]:
        """Get regime-conditioned weights for a specific regime."""
        return REGIME_WEIGHTS.get(regime, REGIME_WEIGHTS['sideways'])

    def detect_transition(
        self,
        previous_regime: str,
        current_regime: str,
    ) -> Optional[Dict]:
        """
        Detect regime transitions and their implications.

        Returns transition info if regime changed, None otherwise.
        """
        if previous_regime == current_regime:
            return None

        transitions = {
            ('bull_trend', 'sideways'): {'action': 'reduce_exposure', 'reason': 'Trend weakening'},
            ('bull_trend', 'bear_trend'): {'action': 'hedge', 'reason': 'Trend reversal'},
            ('bear_trend', 'sideways'): {'action': 'wait', 'reason': 'Decline pausing'},
            ('bear_trend', 'recovery'): {'action': 'accumulate', 'reason': 'Bottom forming'},
            ('sideways', 'breakout'): {'action': 'enter', 'reason': 'Range breakout'},
            ('sideways', 'bull_trend'): {'action': 'enter_long', 'reason': 'Uptrend starting'},
            ('high_volatility', 'low_volatility'): {'action': 'prepare', 'reason': 'Volatility compression'},
            ('low_volatility', 'breakout'): {'action': 'enter', 'reason': 'Volatility expansion'},
            ('capitulation', 'recovery'): {'action': 'buy', 'reason': 'Panic selling exhausted'},
            ('distribution', 'bear_trend'): {'action': 'exit', 'reason': 'Smart money selling'},
            ('accumulation', 'bull_trend'): {'action': 'enter', 'reason': 'Smart money buying'},
        }

        transition = transitions.get((previous_regime, current_regime))
        if transition:
            return {
                'from': previous_regime,
                'to': current_regime,
                'action': transition['action'],
                'reason': transition['reason'],
                'weight_change': self._calculate_weight_change(previous_regime, current_regime),
            }

        return {
            'from': previous_regime,
            'to': current_regime,
            'action': 'monitor',
            'reason': 'Regime changed',
            'weight_change': self._calculate_weight_change(previous_regime, current_regime),
        }

    def _calculate_weight_change(self, from_regime: str, to_regime: str) -> Dict[str, float]:
        """Calculate how weights change between regimes."""
        from_weights = REGIME_WEIGHTS.get(from_regime, {})
        to_weights = REGIME_WEIGHTS.get(to_regime, {})
        changes = {}
        for key in set(list(from_weights.keys()) + list(to_weights.keys())):
            changes[key] = to_weights.get(key, 0) - from_weights.get(key, 0)
        return changes

    # ── Helper Functions ──────────────────────────────────────────────

    def _ema(self, data: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(data) < period:
            return sum(data) / len(data) if data else 0
        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        return ema

    def _calculate_atr(self, highs: List[float], lows: List[float], closes: List[float], period: int) -> float:
        """Calculate Average True Range."""
        if len(closes) < 2:
            return 0
        true_ranges = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            true_ranges.append(tr)
        if not true_ranges:
            return 0
        recent = true_ranges[-period:] if len(true_ranges) >= period else true_ranges
        return sum(recent) / len(recent)

    def _calculate_volatility(self, closes: List[float]) -> float:
        """Calculate price volatility (standard deviation of returns)."""
        if len(closes) < 2:
            return 0
        returns = [(closes[i] / closes[i-1] - 1) for i in range(1, len(closes))]
        if not returns:
            return 0
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        return math.sqrt(variance)

    def _calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """Calculate RSI."""
        if len(closes) < period + 1:
            return 50
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _default_state(self) -> RegimeState:
        """Return default regime state when insufficient data."""
        return RegimeState(
            regime='sideways',
            confidence=20,
            sub_regimes={'trend': 'neutral', 'volatility': 'normal', 'momentum': 'neutral', 'volume': 'normal'},
            features={},
            weights=REGIME_WEIGHTS['sideways'],
        )
