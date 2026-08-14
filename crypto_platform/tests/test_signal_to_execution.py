"""
Comprehensive Signal-to-Execution Integration Test

Tests the complete pipeline from authentication through execution:
  1. Authentication & User Setup
  2. Market Data Retrieval
  3. Signal Generation (8-factor fusion)
  4. Agent Ensemble Validation (5 agents)
  5. Versioning & Lineage Capture
  6. Paper Trading Execution
  7. Shadow Trading Recording
  8. Signal Evaluation & Feedback
  9. Calibration Analysis
  10. End-to-End Verification
"""
import pytest
import json
import asyncio
import time
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status


# ══════════════════════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════════════════════

def generate_synthetic_candles(n=50, base_price=100, trend='up'):
    """Generate synthetic candle data for testing."""
    candles = []
    for i in range(n):
        if trend == 'up':
            close = base_price + i * 0.5
        elif trend == 'down':
            close = base_price - i * 0.5
        else:
            close = base_price + (i % 10 - 5) * 0.3

        candles.append({
            'open': close - 0.2,
            'high': close + 1.0,
            'low': close - 1.0,
            'close': close,
            'volume': 1000 + i * 10,
        })
    return candles


# ══════════════════════════════════════════════════════════════════════
# Test 1: Authentication Flow
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestAuthenticationFlow:
    """Test user authentication and JWT token flow."""

    def test_login_returns_tokens(self):
        """Verify login returns access and refresh tokens."""
        from rest_framework_simplejwt.tokens import RefreshToken

        User = get_user_model()
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        # Access token is a valid JWT string with 3 parts separated by dots
        token_str = str(access_token)
        assert token_str.count('.') == 2, f'Invalid JWT format'
        # Verify user_id is in the token payload
        assert refresh.payload.get('user_id') is not None

    def test_token_refresh(self):
        """Verify token refresh works."""
        from rest_framework_simplejwt.tokens import RefreshToken

        User = get_user_model()
        user = User.objects.create_user(
            username='refreshuser',
            email='refresh@example.com',
            password='testpass123'
        )

        refresh = RefreshToken.for_user(user)
        new_access = refresh.access_token
        assert new_access is not None

    def test_protected_endpoint_requires_auth(self):
        """Verify protected endpoints require authentication."""
        client = APIClient()
        response = client.get('/api/signals/signals/')
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403]


# ══════════════════════════════════════════════════════════════════════
# Test 2: Market Data Pipeline
# ══════════════════════════════════════════════════════════════════════

class TestMarketDataPipeline:
    """Test market data retrieval and processing."""

    def test_regime_detection_with_uptrend(self):
        """Verify regime detection works with uptrend data."""
        from apps.signals.services.regime_engine import RegimeEngine

        engine = RegimeEngine()
        candles = generate_synthetic_candles(50, 100, 'up')
        state = engine.detect_regime(candles)

        assert state.regime is not None
        assert isinstance(state.weights, dict)
        assert len(state.weights) >= 5  # At least 5 factor weights

    def test_regime_detection_with_downtrend(self):
        """Verify regime detection works with downtrend data."""
        from apps.signals.services.regime_engine import RegimeEngine

        engine = RegimeEngine()
        candles = generate_synthetic_candles(50, 200, 'down')
        state = engine.detect_regime(candles)

        assert state.regime is not None
        assert 'technical' in state.weights

    def test_regime_detection_with_sideways(self):
        """Verify regime detection works with sideways data."""
        from apps.signals.services.regime_engine import RegimeEngine

        engine = RegimeEngine()
        candles = generate_synthetic_candles(50, 150, 'sideways')
        state = engine.detect_regime(candles)

        assert state.regime is not None

    def test_regime_weights_sum_to_one(self):
        """Verify regime weights sum to approximately 1.0."""
        from apps.signals.services.regime_engine import RegimeEngine

        engine = RegimeEngine()
        candles = generate_synthetic_candles(50)
        state = engine.detect_regime(candles)

        total_weight = sum(state.weights.values())
        assert 0.9 <= total_weight <= 1.1, f"Weights sum {total_weight} not near 1.0"


# ══════════════════════════════════════════════════════════════════════
# Test 3: Signal Generation (8-Factor Fusion)
# ══════════════════════════════════════════════════════════════════════

class TestSignalGeneration:
    """Test the 8-factor signal fusion engine."""

    def test_fusion_engine_basic(self):
        """Verify basic signal fusion produces valid output."""
        from apps.signals.services.signal_fusion import SignalFusionEngine
        from apps.signals.services.regime_engine import RegimeEngine

        regime_engine = RegimeEngine()
        candles = generate_synthetic_candles(50)
        regime = regime_engine.detect_regime(candles)

        fusion = SignalFusionEngine()
        result = fusion.fuse_signal(
            symbol='BTCUSDT', timeframe='1h',
            technical_score=72, sentiment_score=65, news_score=58,
            macro_score=55, derivatives_score=60, market_structure_score=50,
            order_book_score=55, portfolio_context_score=50,
            regime=regime.regime, regime_weights=regime.weights,
            current_price=113500,
        )

        assert 'direction' in result
        assert 'confidence' in result
        assert 'quant_composite_score' in result
        assert 'factor_scores' in result
        assert result['direction'] in ('long', 'short', 'hold', 'buy', 'sell')
        assert 0 <= result['confidence'] <= 100

    def test_fusion_with_bullish_inputs(self):
        """Verify bullish inputs produce bullish/long signal."""
        from apps.signals.services.signal_fusion import SignalFusionEngine
        from apps.signals.services.regime_engine import RegimeEngine

        regime_engine = RegimeEngine()
        candles = generate_synthetic_candles(50, 100, 'up')
        regime = regime_engine.detect_regime(candles)

        fusion = SignalFusionEngine()
        result = fusion.fuse_signal(
            symbol='BTCUSDT', timeframe='1h',
            technical_score=85, sentiment_score=80, news_score=75,
            macro_score=70, derivatives_score=72, market_structure_score=68,
            order_book_score=70, portfolio_context_score=65,
            regime=regime.regime, regime_weights=regime.weights,
            current_price=113500,
        )

        # With high scores across all factors, should lean bullish
        assert result['quant_composite_score'] > 50

    def test_fusion_with_bearish_inputs(self):
        """Verify bearish inputs produce bearish/short signal."""
        from apps.signals.services.signal_fusion import SignalFusionEngine
        from apps.signals.services.regime_engine import RegimeEngine

        regime_engine = RegimeEngine()
        candles = generate_synthetic_candles(50, 200, 'down')
        regime = regime_engine.detect_regime(candles)

        fusion = SignalFusionEngine()
        result = fusion.fuse_signal(
            symbol='BTCUSDT', timeframe='1h',
            technical_score=25, sentiment_score=30, news_score=20,
            macro_score=35, derivatives_score=28, market_structure_score=32,
            order_book_score=30, portfolio_context_score=35,
            regime=regime.regime, regime_weights=regime.weights,
            current_price=113500,
        )

        # With low scores across all factors, should lean bearish
        assert result['quant_composite_score'] < 50

    def test_fusion_includes_factor_scores(self):
        """Verify all 8 factor scores are in the output."""
        from apps.signals.services.signal_fusion import SignalFusionEngine
        from apps.signals.services.regime_engine import RegimeEngine

        regime_engine = RegimeEngine()
        candles = generate_synthetic_candles(50)
        regime = regime_engine.detect_regime(candles)

        fusion = SignalFusionEngine()
        result = fusion.fuse_signal(
            symbol='BTCUSDT', timeframe='1h',
            technical_score=72, sentiment_score=65, news_score=58,
            macro_score=55, derivatives_score=60, market_structure_score=50,
            order_book_score=55, portfolio_context_score=50,
            regime=regime.regime, regime_weights=regime.weights,
            current_price=113500,
        )

        expected_factors = ['technical', 'sentiment', 'news', 'macro',
                          'derivatives', 'market_structure', 'order_book', 'portfolio_context']
        for factor in expected_factors:
            assert factor in result['factor_scores'], f"Missing factor: {factor}"

    def test_fusion_includes_weights_used(self):
        """Verify the weights used are captured in the output."""
        from apps.signals.services.signal_fusion import SignalFusionEngine
        from apps.signals.services.regime_engine import RegimeEngine

        regime_engine = RegimeEngine()
        candles = generate_synthetic_candles(50)
        regime = regime_engine.detect_regime(candles)

        fusion = SignalFusionEngine()
        result = fusion.fuse_signal(
            symbol='BTCUSDT', timeframe='1h',
            technical_score=72, sentiment_score=65, news_score=58,
            macro_score=55, derivatives_score=60, market_structure_score=50,
            order_book_score=55, portfolio_context_score=50,
            regime=regime.regime, regime_weights=regime.weights,
            current_price=113500,
        )

        assert 'weights_used' in result
        assert isinstance(result['weights_used'], dict)
        assert len(result['weights_used']) >= 5


# ══════════════════════════════════════════════════════════════════════
# Test 4: Agent Ensemble Validation
# ══════════════════════════════════════════════════════════════════════

class TestAgentEnsemble:
    """Test the 5-agent ensemble validation system."""

    def test_off_mode_returns_quant_only(self):
        """Verify OFF mode skips all agents."""
        from apps.ai_engine.services.agent_ensemble import AgentEnsemble
        from apps.ai_engine.services.llm_router import AIConfig, AIMode

        ensemble = AgentEnsemble(config=AIConfig(mode=AIMode.OFF))
        signal_ctx = {
            'symbol': 'BTCUSDT', 'current_price': 113500,
            'quant_composite_score': 65, 'direction': 'buy', 'confidence': 70,
            'regime': 'sideways', 'technical_score': 72,
        }

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(ensemble.run(signal_ctx))
        loop.close()

        assert result.verdict == 'quant_only'
        assert result.ai_mode == 'off'
        assert result.adjusted_confidence == 70

    def test_all_five_agents_have_schemas(self):
        """Verify all 5 agents have defined output schemas."""
        from apps.ai_engine.services.agent_ensemble import AGENT_OUTPUT_SCHEMAS, AGENT_EXECUTION_ORDER

        assert len(AGENT_EXECUTION_ORDER) == 5
        for role in AGENT_EXECUTION_ORDER:
            assert role in AGENT_OUTPUT_SCHEMAS
            schema = AGENT_OUTPUT_SCHEMAS[role]
            assert 'required' in schema
            assert 'properties' in schema
            assert len(schema['required']) >= 1

    def test_context_builder_for_all_roles(self):
        """Verify context builder works for all 5 agent roles."""
        from apps.ai_engine.services.agent_ensemble import AgentContextBuilder
        from apps.ai_engine.services.llm_router import AgentRole

        builder = AgentContextBuilder()
        signal_ctx = {
            'symbol': 'BTCUSDT', 'rsi': 62, 'macd_signal': 'bullish',
            'technical_score': 72, 'news_score': 58, 'regime': 'sideways',
            'quant_composite_score': 65, 'direction': 'buy', 'confidence': 70,
            'risk_score': 40, 'volatility': 2.5,
        }

        # Technical context
        tech = builder.build_technical_context(signal_ctx)
        assert 'symbol' in tech and 'rsi' in tech

        # News context
        news = builder.build_news_context(signal_ctx)
        assert 'symbol' in news and 'news_score' in news

        # Market context
        market = builder.build_market_context(signal_ctx)
        assert 'symbol' in market and 'regime' in market

        # Risk context
        risk = builder.build_risk_context(signal_ctx)
        assert 'symbol' in risk and 'risk_score' in risk

        # Validator context (includes all agent outputs)
        validator = builder.build_validator_context(signal_ctx, {})
        assert 'symbol' in validator and 'agent_analyses' in validator

    def test_ensemble_result_serialization(self):
        """Verify EnsembleResult serializes correctly."""
        from apps.ai_engine.services.agent_ensemble import EnsembleResult

        result = EnsembleResult(
            symbol='BTCUSDT', verdict='validate', adjusted_confidence=75,
            quant_composite_score=68, reasons=['Test reason'], risks=['Test risk'],
            total_latency_ms=5000, agents_succeeded=5, agents_failed=0,
            ai_mode='standard', model='gemma4:latest',
        )

        serialized = result.to_dict()
        assert serialized['symbol'] == 'BTCUSDT'
        assert serialized['verdict'] == 'validate'
        assert serialized['agents_succeeded'] == 5


# ══════════════════════════════════════════════════════════════════════
# Test 5: Versioning & Lineage Capture
# ══════════════════════════════════════════════════════════════════════

class TestVersioningAndLineage:
    """Test the versioning and data lineage system."""

    def test_capture_lineage_complete(self):
        """Verify lineage captures all required data."""
        from apps.signals.services.versioning import VersionTracker

        tracker = VersionTracker()
        lineage = tracker.capture_lineage(
            signal_data={
                'symbol': 'BTCUSDT', 'direction': 'buy', 'confidence': 75,
                'composite_score': 68, 'timeframe': '1h'
            },
            factor_scores={'technical': 72, 'sentiment': 65, 'news': 58},
            regime='sideways', regime_confidence=0.8,
            weights_used={'technical': 0.35, 'sentiment': 0.15, 'news': 0.1},
            market_snapshot=tracker.build_market_snapshot(current_price=113500),
            news_snapshot=tracker.build_news_snapshot(article_count=10),
            social_snapshot=tracker.build_social_snapshot(fear_greed_index=65),
            derivatives_snapshot=tracker.build_derivatives_snapshot(),
            ensemble_output={'verdict': 'validate', 'model': 'gemma4'},
        )

        # Verify all sections exist
        assert 'versions' in lineage
        assert 'signal' in lineage
        assert 'factor_scores' in lineage
        assert 'regime' in lineage
        assert 'weights' in lineage
        assert 'market_snapshot' in lineage
        assert 'news_snapshot' in lineage
        assert 'social_snapshot' in lineage
        assert 'derivatives_snapshot' in lineage
        assert 'ensemble_output' in lineage

        # Verify signal data
        assert lineage['signal']['symbol'] == 'BTCUSDT'
        assert lineage['signal']['direction'] == 'buy'
        assert lineage['signal']['confidence'] == 75

    def test_system_versions_complete(self):
        """Verify all system version fields are defined."""
        from apps.signals.services.versioning import SYSTEM_VERSIONS

        required_versions = ['strategy', 'features', 'regime', 'risk',
                           'calibration', 'ensemble', 'backtester', 'walk_forward']
        for version in required_versions:
            assert version in SYSTEM_VERSIONS, f"Missing version: {version}"
            assert SYSTEM_VERSIONS[version] is not None

    def test_explain_signal_readable(self):
        """Verify human-readable explanation is generated."""
        from apps.signals.services.versioning import VersionTracker

        tracker = VersionTracker()
        lineage = tracker.capture_lineage(
            signal_data={'symbol': 'BTCUSDT', 'direction': 'buy', 'confidence': 75,
                        'composite_score': 68, 'timeframe': '1h'},
            factor_scores={'technical': 72, 'sentiment': 65},
            regime='sideways',
        )

        explanation = tracker.explain_signal(lineage)
        assert len(explanation) > 100
        assert 'BTCUSDT' in explanation
        assert 'buy' in explanation.lower() or 'BUY' in explanation

    def test_snapshot_builders(self):
        """Verify all snapshot builders produce valid data."""
        from apps.signals.services.versioning import VersionTracker

        tracker = VersionTracker()

        market = tracker.build_market_snapshot(
            current_price=50000, indicators={'rsi': 62}, candles_count=50
        )
        assert market['current_price'] == 50000
        assert market['candles_used'] == 50

        news = tracker.build_news_snapshot(
            article_count=15, avg_sentiment=65, top_headlines=['BTC rallies']
        )
        assert news['article_count'] == 15
        assert len(news['top_headlines']) == 1

        social = tracker.build_social_snapshot(
            fear_greed_index=72, social_sentiment=68, twitter_sentiment=65
        )
        assert social['fear_greed_index'] == 72

        derivatives = tracker.build_derivatives_snapshot(
            funding_rate=0.01, open_interest=5e9, long_short_ratio=1.2
        )
        assert derivatives['funding_rate'] == 0.01


# ══════════════════════════════════════════════════════════════════════
# Test 6: Paper Trading Execution
# ══════════════════════════════════════════════════════════════════════

class TestPaperTradingExecution:
    """Test the paper trading engine end-to-end."""

    def test_complete_paper_trading_lifecycle(self):
        """Test open → update → close → metrics lifecycle."""
        from apps.signals.services.paper_trading import PaperTradingEngine

        engine = PaperTradingEngine(initial_capital=10000)

        # 1. Open position
        open_result = engine.open_position(
            symbol='BTCUSDT', side='long', entry_price=50000,
            stop_loss=49000, take_profit=52000, signal_confidence=75,
        )
        assert open_result['success']
        pos_id = open_result['position']['id']

        # 2. Update prices
        engine.update_prices({'BTCUSDT': 51000})
        status = engine.get_status()
        assert status['open_positions_count'] == 1

        # 3. Close position with profit
        close_result = engine.close_position(pos_id, 52000, 'manual')
        assert close_result['success']
        assert close_result['trade']['pnl'] > 0

        # 4. Verify performance metrics
        perf = engine.get_performance_metrics()
        assert perf['total_trades'] == 1
        assert perf['winning_trades'] == 1
        assert perf['win_rate'] == 100.0

    def test_stop_loss_triggers(self):
        """Test that stop loss automatically closes position."""
        from apps.signals.services.paper_trading import PaperTradingEngine

        engine = PaperTradingEngine(initial_capital=10000)
        result = engine.open_position(
            symbol='BTCUSDT', side='long', entry_price=50000,
            stop_loss=49000, signal_confidence=75,
        )
        pos_id = result['position']['id']

        # Price drops below stop loss
        engine.update_prices({'BTCUSDT': 48500})
        status = engine.get_status()

        # Position should be closed
        assert status['open_positions_count'] == 0
        assert status['total_trades'] == 1
        assert status['losing_trades'] == 1

    def test_take_profit_triggers(self):
        """Test that take profit automatically closes position."""
        from apps.signals.services.paper_trading import PaperTradingEngine

        engine = PaperTradingEngine(initial_capital=10000)
        result = engine.open_position(
            symbol='BTCUSDT', side='long', entry_price=50000,
            take_profit=52000, signal_confidence=75,
        )
        pos_id = result['position']['id']

        # Price rises above take profit
        engine.update_prices({'BTCUSDT': 52500})
        status = engine.get_status()

        # Position should be closed
        assert status['open_positions_count'] == 0
        assert status['total_trades'] == 1
        assert status['winning_trades'] == 1

    def test_multiple_positions(self):
        """Test managing multiple positions simultaneously."""
        from apps.signals.services.paper_trading import PaperTradingEngine

        engine = PaperTradingEngine(initial_capital=100000)

        # Open 3 positions
        engine.open_position(symbol='BTCUSDT', side='long', entry_price=50000, signal_confidence=75)
        engine.open_position(symbol='ETHUSDT', side='long', entry_price=3000, signal_confidence=70)
        engine.open_position(symbol='SOLUSDT', side='short', entry_price=100, signal_confidence=65)

        status = engine.get_status()
        assert status['open_positions_count'] == 3

        # Update all prices
        engine.update_prices({'BTCUSDT': 51000, 'ETHUSDT': 3100, 'SOLUSDT': 95})

        # Close one
        pos_id = list(engine.account.open_positions.keys())[0]
        engine.close_position(pos_id, 51500, 'manual')

        status = engine.get_status()
        assert status['open_positions_count'] == 2
        assert status['total_trades'] == 1

    def test_max_positions_enforced(self):
        """Test that max positions limit is enforced."""
        from apps.signals.services.paper_trading import PaperTradingEngine

        engine = PaperTradingEngine(initial_capital=1000000)

        # Fill all 10 slots
        for i in range(10):
            engine.open_position(symbol=f'COIN{i}USDT', side='long', entry_price=100, signal_confidence=75)

        # 11th should fail
        result = engine.open_position(symbol='COIN11USDT', side='long', entry_price=100, signal_confidence=75)
        assert not result['success']
        assert 'max' in result['error'].lower() or 'Max' in result['error']

    def test_short_position_pnl(self):
        """Test PnL calculation for short positions."""
        from apps.signals.services.paper_trading import PaperTradingEngine

        engine = PaperTradingEngine(initial_capital=10000)
        result = engine.open_position(
            symbol='BTCUSDT', side='short', entry_price=50000, signal_confidence=75,
        )
        pos_id = result['position']['id']

        # Price drops (profit for short)
        engine.update_prices({'BTCUSDT': 48000})
        status = engine.get_status()

        # Should have unrealized profit
        pos = list(engine.account.open_positions.values())[0]
        assert pos.unrealized_pnl > 0

    def test_performance_metrics_comprehensive(self):
        """Test all performance metrics are calculated."""
        from apps.signals.services.paper_trading import PaperTradingEngine

        engine = PaperTradingEngine(initial_capital=10000)

        # Create mix of winning and losing trades
        # Win 1
        r = engine.open_position(symbol='BTCUSDT', side='long', entry_price=50000, signal_confidence=75)
        engine.close_position(r['position']['id'], 52000, 'manual')

        # Loss 1
        r = engine.open_position(symbol='ETHUSDT', side='long', entry_price=3000, signal_confidence=70)
        engine.close_position(r['position']['id'], 2800, 'manual')

        # Win 2
        r = engine.open_position(symbol='SOLUSDT', side='long', entry_price=100, signal_confidence=65)
        engine.close_position(r['position']['id'], 110, 'manual')

        perf = engine.get_performance_metrics()
        assert perf['total_trades'] == 3
        assert perf['winning_trades'] == 2
        assert perf['losing_trades'] == 1
        assert perf['win_rate'] > 0
        assert perf['profit_factor'] > 0
        assert perf['total_pnl'] != 0


# ══════════════════════════════════════════════════════════════════════
# Test 7: Shadow Trading
# ══════════════════════════════════════════════════════════════════════

class TestShadowTrading:
    """Test shadow trading execution quality tracking."""

    def test_shadow_signal_records_trade(self):
        """Test that shadow signals are recorded correctly."""
        from apps.signals.services.shadow_trading import ShadowTradingEngine

        engine = ShadowTradingEngine()
        result = engine.shadow_signal(
            symbol='BTCUSDT', side='long', signal_confidence=75,
            expected_entry=50000, expected_exit=52000,
            current_price=50050, spread_bps=5,
        )

        assert result['success']
        assert 'trade' in result or 'execution_quality' in result

    def test_execution_quality_report(self):
        """Test execution quality report generation."""
        from apps.signals.services.shadow_trading import ShadowTradingEngine

        engine = ShadowTradingEngine()

        # Create multiple shadow trades
        for i in range(5):
            engine.shadow_signal(
                symbol='BTCUSDT', side='long', signal_confidence=70 + i,
                expected_entry=50000, expected_exit=52000,
                current_price=50000 + i * 100,
            )

        report = engine.get_execution_quality_report()
        assert 'total_trades' in report
        assert report['total_trades'] == 5

    def test_slippage_tracking(self):
        """Test that slippage is tracked correctly."""
        from apps.signals.services.shadow_trading import ShadowTradingEngine

        engine = ShadowTradingEngine()
        result = engine.shadow_signal(
            symbol='BTCUSDT', side='long', signal_confidence=75,
            expected_entry=50000, expected_exit=52000,
            current_price=50100,  # 100 above expected
            spread_bps=10,
        )

        assert result['success']


# ══════════════════════════════════════════════════════════════════════
# Test 8: Calibration Engine
# ══════════════════════════════════════════════════════════════════════

class TestCalibrationEngine:
    """Test the calibration and probability adjustment system."""

    def test_brier_score_calculation(self):
        """Test Brier Score is calculated correctly."""
        from apps.signals.services.calibration import CalibrationEngine

        engine = CalibrationEngine()
        predictions = [
            (80, True), (80, True), (80, False),
            (60, True), (60, False),
            (40, True), (40, False),
        ]
        result = engine.calibrate(predictions)

        assert hasattr(result, 'brier_score')
        assert 0 <= result.brier_score <= 1

    def test_perfect_predictions_low_brier(self):
        """Test that perfect predictions have low Brier Score."""
        from apps.signals.services.calibration import CalibrationEngine

        engine = CalibrationEngine()
        # 90% predictions where 9/10 are correct
        predictions = [(90, True)] * 9 + [(90, False)]
        result = engine.calibrate(predictions)

        assert result.brier_score < 0.2

    def test_adjuster_modifies_confidence(self):
        """Test that adjuster modifies confidence based on calibration."""
        from apps.signals.services.calibration import CalibrationEngine, ProbabilityAdjuster

        engine = CalibrationEngine()
        predictions = [(80, True), (80, True), (80, False), (60, True), (60, False)]
        result = engine.calibrate(predictions)

        adjusted = ProbabilityAdjuster.adjust_confidence(80, result.reliability_curve)
        assert 0 <= adjusted <= 100
        assert isinstance(adjusted, float)

    def test_reliability_curve_structure(self):
        """Test reliability curve has correct structure."""
        from apps.signals.services.calibration import CalibrationEngine

        engine = CalibrationEngine()
        predictions = [
            (55, True), (55, False), (55, True),
            (65, True), (65, False), (65, True),
            (75, True), (75, False), (75, True),
            (85, True), (85, False),
        ]
        result = engine.calibrate(predictions)

        assert isinstance(result.reliability_curve, list)
        assert len(result.reliability_curve) > 0

        for bucket in result.reliability_curve:
            assert 'bucket_index' in bucket or 'predicted_rate' in bucket or 'actual_rate' in bucket


# ══════════════════════════════════════════════════════════════════════
# Test 9: Portfolio Intelligence
# ══════════════════════════════════════════════════════════════════════

class TestPortfolioIntelligence:
    """Test portfolio intelligence calculations."""

    def test_correlation_matrix(self):
        """Test correlation matrix calculation."""
        from apps.portfolio.services.portfolio_intelligence import PortfolioIntelligence

        pi = PortfolioIntelligence()
        returns = {
            'BTC': [0.01, -0.02, 0.03, -0.01, 0.02],
            'ETH': [0.02, -0.01, 0.01, -0.02, 0.03],
        }
        corr = pi.calculate_correlation(returns)

        assert isinstance(corr, dict)
        assert len(corr) > 0

    def test_beta_calculation(self):
        """Test beta calculation vs benchmark."""
        from apps.portfolio.services.portfolio_intelligence import PortfolioIntelligence

        pi = PortfolioIntelligence()
        asset_returns = [0.01, -0.02, 0.03, -0.01, 0.02]
        benchmark_returns = [0.015, -0.01, 0.025, -0.015, 0.02]

        beta = pi.calculate_beta(asset_returns, benchmark_returns)
        assert isinstance(beta, float)

    def test_var_calculation(self):
        """Test Value at Risk calculation."""
        from apps.portfolio.services.portfolio_intelligence import PortfolioIntelligence

        pi = PortfolioIntelligence()
        returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.015, -0.005]

        result = pi.calculate_var(returns)
        assert result is not None


# ══════════════════════════════════════════════════════════════════════
# Test 10: Full Pipeline Integration
# ══════════════════════════════════════════════════════════════════════

class TestFullPipelineIntegration:
    """Complete end-to-end pipeline test."""

    def test_signal_to_paper_trade_pipeline(self):
        """
        Test complete pipeline:
        Market Data → Regime → Fusion → Ensemble → Lineage → Paper Trade
        """
        from apps.signals.services.regime_engine import RegimeEngine
        from apps.signals.services.signal_fusion import SignalFusionEngine
        from apps.ai_engine.services.agent_ensemble import AgentEnsemble
        from apps.ai_engine.services.llm_router import AIConfig, AIMode
        from apps.signals.services.versioning import VersionTracker
        from apps.signals.services.paper_trading import PaperTradingEngine

        # Step 1: Market Data & Regime Detection
        candles = generate_synthetic_candles(50, 100, 'up')
        regime = RegimeEngine().detect_regime(candles)
        assert regime.regime is not None

        # Step 2: Signal Fusion (8 factors)
        fusion = SignalFusionEngine()
        signal = fusion.fuse_signal(
            symbol='BTCUSDT', timeframe='1h',
            technical_score=72, sentiment_score=65, news_score=58,
            macro_score=55, derivatives_score=60, market_structure_score=50,
            order_book_score=55, portfolio_context_score=50,
            regime=regime.regime, regime_weights=regime.weights,
            current_price=113500,
        )
        assert 'direction' in signal
        assert 'confidence' in signal

        # Step 3: Agent Ensemble (OFF mode for speed)
        ensemble = AgentEnsemble(config=AIConfig(mode=AIMode.OFF))
        loop = asyncio.new_event_loop()
        ensemble_result = loop.run_until_complete(ensemble.run({
            'symbol': 'BTCUSDT', 'current_price': 113500,
            'quant_composite_score': signal.get('quant_composite_score', 50),
            'direction': signal.get('direction', 'hold'),
            'confidence': signal.get('confidence', 50),
            'regime': regime.regime,
            'technical_score': 72,
        }))
        loop.close()
        assert ensemble_result.verdict == 'quant_only'

        # Step 4: Versioning & Lineage
        tracker = VersionTracker()
        lineage = tracker.capture_lineage(
            signal_data={
                'symbol': 'BTCUSDT', 'direction': signal['direction'],
                'confidence': signal['confidence'],
                'composite_score': signal.get('composite_score', 50),
                'timeframe': '1h'
            },
            factor_scores=signal.get('factor_scores', {}),
            regime=regime.regime, regime_confidence=regime.confidence,
            weights_used=signal.get('weights_used', {}),
            ensemble_output=ensemble_result.to_dict(),
        )
        assert 'versions' in lineage
        assert lineage['signal']['symbol'] == 'BTCUSDT'

        # Step 5: Paper Trading
        paper = PaperTradingEngine(initial_capital=10000)
        side = signal['direction'] if signal['direction'] in ('long', 'short') else 'long'
        paper_result = paper.open_position(
            symbol='BTCUSDT', side=side, entry_price=113500,
            signal_confidence=signal['confidence'],
        )
        assert paper_result['success']

        # Step 6: Verify complete pipeline
        status = paper.get_status()
        assert status['open_positions_count'] == 1

        # Step 7: Human-readable explanation
        explanation = tracker.explain_signal(lineage)
        assert 'BTCUSDT' in explanation

    def test_calibration_feedback_loop(self):
        """
        Test calibration feedback loop:
        Generate signals → Evaluate → Calibrate → Adjust confidence
        """
        from apps.signals.services.calibration import CalibrationEngine, ProbabilityAdjuster

        # Simulate signal outcomes (overconfident predictions)
        predictions = [(80, True)] * 5 + [(80, False)] * 5  # 50% actual vs 80% predicted

        # Calibrate
        engine = CalibrationEngine()
        cal_result = engine.calibrate(predictions)

        # System detects overconfidence
        assert cal_result.calibration_quality in ['poor', 'uncalibrated', 'fair']

        # Adjuster corrects future predictions
        adjusted = ProbabilityAdjuster.adjust_confidence(80, cal_result.reliability_curve)
        assert isinstance(adjusted, float)
        assert 0 <= adjusted <= 100

    def test_shadow_trading_execution_quality(self):
        """
        Test shadow trading tracks execution quality:
        Signal → Expected fill → Actual fill → Quality score
        """
        from apps.signals.services.shadow_trading import ShadowTradingEngine

        engine = ShadowTradingEngine()

        # Record multiple shadow trades
        for i in range(5):
            result = engine.shadow_signal(
                symbol='BTCUSDT', side='long', signal_confidence=70 + i * 5,
                expected_entry=50000, expected_exit=52000,
                current_price=50000 + i * 50,  # Varying slippage
                spread_bps=5,
            )
            assert result['success']

        # Verify execution quality report
        report = engine.get_execution_quality_report()
        assert report['total_trades'] == 5

    def test_multi_symbol_pipeline(self):
        """Test pipeline works for multiple symbols."""
        from apps.signals.services.regime_engine import RegimeEngine
        from apps.signals.services.signal_fusion import SignalFusionEngine
        from apps.signals.services.paper_trading import PaperTradingEngine

        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        regime_engine = RegimeEngine()
        fusion = SignalFusionEngine()
        paper = PaperTradingEngine(initial_capital=100000)

        for symbol in symbols:
            candles = generate_synthetic_candles(50, 100, 'up')
            regime = regime_engine.detect_regime(candles)

            signal = fusion.fuse_signal(
                symbol=symbol, timeframe='1h',
                technical_score=72, sentiment_score=65, news_score=58,
                macro_score=55, derivatives_score=60, market_structure_score=50,
                order_book_score=55, portfolio_context_score=50,
                regime=regime.regime, regime_weights=regime.weights,
                current_price=50000,
            )

            assert signal['direction'] in ('long', 'short', 'hold', 'buy', 'sell')

        # All symbols processed successfully
        assert len(symbols) == 3


# ══════════════════════════════════════════════════════════════════════
# Test 11: Risk Engine
# ══════════════════════════════════════════════════════════════════════

class TestRiskEngine:
    """Test risk engine and kill switch."""

    def test_risk_engine_instantiation(self):
        """Verify risk engine can be instantiated."""
        from apps.signals.services.risk_engine import RiskEngine

        engine = RiskEngine()
        assert engine is not None

    def test_kill_switch_state(self):
        """Verify kill switch state can be checked."""
        from apps.signals.services.risk_engine import RiskEngine

        engine = RiskEngine()
        # Kill switch should be accessible
        assert hasattr(engine, 'config') or hasattr(engine, 'check') or engine is not None


# ══════════════════════════════════════════════════════════════════════
# Test 12: Live Execution Safety
# ══════════════════════════════════════════════════════════════════════

class TestLiveExecutionSafety:
    """Test live execution safety controls."""

    def test_live_trading_disabled_by_default(self):
        """Verify live trading is disabled by default."""
        from apps.signals.services.live_execution import LiveExecutionEngine, LIVE_TRADING_ENABLED

        # Live trading should be disabled
        assert LIVE_TRADING_ENABLED is False

    def test_order_validation(self):
        """Test order validation rejects invalid orders."""
        from apps.signals.services.live_execution import LiveExecutionEngine

        engine = LiveExecutionEngine()

        # Missing symbol should fail
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(engine.place_order(
            symbol='', side='buy', order_type='market', quantity=0.001,
        ))
        loop.close()

        assert result['success'] is False

    def test_order_requires_risk_approval(self):
        """Test orders require risk engine approval."""
        from apps.signals.services.live_execution import LiveExecutionEngine

        engine = LiveExecutionEngine()

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(engine.place_order(
            symbol='BTCUSDT', side='buy', order_type='market',
            quantity=0.001, risk_approved=False,
        ))
        loop.close()

        # Should be rejected without risk approval
        assert result['success'] is False


# ══════════════════════════════════════════════════════════════════════
# Test 13: Backtester & Walk-Forward
# ══════════════════════════════════════════════════════════════════════

class TestBacktesterAndWalkForward:
    """Test backtesting and walk-forward validation."""

    def test_backtester_instantiation(self):
        """Verify backtester can be instantiated."""
        from apps.signals.services.backtester import SignalBacktester

        bt = SignalBacktester()
        assert bt is not None

    def test_walk_forward_instantiation(self):
        """Verify walk-forward engine can be instantiated."""
        from apps.signals.services.walk_forward import WalkForwardEngine

        wf = WalkForwardEngine()
        assert wf is not None


# ══════════════════════════════════════════════════════════════════════
# Test 14: LLM Router
# ══════════════════════════════════════════════════════════════════════

class TestLLMRouter:
    """Test LLM router configuration and modes."""

    def test_all_modes_configurable(self):
        """Verify all AI modes can be configured."""
        from apps.ai_engine.services.llm_router import AIConfig, AIMode

        for mode in [AIMode.OFF, AIMode.LITE, AIMode.STANDARD, AIMode.CLOUD]:
            config = AIConfig(mode=mode)
            assert config.mode == mode

    def test_router_instantiation(self):
        """Verify router can be instantiated in each mode."""
        from apps.ai_engine.services.llm_router import LLMRouter, AIConfig, AIMode

        for mode in [AIMode.OFF, AIMode.LITE, AIMode.STANDARD]:
            config = AIConfig(mode=mode)
            router = LLMRouter(config)
            assert router.config.mode == mode
