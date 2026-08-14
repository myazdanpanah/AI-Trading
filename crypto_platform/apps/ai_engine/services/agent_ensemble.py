"""Agent Ensemble — 5 role-based local agents for multi-perspective signal validation.

Architecture:
    ┌─────────────────────────────────────────────────┐
    │              SIGNAL CONTEXT                       │
    │  (quant_composite, regime, factor_scores, etc.)   │
    └───────────┬──────────┬──────────┬────────────────┘
                │          │          │
    ┌───────────▼──┐ ┌─────▼────┐ ┌──▼───────────┐
    │  Technical   │ │  News    │ │  Market      │
    │  Analyst     │ │  Analyst │ │  Analyst     │
    └──────┬───────┘ └────┬─────┘ └──────┬───────┘
           │              │              │
    ┌──────▼──────────────▼──────────────▼───────┐
    │           Risk Analyst                       │
    └──────────────────┬──────────────────────────┘
                       │
    ┌──────────────────▼──────────────────────────┐
    │          Final Validator                      │
    │  (reviews all agent outputs + quant score)   │
    └──────────────────┬──────────────────────────┘
                       │
                  FINAL VERDICT

Each agent:
  - Has defined input schema
  - Has defined output schema
  - Uses role-specific prompt
  - Returns structured JSON
  - Tracks latency and success rate
  - Falls back gracefully on failure

Key Design:
  - Agents run sequentially (Technical → News → Market → Risk → Validator)
    so each agent can see previous agents' outputs
  - One local model (gemma4) performs all 5 roles
  - AI OFF mode skips all agents entirely
  - AI LITE mode runs only Technical + Final Validator (2 of 5)
  - AI STANDARD mode runs all 5 agents
"""
import logging
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .llm_router import (
    LLMRouter, AIConfig, AIMode, AgentRole,
    AIRouterResponse, ROLE_PROMPTS,
)

logger = logging.getLogger(__name__)


# ── Agent Output Schemas ──────────────────────────────────────────────

AGENT_OUTPUT_SCHEMAS = {
    AgentRole.TECHNICAL_ANALYST: {
        'type': 'object',
        'required': ['direction', 'confidence', 'recommendation'],
        'properties': {
            'direction': {'type': 'string', 'enum': ['bullish', 'bearish', 'neutral']},
            'confidence': {'type': 'number'},
            'key_levels': {'type': 'object'},
            'patterns': {'type': 'array'},
            'trend_quality': {'type': 'string'},
            'recommendation': {'type': 'string'},
        },
    },
    AgentRole.NEWS_ANALYST: {
        'type': 'object',
        'required': ['sentiment', 'impact', 'recommendation'],
        'properties': {
            'sentiment': {'type': 'string', 'enum': ['positive', 'negative', 'neutral']},
            'impact': {'type': 'string', 'enum': ['high', 'medium', 'low']},
            'key_events': {'type': 'array'},
            'affected_assets': {'type': 'array'},
            'time_horizon': {'type': 'string'},
            'recommendation': {'type': 'string'},
        },
    },
    AgentRole.MARKET_ANALYST: {
        'type': 'object',
        'required': ['regime_assessment', 'risk_level', 'recommendation'],
        'properties': {
            'regime_assessment': {'type': 'string'},
            'key_drivers': {'type': 'array'},
            'risk_level': {'type': 'string', 'enum': ['low', 'medium', 'high']},
            'volatility_outlook': {'type': 'string'},
            'opportunity': {'type': 'string'},
            'recommendation': {'type': 'string'},
        },
    },
    AgentRole.RISK_ANALYST: {
        'type': 'object',
        'required': ['risk_level', 'key_risks', 'recommendation'],
        'properties': {
            'risk_level': {'type': 'string', 'enum': ['low', 'medium', 'high', 'extreme']},
            'key_risks': {'type': 'array'},
            'position_sizing': {'type': 'string'},
            'max_drawdown_expected': {'type': 'string'},
            'portfolio_impact': {'type': 'string'},
            'recommendation': {'type': 'string'},
        },
    },
    AgentRole.FINAL_VALIDATOR: {
        'type': 'object',
        'required': ['verdict', 'adjusted_confidence', 'reasons'],
        'properties': {
            'verdict': {'type': 'string', 'enum': ['validate', 'reject', 'modify']},
            'adjusted_confidence': {'type': 'number'},
            'reasons': {'type': 'array'},
            'risks': {'type': 'array'},
            'modification': {'type': 'string'},
        },
    },
}


# ── Agent Context Builder ─────────────────────────────────────────────

class AgentContextBuilder:
    """Builds role-specific context from the signal context.

    Each agent receives only the data relevant to its role.
    This prevents information overload and keeps prompts focused.
    """

    @staticmethod
    def build_technical_context(signal_ctx: Dict) -> Dict:
        """Context for Technical Analyst."""
        return {
            'symbol': signal_ctx.get('symbol', 'BTC'),
            'current_price': signal_ctx.get('current_price', 0),
            'technical_score': signal_ctx.get('technical_score', 50),
            'rsi': signal_ctx.get('rsi', 50),
            'macd_signal': signal_ctx.get('macd_signal', 'neutral'),
            'trend': signal_ctx.get('trend', 'neutral'),
            'support': signal_ctx.get('support', 0),
            'resistance': signal_ctx.get('resistance', 0),
            'volume_signal': signal_ctx.get('volume_signal', 'normal'),
            'volatility': signal_ctx.get('volatility', 2),
            'vwap_signal': signal_ctx.get('vwap_signal', 'neutral'),
            'ichimoku_signal': signal_ctx.get('ichimoku_signal', 'neutral'),
            'stochastic_k': signal_ctx.get('stochastic_k', 50),
            'stochastic_d': signal_ctx.get('stochastic_d', 50),
        }

    @staticmethod
    def build_news_context(signal_ctx: Dict) -> Dict:
        """Context for News Analyst."""
        return {
            'symbol': signal_ctx.get('symbol', 'BTC'),
            'news_score': signal_ctx.get('news_score', 50),
            'fear_greed_index': signal_ctx.get('fear_greed_index', 50),
            'social_sentiment': signal_ctx.get('social_sentiment', 50),
            'recent_headlines': signal_ctx.get('recent_headlines', []),
            'news_sentiment_trend': signal_ctx.get('news_sentiment_trend', 'neutral'),
            'geo_political_risk': signal_ctx.get('geo_political_risk', 'low'),
        }

    @staticmethod
    def build_market_context(signal_ctx: Dict) -> Dict:
        """Context for Market Analyst."""
        return {
            'symbol': signal_ctx.get('symbol', 'BTC'),
            'regime': signal_ctx.get('regime', 'sideways'),
            'regime_strength': signal_ctx.get('regime_strength', 0.5),
            'macro_score': signal_ctx.get('macro_score', 50),
            'derivatives_score': signal_ctx.get('derivatives_score', 50),
            'funding_rate': signal_ctx.get('funding_rate', 0),
            'open_interest_change': signal_ctx.get('open_interest_change', 0),
            'btc_dominance': signal_ctx.get('btc_dominance', 50),
            'market_structure': signal_ctx.get('market_structure', 'neutral'),
        }

    @staticmethod
    def build_risk_context(signal_ctx: Dict) -> Dict:
        """Context for Risk Analyst."""
        return {
            'symbol': signal_ctx.get('symbol', 'BTC'),
            'quant_composite_score': signal_ctx.get('quant_composite_score', 50),
            'direction': signal_ctx.get('direction', 'hold'),
            'confidence': signal_ctx.get('confidence', 50),
            'risk_score': signal_ctx.get('risk_score', 50),
            'portfolio_exposure': signal_ctx.get('portfolio_exposure', 0),
            'current_drawdown': signal_ctx.get('current_drawdown', 0),
            'max_drawdown_limit': signal_ctx.get('max_drawdown_limit', 15),
            'active_positions': signal_ctx.get('active_positions', 0),
            'volatility': signal_ctx.get('volatility', 2),
        }

    @staticmethod
    def build_validator_context(
        signal_ctx: Dict,
        agent_outputs: Dict[AgentRole, Dict],
    ) -> Dict:
        """Context for Final Validator — includes all agent outputs."""
        return {
            'symbol': signal_ctx.get('symbol', 'BTC'),
            'quant_composite_score': signal_ctx.get('quant_composite_score', 50),
            'direction': signal_ctx.get('direction', 'hold'),
            'confidence': signal_ctx.get('confidence', 50),
            'regime': signal_ctx.get('regime', 'sideways'),
            'agent_analyses': {
                role.value: output
                for role, output in agent_outputs.items()
            },
        }


# ── Agent Run Result ──────────────────────────────────────────────────

@dataclass
class AgentRunResult:
    """Result from a single agent run."""
    role: AgentRole
    success: bool
    output: Dict
    latency_ms: int = 0
    model: str = ''
    error: str = ''
    validation_errors: List[str] = field(default_factory=list)

    @property
    def direction(self) -> str:
        """Extract direction/bias from agent output."""
        if not self.output:
            return 'neutral'
        if self.role == AgentRole.TECHNICAL_ANALYST:
            return self.output.get('direction', 'neutral')
        elif self.role == AgentRole.NEWS_ANALYST:
            return self.output.get('sentiment', 'neutral')
        elif self.role == AgentRole.RISK_ANALYST:
            return self.output.get('risk_level', 'medium')
        return 'neutral'

    @property
    def recommendation(self) -> str:
        """Extract recommendation from agent output."""
        return self.output.get('recommendation', '')


# ── Ensemble Result ───────────────────────────────────────────────────

@dataclass
class EnsembleResult:
    """Result from the full agent ensemble run."""
    symbol: str
    verdict: str  # validate, reject, modify
    adjusted_confidence: int
    quant_composite_score: float
    agent_results: Dict[str, AgentRunResult] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    total_latency_ms: int = 0
    agents_succeeded: int = 0
    agents_failed: int = 0
    ai_mode: str = 'off'
    model: str = ''
    generated_at: str = ''

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """Serialize for API response."""
        return {
            'symbol': self.symbol,
            'verdict': self.verdict,
            'adjusted_confidence': self.adjusted_confidence,
            'quant_composite_score': self.quant_composite_score,
            'agent_analyses': {
                name: {
                    'role': result.role.value,
                    'success': result.success,
                    'output': result.output,
                    'latency_ms': result.latency_ms,
                    'direction': result.direction,
                    'recommendation': result.recommendation,
                }
                for name, result in self.agent_results.items()
            },
            'reasons': self.reasons,
            'risks': self.risks,
            'total_latency_ms': self.total_latency_ms,
            'agents_succeeded': self.agents_succeeded,
            'agents_failed': self.agents_failed,
            'ai_mode': self.ai_mode,
            'model': self.model,
            'generated_at': self.generated_at,
        }


# ── Agent Ensemble ────────────────────────────────────────────────────

# Agent execution order — each agent can see previous agents' outputs
AGENT_EXECUTION_ORDER = [
    AgentRole.TECHNICAL_ANALYST,
    AgentRole.NEWS_ANALYST,
    AgentRole.MARKET_ANALYST,
    AgentRole.RISK_ANALYST,
    AgentRole.FINAL_VALIDATOR,
]

# AI LITE mode only runs these agents (2 of 5)
LITE_AGENTS = [
    AgentRole.TECHNICAL_ANALYST,
    AgentRole.FINAL_VALIDATOR,
]

# AI STANDARD mode runs all 5
STANDARD_AGENTS = AGENT_EXECUTION_ORDER


class AgentEnsemble:
    """Orchestrates 5 role-based agents for multi-perspective signal validation.

    Usage:
        ensemble = AgentEnsemble(config=AIConfig(mode=AIMode.STANDARD))
        result = await ensemble.run(
            signal_ctx={
                'symbol': 'BTC',
                'quant_composite_score': 68,
                'regime': 'bull_trend',
                'technical_score': 72,
                ...
            }
        )
        if result.verdict == 'validate':
            # Signal is validated by all agents
        elif result.verdict == 'reject':
            # Signal was rejected by ensemble
    """

    def __init__(self, config: AIConfig = None):
        self.config = config or AIConfig()
        self.router = LLMRouter(self.config)
        self.context_builder = AgentContextBuilder()

    async def initialize(self):
        """Initialize the LLM router."""
        await self.router.initialize()

    async def run(self, signal_ctx: Dict) -> EnsembleResult:
        """Run the full agent ensemble on a signal context.

        Args:
            signal_ctx: Signal context with all data needed by agents.
                       Must include: symbol, quant_composite_score, regime,
                       technical_score, etc.

        Returns:
            EnsembleResult with all agent outputs and final verdict.
        """
        start_time = time.time()
        symbol = signal_ctx.get('symbol', 'BTC')

        # AI OFF mode — skip all agents, return quant-only
        if self.config.mode == AIMode.OFF:
            return EnsembleResult(
                symbol=symbol,
                verdict='quant_only',
                adjusted_confidence=signal_ctx.get('confidence', 50),
                quant_composite_score=signal_ctx.get('quant_composite_score', 50),
                ai_mode='off',
                generated_at=datetime.now().isoformat(),
            )

        # Determine which agents to run based on AI mode
        if self.config.mode == AIMode.LITE:
            agents_to_run = LITE_AGENTS
        else:
            agents_to_run = STANDARD_AGENTS

        # Run agents sequentially (each sees previous outputs)
        agent_results: Dict[str, AgentRunResult] = {}
        agent_outputs_for_validator: Dict[AgentRole, Dict] = {}
        succeeded = 0
        failed = 0

        for role in agents_to_run:
            result = await self._run_agent(role, signal_ctx, agent_outputs_for_validator)
            agent_results[role.value] = result

            if result.success:
                succeeded += 1
                agent_outputs_for_validator[role] = result.output
            else:
                failed += 1
                # Use empty/default output for failed agents
                agent_outputs_for_validator[role] = {
                    'error': result.error,
                    'direction': 'neutral',
                }

        # Extract final verdict from the Final Validator
        validator_result = agent_results.get(AgentRole.FINAL_VALIDATOR.value)
        if validator_result and validator_result.success:
            verdict = validator_result.output.get('verdict', 'validate')
            adjusted_confidence = validator_result.output.get(
                'adjusted_confidence', signal_ctx.get('confidence', 50)
            )
            reasons = validator_result.output.get('reasons', [])
            risks = validator_result.output.get('risks', [])
        else:
            # Fallback: use quant composite without AI validation
            verdict = 'quant_only'
            adjusted_confidence = signal_ctx.get('confidence', 50)
            reasons = ['AI validation unavailable — using quant composite']
            risks = []

        total_latency = int((time.time() - start_time) * 1000)

        result = EnsembleResult(
            symbol=symbol,
            verdict=verdict,
            adjusted_confidence=adjusted_confidence,
            quant_composite_score=signal_ctx.get('quant_composite_score', 50),
            agent_results=agent_results,
            reasons=reasons,
            risks=risks,
            total_latency_ms=total_latency,
            agents_succeeded=succeeded,
            agents_failed=failed,
            ai_mode=self.config.mode.value,
            model=self.config.model,
        )

        logger.info(
            f"Ensemble complete: {symbol} | Verdict: {verdict} | "
            f"Confidence: {adjusted_confidence}% | "
            f"Agents: {succeeded}/{succeeded + failed} | "
            f"Latency: {total_latency}ms"
        )

        return result

    async def _run_agent(
        self,
        role: AgentRole,
        signal_ctx: Dict,
        previous_outputs: Dict[AgentRole, Dict],
    ) -> AgentRunResult:
        """Run a single agent with role-specific context."""
        # Build context for this role
        context = self._build_context_for_role(role, signal_ctx, previous_outputs)

        # Get schema for validation
        schema = AGENT_OUTPUT_SCHEMAS.get(role)

        try:
            response = await self.router.analyze(
                context=context,
                role=role,
                schema=schema,
            )

            return AgentRunResult(
                role=role,
                success=response.success,
                output=response.parsed_output or {},
                latency_ms=response.latency_ms,
                model=response.model,
                error=response.error,
                validation_errors=response.validation_errors or [],
            )

        except Exception as e:
            logger.error(f"Agent {role.value} failed: {e}")
            return AgentRunResult(
                role=role,
                success=False,
                output={},
                error=str(e),
            )

    def _build_context_for_role(
        self,
        role: AgentRole,
        signal_ctx: Dict,
        previous_outputs: Dict[AgentRole, Dict],
    ) -> Dict:
        """Build context for a specific agent role."""
        if role == AgentRole.TECHNICAL_ANALYST:
            return self.context_builder.build_technical_context(signal_ctx)

        elif role == AgentRole.NEWS_ANALYST:
            return self.context_builder.build_news_context(signal_ctx)

        elif role == AgentRole.MARKET_ANALYST:
            return self.context_builder.build_market_context(signal_ctx)

        elif role == AgentRole.RISK_ANALYST:
            return self.context_builder.build_risk_context(signal_ctx)

        elif role == AgentRole.FINAL_VALIDATOR:
            return self.context_builder.build_validator_context(
                signal_ctx, previous_outputs
            )

        return signal_ctx

    def get_agent_performance(self) -> Dict:
        """Get performance metrics for all agents."""
        # This would typically read from the database
        # For now, return static config info
        return {
            'mode': self.config.mode.value,
            'model': self.config.model,
            'agents': {
                role.value: {
                    'schema': AGENT_OUTPUT_SCHEMAS.get(role, {}),
                    'prompt_preview': ROLE_PROMPTS.get(role, '')[:100] + '...',
                }
                for role in AgentRole
            },
        }
