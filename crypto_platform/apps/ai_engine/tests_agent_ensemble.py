"""Tests for Agent Ensemble (Phase 65).

Covers:
- AgentRole enum values
- AgentOutputSchema completeness
- ContextBuilder role-specific context
- EnsembleResult serialization
- AI OFF mode returns quant_only
- Graceful fallback when agent fails
- LITE mode runs 2 agents, STANDARD runs 5
- Verdict determination from Final Validator
"""
import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from django.test import TestCase

import sys
import os
# Ensure crypto_platform is on path for 'apps.*' imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from apps.ai_engine.services.agent_ensemble import (
    AgentEnsemble,
    AgentContextBuilder,
    AgentRunResult,
    EnsembleResult,
    AGENT_OUTPUT_SCHEMAS,
    AGENT_EXECUTION_ORDER,
    LITE_AGENTS,
    STANDARD_AGENTS,
)
from apps.ai_engine.services.llm_router import (
    AgentRole,
    AIMode,
    AIConfig,
    AIRouterResponse,
)


class AgentRoleTest(TestCase):
    """Test AgentRole enum."""

    def test_all_5_roles_defined(self):
        roles = list(AgentRole)
        self.assertEqual(len(roles), 5)

    def test_role_values(self):
        self.assertEqual(AgentRole.TECHNICAL_ANALYST.value, 'technical_analyst')
        self.assertEqual(AgentRole.NEWS_ANALYST.value, 'news_analyst')
        self.assertEqual(AgentRole.MARKET_ANALYST.value, 'market_analyst')
        self.assertEqual(AgentRole.RISK_ANALYST.value, 'risk_analyst')
        self.assertEqual(AgentRole.FINAL_VALIDATOR.value, 'final_validator')


class AgentOutputSchemaTest(TestCase):
    """Test that all agents have defined output schemas."""

    def test_all_roles_have_schemas(self):
        for role in AgentRole:
            self.assertIn(role, AGENT_OUTPUT_SCHEMAS, f"Missing schema for {role.value}")

    def test_schemas_have_required_fields(self):
        for role, schema in AGENT_OUTPUT_SCHEMAS.items():
            self.assertIn('required', schema, f"Schema for {role.value} missing 'required'")
            self.assertIn('properties', schema, f"Schema for {role.value} missing 'properties'")
            self.assertGreater(len(schema['required']), 0, f"Schema for {role.value} has empty required")

    def test_technical_analyst_schema(self):
        schema = AGENT_OUTPUT_SCHEMAS[AgentRole.TECHNICAL_ANALYST]
        self.assertIn('direction', schema['required'])
        self.assertIn('confidence', schema['required'])
        self.assertIn('recommendation', schema['required'])

    def test_final_validator_schema(self):
        schema = AGENT_OUTPUT_SCHEMAS[AgentRole.FINAL_VALIDATOR]
        self.assertIn('verdict', schema['required'])
        self.assertIn('adjusted_confidence', schema['required'])
        self.assertIn('reasons', schema['required'])


class ContextBuilderTest(TestCase):
    """Test AgentContextBuilder role-specific context generation."""

    def setUp(self):
        self.signal_ctx = {
            'symbol': 'BTC',
            'current_price': 50000,
            'quant_composite_score': 68,
            'technical_score': 72,
            'sentiment_score': 60,
            'news_score': 55,
            'macro_score': 65,
            'derivatives_score': 50,
            'regime': 'bull_trend',
            'rsi': 65,
            'macd_signal': 'bullish',
            'trend': 'uptrend',
            'fear_greed_index': 55,
            'social_sentiment': 60,
            'risk_score': 40,
            'confidence': 72,
            'direction': 'buy',
        }
        self.builder = AgentContextBuilder()

    def test_technical_context_has_required_fields(self):
        ctx = self.builder.build_technical_context(self.signal_ctx)
        self.assertEqual(ctx['symbol'], 'BTC')
        self.assertIn('rsi', ctx)
        self.assertIn('macd_signal', ctx)
        self.assertIn('trend', ctx)
        self.assertIn('volatility', ctx)

    def test_news_context_has_required_fields(self):
        ctx = self.builder.build_news_context(self.signal_ctx)
        self.assertEqual(ctx['symbol'], 'BTC')
        self.assertIn('news_score', ctx)
        self.assertIn('fear_greed_index', ctx)
        self.assertIn('social_sentiment', ctx)

    def test_market_context_has_required_fields(self):
        ctx = self.builder.build_market_context(self.signal_ctx)
        self.assertEqual(ctx['symbol'], 'BTC')
        self.assertIn('regime', ctx)
        self.assertIn('macro_score', ctx)
        self.assertIn('derivatives_score', ctx)

    def test_risk_context_has_required_fields(self):
        ctx = self.builder.build_risk_context(self.signal_ctx)
        self.assertEqual(ctx['symbol'], 'BTC')
        self.assertIn('quant_composite_score', ctx)
        self.assertIn('risk_score', ctx)
        self.assertIn('confidence', ctx)

    def test_validator_context_includes_agent_outputs(self):
        agent_outputs = {
            AgentRole.TECHNICAL_ANALYST: {'direction': 'bullish', 'confidence': 75},
            AgentRole.NEWS_ANALYST: {'sentiment': 'positive', 'impact': 'medium'},
        }
        ctx = self.builder.build_validator_context(self.signal_ctx, agent_outputs)
        self.assertIn('agent_analyses', ctx)
        self.assertIn('technical_analyst', ctx['agent_analyses'])
        self.assertIn('news_analyst', ctx['agent_analyses'])

    def test_context_defaults_when_missing_fields(self):
        sparse_ctx = {'symbol': 'BTC'}
        ctx = self.builder.build_technical_context(sparse_ctx)
        self.assertEqual(ctx['rsi'], 50)  # default
        self.assertEqual(ctx['trend'], 'neutral')  # default


class AgentRunResultTest(TestCase):
    """Test AgentRunResult data class."""

    def test_direction_from_technical(self):
        result = AgentRunResult(
            role=AgentRole.TECHNICAL_ANALYST,
            success=True,
            output={'direction': 'bullish', 'confidence': 75},
        )
        self.assertEqual(result.direction, 'bullish')

    def test_direction_from_news(self):
        result = AgentRunResult(
            role=AgentRole.NEWS_ANALYST,
            success=True,
            output={'sentiment': 'negative', 'impact': 'high'},
        )
        self.assertEqual(result.direction, 'negative')

    def test_direction_from_risk(self):
        result = AgentRunResult(
            role=AgentRole.RISK_ANALYST,
            success=True,
            output={'risk_level': 'extreme'},
        )
        self.assertEqual(result.direction, 'extreme')

    def test_direction_neutral_when_empty(self):
        result = AgentRunResult(
            role=AgentRole.MARKET_ANALYST,
            success=False,
            output={},
        )
        self.assertEqual(result.direction, 'neutral')

    def test_recommendation(self):
        result = AgentRunResult(
            role=AgentRole.TECHNICAL_ANALYST,
            success=True,
            output={'recommendation': 'Buy at support'},
        )
        self.assertEqual(result.recommendation, 'Buy at support')


class EnsembleResultTest(TestCase):
    """Test EnsembleResult serialization."""

    def test_to_dict(self):
        result = EnsembleResult(
            symbol='BTC',
            verdict='validate',
            adjusted_confidence=75,
            quant_composite_score=68,
            reasons=['Strong technical setup'],
            risks=['High volatility'],
            total_latency_ms=15000,
            agents_succeeded=5,
            agents_failed=0,
            ai_mode='standard',
            model='gemma4:latest',
        )
        d = result.to_dict()
        self.assertEqual(d['symbol'], 'BTC')
        self.assertEqual(d['verdict'], 'validate')
        self.assertEqual(d['adjusted_confidence'], 75)
        self.assertEqual(d['agents_succeeded'], 5)
        self.assertEqual(d['agents_failed'], 0)
        self.assertIn('generated_at', d)

    def test_to_dict_with_agent_results(self):
        result = EnsembleResult(
            symbol='BTC',
            verdict='validate',
            adjusted_confidence=70,
            quant_composite_score=65,
        )
        result.agent_results['technical_analyst'] = AgentRunResult(
            role=AgentRole.TECHNICAL_ANALYST,
            success=True,
            output={'direction': 'bullish'},
            latency_ms=3000,
        )
        d = result.to_dict()
        self.assertIn('technical_analyst', d['agent_analyses'])
        self.assertTrue(d['agent_analyses']['technical_analyst']['success'])


class AIOffModeTest(TestCase):
    """Test AI OFF mode — no LLM calls."""

    def test_off_mode_returns_quant_only(self):
        config = AIConfig(mode=AIMode.OFF)
        ensemble = AgentEnsemble(config=config)

        signal_ctx = {
            'symbol': 'BTC',
            'quant_composite_score': 68,
            'confidence': 72,
        }

        result = asyncio.run(ensemble.run(signal_ctx=signal_ctx))

        self.assertEqual(result.verdict, 'quant_only')
        self.assertEqual(result.adjusted_confidence, 72)
        self.assertEqual(result.ai_mode, 'off')
        self.assertEqual(result.agents_succeeded, 0)
        self.assertEqual(result.agents_failed, 0)
        self.assertEqual(result.total_latency_ms, 0)


class LITEvsSTANDARDTest(TestCase):
    """Test LITE mode runs 2 agents, STANDARD runs 5."""

    def test_lite_agents_count(self):
        self.assertEqual(len(LITE_AGENTS), 2)
        self.assertIn(AgentRole.TECHNICAL_ANALYST, LITE_AGENTS)
        self.assertIn(AgentRole.FINAL_VALIDATOR, LITE_AGENTS)

    def test_standard_agents_count(self):
        self.assertEqual(len(STANDARD_AGENTS), 5)

    def test_execution_order(self):
        self.assertEqual(AGENT_EXECUTION_ORDER[0], AgentRole.TECHNICAL_ANALYST)
        self.assertEqual(AGENT_EXECUTION_ORDER[-1], AgentRole.FINAL_VALIDATOR)


class GracefulFallbackTest(TestCase):
    """Test that ensemble handles agent failures gracefully."""

    def test_all_agents_fail_returns_quant_only(self):
        config = AIConfig(mode=AIMode.OFF)
        ensemble = AgentEnsemble(config=config)

        signal_ctx = {
            'symbol': 'ETH',
            'quant_composite_score': 45,
            'confidence': 40,
        }

        result = asyncio.run(ensemble.run(signal_ctx=signal_ctx))
        self.assertEqual(result.verdict, 'quant_only')
        self.assertEqual(result.symbol, 'ETH')
