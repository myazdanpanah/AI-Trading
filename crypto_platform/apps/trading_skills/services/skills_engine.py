"""
Trading Skills Engine
Integrates skills from https://github.com/tradermonty/claude-trading-skills
for the LLM to use when analyzing crypto markets.

Skills integrated:
1. Crypto Regime Analyzer - Market regime health (0-100 score)
2. Position Sizer - Risk-based position sizing
3. Technical Analyst - Multi-indicator technical analysis
4. Exposure Coach - Market posture recommendations
5. Signal Postmortem - Trade review framework
"""
import json
import math
import os
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# ============================================================
# Crypto Regime Analyzer (from claude-trading-skills)
# ============================================================

COMPONENT_WEIGHTS = {
    "btc_trend": 0.25,
    "alt_breadth": 0.20,
    "dominance": 0.15,
    "funding": 0.15,
    "drawdown_vol": 0.15,
    "momentum_thrust": 0.10,
}

COMPONENT_LABELS = {
    "btc_trend": "BTC Trend Structure",
    "alt_breadth": "Alt Breadth Participation",
    "dominance": "BTC Dominance Regime",
    "funding": "Perpetual Funding Regime",
    "drawdown_vol": "Drawdown & Volatility Position",
    "momentum_thrust": "Momentum Thrust / Washout",
}

ZONES = [
    (80, "RISK_ON", "Broad risk-on conditions; review risk limits before decisions"),
    (40, "NEUTRAL", "Mixed conditions; no strong regime conclusion"),
    (0, "RISK_OFF", "Defensive conditions; review existing risk controls"),
]


def calculate_btc_trend(closes: List[float]) -> Dict:
    """Calculate BTC trend structure score (0-100)."""
    if len(closes) < 200:
        return {"score": 50, "signal": "Insufficient data", "data_available": False}

    # Moving averages
    sma50 = sum(closes[-50:]) / 50
    sma200 = sum(closes[-200:]) / 200
    current = closes[-1]

    # 200DMA slope (20-day change)
    slope = (sma200 - sum(closes[-220:-20]) / 200) / 20 if len(closes) >= 220 else 0

    score = 50  # Base

    # Price vs MAs
    if current > sma50 > sma200:
        score += 25  # Perfect stack
    elif current > sma200:
        score += 15
    elif current < sma200:
        score -= 20

    # 50DMA vs 200DMA
    if sma50 > sma200:
        score += 10  # Golden cross territory
    else:
        score -= 10

    # 200DMA slope
    if slope > 0:
        score += min(15, slope / current * 10000)
    else:
        score -= min(15, abs(slope) / current * 10000)

    score = max(0, min(100, score))

    signal = f"Price {'above' if current > sma200 else 'below'} 200DMA"
    if current > sma50 > sma200:
        signal += ", bullish stack"
    elif current < sma50 < sma200:
        signal += ", bearish stack"

    return {"score": round(score, 1), "signal": signal, "data_available": True}


def calculate_alt_breadth(alt_series: Dict[str, List[float]]) -> Dict:
    """Calculate alt breadth participation score (0-100)."""
    if not alt_series:
        return {"score": 50, "signal": "No alt data", "data_available": False}

    above_200dma = 0
    above_50dma = 0
    total = len(alt_series)

    for symbol, closes in alt_series.items():
        if len(closes) < 200:
            continue
        current = closes[-1]
        sma200 = sum(closes[-200:]) / 200
        sma50 = sum(closes[-50:]) / 50

        if current > sma200:
            above_200dma += 1
        if current > sma50:
            above_50dma += 1

    if total == 0:
        return {"score": 50, "signal": "Insufficient data", "data_available": False}

    pct_200 = above_200dma / total * 100
    pct_50 = above_50dma / total * 100

    # Score: broad participation = high score
    score = (pct_200 * 0.6 + pct_50 * 0.4)
    score = max(0, min(100, score))

    signal = f"{pct_200:.0f}% above 200DMA, {pct_50:.0f}% above 50DMA"
    return {"score": round(score, 1), "signal": signal, "data_available": True}


def calculate_dominance_regime(dominance_series: List[float], btc_trend_up: bool) -> Dict:
    """Calculate BTC dominance regime score (0-100)."""
    if len(dominance_series) < 31:
        return {"score": 50, "signal": "Insufficient dominance history", "data_available": False}

    current = dominance_series[-1]
    avg_30d = sum(dominance_series[-30:]) / 30
    trend = current - avg_30d

    # Rising dominance + BTC downtrend = risk-off (capital flees to BTC)
    # Falling dominance + BTC uptrend = alt season (risk-on)
    if btc_trend_up and trend < -1:
        score = 80  # Alt season
        signal = f"Alt season: dominance falling ({trend:+.1f}%) with BTC uptrend"
    elif btc_trend_up and trend > 1:
        score = 60  # BTC strength, alts lagging
        signal = f"BTC strength: dominance rising ({trend:+.1f}%)"
    elif not btc_trend_up and trend > 1:
        score = 20  # Risk-off: capital fleeing to BTC
        signal = f"Risk-off: dominance rising ({trend:+.1f}%) in downtrend"
    else:
        score = 50
        signal = f"Neutral: dominance {trend:+.1f}% over 30d"

    return {"score": round(score, 1), "signal": signal, "data_available": True}


def calculate_funding_regime(funding: Dict[str, float]) -> Dict:
    """Calculate perpetual funding regime score (0-100)."""
    if not funding:
        return {"score": 50, "signal": "No funding data", "data_available": False}

    rates = list(funding.values())
    avg_rate = sum(rates) / len(rates)

    # Funding rate is per 8h; annualize for context
    # Normal: 0.01% per 8h = ~10.95% APR
    # Extreme long: > 0.05% per 8h = ~54.75% APR
    # Extreme short: < -0.05% per 8h

    if abs(avg_rate) < 0.0001:
        score = 70  # Healthy leverage
        signal = f"Healthy leverage: avg funding {avg_rate*100:.4f}%"
    elif avg_rate > 0.001:
        score = 25  # Crowded longs - contrarian risk
        signal = f"Crowded longs: avg funding {avg_rate*100:.4f}% - overleveraged"
    elif avg_rate > 0.0005:
        score = 50  # Elevated but not extreme
        signal = f"Elevated long funding: {avg_rate*100:.4f}%"
    elif avg_rate < -0.001:
        score = 35  # Crowded shorts
        signal = f"Crowded shorts: avg funding {avg_rate*100:.4f}%"
    elif avg_rate < -0.0005:
        score = 45
        signal = f"Elevated short funding: {avg_rate*100:.4f}%"
    else:
        score = 60
        signal = f"Normal funding: {avg_rate*100:.4f}%"

    return {"score": round(score, 1), "signal": signal, "data_available": True}


def calculate_drawdown_vol(closes: List[float]) -> Dict:
    """Calculate drawdown and volatility position (0-100)."""
    if len(closes) < 30:
        return {"score": 50, "signal": "Insufficient data", "data_available": False}

    current = closes[-1]
    high_1y = max(closes[-365:]) if len(closes) >= 365 else max(closes)
    low_1y = min(closes[-365:]) if len(closes) >= 365 else min(closes)

    # Drawdown from 1y high
    drawdown = (current - high_1y) / high_1y * 100 if high_1y > 0 else 0

    # Realized volatility (30-day)
    returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(-30, 0) if closes[i-1] > 0]
    if returns:
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        vol_30d = math.sqrt(variance) * math.sqrt(365) * 100  # Annualized
    else:
        vol_30d = 50

    # Score: small drawdown + low vol = healthy (high score)
    score = 50

    # Drawdown component
    if drawdown > -10:
        score += 20  # Near highs
    elif drawdown > -30:
        score += 10  # Moderate pullback
    elif drawdown > -50:
        score -= 10  # Deep correction
    else:
        score -= 25  # Capitulation

    # Volatility component (lower vol = healthier)
    if vol_30d < 30:
        score += 15
    elif vol_30d < 60:
        score += 5
    elif vol_30d > 100:
        score -= 15

    score = max(0, min(100, score))
    signal = f"Drawdown: {drawdown:.1f}%, Vol(30d): {vol_30d:.0f}%"
    return {"score": round(score, 1), "signal": signal, "data_available": True}


def calculate_momentum_thrust(series: Dict[str, List[float]]) -> Dict:
    """Calculate momentum thrust score (0-100)."""
    if not series:
        return {"score": 50, "signal": "No data", "data_available": False}

    positive_30d = 0
    total = 0

    for symbol, closes in series.items():
        if len(closes) < 31:
            continue
        if closes[-31] > 0:
            change_30d = (closes[-1] - closes[-31]) / closes[-31] * 100
            if change_30d > 0:
                positive_30d += 1
            total += 1

    if total == 0:
        return {"score": 50, "signal": "Insufficient data", "data_available": False}

    pct_positive = positive_30d / total * 100
    score = max(0, min(100, pct_positive))

    signal = f"{pct_positive:.0f}% of universe positive over 30d"
    return {"score": round(score, 1), "signal": signal, "data_available": True}


def calculate_composite_score(components: Dict) -> Dict:
    """Calculate weighted composite score from components."""
    available = {
        cid: comp
        for cid, comp in components.items()
        if cid in COMPONENT_WEIGHTS and comp.get("data_available", False)
    }

    total_weight = sum(COMPONENT_WEIGHTS[cid] for cid in available)

    if len(available) < 4 or total_weight < 0.65:
        return {
            "score": None,
            "zone": "UNKNOWN",
            "guidance": f"Insufficient data ({len(available)}/6 components, {total_weight:.0%} weight)",
            "effective_weights": {},
        }

    effective = {cid: COMPONENT_WEIGHTS[cid] / total_weight for cid in available}
    score = sum(available[cid]["score"] * w for cid, w in effective.items())
    score = round(max(0.0, min(100.0, score)), 1)

    zone, guidance = ZONES[-1][1], ZONES[-1][2]
    for threshold, z, g in ZONES:
        if score >= threshold:
            zone, guidance = z, g
            break

    return {
        "score": score,
        "zone": zone,
        "guidance": guidance,
        "effective_weights": {k: round(v, 4) for k, v in effective.items()},
        "components_available": len(available),
    }


# ============================================================
# Position Sizer (from claude-trading-skills)
# ============================================================

def calculate_position_size(
    account_size: float,
    risk_pct: float,
    entry_price: float,
    stop_loss_price: float,
    current_price: float = None,
) -> Dict:
    """
    Calculate position size using fixed-fractional risk model.
    
    Args:
        account_size: Total account value in USD
        risk_pct: Max risk per trade as decimal (e.g., 0.02 = 2%)
        entry_price: Planned entry price
        stop_loss_price: Stop loss price
        current_price: Current market price (for adjusted entry)
    
    Returns:
        Position size details
    """
    if current_price is None:
        current_price = entry_price

    risk_amount = account_size * risk_pct
    risk_per_unit = abs(entry_price - stop_loss_price)

    if risk_per_unit <= 0:
        return {"error": "Stop loss must be different from entry price"}

    position_size = risk_amount / risk_per_unit
    position_value = position_size * current_price
    position_pct = (position_value / account_size) * 100

    # Risk/reward ratio
    if current_price > entry_price:
        # Long trade
        reward = current_price * 1.1 - current_price  # Assume 10% target
    else:
        reward = current_price - current_price * 0.9

    rr_ratio = reward / risk_per_unit if risk_per_unit > 0 else 0

    return {
        "position_size": round(position_size, 6),
        "position_value_usd": round(position_value, 2),
        "position_pct_of_account": round(position_pct, 2),
        "risk_amount_usd": round(risk_amount, 2),
        "risk_per_unit": round(risk_per_unit, 8),
        "risk_reward_ratio": round(rr_ratio, 2),
        "entry_price": entry_price,
        "stop_loss": stop_loss_price,
        "current_price": current_price,
    }


# ============================================================
# Technical Analyst (from claude-trading-skills)
# ============================================================

def analyze_technical(closes: List[float], highs: List[float] = None, lows: List[float] = None) -> Dict:
    """
    Multi-indicator technical analysis.
    
    Returns scores and signals for:
    - Trend (SMA crossover, price vs MAs)
    - Momentum (RSI, MACD)
    - Volatility (Bollinger Bands, ATR)
    - Support/Resistance
    """
    if len(closes) < 200:
        return {"error": "Need at least 200 data points for full analysis"}

    current = closes[-1]

    # --- Trend ---
    sma20 = sum(closes[-20:]) / 20
    sma50 = sum(closes[-50:]) / 50
    sma200 = sum(closes[-200:]) / 200

    trend_score = 50
    if current > sma20 > sma50 > sma200:
        trend_score = 90
        trend_signal = "Strong uptrend: price > SMA20 > SMA50 > SMA200"
    elif current > sma50 > sma200:
        trend_score = 75
        trend_signal = "Uptrend: price > SMA50 > SMA200"
    elif current < sma20 < sma50 < sma200:
        trend_score = 10
        trend_signal = "Strong downtrend: price < SMA20 < SMA50 < SMA200"
    elif current < sma50 < sma200:
        trend_score = 25
        trend_signal = "Downtrend: price < SMA50 < SMA200"
    else:
        trend_score = 50
        trend_signal = "Mixed trend signals"

    # --- RSI (14-period) ---
    if len(closes) >= 15:
        deltas = [closes[i] - closes[i-1] for i in range(-14, 0)]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = sum(gains) / 14
        avg_loss = sum(losses) / 14

        if avg_loss > 0:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        else:
            rsi = 100

        if rsi > 70:
            momentum_score = 25
            momentum_signal = f"RSI {rsi:.1f} - Overbought"
        elif rsi < 30:
            momentum_score = 75
            momentum_signal = f"RSI {rsi:.1f} - Oversold (potential buy)"
        elif rsi > 60:
            momentum_score = 65
            momentum_signal = f"RSI {rsi:.1f} - Bullish momentum"
        elif rsi < 40:
            momentum_score = 35
            momentum_signal = f"RSI {rsi:.1f} - Bearish momentum"
        else:
            momentum_score = 50
            momentum_signal = f"RSI {rsi:.1f} - Neutral"
    else:
        rsi = 50
        momentum_score = 50
        momentum_signal = "RSI: insufficient data"

    # --- Bollinger Bands ---
    if len(closes) >= 20:
        sma20 = sum(closes[-20:]) / 20
        variance = sum((c - sma20) ** 2 for c in closes[-20:]) / 20
        std20 = math.sqrt(variance)
        bb_upper = sma20 + 2 * std20
        bb_lower = sma20 - 2 * std20
        bb_width = (bb_upper - bb_lower) / sma20 * 100

        if current > bb_upper:
            volatility_signal = f"Price above upper BB ({bb_width:.1f}% width) - Overbought"
        elif current < bb_lower:
            volatility_signal = f"Price below lower BB ({bb_width:.1f}% width) - Oversold"
        else:
            volatility_signal = f"Price within BB ({bb_width:.1f}% width)"

        volatility_score = 50
        if bb_width < 5:
            volatility_score = 70  # Low vol = opportunity
            volatility_signal += " - Low volatility squeeze"
        elif bb_width > 15:
            volatility_score = 30  # High vol = caution
            volatility_signal += " - High volatility"
    else:
        volatility_score = 50
        volatility_signal = "BB: insufficient data"

    # --- Support/Resistance ---
    if highs and lows and len(highs) >= 50 and len(lows) >= 50:
        resistance = max(highs[-50:])
        support = min(lows[-50:])
        range_pct = (resistance - support) / current * 100

        if current > resistance * 0.98:
            sr_signal = f"Near resistance ${resistance:,.2f} - Breakout watch"
        elif current < support * 1.02:
            sr_signal = f"Near support ${support:,.2f} - Breakdown watch"
        else:
            sr_signal = f"Range: ${support:,.2f} - ${resistance:,.2f} ({range_pct:.1f}%)"
    else:
        sr_signal = "S/R: insufficient data"

    # Overall score
    overall = (trend_score * 0.35 + momentum_score * 0.30 + volatility_score * 0.20 + 50 * 0.15)

    return {
        "overall_score": round(overall, 1),
        "trend": {"score": trend_score, "signal": trend_signal},
        "momentum": {"score": momentum_score, "signal": momentum_signal, "rsi": round(rsi, 1)},
        "volatility": {"score": volatility_score, "signal": volatility_signal},
        "support_resistance": {"signal": sr_signal},
    }


# ============================================================
# Exposure Coach (from claude-trading-skills)
# ============================================================

def calculate_exposure_posture(regime_result: Dict) -> Dict:
    """
    Generate exposure posture recommendation based on regime analysis.
    """
    if regime_result.get("composite", {}).get("zone") == "UNKNOWN":
        return {
            "posture": "UNCERTAIN",
            "max_exposure": 0.3,
            "recommendation": "Insufficient data for posture recommendation",
        }

    score = regime_result["composite"]["score"]
    zone = regime_result["composite"]["zone"]

    if zone == "RISK_ON":
        posture = "AGGRESSIVE"
        max_exposure = 0.8
        recommendation = "Broad risk-on; consider full position sizing"
    elif zone == "NEUTRAL":
        posture = "MODERATE"
        max_exposure = 0.5
        recommendation = "Mixed signals; moderate exposure with tight stops"
    else:
        posture = "DEFENSIVE"
        max_exposure = 0.2
        recommendation = "Risk-off; reduce exposure, raise cash levels"

    return {
        "posture": posture,
        "max_exposure": max_exposure,
        "recommendation": recommendation,
        "regime_score": score,
        "regime_zone": zone,
    }


# ============================================================
# Main Skill Runner
# ============================================================

class TradingSkillsEngine:
    """Main engine that runs all trading skills and returns structured results."""

    def __init__(self, coingecko_client=None):
        self.coingecko = coingecko_client

    async def run_crypto_regime_analysis(self, market_data: Dict) -> Dict:
        """Run full crypto regime analysis from market data."""
        series = market_data.get("series", {})
        funding = market_data.get("funding", {})
        dominance_series = market_data.get("dominance_series", [])

        btc_closes = series.get("BTCUSDT", series.get("BTC", []))
        alt_series = {k: v for k, v in series.items() if k not in ("BTCUSDT", "BTC")}

        # Run all 6 components
        btc_trend = calculate_btc_trend(btc_closes)
        btc_trend_up = btc_trend.get("data_available", False) and btc_trend["score"] >= 60

        components = {
            "btc_trend": btc_trend,
            "alt_breadth": calculate_alt_breadth(alt_series),
            "dominance": calculate_dominance_regime(dominance_series, btc_trend_up),
            "funding": calculate_funding_regime(funding),
            "drawdown_vol": calculate_drawdown_vol(btc_closes),
            "momentum_thrust": calculate_momentum_thrust(series),
        }

        composite = calculate_composite_score(components)
        exposure = calculate_exposure_posture({"composite": composite})

        return {
            "metadata": {
                "as_of": datetime.now(timezone.utc).isoformat(),
                "universe_size": len(series),
                "components_with_data": sum(1 for c in components.values() if c.get("data_available")),
            },
            "components": {
                cid: {
                    "label": COMPONENT_LABELS.get(cid, cid),
                    "weight": f"{COMPONENT_WEIGHTS[cid]*100:.0f}%",
                    **comp,
                }
                for cid, comp in components.items()
            },
            "composite": composite,
            "exposure": exposure,
        }

    def run_position_sizer(self, params: Dict) -> Dict:
        """Run position sizing calculation."""
        return calculate_position_size(
            account_size=params.get("account_size", 10000),
            risk_pct=params.get("risk_pct", 0.02),
            entry_price=params.get("entry_price", 0),
            stop_loss_price=params.get("stop_loss_price", 0),
            current_price=params.get("current_price"),
        )

    def run_technical_analysis(self, closes: List[float], highs: List[float] = None, lows: List[float] = None) -> Dict:
        """Run technical analysis on price data."""
        return analyze_technical(closes, highs, lows)

    def run_candlestick_analysis(self, closes: List[float], highs: List[float], lows: List[float],
                                   opens: List[float] = None, volumes: List[float] = None) -> Dict:
        """Run candlestick pattern analysis using T.A.E. framework."""
        from .candlestick_skill import CandlestickSkill
        return CandlestickSkill.analyze(closes, highs, lows, opens, volumes)

    def get_skill_definitions(self) -> List[Dict]:
        """Return definitions of all available skills for the LLM."""
        return [
            {
                "name": "crypto_regime_analyzer",
                "description": "Quantifies crypto market regime health (0-100 composite) from 6 components. Use to determine market posture before any coin-level analysis.",
                "inputs": ["market_series", "funding_rates", "dominance_history"],
                "outputs": ["composite_score", "zone", "exposure_posture"],
                "source": "https://github.com/tradermonty/claude-trading-skills",
            },
            {
                "name": "position_sizer",
                "description": "Calculates position size using fixed-fractional risk model. Enter account size, risk %, entry/stop prices.",
                "inputs": ["account_size", "risk_pct", "entry_price", "stop_loss_price"],
                "outputs": ["position_size", "risk_amount", "risk_reward"],
                "source": "https://github.com/tradermonty/claude-trading-skills",
            },
            {
                "name": "technical_analyst",
                "description": "Multi-indicator technical analysis: trend (SMA), momentum (RSI), volatility (Bollinger), support/resistance.",
                "inputs": ["closes", "highs", "lows"],
                "outputs": ["overall_score", "trend", "momentum", "volatility"],
                "source": "https://github.com/tradermonty/claude-trading-skills",
            },
            {
                "name": "exposure_coach",
                "description": "Generates market posture recommendation (AGGRESSIVE/MODERATE/DEFENSIVE) with max exposure % based on regime analysis.",
                "inputs": ["regime_analysis"],
                "outputs": ["posture", "max_exposure", "recommendation"],
                "source": "https://github.com/tradermonty/claude-trading-skills",
            },
            {
                "name": "candlestick_analyst",
                "description": "Analyzes candlestick patterns using T.A.E. framework (Trend, Area of Value, Entry Trigger). Detects 5 powerful patterns: Engulfing, Hammer/Shooting Star, Doji, Morning/Evening Star, Tweezer.",
                "inputs": ["closes", "highs", "lows", "opens"],
                "outputs": ["patterns", "signals", "trend_bias", "overall_score"],
                "source": "Rayner Teo - Ultimate Candlestick Patterns Trading Course",
            },
        ]
