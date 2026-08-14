"""Versioning & Data Lineage — full signal reproducibility.

Every signal must store enough information to answer:
  "Why was this signal generated at this exact moment?"

Stores:
  1. Strategy version (which signal generation logic)
  2. Feature version (which indicator calculations)
  3. Model version (which LLM model, if used)
  4. Prompt version (which prompt template)
  5. Weight snapshot (exact factor weights used)
  6. Market snapshot (price, indicators at T)
  7. News snapshot (articles, sentiment at T)
  8. Social snapshot (fear/greed, X/Twitter at T)
  9. Regime snapshot (detected regime at T)
  10. LLM context/output (if AI was used)
  11. Agent ensemble output (if ensemble was used)

Architecture:
    SignalGenerationRequest
        ↓
    VersionTracker.capture_lineage()
        ↓
    SignalLineage (stored in DB)
        ↓
    GET /signals/lineage/{signal_id}/ → full reproducibility report

Usage:
    tracker = VersionTracker()
    lineage = tracker.capture_lineage(
        signal=signal,
        factor_scores=...,
        regime='bull_trend',
        weights_used=...,
        market_snapshot=...,
    )
"""
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


# ── Current System Versions ───────────────────────────────────────────

SYSTEM_VERSIONS = {
    'strategy': '2.0',          # SignalFusionEngine v2
    'features': '1.2',          # IndicatorEngine v1.2
    'regime': '1.0',            # RegimeEngine v1
    'risk': '1.0',              # RiskEngine v1
    'calibration': '1.0',       # CalibrationEngine v1
    'ensemble': '1.0',          # AgentEnsemble v1
    'backtester': '1.0',        # SignalBacktester v1
    'walk_forward': '1.0',      # WalkForwardEngine v1
}


class VersionTracker:
    """Tracks versions and captures data lineage for every signal.

    The tracker ensures every signal is reproducible by storing:
    - Which code version generated it
    - Which data was available at that moment
    - Which weights were active
    - Which LLM response was received
    """

    def __init__(self):
        self.versions = SYSTEM_VERSIONS.copy()

    def capture_lineage(
        self,
        signal_data: Dict,
        factor_scores: Dict[str, float] = None,
        regime: str = 'unknown',
        regime_confidence: float = 0.0,
        weights_used: Dict[str, float] = None,
        market_snapshot: Dict = None,
        news_snapshot: Dict = None,
        social_snapshot: Dict = None,
        derivatives_snapshot: Dict = None,
        llm_context: Dict = None,
        llm_output: Dict = None,
        ensemble_output: Dict = None,
        risk_decision: Dict = None,
        metadata: Dict = None,
    ) -> Dict:
        """Capture full lineage for a signal.

        Args:
            signal_data: Signal creation data (symbol, direction, confidence, etc.)
            factor_scores: Individual factor scores
            regime: Detected market regime
            regime_confidence: Regime detection confidence
            weights_used: Factor weights used
            market_snapshot: Price, indicators, order book at T
            news_snapshot: Recent news, sentiment at T
            social_snapshot: Fear/greed, social sentiment at T
            derivatives_snapshot: Funding, OI, liquidations at T
            llm_context: What was sent to LLM
            llm_output: What LLM returned
            ensemble_output: Agent ensemble results
            risk_decision: Risk engine decision
            metadata: Any additional metadata

        Returns:
            Dict suitable for storing in SignalLineage.data_lineage
        """
        lineage = {
            'version': '1.0',  # Lineage schema version
            'captured_at': datetime.now().isoformat(),

            # ── Code Versions ────────────────────────────────────────
            'versions': self.versions.copy(),

            # ── Signal Context ───────────────────────────────────────
            'signal': {
                'symbol': signal_data.get('symbol', 'UNKNOWN'),
                'direction': signal_data.get('direction', 'hold'),
                'confidence': signal_data.get('confidence', 50),
                'composite_score': signal_data.get('composite_score', 50),
                'timeframe': signal_data.get('timeframe', '1h'),
            },

            # ── Factor Scores ────────────────────────────────────────
            'factor_scores': factor_scores or {},

            # ── Regime ───────────────────────────────────────────────
            'regime': {
                'detected': regime,
                'confidence': regime_confidence,
            },

            # ── Weights ──────────────────────────────────────────────
            'weights': weights_used or {},

            # ── Data Snapshots ───────────────────────────────────────
            'market_snapshot': market_snapshot or {},
            'news_snapshot': news_snapshot or {},
            'social_snapshot': social_snapshot or {},
            'derivatives_snapshot': derivatives_snapshot or {},

            # ── AI Context ───────────────────────────────────────────
            'llm_context': llm_context or {},
            'llm_output': llm_output or {},

            # ── Ensemble ─────────────────────────────────────────────
            'ensemble_output': ensemble_output or {},

            # ── Risk ─────────────────────────────────────────────────
            'risk_decision': risk_decision or {},

            # ── Metadata ─────────────────────────────────────────────
            'metadata': metadata or {},
        }

        return lineage

    def build_market_snapshot(
        self,
        current_price: float = 0,
        indicators: Dict = None,
        candles_count: int = 0,
        volume_24h: float = 0,
    ) -> Dict:
        """Build market data snapshot."""
        return {
            'current_price': current_price,
            'indicators': indicators or {},
            'candles_used': candles_count,
            'volume_24h': volume_24h,
            'snapshot_time': datetime.now().isoformat(),
        }

    def build_news_snapshot(
        self,
        article_count: int = 0,
        avg_sentiment: float = 50,
        top_headlines: List[str] = None,
        sources_used: List[str] = None,
    ) -> Dict:
        """Build news data snapshot."""
        return {
            'article_count': article_count,
            'avg_sentiment': avg_sentiment,
            'top_headlines': top_headlines or [],
            'sources_used': sources_used or [],
            'snapshot_time': datetime.now().isoformat(),
        }

    def build_social_snapshot(
        self,
        fear_greed_index: int = 50,
        social_sentiment: float = 50,
        twitter_sentiment: float = 50,
        trending_topics: List[str] = None,
    ) -> Dict:
        """Build social data snapshot."""
        return {
            'fear_greed_index': fear_greed_index,
            'social_sentiment': social_sentiment,
            'twitter_sentiment': twitter_sentiment,
            'trending_topics': trending_topics or [],
            'snapshot_time': datetime.now().isoformat(),
        }

    def build_derivatives_snapshot(
        self,
        funding_rate: float = 0,
        open_interest: float = 0,
        long_short_ratio: float = 1.0,
        liquidation_24h: float = 0,
    ) -> Dict:
        """Build derivatives data snapshot."""
        return {
            'funding_rate': funding_rate,
            'open_interest': open_interest,
            'long_short_ratio': long_short_ratio,
            'liquidation_24h': liquidation_24h,
            'snapshot_time': datetime.now().isoformat(),
        }

    def build_llm_context(
        self,
        model: str = '',
        prompt_version: str = '1.0',
        system_prompt_preview: str = '',
        user_context_size: int = 0,
        temperature: float = 0.3,
    ) -> Dict:
        """Build LLM context snapshot."""
        return {
            'model': model,
            'prompt_version': prompt_version,
            'system_prompt_preview': system_prompt_preview[:200],
            'user_context_size': user_context_size,
            'temperature': temperature,
            'snapshot_time': datetime.now().isoformat(),
        }

    def build_llm_output(
        self,
        content: str = '',
        parsed_output: Dict = None,
        latency_ms: int = 0,
        tokens_used: int = 0,
        success: bool = True,
    ) -> Dict:
        """Build LLM output snapshot."""
        return {
            'content_preview': content[:500] if content else '',
            'parsed_output': parsed_output or {},
            'latency_ms': latency_ms,
            'tokens_used': tokens_used,
            'success': success,
            'snapshot_time': datetime.now().isoformat(),
        }

    def explain_signal(self, lineage_data: Dict) -> str:
        """Generate a human-readable explanation of why a signal was generated.

        Args:
            lineage_data: The stored lineage data for a signal

        Returns:
            Plain text explanation
        """
        if not lineage_data:
            return "No lineage data available for this signal."

        signal = lineage_data.get('signal', {})
        versions = lineage_data.get('versions', {})
        factor_scores = lineage_data.get('factor_scores', {})
        regime = lineage_data.get('regime', {})
        weights = lineage_data.get('weights', {})

        parts = []

        # Signal overview
        parts.append(
            f"Signal: {signal.get('symbol', '?')} {signal.get('direction', '?').upper()} "
            f"with {signal.get('confidence', 0)}% confidence"
        )
        parts.append(f"Timeframe: {signal.get('timeframe', '?')}")
        parts.append(f"Composite Score: {signal.get('composite_score', 0):.1f}/100")

        # Regime
        parts.append(f"\nMarket Regime: {regime.get('detected', 'unknown')} "
                     f"(confidence: {regime.get('confidence', 0):.0%})")

        # Factor breakdown
        if factor_scores:
            parts.append("\nFactor Scores:")
            for factor, score in sorted(factor_scores.items(), key=lambda x: -x[1]):
                weight = weights.get(factor, 0)
                contribution = score * weight if weight else 0
                parts.append(f"  {factor}: {score:.1f} (weight: {weight:.0%}, contribution: {contribution:.1f})")

        # Versions
        parts.append(f"\nStrategy: v{versions.get('strategy', '?')}")
        parts.append(f"Features: v{versions.get('features', '?')}")
        if versions.get('ensemble'):
            parts.append(f"Ensemble: v{versions.get('ensemble', '?')}")

        # AI
        llm_output = lineage_data.get('llm_output', {})
        if llm_output and llm_output.get('success'):
            parts.append(f"\nAI Model: {lineage_data.get('llm_context', {}).get('model', '?')}")
            parts.append(f"AI Latency: {llm_output.get('latency_ms', 0)}ms")

        ensemble = lineage_data.get('ensemble_output', {})
        if ensemble and ensemble.get('verdict'):
            parts.append(f"Ensemble Verdict: {ensemble['verdict']} "
                        f"(adjusted confidence: {ensemble.get('adjusted_confidence', '?')}%)")

        return '\n'.join(parts)
