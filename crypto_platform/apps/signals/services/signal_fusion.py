"""Signal Fusion Engine — regime-aware multi-factor signal generation.

Upgrades the existing 5-factor composite to 8 quant factors with
regime-conditioned weights and AI as post-fusion validator.

Architecture:
    Quant Factors (regime-conditioned weights):
        1. Technical Analysis (35%)
        2. Sentiment (15%)
        3. News (10%)
        4. Macro (15%)
        5. Derivatives (10%)  — NEW (Phase 60)
        6. Market Structure (8%) — NEW
        7. Order Book (4%) — NEW
        8. Portfolio Context (3%) — NEW

    → quant_composite_score (AI-free)

    → AI Validation (post-fusion, optional):
        LLM reasons over quant_composite_score + context
        Outputs: validation, adjusted confidence, risks

    → final_signal = validated composite

Key Design Decisions:
    1. AI is NOT a weighted input — it's a post-fusion validator
    2. Weights are regime-conditioned (from RegimeEngine)
    3. Weight Adjuster fine-tunes regime baseline weights
    4. Per-component contributions stored for reproducibility
"""
import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)


# ── Default Factor Weights (when no regime data available) ─────────────
# Redistributed from original 5-factor: AI's 25% split across quant factors

DEFAULT_QUANT_WEIGHTS = {
    'technical': Decimal('0.35'),
    'sentiment': Decimal('0.15'),
    'news': Decimal('0.10'),
    'macro': Decimal('0.15'),
    'derivatives': Decimal('0.10'),
    'market_structure': Decimal('0.08'),
    'order_book': Decimal('0.04'),
    'portfolio_context': Decimal('0.03'),
}


class SignalFusionEngine:
    """
    Regime-aware signal fusion engine.

    The fusion engine:
    1. Collects scores from all 8 quant factors
    2. Applies regime-conditioned weights
    3. Computes quant_composite_score (AI-free)
    4. Optionally validates via AI (post-fusion)
    5. Stores per-component contributions
    """

    def __init__(self):
        self.quant_weights = DEFAULT_QUANT_WEIGHTS.copy()

    def fuse_signal(
        self,
        symbol: str,
        timeframe: str,
        technical_score: float = 50.0,
        sentiment_score: float = 50.0,
        news_score: float = 50.0,
        macro_score: float = 50.0,
        derivatives_score: float = 50.0,
        market_structure_score: float = 50.0,
        order_book_score: float = 50.0,
        portfolio_context_score: float = 50.0,
        regime: str = 'sideways',
        regime_weights: Dict[str, float] = None,
        adjusted_weights: Dict[str, float] = None,
        ai_validation: Dict = None,
        current_price: float = 0.0,
    ) -> Dict:
        """
        Fuse multi-factor scores into a single signal.

        Args:
            symbol: Trading pair
            timeframe: Candle timeframe
            technical_score: Technical analysis score (0-100)
            sentiment_score: Sentiment score (0-100)
            news_score: News sentiment score (0-100)
            macro_score: Macro factors score (0-100)
            derivatives_score: Derivatives intelligence score (0-100)
            market_structure_score: Market structure score (0-100)
            order_book_score: Order book analysis score (0-100)
            portfolio_context_score: Portfolio context score (0-100)
            regime: Current market regime (from RegimeEngine)
            regime_weights: Regime-conditioned weights (overrides defaults)
            adjusted_weights: Weight Adjuster overrides (fine-tunes regime)
            ai_validation: AI post-fusion validation (optional)
            current_price: Current market price

        Returns:
            Dict with quant_composite_score, per-component contributions,
            final signal direction, confidence, and reasoning
        """
        # ── Step 1: Determine weights ────────────────────────────────
        weights = self._resolve_weights(regime, regime_weights, adjusted_weights)

        # ── Step 2: Calculate per-component contributions ────────────
        # contribution = score × weight (shows how much each factor moved the needle)
        raw_scores = {
            'technical': technical_score,
            'sentiment': sentiment_score,
            'news': news_score,
            'macro': macro_score,
            'derivatives': derivatives_score,
            'market_structure': market_structure_score,
            'order_book': order_book_score,
            'portfolio_context': portfolio_context_score,
        }

        contributions = {}
        for factor, score in raw_scores.items():
            weight = weights.get(factor, Decimal('0'))
            contributions[factor] = {
                'score': score,
                'weight': float(weight),
                'contribution': score * float(weight),
            }

        # ── Step 3: Calculate quant composite score (AI-free) ────────
        # contribution = score × weight; weights sum to 1.0
        # So composite is already in 0-100 range
        quant_composite = sum(
            c['contribution'] for c in contributions.values()
        )

        quant_composite = max(0, min(100, quant_composite))

        # ── Step 4: AI validation (post-fusion, optional) ───────────
        final_composite = quant_composite
        ai_adjustment = None
        ai_risks = []
        ai_reasons = []

        if ai_validation:
            final_composite, ai_adjustment, ai_risks, ai_reasons = (
                self._apply_ai_validation(quant_composite, ai_validation)
            )

        # ── Step 5: Determine direction and confidence ──────────────
        direction, confidence = self._determine_direction(final_composite)

        # ── Step 6: Build signal output ─────────────────────────────
        result = {
            'symbol': symbol,
            'timeframe': timeframe,
            'direction': direction,
            'confidence': confidence,

            # Quant composite (AI-free) — for reproducibility
            'quant_composite_score': round(quant_composite, 2),

            # Final composite (after AI validation)
            'composite_score': round(final_composite, 2),

            # Per-component breakdown
            'factor_contributions': {
                k: {
                    'score': v['score'],
                    'weight': v['weight'],
                    'contribution': round(v['contribution'], 2),
                }
                for k, v in contributions.items()
            },

            # Factor scores (backward compatible)
            'factor_scores': {
                'technical': technical_score,
                'sentiment': sentiment_score,
                'news': news_score,
                'macro': macro_score,
                'derivatives': derivatives_score,
                'market_structure': market_structure_score,
                'order_book': order_book_score,
                'portfolio_context': portfolio_context_score,
            },

            # Weights used
            'weights_used': {k: float(v) for k, v in weights.items()},
            'regime': regime,
            'regime_weights_applied': regime_weights is not None,

            # AI validation (if applied)
            'ai_validated': ai_validation is not None,
            'ai_adjustment': ai_adjustment,
            'ai_risks': ai_risks,
            'ai_reasons': ai_reasons,

            # Metadata
            'generated_at': datetime.now().isoformat(),
            'engine_version': '2.0',  # Signal Fusion Engine v2
        }

        logger.info(
            f"Signal fused: {symbol} {direction} (confidence={confidence}%) | "
            f"Quant: {quant_composite:.1f} | Final: {final_composite:.1f} | "
            f"Regime: {regime}"
        )

        return result

    def _resolve_weights(
        self,
        regime: str,
        regime_weights: Dict[str, float] = None,
        adjusted_weights: Dict[str, float] = None,
    ) -> Dict[str, Decimal]:
        """
        Resolve final weights through the priority chain:
        1. Regime-conditioned weights (baseline)
        2. Weight Adjuster overrides (fine-tuning)
        3. Default weights (fallback)
        """
        from .regime_engine import REGIME_WEIGHTS

        # Start with regime weights
        if regime_weights:
            base = {k: Decimal(str(v)) for k, v in regime_weights.items()}
        elif regime in REGIME_WEIGHTS:
            base = {k: Decimal(str(v)) for k, v in REGIME_WEIGHTS[regime].items()}
        else:
            base = DEFAULT_QUANT_WEIGHTS.copy()

        # Apply Weight Adjuster overrides (if any)
        if adjusted_weights:
            for k, v in adjusted_weights.items():
                if k in base:
                    base[k] = Decimal(str(v))

        # Ensure all required factors have weights
        for factor in DEFAULT_QUANT_WEIGHTS:
            if factor not in base:
                base[factor] = DEFAULT_QUANT_WEIGHTS[factor]

        # Normalize to sum to 1.0
        total = sum(base.values())
        if total > 0:
            base = {k: v / total for k, v in base.items()}

        return base

    def _apply_ai_validation(
        self,
        quant_score: float,
        ai_data: Dict,
    ) -> Tuple[float, float, List, List]:
        """
        Apply AI post-fusion validation.

        The AI doesn't contribute to the score — it reasons over the
        quant composite and adjusts confidence/risks.

        Returns:
            Tuple of (adjusted_score, adjustment, risks, reasons)
        """
        adjustment = 0.0
        risks = []
        reasons = []

        # AI can adjust score by ±10% max
        ai_confidence = ai_data.get('confidence', 50) / 100
        ai_direction = ai_data.get('direction', 'neutral')

        if ai_direction == 'bullish':
            adjustment = 10 * ai_confidence  # Max +10
        elif ai_direction == 'bearish':
            adjustment = -10 * ai_confidence  # Max -10

        adjusted = max(0, min(100, quant_score + adjustment))

        # AI risks
        if ai_data.get('risks'):
            risks = ai_data['risks']
        if ai_data.get('reasons'):
            reasons = ai_data['reasons']

        return adjusted, adjustment, risks, reasons

    def _determine_direction(self, score: float) -> Tuple[str, int]:
        """Determine signal direction and confidence from composite score."""
        if score >= 75:
            direction = 'strong_buy'
        elif score >= 60:
            direction = 'buy'
        elif score >= 40:
            direction = 'hold'
        elif score >= 25:
            direction = 'sell'
        else:
            direction = 'strong_sell'

        # Confidence: distance from 50, scaled to 10-95
        confidence = int(50 + abs(score - 50) * 0.9)
        confidence = max(10, min(95, confidence))

        return direction, confidence

    def get_quant_composite_only(
        self,
        scores: Dict[str, float],
        regime: str = 'sideways',
    ) -> float:
        """
        Get pure quant composite without AI — for AI OFF mode.

        This is the same calculation as fuse_signal but without any AI dependency.
        """
        from .regime_engine import REGIME_WEIGHTS

        weights = REGIME_WEIGHTS.get(regime, {})
        if not weights:
            weights = {k: float(v) for k, v in DEFAULT_QUANT_WEIGHTS.items()}

        total = 0.0
        for factor, score in scores.items():
            w = weights.get(factor, 0)
            total += score * w

        # Weights sum to 1.0, so total is already 0-100
        return max(0, min(100, total))
