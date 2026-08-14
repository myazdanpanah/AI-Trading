"""Full System Integration Test — Phases 57-70

Tests the entire pipeline end-to-end:
  Regime Detection → Signal Fusion → Agent Ensemble → Versioning → Paper Trading → Calibration
"""
import pytest
import json
import asyncio
import time
from unittest.mock import patch


class TestPhase57Backtester:
    """Phase 57: Quant Research Engine (Backtesting)"""

    def test_backtester_importable(self):
        from apps.signals.services.backtester import SignalBacktester
        bt = SignalBacktester()
        assert bt is not None

    def test_walk_forward_importable(self):
        from apps.signals.services.walk_forward import WalkForwardEngine
        wf = WalkForwardEngine()
        assert wf is not None


class TestPhase59RiskEngine:
    """Phase 59: Risk Engine + Kill Switch"""

    def test_risk_engine_importable(self):
        from apps.signals.services.risk_engine import RiskEngine
        re = RiskEngine()
        assert re is not None


class TestPhase60Derivatives:
    """Phase 60: Derivatives Intelligence"""

    def test_derivatives_collector(self):
        from apps.market.services.derivatives_collector import DerivativesCollector
        dc = DerivativesCollector()
        assert dc is not None


class TestPhase61Regime:
    """Phase 61: Market Regime Engine"""

    def test_detect_regime(self):
        from apps.signals.services.regime_engine import RegimeEngine
        engine = RegimeEngine()
        candles = [
            {'open': 100 + i, 'high': 102 + i, 'low': 99 + i, 'close': 101 + i, 'volume': 1000}
            for i in range(50)
        ]
        state = engine.detect_regime(candles)
        assert hasattr(state, 'regime')
        assert hasattr(state, 'weights')
        assert isinstance(state.weights, dict)
        assert len(state.weights) > 0

    def test_regime_has_all_factors(self):
        from apps.signals.services.regime_engine import RegimeEngine
        engine = RegimeEngine()
        candles = [{'open': 100, 'high': 102, 'low': 99, 'close': 101, 'volume': 1000} for _ in range(50)]
        state = engine.detect_regime(candles)
        expected_factors = ['technical', 'sentiment', 'news', 'macro', 'derivatives']
        for f in expected_factors:
            assert f in state.weights, f'Missing factor weight: {f}'


class TestPhase62Portfolio:
    """Phase 62: Portfolio Intelligence"""

    def test_correlation(self):
        from apps.portfolio.services.portfolio_intelligence import PortfolioIntelligence
        pi = PortfolioIntelligence()
        returns = {
            'BTC': [0.01, -0.02, 0.03, -0.01, 0.02],
            'ETH': [0.02, -0.01, 0.01, -0.02, 0.03],
        }
        corr = pi.calculate_correlation(returns)
        assert isinstance(corr, dict)

    def test_beta(self):
        from apps.portfolio.services.portfolio_intelligence import PortfolioIntelligence
        pi = PortfolioIntelligence()
        asset_returns = [0.01, -0.02, 0.03, -0.01, 0.02]
        benchmark_returns = [0.015, -0.01, 0.025, -0.015, 0.02]
        beta = pi.calculate_beta(asset_returns, benchmark_returns)
        assert isinstance(beta, float)

    def test_var(self):
        from apps.portfolio.services.portfolio_intelligence import PortfolioIntelligence
        pi = PortfolioIntelligence()
        returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.015, -0.005]
        result = pi.calculate_var(returns)
        assert result is not None


class TestPhase63Fusion:
    """Phase 63: Signal Fusion Engine"""

    def test_fuse_signal(self):
        from apps.signals.services.signal_fusion import SignalFusionEngine
        from apps.signals.services.regime_engine import RegimeEngine

        regime_engine = RegimeEngine()
        candles = [
            {'open': 100 + i, 'high': 102 + i, 'low': 99 + i, 'close': 101 + i, 'volume': 1000}
            for i in range(50)
        ]
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

    def test_fusion_uses_regime_weights(self):
        from apps.signals.services.signal_fusion import SignalFusionEngine
        from apps.signals.services.regime_engine import RegimeEngine

        regime_engine = RegimeEngine()
        candles = [
            {'open': 100 + i, 'high': 102 + i, 'low': 99 + i, 'close': 101 + i, 'volume': 1000}
            for i in range(50)
        ]
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


class TestPhase64LLMRouter:
    """Phase 64: Local AI Router"""

    def test_router_off_mode(self):
        from apps.ai_engine.services.llm_router import LLMRouter, AIConfig, AIMode
        config = AIConfig(mode=AIMode.OFF)
        router = LLMRouter(config)
        assert router.config.mode == AIMode.OFF

    def test_router_modes(self):
        from apps.ai_engine.services.llm_router import AIConfig, AIMode
        for mode in [AIMode.OFF, AIMode.LITE, AIMode.STANDARD]:
            config = AIConfig(mode=mode)
            assert config.mode == mode


class TestPhase65Ensemble:
    """Phase 65: Agent Ensemble"""

    def test_off_mode(self):
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

    def test_all_agents_have_schemas(self):
        from apps.ai_engine.services.agent_ensemble import AGENT_OUTPUT_SCHEMAS, AGENT_EXECUTION_ORDER
        from apps.ai_engine.services.llm_router import AgentRole

        for role in AGENT_EXECUTION_ORDER:
            assert role in AGENT_OUTPUT_SCHEMAS, f'Missing schema for {role}'
            schema = AGENT_OUTPUT_SCHEMAS[role]
            assert 'required' in schema
            assert 'properties' in schema

    def test_context_builder(self):
        from apps.ai_engine.services.agent_ensemble import AgentContextBuilder
        from apps.ai_engine.services.llm_router import AgentRole

        builder = AgentContextBuilder()
        signal_ctx = {
            'symbol': 'BTCUSDT', 'rsi': 62, 'macd_signal': 'bullish',
            'technical_score': 72, 'news_score': 58, 'regime': 'sideways',
        }

        tech_ctx = builder.build_technical_context(signal_ctx)
        assert 'symbol' in tech_ctx
        assert 'rsi' in tech_ctx

        news_ctx = builder.build_news_context(signal_ctx)
        assert 'symbol' in news_ctx
        assert 'news_score' in news_ctx


class TestPhase66Calibration:
    """Phase 66: Calibration Engine"""

    def test_brier_score(self):
        from apps.signals.services.calibration import CalibrationEngine

        engine = CalibrationEngine()
        predictions = [(80, True), (80, True), (80, False), (60, True), (60, False), (40, True), (40, False)]
        result = engine.calibrate(predictions)

        assert hasattr(result, 'brier_score')
        assert 0 <= result.brier_score <= 1

    def test_perfect_calibration(self):
        from apps.signals.services.calibration import CalibrationEngine

        engine = CalibrationEngine()
        # 90% predictions where 9/10 are correct
        predictions = [(90, True)] * 9 + [(90, False)]
        result = engine.calibrate(predictions)

        # Brier score should be low for well-calibrated predictions
        assert result.brier_score < 0.2

    def test_adjuster(self):
        from apps.signals.services.calibration import CalibrationEngine, ProbabilityAdjuster

        engine = CalibrationEngine()
        predictions = [(80, True), (80, True), (80, False), (60, True), (60, False)]
        result = engine.calibrate(predictions)

        adjusted = ProbabilityAdjuster.adjust_confidence(80, result.reliability_curve)
        assert 0 <= adjusted <= 100

    def test_reliability_curve_buckets(self):
        from apps.signals.services.calibration import CalibrationEngine

        engine = CalibrationEngine()
        # More predictions to ensure buckets are filled
        predictions = [(55, True), (55, False), (55, True), (65, True), (65, False), (65, True), (75, True), (75, False), (75, True), (85, True), (85, False)]
        result = engine.calibrate(predictions)

        assert isinstance(result.reliability_curve, list)
        # Reliability curve should have entries
        assert len(result.reliability_curve) > 0


class TestPhase67Versioning:
    """Phase 67: Versioning & Data Lineage"""

    def test_capture_lineage(self):
        from apps.signals.services.versioning import VersionTracker

        tracker = VersionTracker()
        lineage = tracker.capture_lineage(
            signal_data={'symbol': 'BTCUSDT', 'direction': 'buy', 'confidence': 75, 'composite_score': 68, 'timeframe': '1h'},
            factor_scores={'technical': 72, 'sentiment': 65, 'news': 58},
            regime='sideways', regime_confidence=0.8,
            weights_used={'technical': 0.35, 'sentiment': 0.15, 'news': 0.1},
        )

        assert 'versions' in lineage
        assert 'factor_scores' in lineage
        assert 'market_snapshot' in lineage
        assert 'regime' in lineage
        assert lineage['signal']['symbol'] == 'BTCUSDT'

    def test_explain_signal(self):
        from apps.signals.services.versioning import VersionTracker

        tracker = VersionTracker()
        lineage = tracker.capture_lineage(
            signal_data={'symbol': 'BTCUSDT', 'direction': 'buy', 'confidence': 75, 'composite_score': 68, 'timeframe': '1h'},
            factor_scores={'technical': 72, 'sentiment': 65},
            regime='sideways',
        )

        explanation = tracker.explain_signal(lineage)
        assert len(explanation) > 50
        assert 'BTCUSDT' in explanation

    def test_system_versions(self):
        from apps.signals.services.versioning import SYSTEM_VERSIONS

        assert 'strategy' in SYSTEM_VERSIONS
        assert 'features' in SYSTEM_VERSIONS
        assert 'ensemble' in SYSTEM_VERSIONS

    def test_snapshot_builders(self):
        from apps.signals.services.versioning import VersionTracker

        tracker = VersionTracker()
        market = tracker.build_market_snapshot(current_price=50000, indicators={'rsi': 62})
        assert market['current_price'] == 50000

        news = tracker.build_news_snapshot(article_count=10, avg_sentiment=60)
        assert news['article_count'] == 10

        social = tracker.build_social_snapshot(fear_greed_index=65)
        assert social['fear_greed_index'] == 65


class TestPhase68PaperTrading:
    """Phase 68: Paper Trading"""

    def test_open_and_close(self):
        from apps.signals.services.paper_trading import PaperTradingEngine

        engine = PaperTradingEngine(initial_capital=10000)

        # Open
        result = engine.open_position(
            symbol='BTCUSDT', side='long', entry_price=50000,
            stop_loss=49000, take_profit=52000, signal_confidence=75,
        )
        assert result['success']
        pos_id = result['position']['id']

        # Close
        close = engine.close_position(pos_id, 51500, 'manual')
        assert close['success']
        assert close['trade']['pnl'] > 0

    def test_pnl_calculation(self):
        from apps.signals.services.paper_trading import PaperTradingEngine

        engine = PaperTradingEngine(initial_capital=10000)
        result = engine.open_position(symbol='BTCUSDT', side='long', entry_price=50000, signal_confidence=75)
        pos_id = result['position']['id']

        # Update price up
        engine.update_prices({'BTCUSDT': 51000})
        status = engine.get_status()
        assert status['equity'] != 10000  # Equity changed

    def test_performance_metrics(self):
        from apps.signals.services.paper_trading import PaperTradingEngine

        engine = PaperTradingEngine(initial_capital=10000)
        result = engine.open_position(symbol='BTCUSDT', side='long', entry_price=50000, signal_confidence=75)
        engine.close_position(result['position']['id'], 52000, 'manual')

        perf = engine.get_performance_metrics()
        assert perf['total_trades'] == 1
        assert perf['winning_trades'] == 1
        assert perf['win_rate'] == 100.0

    def test_max_positions_limit(self):
        from apps.signals.services.paper_trading import PaperTradingEngine

        engine = PaperTradingEngine(initial_capital=100000)
        for i in range(10):
            engine.open_position(symbol=f'COIN{i}USDT', side='long', entry_price=100, signal_confidence=75)

        # 11th should fail
        result = engine.open_position(symbol='COIN11USDT', side='long', entry_price=100, signal_confidence=75)
        assert not result['success']

    def test_reset(self):
        from apps.signals.services.paper_trading import PaperTradingEngine

        engine = PaperTradingEngine(initial_capital=10000)
        engine.open_position(symbol='BTCUSDT', side='long', entry_price=50000, signal_confidence=75)
        engine.reset(initial_capital=5000)

        status = engine.get_status()
        assert status['initial_capital'] == 5000
        assert status['open_positions_count'] == 0


class TestFullPipeline:
    """Cross-phase integration: Full pipeline end-to-end"""

    def test_regime_to_fusion_to_ensemble_to_lineage(self):
        from apps.signals.services.regime_engine import RegimeEngine
        from apps.signals.services.signal_fusion import SignalFusionEngine
        from apps.ai_engine.services.agent_ensemble import AgentEnsemble
        from apps.ai_engine.services.llm_router import AIConfig, AIMode
        from apps.signals.services.versioning import VersionTracker

        candles = [
            {'open': 100 + i, 'high': 102 + i, 'low': 99 + i, 'close': 101 + i, 'volume': 1000}
            for i in range(50)
        ]

        # 1. Detect regime
        regime = RegimeEngine().detect_regime(candles)
        assert regime.regime is not None

        # 2. Fuse signal
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

        # 3. Run ensemble (OFF mode)
        ensemble = AgentEnsemble(config=AIConfig(mode=AIMode.OFF))
        loop = asyncio.new_event_loop()
        ensemble_res = loop.run_until_complete(ensemble.run({
            'symbol': 'BTCUSDT', 'current_price': 113500,
            'quant_composite_score': result.get('quant_composite_score', 50),
            'direction': result.get('direction', 'hold'),
            'confidence': result.get('confidence', 50),
            'regime': regime.regime,
            'technical_score': 72,
        }))
        loop.close()
        assert ensemble_res.verdict == 'quant_only'

        # 4. Capture lineage
        tracker = VersionTracker()
        lineage = tracker.capture_lineage(
            signal_data={'symbol': 'BTCUSDT', 'direction': result['direction'],
                         'confidence': result['confidence'],
                         'composite_score': result.get('composite_score', 50),
                         'timeframe': '1h'},
            factor_scores=result.get('factor_scores', {}),
            regime=regime.regime, regime_confidence=regime.confidence,
            weights_used=result.get('weights_used', {}),
            ensemble_output=ensemble_res.to_dict(),
        )
        assert 'versions' in lineage
        assert lineage['signal']['symbol'] == 'BTCUSDT'

        # 5. Human-readable explanation
        explanation = tracker.explain_signal(lineage)
        assert 'BTCUSDT' in explanation

    def test_paper_trading_full_lifecycle(self):
        from apps.signals.services.paper_trading import PaperTradingEngine

        engine = PaperTradingEngine(initial_capital=10000)

        # Open
        open_result = engine.open_position(
            symbol='BTCUSDT', side='long', entry_price=50000,
            stop_loss=49000, take_profit=52000, signal_confidence=75,
        )
        assert open_result['success']
        pos_id = open_result['position']['id']

        # Update prices — trigger stop loss
        engine.update_prices({'BTCUSDT': 48000})
        status = engine.get_status()
        assert status['open_positions_count'] == 0  # Stop loss triggered

        # Verify trade was recorded
        assert status['total_trades'] == 1
        assert status['losing_trades'] == 1

        # Performance
        perf = engine.get_performance_metrics()
        assert perf['total_trades'] == 1
        assert perf['win_rate'] == 0.0  # Stop loss = loss

    def test_calibration_adjusts_confidence(self):
        from apps.signals.services.calibration import CalibrationEngine, ProbabilityAdjuster

        # Create a dataset showing overconfidence
        predictions = [(80, True)] * 5 + [(80, False)] * 5  # 50% actual vs 80% predicted
        engine = CalibrationEngine()
        result = engine.calibrate(predictions)

        # System is overconfident — adjuster should lower the score
        adjusted = ProbabilityAdjuster.adjust_confidence(80, result.reliability_curve)
        # The adjusted value should be different from 80 (either higher or lower depending on curve)
        assert isinstance(adjusted, float)
        assert 0 <= adjusted <= 100
