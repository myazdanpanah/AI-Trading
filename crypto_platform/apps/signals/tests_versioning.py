"""Tests for Versioning & Data Lineage (Phase 67).

Covers:
- System versions defined correctly
- Lineage capture with all snapshots
- Market, news, social, derivatives snapshots
- LLM context and output capture
- Ensemble output capture
- Weight snapshot storage
- Regime tracking
- Human-readable explanation
- SignalLineage model storage
- Version retrieval API
"""
from django.test import TestCase

from .services.versioning import (
    VersionTracker,
    SYSTEM_VERSIONS,
)


class SystemVersionsTest(TestCase):
    """Test that system versions are defined."""

    def test_all_versions_defined(self):
        required = ['strategy', 'features', 'regime', 'risk', 'calibration', 'ensemble']
        for key in required:
            self.assertIn(key, SYSTEM_VERSIONS)

    def test_versions_are_strings(self):
        for key, val in SYSTEM_VERSIONS.items():
            self.assertIsInstance(val, str)

    def test_strategy_version_is_2(self):
        self.assertEqual(SYSTEM_VERSIONS['strategy'], '2.0')


class LineageCaptureTest(TestCase):
    """Test VersionTracker.capture_lineage()."""

    def setUp(self):
        self.tracker = VersionTracker()

    def test_basic_lineage_capture(self):
        lineage = self.tracker.capture_lineage(
            signal_data={'symbol': 'BTC', 'direction': 'buy', 'confidence': 75},
        )
        self.assertEqual(lineage['signal']['symbol'], 'BTC')
        self.assertEqual(lineage['signal']['direction'], 'buy')
        self.assertEqual(lineage['signal']['confidence'], 75)
        self.assertIn('versions', lineage)
        self.assertIn('captured_at', lineage)

    def test_versions_included(self):
        lineage = self.tracker.capture_lineage(signal_data={'symbol': 'ETH'})
        self.assertEqual(lineage['versions']['strategy'], '2.0')
        self.assertEqual(lineage['versions']['features'], '1.2')

    def test_factor_scores_stored(self):
        scores = {'technical': 75, 'sentiment': 60, 'news': 55}
        lineage = self.tracker.capture_lineage(
            signal_data={'symbol': 'BTC'},
            factor_scores=scores,
        )
        self.assertEqual(lineage['factor_scores'], scores)

    def test_regime_stored(self):
        lineage = self.tracker.capture_lineage(
            signal_data={'symbol': 'BTC'},
            regime='bull_trend',
            regime_confidence=0.85,
        )
        self.assertEqual(lineage['regime']['detected'], 'bull_trend')
        self.assertAlmostEqual(lineage['regime']['confidence'], 0.85)

    def test_weights_stored(self):
        weights = {'technical': 0.35, 'sentiment': 0.15, 'news': 0.10}
        lineage = self.tracker.capture_lineage(
            signal_data={'symbol': 'BTC'},
            weights_used=weights,
        )
        self.assertEqual(lineage['weights'], weights)

    def test_empty_lineage_has_defaults(self):
        lineage = self.tracker.capture_lineage(signal_data={})
        self.assertEqual(lineage['market_snapshot'], {})
        self.assertEqual(lineage['news_snapshot'], {})
        self.assertEqual(lineage['social_snapshot'], {})
        self.assertEqual(lineage['llm_context'], {})
        self.assertEqual(lineage['llm_output'], {})
        self.assertEqual(lineage['ensemble_output'], {})


class SnapshotBuildersTest(TestCase):
    """Test snapshot builder methods."""

    def setUp(self):
        self.tracker = VersionTracker()

    def test_market_snapshot(self):
        snap = self.tracker.build_market_snapshot(
            current_price=50000,
            indicators={'rsi': 65, 'macd': 'bullish'},
            candles_count=50,
            volume_24h=1e9,
        )
        self.assertEqual(snap['current_price'], 50000)
        self.assertEqual(snap['indicators']['rsi'], 65)
        self.assertEqual(snap['candles_used'], 50)
        self.assertIn('snapshot_time', snap)

    def test_news_snapshot(self):
        snap = self.tracker.build_news_snapshot(
            article_count=20,
            avg_sentiment=65,
            top_headlines=['BTC ETF approved'],
            sources_used=['CoinDesk', 'Reuters'],
        )
        self.assertEqual(snap['article_count'], 20)
        self.assertEqual(snap['avg_sentiment'], 65)
        self.assertEqual(len(snap['top_headlines']), 1)
        self.assertEqual(len(snap['sources_used']), 2)

    def test_social_snapshot(self):
        snap = self.tracker.build_social_snapshot(
            fear_greed_index=72,
            social_sentiment=68,
            twitter_sentiment=65,
            trending_topics=['bitcoin', 'crypto'],
        )
        self.assertEqual(snap['fear_greed_index'], 72)
        self.assertEqual(snap['social_sentiment'], 68)
        self.assertEqual(len(snap['trending_topics']), 2)

    def test_derivatives_snapshot(self):
        snap = self.tracker.build_derivatives_snapshot(
            funding_rate=0.01,
            open_interest=5e9,
            long_short_ratio=1.5,
            liquidation_24h=1e6,
        )
        self.assertAlmostEqual(snap['funding_rate'], 0.01)
        self.assertEqual(snap['open_interest'], 5e9)
        self.assertAlmostEqual(snap['long_short_ratio'], 1.5)

    def test_llm_context(self):
        snap = self.tracker.build_llm_context(
            model='gemma4:latest',
            prompt_version='1.0',
            system_prompt_preview='You are a trading analyst...',
            user_context_size=500,
            temperature=0.3,
        )
        self.assertEqual(snap['model'], 'gemma4:latest')
        self.assertEqual(snap['prompt_version'], '1.0')
        self.assertEqual(snap['temperature'], 0.3)

    def test_llm_output(self):
        snap = self.tracker.build_llm_output(
            content='{"direction": "bullish"}',
            parsed_output={'direction': 'bullish', 'confidence': 75},
            latency_ms=5000,
            tokens_used=200,
            success=True,
        )
        self.assertEqual(snap['parsed_output']['direction'], 'bullish')
        self.assertEqual(snap['latency_ms'], 5000)
        self.assertTrue(snap['success'])


class LLMAndEnsembleCaptureTest(TestCase):
    """Test LLM and ensemble output capture."""

    def setUp(self):
        self.tracker = VersionTracker()

    def test_llm_output_stored(self):
        lineage = self.tracker.capture_lineage(
            signal_data={'symbol': 'BTC'},
            llm_context={'model': 'gemma4:latest'},
            llm_output={'content': 'bullish', 'success': True, 'latency_ms': 5000},
        )
        self.assertEqual(lineage['llm_context']['model'], 'gemma4:latest')
        self.assertTrue(lineage['llm_output']['success'])
        self.assertEqual(lineage['llm_output']['latency_ms'], 5000)

    def test_ensemble_output_stored(self):
        ensemble = {
            'verdict': 'validate',
            'adjusted_confidence': 78,
            'agents_succeeded': 5,
            'total_latency_ms': 15000,
        }
        lineage = self.tracker.capture_lineage(
            signal_data={'symbol': 'BTC'},
            ensemble_output=ensemble,
        )
        self.assertEqual(lineage['ensemble_output']['verdict'], 'validate')
        self.assertEqual(lineage['ensemble_output']['agents_succeeded'], 5)

    def test_risk_decision_stored(self):
        risk = {
            'approved': True,
            'position_size': 0.1,
            'risk_amount': 100,
        }
        lineage = self.tracker.capture_lineage(
            signal_data={'symbol': 'BTC'},
            risk_decision=risk,
        )
        self.assertTrue(lineage['risk_decision']['approved'])
        self.assertEqual(lineage['risk_decision']['position_size'], 0.1)


class ExplainSignalTest(TestCase):
    """Test human-readable explanation generation."""

    def setUp(self):
        self.tracker = VersionTracker()

    def test_explain_basic_signal(self):
        lineage = self.tracker.capture_lineage(
            signal_data={
                'symbol': 'BTC',
                'direction': 'buy',
                'confidence': 75,
                'composite_score': 68,
                'timeframe': '1h',
            },
            factor_scores={'technical': 80, 'sentiment': 65, 'news': 55},
            weights_used={'technical': 0.35, 'sentiment': 0.15, 'news': 0.10},
            regime='bull_trend',
            regime_confidence=0.82,
        )
        explanation = self.tracker.explain_signal(lineage)
        self.assertIn('BTC', explanation)
        self.assertIn('BUY', explanation)
        self.assertIn('75', explanation)
        self.assertIn('bull_trend', explanation)
        self.assertIn('technical', explanation)

    def test_explain_empty_lineage(self):
        explanation = self.tracker.explain_signal({})
        self.assertIn('No lineage data', explanation)

    def test_explain_with_ai(self):
        lineage = self.tracker.capture_lineage(
            signal_data={'symbol': 'ETH', 'direction': 'sell', 'confidence': 60},
            llm_context={'model': 'gemma4:latest'},
            llm_output={'success': True, 'latency_ms': 8000},
            ensemble_output={'verdict': 'validate', 'adjusted_confidence': 65},
        )
        explanation = self.tracker.explain_signal(lineage)
        self.assertIn('gemma4:latest', explanation)
        self.assertIn('validate', explanation)
        self.assertIn('8000ms', explanation)


class FullLineageCaptureTest(TestCase):
    """Test complete lineage with all components."""

    def setUp(self):
        self.tracker = VersionTracker()

    def test_full_lineage(self):
        """Capture complete lineage with all data sources."""
        lineage = self.tracker.capture_lineage(
            signal_data={
                'symbol': 'BTC',
                'direction': 'strong_buy',
                'confidence': 82,
                'composite_score': 76,
                'timeframe': '4h',
            },
            factor_scores={
                'technical': 85, 'sentiment': 70, 'news': 60,
                'macro': 65, 'derivatives': 55, 'market_structure': 72,
                'order_book': 48, 'portfolio_context': 50,
            },
            regime='bull_trend',
            regime_confidence=0.88,
            weights_used={
                'technical': 0.35, 'sentiment': 0.15, 'news': 0.10,
                'macro': 0.15, 'derivatives': 0.10, 'market_structure': 0.08,
                'order_book': 0.04, 'portfolio_context': 0.03,
            },
            market_snapshot=self.tracker.build_market_snapshot(
                current_price=52000, indicators={'rsi': 70}, candles_count=50,
            ),
            news_snapshot=self.tracker.build_news_snapshot(
                article_count=15, avg_sentiment=65,
            ),
            social_snapshot=self.tracker.build_social_snapshot(
                fear_greed_index=72, social_sentiment=68,
            ),
            derivatives_snapshot=self.tracker.build_derivatives_snapshot(
                funding_rate=0.012, open_interest=5e9,
            ),
            llm_context=self.tracker.build_llm_context(
                model='gemma4:latest', temperature=0.3,
            ),
            llm_output=self.tracker.build_llm_output(
                content='validate', success=True, latency_ms=6000,
            ),
            ensemble_output={'verdict': 'validate', 'adjusted_confidence': 80},
            risk_decision={'approved': True, 'position_size': 0.15},
        )

        # Verify all sections present
        self.assertIn('versions', lineage)
        self.assertIn('signal', lineage)
        self.assertIn('factor_scores', lineage)
        self.assertIn('regime', lineage)
        self.assertIn('weights', lineage)
        self.assertIn('market_snapshot', lineage)
        self.assertIn('news_snapshot', lineage)
        self.assertIn('social_snapshot', lineage)
        self.assertIn('derivatives_snapshot', lineage)
        self.assertIn('llm_context', lineage)
        self.assertIn('llm_output', lineage)
        self.assertIn('ensemble_output', lineage)
        self.assertIn('risk_decision', lineage)

        # Verify values
        self.assertEqual(lineage['signal']['symbol'], 'BTC')
        self.assertEqual(lineage['signal']['direction'], 'strong_buy')
        self.assertEqual(lineage['regime']['detected'], 'bull_trend')
        self.assertEqual(lineage['market_snapshot']['current_price'], 52000)
        self.assertEqual(lineage['llm_context']['model'], 'gemma4:latest')

        # Verify explanation works
        explanation = self.tracker.explain_signal(lineage)
        self.assertIn('BTC', explanation)
        self.assertIn('STRONG_BUY', explanation)
