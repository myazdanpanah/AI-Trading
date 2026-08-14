"""Signal views - Full CRUD + analysis endpoints."""
import logging
from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import (
    Signal, SignalReason, SignalGenerationRequest,
    FactorWeight, RiskProfile, PortfolioPosition,
    SignalPerformance, BacktestResult,
    WalkForwardRun, WalkForwardWindow,
    RiskConfig, RiskEvent, KillSwitchState,
)
from .serializers import (
    SignalSerializer, SignalReasonSerializer,
    SignalGenerationRequestSerializer, FactorWeightSerializer,
    WeightHistorySerializer,
    RiskProfileSerializer, PortfolioPositionSerializer,
    SignalPerformanceSerializer, BacktestResultSerializer,
    WalkForwardRunSerializer, WalkForwardWindowSerializer,
    WalkForwardInputSerializer,
    RiskConfigSerializer, RiskEventSerializer, KillSwitchStateSerializer,
    RiskValidationInputSerializer,
    SignalGenerationInputSerializer, RiskCalculationInputSerializer,
    BacktestInputSerializer,
    AlertRuleSerializer, AlertHistorySerializer,
)
from .models import AlertRule, AlertHistory
from .services import SignalGenerator, RiskManager, PortfolioTracker, SignalBacktester, SignalFusionEngine, RegimeEngine

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(tags=['Signals'], summary='List trading signals'),
    create=extend_schema(tags=['Signals'], summary='Create trading signal'),
    retrieve=extend_schema(tags=['Signals'], summary='Get trading signal'),
    update=extend_schema(tags=['Signals'], summary='Update trading signal'),
    partial_update=extend_schema(tags=['Signals'], summary='Partial update trading signal'),
    destroy=extend_schema(tags=['Signals'], summary='Delete trading signal'),
    generate=extend_schema(tags=['Signals'], summary='Generate a new trading signal using multi-factor scoring'),
    latest=extend_schema(tags=['Signals'], summary='Get latest active signals'),
)
class SignalViewSet(viewsets.ModelViewSet):
    """ViewSet for Signal CRUD and analysis."""
    queryset = Signal.objects.prefetch_related('reasons').all()
    serializer_class = SignalSerializer
    filterset_fields = ['symbol', 'direction', 'is_active', 'timeframe']

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a trading signal using regime-aware 8-factor fusion (Phase 63)."""
        serializer = SignalGenerationInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Convert Decimal values to float for JSON serialization
        def decimal_to_float(obj):
            if isinstance(obj, dict):
                return {k: decimal_to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [decimal_to_float(i) for i in obj]
            elif hasattr(obj, '__float__'):
                return float(obj)
            return obj

        try:
            # ── Initialize engines ───────────────────────────────────
            fusion_engine = SignalFusionEngine()
            regime_engine = RegimeEngine()

            # Fetch live data and run technical analysis
            symbol = data['symbol'].upper()
            technical_data = data.get('technical_data', {})
            sentiment_data = data.get('sentiment_data', {})
            current_price = data.get('current_price')
            historical_candles = []

            try:
                from apps.market.services.unified_data import fetch_market_data
                from apps.technical_analysis.services.indicator_engine import IndicatorEngine

                market = fetch_market_data(symbol)
                closes = market['closes'][-50:]
                highs = market['highs'][-50:]
                lows = market['lows'][-50:]
                volumes = market['volumes'][-50:]
                current_price = current_price or market['current_price']

                # Build candle data for regime detection
                historical_candles = [
                    {'open': c * 0.999, 'high': h, 'low': l, 'close': c, 'volume': v}
                    for c, h, l, v in zip(closes, highs, lows, volumes)
                ]

                # Run indicator engine
                indicators = IndicatorEngine.calculate_all_indicators(
                    [{'close': c, 'high': h, 'low': l, 'volume': v}
                     for c, h, l, v in zip(closes, highs, lows, volumes)]
                )

                # Translate indicator engine output
                rsi_data = indicators.get('rsi_14', {})
                macd_data = indicators.get('macd', {})
                ema9 = indicators.get('ema_9', {})
                ema21 = indicators.get('ema_21', {})
                ema50 = indicators.get('ema_50', {})
                bb_data = indicators.get('bollinger_bands', {})
                atr_data = indicators.get('atr_14', {})
                vwap_data = indicators.get('vwap', {})
                ichimoku_data = indicators.get('ichimoku', {})
                stoch_data = indicators.get('stochastic', {})

                # Determine trend from EMAs
                if ema9.get('signal') == 'bullish' and ema21.get('signal') == 'bullish':
                    trend = 'strong_uptrend'
                elif ema9.get('signal') == 'bullish' or ema50.get('signal') == 'bullish':
                    trend = 'uptrend'
                elif ema9.get('signal') == 'bearish' and ema21.get('signal') == 'bearish':
                    trend = 'strong_downtrend'
                elif ema9.get('signal') == 'bearish' or ema50.get('signal') == 'bearish':
                    trend = 'downtrend'
                else:
                    trend = 'neutral'

                # Determine support/resistance
                bb_lower = bb_data.get('lower', 0)
                bb_upper = bb_data.get('upper', 999999)
                if current_price and current_price <= bb_lower * 1.01:
                    sr_signal = 'near_support'
                elif current_price and current_price >= bb_upper * 0.99:
                    sr_signal = 'near_resistance'
                else:
                    sr_signal = 'neutral'

                # MACD signal string
                macd_trend = macd_data.get('trend', 'neutral')
                if macd_trend == 'bullish' and macd_data.get('histogram', 0) > 0:
                    macd_signal = 'bullish_crossover'
                elif macd_trend == 'bearish' and macd_data.get('histogram', 0) < 0:
                    macd_signal = 'bearish_crossover'
                else:
                    macd_signal = macd_trend

                technical_data = {
                    'rsi': rsi_data.get('value', 50),
                    'macd_signal': macd_signal,
                    'trend': trend,
                    'vwap_signal': vwap_data.get('signal', 'neutral'),
                    'vwap_deviation': vwap_data.get('deviation', 0),
                    'ichimoku_signal': ichimoku_data.get('signal', 'neutral'),
                    'volume_signal': 'high_volume_breakout' if atr_data.get('volatility') == 'high' else 'normal',
                    'sr_signal': sr_signal,
                    'volatility': atr_data.get('percent', 2),
                    'atr': atr_data.get('value', current_price * 0.02 if current_price else 1000),
                    'stochastic_k': stoch_data.get('k', 50),
                    'stochastic_d': stoch_data.get('d', 50),
                }

                # Try to fetch sentiment data
                try:
                    from apps.journal.services.journal_writer import fetch_fear_greed_index
                    fg = fetch_fear_greed_index()
                    sentiment_data = {
                        'fear_greed_index': fg.get('value', 50),
                        'social_sentiment': 50,
                    }
                except Exception:
                    sentiment_data = {'fear_greed_index': 50, 'social_sentiment': 50}

            except Exception as data_err:
                logger.warning(f"Failed to fetch live data for signal: {data_err}")
                current_price = current_price or 0

            # ── Detect market regime ─────────────────────────────────
            regime_state = regime_engine.detect_regime(historical_candles)
            regime = regime_state.regime
            regime_weights = regime_state.weights

            # ── Calculate factor scores ──────────────────────────────
            # Use old SignalGenerator to get individual scores
            old_generator = SignalGenerator()
            try:
                factor_weights = FactorWeight.objects.filter(is_active=True)
                if factor_weights.exists():
                    old_generator.load_weights(factor_weights)
            except Exception:
                pass

            old_result = old_generator.generate_signal(
                symbol=symbol, timeframe=data['timeframe'],
                technical_data=technical_data, sentiment_data=sentiment_data,
                news_data=data.get('news_data', {}),
                ai_data=data.get('ai_data', {}),
                macro_data=data.get('macro_data', {}),
                current_price=current_price,
            )

            # Extract scores for fusion engine (8 factors)
            factor_scores = old_result.get('factor_scores', {})

            # ── Fuse signal with regime-conditioned weights ──────────
            result = fusion_engine.fuse_signal(
                symbol=symbol,
                timeframe=data['timeframe'],
                technical_score=factor_scores.get('technical', 50),
                sentiment_score=factor_scores.get('sentiment', 50),
                news_score=factor_scores.get('news', 50),
                macro_score=factor_scores.get('macro', 50),
                derivatives_score=50,  # Default — would be fetched from DerivativesCollector
                market_structure_score=50,  # Default — would be fetched from market structure
                order_book_score=50,  # Default — would be fetched from order book
                portfolio_context_score=50,  # Default — would be fetched from portfolio intelligence
                regime=regime,
                regime_weights=regime_weights,
                current_price=float(current_price) if current_price else 0,
            )

            # Add entry levels from old generator
            result['entry_price'] = old_result.get('entry_price')
            result['stop_loss'] = old_result.get('stop_loss')
            result['take_profit'] = old_result.get('take_profit', [])
            result['risk_score'] = old_result.get('risk_score', 50)
            result['reasons'] = old_result.get('reasons', [])

            # ── AI Validation via Agent Ensemble (Phase 65) ─────────
            ensemble_result = None
            try:
                from apps.ai_engine.services.agent_ensemble import AgentEnsemble
                from apps.ai_engine.services.llm_router import AIConfig, AIMode
                import asyncio

                # Get AI mode from settings
                ai_mode = getattr(__import__('django.conf', fromlist=['settings']).settings, 'AI_MODE', 'off')
                ollama_url = getattr(__import__('django.conf', fromlist=['settings']).settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')

                if ai_mode != 'off':
                    ai_config = AIConfig(
                        mode=AIMode(ai_mode) if ai_mode in ['off', 'lite', 'standard', 'cloud'] else AIMode.STANDARD,
                        base_url=ollama_url,
                        timeout=50000,
                    )
                    ensemble = AgentEnsemble(config=ai_config)

                    # Build full signal context for ensemble
                    signal_context = {
                        'symbol': symbol,
                        'current_price': float(current_price) if current_price else 0,
                        'quant_composite_score': result.get('quant_composite_score', 50),
                        'direction': result.get('direction', 'hold'),
                        'confidence': result.get('confidence', 50),
                        'regime': regime,
                        'technical_score': factor_scores.get('technical', 50),
                        'sentiment_score': factor_scores.get('sentiment', 50),
                        'news_score': factor_scores.get('news', 50),
                        'macro_score': factor_scores.get('macro', 50),
                        'derivatives_score': 50,
                        'rsi': technical_data.get('rsi', 50),
                        'macd_signal': technical_data.get('macd_signal', 'neutral'),
                        'trend': technical_data.get('trend', 'neutral'),
                        'volatility': technical_data.get('volatility', 2),
                        'fear_greed_index': sentiment_data.get('fear_greed_index', 50),
                        'social_sentiment': sentiment_data.get('social_sentiment', 50),
                    }

                    # Run ensemble (all 5 agents in sequence)
                    loop = asyncio.new_event_loop()
                    ensemble_result = loop.run_until_complete(
                        ensemble.run(signal_ctx=signal_context)
                    )
                    loop.close()

                    # Apply ensemble verdict to result
                    if ensemble_result.verdict == 'validate':
                        result['ai_validated'] = True
                        result['confidence'] = ensemble_result.adjusted_confidence
                        result['ai_risks'] = ensemble_result.risks
                        result['ai_reasons'] = ensemble_result.reasons
                    elif ensemble_result.verdict == 'reject':
                        result['direction'] = 'hold'
                        result['confidence'] = max(10, result['confidence'] - 20)
                        result['ai_validated'] = False
                        result['ai_risks'] = ensemble_result.risks or ['Ensemble rejected signal']
                    elif ensemble_result.verdict == 'modify':
                        result['confidence'] = ensemble_result.adjusted_confidence
                        result['ai_risks'] = ensemble_result.risks
                        result['ai_reasons'] = ensemble_result.reasons

                    result['ensemble_result'] = ensemble_result.to_dict()

                    logger.info(
                        f"Ensemble: {ensemble_result.verdict} | "
                        f"Agents: {ensemble_result.agents_succeeded}/5 | "
                        f"Latency: {ensemble_result.total_latency_ms}ms"
                    )
            except Exception as ai_err:
                logger.warning(f"Agent ensemble failed (continuing with quant-only): {ai_err}")

            # ── Save to database ─────────────────────────────────────
            signal = None
            try:
                with transaction.atomic():
                    entry_price_val = result.get('entry_price')
                    stop_loss_val = result.get('stop_loss')
                    entry_price_float = float(entry_price_val) if entry_price_val else 0.0
                    stop_loss_float = float(stop_loss_val) if stop_loss_val else entry_price_float * 0.97

                    signal = Signal.objects.create(
                        symbol=result['symbol'],
                        direction=result['direction'],
                        confidence=result['confidence'],
                        risk_score=result.get('risk_score', 50),
                        entry_price=entry_price_float,
                        stop_loss=stop_loss_float,
                        take_profit=result.get('take_profit', []),
                        timeframe=result['timeframe'],
                        technical_score=result['factor_scores'].get('technical', 0),
                        sentiment_score=result['factor_scores'].get('sentiment', 0),
                        news_score=result['factor_scores'].get('news', 0),
                        ai_score=0,  # AI is post-fusion, not pre-fusion
                        macro_score=result['factor_scores'].get('macro', 0),
                        composite_score=result['composite_score'],
                        is_active=True,
                    )

                    # Create signal reasons
                    for reason in result.get('reasons', []):
                        SignalReason.objects.create(
                            signal=signal,
                            reason_type=reason.get('type', 'technical'),
                            description=reason.get('description', ''),
                            confidence=reason.get('confidence', 50),
                        )

                    # Create generation request record
                    SignalGenerationRequest.objects.create(
                        symbol=result['symbol'],
                        timeframe=result['timeframe'],
                        input_data=decimal_to_float({**data, 'ensemble_result': ensemble_result.to_dict()} if ensemble_result else data),
                        weights_used=result.get('weights_used', {}),
                        status='completed',
                    )
            except Exception as db_err:
                logger.warning(f"DB save failed (returning result anyway): {db_err}")

            serializable_result = decimal_to_float(result)

            # Build response
            if signal:
                signal_data = SignalSerializer(signal).data
            else:
                signal_data = {
                    'id': f"gen-{result['symbol']}-{result['timeframe']}",
                    'symbol': result['symbol'],
                    'direction': result['direction'],
                    'confidence': result['confidence'],
                    'risk_score': result.get('risk_score', 50),
                    'entry_price': result.get('entry_price', 0),
                    'stop_loss': result.get('stop_loss', 0),
                    'take_profit': result.get('take_profit', []),
                    'timeframe': result['timeframe'],
                    'technical_score': result['factor_scores'].get('technical', 0),
                    'sentiment_score': result['factor_scores'].get('sentiment', 0),
                    'news_score': result['factor_scores'].get('news', 0),
                    'ai_score': 0,
                    'macro_score': result['factor_scores'].get('macro', 0),
                    'composite_score': result['composite_score'],
                    'reasons': result.get('reasons', []),
                    'created_at': result['generated_at'],
                    'is_active': True,
                }

            # Add ensemble results to response
            if ensemble_result:
                serializable_result['agent_ensemble'] = ensemble_result.to_dict()

            return Response({
                'signal': signal_data,
                'details': serializable_result,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Signal generation failed: {e}", exc_info=True)
            return Response(
                {'error': f'An error occurred during signal generation: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest signals, optionally filtered by symbol."""
        symbol = request.query_params.get('symbol')
        queryset = self.queryset.filter(is_active=True)

        if symbol:
            queryset = queryset.filter(symbol=symbol)

        signals = queryset[:20]
        return Response(SignalSerializer(signals, many=True).data)

    @action(detail=False, methods=['post'])
    def evaluate(self, request):
        """Evaluate pending signals and record outcomes for the feedback loop."""
        try:
            from .services.signal_evaluator import SignalEvaluator
            min_age = int(request.data.get('min_age_hours', 4))
            results = SignalEvaluator.evaluate_pending_signals(min_age_hours=min_age)
            return Response(results, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Signal evaluation failed: {e}")
            return Response(
                {'error': f'Evaluation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def calibration(self, request):
        """Get calibration analysis for signal confidence.

        Returns Brier Score, ECE, reliability curve, and per-group breakdowns.
        Use ?symbol=BTC to filter by symbol.
        Use ?limit=500 to control sample size.
        Use ?predictions=[(80,true),(60,false),...] for custom analysis.
        """
        try:
            from .services.calibration import CalibrationEngine, ProbabilityAdjuster

            symbol = request.query_params.get('symbol')
            limit = int(request.query_params.get('limit', 500))

            # Custom predictions from request
            custom_predictions = request.query_params.get('predictions')

            engine = CalibrationEngine()

            if custom_predictions:
                import json
                try:
                    preds = json.loads(custom_predictions)
                    predictions = [(float(p), bool(o)) for p, o in preds]
                    result = engine.calibrate(predictions)
                except (json.JSONDecodeError, ValueError) as e:
                    return Response(
                        {'error': f'Invalid predictions format: {str(e)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                result = engine.calibrate_from_database(symbol=symbol, limit=limit)

            return Response(result.to_dict())

        except Exception as e:
            logger.error(f"Calibration analysis failed: {e}")
            return Response(
                {'error': f'Calibration failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def adjust_confidence(self, request):
        """Adjust a raw confidence score using the calibration curve.

        POST {"confidence": 80, "symbol": "BTC"}
        """
        try:
            from .services.calibration import CalibrationEngine, ProbabilityAdjuster

            confidence = request.data.get('confidence', 50)
            symbol = request.data.get('symbol')

            # Get calibration data
            cal_engine = CalibrationEngine()
            cal_result = cal_engine.calibrate_from_database(symbol=symbol)

            # Adjust confidence
            adjusted = ProbabilityAdjuster.adjust_confidence(
                confidence, cal_result.reliability_curve
            )

            return Response({
                'raw_confidence': confidence,
                'adjusted_confidence': round(adjusted, 2),
                'calibration_quality': cal_result.calibration_quality,
                'ece': cal_result.ece,
                'brier_score': cal_result.brier_score,
            })

        except Exception as e:
            logger.error(f"Confidence adjustment failed: {e}")
            return Response(
                {'error': f'Adjustment failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def lineage(self, request, pk=None):
        """Get full data lineage for a signal.

        Returns version info, data snapshots, LLM context, and human-readable explanation.
        """
        try:
            from .models import SignalLineage
            from .services.versioning import VersionTracker

            signal = self.get_object()
            lineage = SignalLineage.objects.filter(signal=signal).first()

            if not lineage:
                return Response({
                    'signal_id': str(signal.id),
                    'lineage': None,
                    'message': 'No lineage data recorded for this signal',
                })

            # Generate human-readable explanation
            tracker = VersionTracker()
            explanation = tracker.explain_signal(lineage.data_lineage)

            return Response({
                'signal_id': str(signal.id),
                'lineage': {
                    'strategy_version': lineage.strategy_version,
                    'feature_version': lineage.feature_version,
                    'model_version': lineage.model_version,
                    'prompt_version': lineage.prompt_version,
                    'ensemble_version': lineage.ensemble_version,
                    'risk_version': lineage.risk_version,
                    'regime': lineage.regime,
                    'regime_confidence': lineage.regime_confidence,
                    'weights_snapshot': lineage.weights_snapshot,
                    'factor_scores': lineage.factor_scores,
                    'market_snapshot': lineage.market_snapshot,
                    'news_snapshot': lineage.news_snapshot,
                    'social_snapshot': lineage.social_snapshot,
                    'derivatives_snapshot': lineage.derivatives_snapshot,
                    'llm_context': lineage.llm_context,
                    'llm_output': lineage.llm_output,
                    'ensemble_output': lineage.ensemble_output,
                    'risk_decision': lineage.risk_decision,
                    'created_at': lineage.created_at.isoformat(),
                },
                'explanation': explanation,
            })

        except Exception as e:
            logger.error(f"Lineage retrieval failed: {e}")
            return Response(
                {'error': f'Lineage retrieval failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def versions(self, request):
        """Get current system versions."""
        from .services.versioning import SYSTEM_VERSIONS
        return Response(SYSTEM_VERSIONS)

    # ── Paper Trading Endpoints ──────────────────────────────────────

    @action(detail=False, methods=['get'])
    def paper_status(self, request):
        """Get paper trading account status."""
        try:
            from .services.paper_trading import PaperTradingEngine
            engine = PaperTradingEngine()
            return Response(engine.get_status())
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def paper_open(self, request):
        """Open a paper position.

        POST {
            "symbol": "BTCUSDT",
            "side": "long",
            "entry_price": 50000,
            "stop_loss": 49000,
            "take_profit": 52000,
            "signal_confidence": 75,
            "signal_id": "..."
        }
        """
        try:
            from .services.paper_trading import PaperTradingEngine

            data = request.data
            required = ['symbol', 'side', 'entry_price']
            for field in required:
                if field not in data:
                    return Response(
                        {'error': f'Missing required field: {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            engine = PaperTradingEngine()
            result = engine.open_position(
                symbol=data['symbol'],
                side=data['side'],
                entry_price=float(data['entry_price']),
                quantity=float(data['quantity']) if 'quantity' in data else None,
                stop_loss=float(data['stop_loss']) if 'stop_loss' in data else None,
                take_profit=float(data['take_profit']) if 'take_profit' in data else None,
                signal_confidence=int(data.get('signal_confidence', 50)),
                signal_id=data.get('signal_id'),
            )

            status_code = status.HTTP_201_CREATED if result['success'] else status.HTTP_400_BAD_REQUEST
            return Response(result, status=status_code)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def paper_close(self, request):
        """Close a paper position.

        POST {"position_id": "PAPER-000001", "exit_price": 51000, "reason": "manual"}
        """
        try:
            from .services.paper_trading import PaperTradingEngine

            data = request.data
            position_id = data.get('position_id')
            exit_price = data.get('exit_price')
            reason = data.get('reason', 'manual')

            if not position_id or exit_price is None:
                return Response(
                    {'error': 'position_id and exit_price are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            engine = PaperTradingEngine()
            result = engine.close_position(position_id, float(exit_price), reason)

            status_code = status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST
            return Response(result, status=status_code)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def paper_update_prices(self, request):
        """Update prices for all paper positions.

        POST {"prices": {"BTCUSDT": 51000, "ETHUSDT": 3200}}
        """
        try:
            from .services.paper_trading import PaperTradingEngine

            prices = request.data.get('prices', {})
            engine = PaperTradingEngine()
            result = engine.update_prices(prices)
            return Response(result)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def paper_performance(self, request):
        """Get paper trading performance metrics."""
        try:
            from .services.paper_trading import PaperTradingEngine
            engine = PaperTradingEngine()
            return Response(engine.get_performance_metrics())
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def paper_reset(self, request):
        """Reset paper trading account."""
        try:
            from .services.paper_trading import PaperTradingEngine
            initial = float(request.data.get('initial_capital', 10000))
            engine = PaperTradingEngine(initial_capital=initial)
            return Response(engine.get_status())
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ── Shadow Trading Endpoints ─────────────────────────────────────

    @action(detail=False, methods=['get'])
    def shadow_status(self, request):
        """Get shadow trading account status."""
        try:
            from .services.shadow_trading import ShadowTradingEngine
            engine = ShadowTradingEngine()
            return Response(engine.get_status())
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def shadow_signal(self, request):
        """Record a shadow trade from a signal.

        POST {
            "symbol": "BTCUSDT",
            "side": "long",
            "signal_confidence": 75,
            "expected_entry": 50000,
            "expected_exit": 52000,
            "current_price": 50100,
            "spread_bps": 5
        }
        """
        try:
            from .services.shadow_trading import ShadowTradingEngine

            data = request.data
            required = ['symbol', 'side', 'signal_confidence', 'expected_entry']
            for field in required:
                if field not in data:
                    return Response(
                        {'error': f'Missing required field: {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            engine = ShadowTradingEngine()
            result = engine.shadow_signal(
                symbol=data['symbol'],
                side=data['side'],
                signal_confidence=int(data['signal_confidence']),
                expected_entry=float(data['expected_entry']),
                expected_exit=float(data['expected_exit']) if 'expected_exit' in data else None,
                signal_id=data.get('signal_id'),
                current_price=float(data['current_price']) if 'current_price' in data else None,
                spread_bps=float(data.get('spread_bps', 5.0)),
            )

            return Response(result, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def shadow_quality(self, request):
        """Get shadow trading execution quality report."""
        try:
            from .services.shadow_trading import ShadowTradingEngine
            engine = ShadowTradingEngine()
            return Response(engine.get_execution_quality_report())
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ── Live Execution Endpoints ────────────────────────────────────

    @action(detail=False, methods=['get'])
    def live_status(self, request):
        """Get live execution account status."""
        try:
            from .services.live_execution import LiveExecutionEngine, LIVE_TRADING_ENABLED
            engine = LiveExecutionEngine()
            status_data = engine.get_status()
            status_data['live_trading_enabled'] = LIVE_TRADING_ENABLED
            return Response(status_data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def live_order(self, request):
        """Place a live order (requires Risk Engine approval).

        POST {
            "symbol": "BTCUSDT",
            "side": "buy",
            "type": "market",
            "quantity": 0.001,
            "risk_approved": true
        }
        """
        try:
            from .services.live_execution import LiveExecutionEngine

            data = request.data
            required = ['symbol', 'side', 'type', 'quantity']
            for field in required:
                if field not in data:
                    return Response(
                        {'error': f'Missing required field: {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            engine = LiveExecutionEngine(
                exchange=data.get('exchange', 'binance'),
                testnet=data.get('testnet', True),
            )

            import asyncio
            result = asyncio.run(engine.place_order(
                symbol=data['symbol'],
                side=data['side'],
                order_type=data['type'],
                quantity=float(data['quantity']),
                price=float(data['price']) if 'price' in data else None,
                stop_price=float(data['stop_price']) if 'stop_price' in data else None,
                signal_id=data.get('signal_id'),
                risk_approved=data.get('risk_approved', False),
            ))

            status_code = status.HTTP_201_CREATED if result['success'] else status.HTTP_400_BAD_REQUEST
            return Response(result, status=status_code)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def live_cancel(self, request):
        """Cancel a live order."""
        try:
            from .services.live_execution import LiveExecutionEngine

            order_id = request.data.get('order_id')
            if not order_id:
                return Response(
                    {'error': 'order_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            engine = LiveExecutionEngine()
            import asyncio
            result = asyncio.run(engine.cancel_order(order_id))
            return Response(result)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def live_open_orders(self, request):
        """Get all open live orders."""
        try:
            from .services.live_execution import LiveExecutionEngine
            symbol = request.query_params.get('symbol')
            engine = LiveExecutionEngine()
            import asyncio
            orders = asyncio.run(engine.get_open_orders(symbol=symbol))
            return Response({'orders': orders, 'count': len(orders)})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema_view(
    list=extend_schema(tags=['Signals'], summary='List signal reasons'),
    create=extend_schema(tags=['Signals'], summary='Create signal reason'),
    retrieve=extend_schema(tags=['Signals'], summary='Get signal reason'),
    update=extend_schema(tags=['Signals'], summary='Update signal reason'),
    partial_update=extend_schema(tags=['Signals'], summary='Partial update signal reason'),
    destroy=extend_schema(tags=['Signals'], summary='Delete signal reason'),
)
class SignalReasonViewSet(viewsets.ModelViewSet):
    """ViewSet for SignalReason CRUD."""
    queryset = SignalReason.objects.all()
    serializer_class = SignalReasonSerializer


@extend_schema_view(
    list=extend_schema(tags=['Signals'], summary='List factor weights'),
    create=extend_schema(tags=['Signals'], summary='Create factor weight'),
    retrieve=extend_schema(tags=['Signals'], summary='Get factor weight'),
    update=extend_schema(tags=['Signals'], summary='Update factor weight'),
    partial_update=extend_schema(tags=['Signals'], summary='Partial update factor weight'),
    destroy=extend_schema(tags=['Signals'], summary='Delete factor weight'),
)
class FactorWeightViewSet(viewsets.ModelViewSet):
    """ViewSet for FactorWeight CRUD and auto-adjustment."""
    queryset = FactorWeight.objects.all()
    serializer_class = FactorWeightSerializer

    @action(detail=False, methods=['post'])
    def adjust(self, request):
        """Automatically adjust weights based on signal performance."""
        try:
            from .services.weight_adjuster import WeightAdjuster
            lookback_days = int(request.data.get('lookback_days', 30))
            result = WeightAdjuster.adjust_weights(lookback_days=lookback_days)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Weight adjustment failed: {e}")
            return Response(
                {'error': f'Adjustment failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def reset(self, request):
        """Reset weights to defaults."""
        try:
            from .services.weight_adjuster import WeightAdjuster
            result = WeightAdjuster.reset_weights()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Reset failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current weights with performance data."""
        try:
            from .services.weight_adjuster import WeightAdjuster
            result = WeightAdjuster.get_current_weights()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema_view(
    list=extend_schema(tags=['Signals'], summary='List risk profiles'),
    create=extend_schema(tags=['Signals'], summary='Create risk profile'),
    retrieve=extend_schema(tags=['Signals'], summary='Get risk profile'),
    update=extend_schema(tags=['Signals'], summary='Update risk profile'),
    partial_update=extend_schema(tags=['Signals'], summary='Partial update risk profile'),
    destroy=extend_schema(tags=['Signals'], summary='Delete risk profile'),
)
class WeightHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for WeightHistory - read only, created by weight adjuster."""
    from .models import WeightHistory
    queryset = WeightHistory.objects.all()[:100]
    serializer_class = WeightHistorySerializer


class RiskProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for RiskProfile CRUD."""
    queryset = RiskProfile.objects.all()
    serializer_class = RiskProfileSerializer


@extend_schema_view(
    list=extend_schema(tags=['Signals'], summary='List portfolio positions'),
    create=extend_schema(tags=['Signals'], summary='Create portfolio position'),
    retrieve=extend_schema(tags=['Signals'], summary='Get portfolio position'),
    update=extend_schema(tags=['Signals'], summary='Update portfolio position'),
    partial_update=extend_schema(tags=['Signals'], summary='Partial update portfolio position'),
    destroy=extend_schema(tags=['Signals'], summary='Delete portfolio position'),
    calculate_risk=extend_schema(tags=['Signals'], summary='Calculate risk metrics for a potential position'),
    summary=extend_schema(tags=['Signals'], summary='Get portfolio summary'),
)
class PortfolioPositionViewSet(viewsets.ModelViewSet):
    """ViewSet for PortfolioPosition CRUD."""
    queryset = PortfolioPosition.objects.all()
    serializer_class = PortfolioPositionSerializer
    filterset_fields = ['symbol', 'side', 'is_active']

    @action(detail=False, methods=['post'])
    def calculate_risk(self, request):
        """Calculate risk metrics for a potential position."""
        serializer = RiskCalculationInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            # Get active risk profile
            risk_profile = RiskProfile.objects.filter(is_active=True).first()
            risk_manager = RiskManager(risk_profile)

            # Get current positions
            current_positions = PortfolioPosition.objects.filter(
                is_active=True
            ).values('symbol', 'quantity', 'current_price', 'risk_amount', 'side')

            result = risk_manager.calculate_position_size(
                account_balance=data['account_balance'],
                entry_price=data['entry_price'],
                stop_loss=data['stop_loss'],
                signal_confidence=data['signal_confidence'],
                signal_direction=data['signal_direction'],
                current_positions=list(current_positions),
            )

            # Portfolio risk assessment
            portfolio_risk = risk_manager.assess_portfolio_risk(
                account_balance=data['account_balance'],
                current_positions=list(current_positions),
            )

            return Response({
                'position_sizing': result,
                'portfolio_risk': portfolio_risk,
            })

        except Exception as e:
            logger.error(f"Risk calculation failed: {e}")
            return Response(
                {'error': 'An error occurred during risk calculation. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get portfolio summary."""
        try:
            account_balance = request.query_params.get('account_balance', 10000)
            tracker = PortfolioTracker(initial_capital=account_balance)

            positions = PortfolioPosition.objects.filter(
                is_active=True
            ).values()

            result = tracker.generate_portfolio_summary(
                positions=list(positions),
                account_balance=account_balance,
            )

            return Response(result)

        except Exception as e:
            logger.error(f"Portfolio summary failed: {e}")
            return Response(
                {'error': 'An error occurred generating portfolio summary.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema_view(
    list=extend_schema(tags=['Signals'], summary='List signal performance records'),
    create=extend_schema(tags=['Signals'], summary='Create signal performance record'),
    retrieve=extend_schema(tags=['Signals'], summary='Get signal performance record'),
    update=extend_schema(tags=['Signals'], summary='Update signal performance record'),
    partial_update=extend_schema(tags=['Signals'], summary='Partial update signal performance record'),
    destroy=extend_schema(tags=['Signals'], summary='Delete signal performance record'),
)
class SignalPerformanceViewSet(viewsets.ModelViewSet):
    """ViewSet for SignalPerformance CRUD."""
    queryset = SignalPerformance.objects.all()
    serializer_class = SignalPerformanceSerializer


@extend_schema_view(
    list=extend_schema(tags=['Signals'], summary='List backtest results'),
    create=extend_schema(tags=['Signals'], summary='Create backtest result'),
    retrieve=extend_schema(tags=['Signals'], summary='Get backtest result'),
    update=extend_schema(tags=['Signals'], summary='Update backtest result'),
    partial_update=extend_schema(tags=['Signals'], summary='Partial update backtest result'),
    destroy=extend_schema(tags=['Signals'], summary='Delete backtest result'),
    run=extend_schema(tags=['Signals'], summary='Run a backtest'),
)
class WalkForwardResultViewSet(viewsets.ModelViewSet):
    """ViewSet for WalkForwardRun CRUD and walk-forward validation."""
    queryset = WalkForwardRun.objects.all()
    serializer_class = WalkForwardRunSerializer

    @action(detail=False, methods=['post'])
    def run(self, request):
        """Run a walk-forward validation."""
        serializer = WalkForwardInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            import asyncio
            from decimal import Decimal
            from .services.walk_forward import WalkForwardEngine
            from .services.backtester import HistoricalDataFetcher

            engine = WalkForwardEngine(
                initial_capital=data.get('initial_capital', 10000),
                fee_rate=data.get('fee_rate', Decimal('0.001')),
                slippage_rate=data.get('slippage_rate', Decimal('0.0005')),
            )

            # Fetch historical data
            # Map symbol to CoinGecko id
            symbol_map = {
                'BTC/USDT': 'bitcoin', 'ETH/USDT': 'ethereum',
                'SOL/USDT': 'solana', 'BNB/USDT': 'binancecoin',
                'XRP/USDT': 'ripple', 'ADA/USDT': 'cardano',
            }
            coin_id = symbol_map.get(data['symbol'].upper(), 'bitcoin')

            days_needed = (data['end_date'] - data['start_date']).days
            loop = asyncio.new_event_loop()
            historical_data = loop.run_until_complete(
                HistoricalDataFetcher.fetch_candles(coin_id, data['timeframe'], days_needed)
            )
            loop.close()

            if not historical_data:
                return Response(
                    {'error': 'Failed to fetch historical data'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Capture current weights
            weight_snapshot = {}
            try:
                for fw in FactorWeight.objects.filter(is_active=True):
                    weight_snapshot[fw.name] = float(fw.weight)
            except Exception:
                pass

            # Create run record
            run_record = WalkForwardRun.objects.create(
                strategy_name=data['strategy_name'],
                strategy_version=data.get('strategy_version', '1.0'),
                symbol=data['symbol'],
                timeframe=data['timeframe'],
                train_days=data.get('train_days', 90),
                validate_days=data.get('validate_days', 30),
                test_days=data.get('test_days', 30),
                step_days=data.get('step_days', 30),
                start_date=data['start_date'],
                end_date=data['end_date'],
                initial_capital=data.get('initial_capital', 10000),
                fee_rate=data.get('fee_rate', Decimal('0.001')),
                slippage_rate=data.get('slippage_rate', Decimal('0.0005')),
                weight_snapshot=weight_snapshot,
                status='running',
                started_at=datetime.now(),
            )

            # Run walk-forward
            result = engine.run_walk_forward(
                strategy_name=data['strategy_name'],
                symbol=data['symbol'],
                timeframe=data['timeframe'],
                start_date=data['start_date'],
                end_date=data['end_date'],
                historical_data=historical_data,
                train_days=data.get('train_days', 90),
                validate_days=data.get('validate_days', 30),
                test_days=data.get('test_days', 30),
                step_days=data.get('step_days', 30),
                strategy_version=data.get('strategy_version', '1.0'),
                weight_snapshot=weight_snapshot,
            )

            # Update run record
            run_record.status = result.get('status', 'completed')
            run_record.total_windows = result.get('total_windows', 0)
            run_record.avg_oos_return = result.get('avg_oos_return', 0)
            run_record.avg_oos_sharpe = result.get('avg_oos_sharpe', 0)
            run_record.avg_oos_win_rate = result.get('avg_oos_win_rate', 0)
            run_record.oos_vs_is_ratio = result.get('oos_vs_is_ratio', 0)
            run_record.max_oos_drawdown = result.get('max_oos_drawdown', 0)
            run_record.leakage_detected = result.get('leakage_detected', False)
            run_record.leakage_details = result.get('leakage_details', {})
            run_record.completed_at = datetime.now()
            run_record.save()

            # Save individual windows
            for w in result.get('windows', []):
                WalkForwardWindow.objects.create(
                    run=run_record,
                    window_index=w['window_index'],
                    train_start=w['train_start'],
                    train_end=w['train_end'],
                    validate_start=w['validate_start'],
                    validate_end=w['validate_end'],
                    test_start=w['test_start'],
                    test_end=w['test_end'],
                    is_return_percent=w.get('is_return_percent', 0),
                    is_sharpe=w.get('is_sharpe', 0),
                    is_win_rate=w.get('is_win_rate', 0),
                    is_trades=w.get('is_trades', 0),
                    is_max_drawdown=w.get('is_max_drawdown', 0),
                    oos_return_percent=w.get('oos_return_percent', 0),
                    oos_sharpe=w.get('oos_sharpe', 0),
                    oos_win_rate=w.get('oos_win_rate', 0),
                    oos_trades=w.get('oos_trades', 0),
                    oos_max_drawdown=w.get('oos_max_drawdown', 0),
                    frozen_weights=w.get('frozen_weights', {}),
                    is_equity_curve=w.get('is_equity_curve', []),
                    oos_equity_curve=w.get('oos_equity_curve', []),
                    has_leakage=w.get('has_leakage', False),
                    leakage_reason=w.get('leakage_reason', ''),
                )

            return Response(
                WalkForwardRunSerializer(run_record).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Walk-forward failed: {e}")
            # Update run record if it exists
            if 'run_record' in locals():
                run_record.status = 'failed'
                run_record.error_message = str(e)
                run_record.completed_at = datetime.now()
                run_record.save()
            return Response(
                {'error': f'Walk-forward failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def windows(self, request, pk=None):
        """Get all windows for a walk-forward run."""
        run = self.get_object()
        windows = WalkForwardWindow.objects.filter(run=run)
        return Response(WalkForwardWindowSerializer(windows, many=True).data)

    @action(detail=True, methods=['get'])
    def compare(self, request, pk=None):
        """Compare IS vs OOS performance for a walk-forward run."""
        from .services.walk_forward import WalkForwardEngine
        run = self.get_object()
        windows = WalkForwardWindow.objects.filter(run=run).values()
        window_list = list(windows)
        engine = WalkForwardEngine()
        comparison = engine.compare_windows(window_list)
        return Response(comparison)


@extend_schema_view(
    list=extend_schema(tags=['Signals'], summary='List alert rules'),
    create=extend_schema(tags=['Signals'], summary='Create alert rule'),
    retrieve=extend_schema(tags=['Signals'], summary='Get alert rule'),
    update=extend_schema(tags=['Signals'], summary='Update alert rule'),
    partial_update=extend_schema(tags=['Signals'], summary='Partial update alert rule'),
    destroy=extend_schema(tags=['Signals'], summary='Delete alert rule'),
    run=extend_schema(tags=['Signals'], summary='Run a backtest'),
)
class RiskEngineViewSet(viewsets.ViewSet):
    """ViewSet for the independent Risk Engine — the safety gate."""

    @action(detail=False, methods=['post'])
    def validate_signal(self, request):
        """Validate a signal through the Risk Engine (Signal → Risk → Execution)."""
        serializer = RiskValidationInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            from decimal import Decimal
            from .services.risk_engine import RiskEngine

            # Get active risk config
            config = RiskConfig.objects.filter(is_active=True).first()
            engine = RiskEngine(config=config)

            # Get current positions
            positions = list(PortfolioPosition.objects.filter(
                is_active=True
            ).values('symbol', 'quantity', 'current_price', 'risk_amount', 'side', 'is_active'))

            # Validate signal
            decision = engine.validate_signal(
                signal={
                    'symbol': data['symbol'],
                    'direction': data['direction'],
                    'entry_price': data['entry_price'],
                    'stop_loss': data['stop_loss'],
                    'confidence': data.get('confidence', 50),
                },
                account_balance=data['account_balance'],
                current_positions=positions,
                current_prices={},
            )

            # Log risk event
            RiskEvent.objects.create(
                risk_config=config,
                event_type='signal_approved' if decision.approved else 'signal_rejected',
                symbol=data['symbol'],
                decision='approved' if decision.approved else 'rejected',
                reason=decision.reason,
                risk_data={
                    'position_size': decision.position_size,
                    'risk_amount': decision.risk_amount,
                    'risk_percent': decision.risk_percent,
                    'modified': decision.modified,
                },
                portfolio_exposure_pct=decision.risk_state.get('exposure_pct', 0),
                portfolio_risk_pct=decision.risk_state.get('risk_pct', 0),
                active_positions=decision.risk_state.get('active_positions', 0),
            )

            return Response({
                'approved': decision.approved,
                'modified': decision.modified,
                'reason': decision.reason,
                'position_size': decision.position_size,
                'risk_amount': decision.risk_amount,
                'risk_percent': decision.risk_percent,
                'kill_switch_active': decision.kill_switch_active,
                'risk_state': decision.risk_state,
            })

        except Exception as e:
            logger.error(f"Risk validation failed: {e}")
            return Response(
                {'error': f'Risk validation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get current risk engine status and portfolio risk state."""
        try:
            from decimal import Decimal
            from .services.risk_engine import RiskEngine

            config = RiskConfig.objects.filter(is_active=True).first()
            engine = RiskEngine(config=config)

            account_balance = Decimal(str(request.query_params.get('balance', 10000)))
            positions = list(PortfolioPosition.objects.filter(
                is_active=True
            ).values('symbol', 'quantity', 'current_price', 'risk_amount', 'side', 'is_active'))

            risk_state = engine.get_portfolio_risk_state(
                account_balance=account_balance,
                current_positions=positions,
            )

            return Response(risk_state)

        except Exception as e:
            logger.error(f"Risk status failed: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def kill_switch(self, request):
        """Get kill switch state."""
        state = KillSwitchState.objects.order_by('-created_at').first()
        if state:
            return Response(KillSwitchStateSerializer(state).data)
        return Response({'is_active': False, 'reason': 'No kill switch events'})

    @action(detail=False, methods=['post'])
    def activate_kill_switch(self, request):
        """Manually activate kill switch."""
        reason = request.data.get('reason', 'Manual activation')

        state = KillSwitchState.objects.create(
            is_active=True,
            triggered_by=reason,
            triggered_at=datetime.now(),
        )

        # Also log a risk event
        RiskEvent.objects.create(
            event_type='kill_switch_activated',
            decision='rejected',
            reason=reason,
        )

        return Response(KillSwitchStateSerializer(state).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def deactivate_kill_switch(self, request):
        """Deactivate kill switch."""
        reason = request.data.get('reason', 'Manual deactivation')
        state = KillSwitchState.objects.order_by('-created_at').first()

        if state and state.is_active:
            state.is_active = False
            state.deactivated_at = datetime.now()
            state.deactivation_reason = reason
            state.save()

            RiskEvent.objects.create(
                event_type='kill_switch_deactivated',
                decision='approved',
                reason=reason,
            )

            return Response(KillSwitchStateSerializer(state).data)

        return Response({'message': 'Kill switch was not active'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def events(self, request):
        """Get recent risk events."""
        limit = int(request.query_params.get('limit', 50))
        event_type = request.query_params.get('type')

        qs = RiskEvent.objects.all()
        if event_type:
            qs = qs.filter(event_type=event_type)

        events = qs[:limit]
        return Response(RiskEventSerializer(events, many=True).data)


@extend_schema_view(
    list=extend_schema(tags=['Signals'], summary='List alert rules'),
    create=extend_schema(tags=['Signals'], summary='Create alert rule'),
    retrieve=extend_schema(tags=['Signals'], summary='Get alert rule'),
    update=extend_schema(tags=['Signals'], summary='Update alert rule'),
    partial_update=extend_schema(tags=['Signals'], summary='Partial update alert rule'),
    destroy=extend_schema(tags=['Signals'], summary='Delete alert rule'),
    run=extend_schema(tags=['Signals'], summary='Run a backtest'),
)
class AlertRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for AlertRule CRUD and checking."""
    serializer_class = AlertRuleSerializer

    def get_queryset(self):
        return AlertRule.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def check(self, request):
        """Check all active alert rules against current data."""
        from apps.market.services.unified_data import fetch_market_data
        from apps.technical_analysis.services.indicator_engine import IndicatorEngine
        from django.utils import timezone
        
        user_rules = AlertRule.objects.filter(user=request.user, is_active=True)
        triggered = []
        
        # Group rules by symbol
        symbols = set(r.symbol for r in user_rules)
        
        for symbol in symbols:
            try:
                market = fetch_market_data(symbol)
                current_price = market.get('current_price', 0)
                closes = market.get('closes', [])[-50:]
                
                # Calculate indicators
                indicators = {}
                if closes:
                    indicators = IndicatorEngine.calculate_all_indicators(
                        [{'close': c, 'high': c, 'low': c, 'volume': 1000} for c in closes]
                    )
                
                rsi = indicators.get('rsi_14', {}).get('value', 50)
                
                symbol_rules = user_rules.filter(symbol=symbol)
                for rule in symbol_rules:
                    # Check cooldown
                    if rule.last_triggered:
                        elapsed = (timezone.now() - rule.last_triggered).total_seconds() / 60
                        if elapsed < rule.cooldown_minutes:
                            continue
                    
                    triggered_value = None
                    should_trigger = False
                    
                    if rule.alert_type == 'rsi_above' and rsi > rule.threshold:
                        should_trigger = True
                        triggered_value = rsi
                    elif rule.alert_type == 'rsi_below' and rsi < rule.threshold:
                        should_trigger = True
                        triggered_value = rsi
                    elif rule.alert_type == 'price_above' and current_price > rule.threshold:
                        should_trigger = True
                        triggered_value = current_price
                    elif rule.alert_type == 'price_below' and current_price < rule.threshold:
                        should_trigger = True
                        triggered_value = current_price
                    
                    if should_trigger and triggered_value is not None:
                        # Create alert history
                        message = rule.message_template or f"{symbol} {rule.get_alert_type_display()}: {triggered_value:.2f} (threshold: {rule.threshold})"
                        history = AlertHistory.objects.create(
                            rule=rule,
                            trigger_value=triggered_value,
                            message=message,
                        )
                        rule.last_triggered = timezone.now()
                        rule.save(update_fields=['last_triggered'])
                        triggered.append({
                            'rule_id': str(rule.id),
                            'symbol': symbol,
                            'alert_type': rule.alert_type,
                            'triggered_value': triggered_value,
                            'threshold': rule.threshold,
                            'message': message,
                        })
            except Exception as e:
                logger.warning(f"Failed to check alerts for {symbol}: {e}")
        
        return Response({
            'checked_symbols': len(symbols),
            'triggered_alerts': triggered,
            'total_triggered': len(triggered),
        })

    @action(detail=False, methods=['get'])
    def defaults(self, request):
        """Get default alert rules for common scenarios."""
        default_rules = [
            {'symbol': 'BTCUSDT', 'alert_type': 'rsi_above', 'threshold': 70, 'message_template': 'BTC RSI overbought (>70) - potential sell signal'},
            {'symbol': 'BTCUSDT', 'alert_type': 'rsi_below', 'threshold': 30, 'message_template': 'BTC RSI oversold (<30) - potential buy signal'},
            {'symbol': 'ETHUSDT', 'alert_type': 'rsi_above', 'threshold': 70, 'message_template': 'ETH RSI overbought (>70) - potential sell signal'},
            {'symbol': 'ETHUSDT', 'alert_type': 'rsi_below', 'threshold': 30, 'message_template': 'ETH RSI oversold (<30) - potential buy signal'},
            {'symbol': 'BTCUSDT', 'alert_type': 'confidence_above', 'threshold': 80, 'message_template': 'High confidence BTC signal (>{threshold}%)'},
            {'symbol': 'ETHUSDT', 'alert_type': 'confidence_above', 'threshold': 80, 'message_template': 'High confidence ETH signal (>{threshold}%)'},
            {'symbol': 'BTCUSDT', 'alert_type': 'composite_above', 'threshold': 75, 'message_template': 'BTC composite score strong bullish (>{threshold})'},
            {'symbol': 'BTCUSDT', 'alert_type': 'composite_below', 'threshold': 25, 'message_template': 'BTC composite score strong bearish (<{threshold})'},
        ]
        return Response(default_rules)


class AlertHistoryViewSet(viewsets.ModelViewSet):
    """ViewSet for AlertHistory."""
    serializer_class = AlertHistorySerializer

    def get_queryset(self):
        return AlertHistory.objects.filter(rule__user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark an alert as read."""
        history = self.get_object()
        history.read = True
        history.save(update_fields=['read'])
        return Response({'status': 'ok'})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all alerts as read."""
        updated = AlertHistory.objects.filter(rule__user=request.user, read=False).update(read=True)
        return Response({'marked_read': updated})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread alerts."""
        count = AlertHistory.objects.filter(rule__user=request.user, read=False).count()
        return Response({'count': count})


class BacktestResultViewSet(viewsets.ModelViewSet):
    """ViewSet for BacktestResult CRUD."""
    queryset = BacktestResult.objects.all()
    serializer_class = BacktestResultSerializer

    @action(detail=False, methods=['post'])
    def run(self, request):
        """Run a backtest with fees, slippage, and full reproducibility."""
        serializer = BacktestInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            from decimal import Decimal

            backtester = SignalBacktester(
                initial_capital=data.get('initial_capital', 10000),
                risk_per_trade=data.get('risk_per_trade', Decimal('1.0')),
                fee_rate=data.get('fee_rate', Decimal('0.001')),
                slippage_rate=data.get('slippage_rate', Decimal('0.0005')),
                stop_loss_pct=data.get('stop_loss_pct', Decimal('0.02')),
                take_profit_pct=data.get('take_profit_pct', Decimal('0.04')),
            )

            # Capture current factor weights for reproducibility
            weight_snapshot = {}
            try:
                for fw in FactorWeight.objects.filter(is_active=True):
                    weight_snapshot[fw.name] = float(fw.weight)
            except Exception:
                pass

            result = backtester.run_backtest(
                strategy_name=data['strategy_name'],
                symbol=data['symbol'],
                timeframe=data['timeframe'],
                start_date=data['start_date'],
                end_date=data['end_date'],
                strategy_version=data.get('strategy_version', '1.0'),
                feature_version=data.get('feature_version', '1.0'),
                weight_snapshot=weight_snapshot,
            )

            # Save backtest result with all new fields
            backtest = BacktestResult.objects.create(
                strategy_name=result['strategy_name'],
                strategy_version=result.get('strategy_version', '1.0'),
                feature_version=result.get('feature_version', '1.0'),
                symbol=result['symbol'],
                timeframe=result['timeframe'],
                start_date=data['start_date'],
                end_date=data['end_date'],
                initial_capital=result['initial_capital'],
                final_capital=result['final_capital'],
                total_return=result['total_return'],
                total_return_percent=result['total_return_percent'],
                max_drawdown=result['max_drawdown'],
                sharpe_ratio=result['sharpe_ratio'],
                sortino_ratio=result.get('sortino_ratio', 0),
                cagr=result.get('cagr', 0),
                expectancy=result.get('expectancy', 0),
                win_rate=result['win_rate'],
                total_trades=result['total_trades'],
                winning_trades=result['winning_trades'],
                losing_trades=result['losing_trades'],
                avg_win=result['avg_win'],
                avg_loss=result['avg_loss'],
                profit_factor=result['profit_factor'],
                max_favorable_excursion=result.get('max_favorable_excursion', 0),
                max_adverse_excursion=result.get('max_adverse_excursion', 0),
                total_fees=result.get('total_fees', 0),
                total_slippage=result.get('total_slippage', 0),
                fee_rate=data.get('fee_rate', Decimal('0.001')),
                slippage_rate=data.get('slippage_rate', Decimal('0.0005')),
                execution_mode='backtest',
                trades_data=result['trades'],
                equity_curve=result['equity_curve'],
                signal_snapshot=result.get('signal_snapshot', {}),
                weight_snapshot=result.get('weight_snapshot', {}),
            )

            return Response(
                BacktestResultSerializer(backtest).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            return Response(
                {'error': f'Backtest failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def historical_data(self, request):
        """Fetch historical candle data from CoinGecko for backtesting."""
        symbol = request.query_params.get('symbol', 'bitcoin')
        timeframe = request.query_params.get('timeframe', '1h')
        days = int(request.query_params.get('days', 30))

        import asyncio
        from .services.backtester import HistoricalDataFetcher

        try:
            loop = asyncio.new_event_loop()
            candles = loop.run_until_complete(
                HistoricalDataFetcher.fetch_candles(symbol, timeframe, days)
            )
            loop.close()

            return Response({
                'symbol': symbol,
                'timeframe': timeframe,
                'days': days,
                'count': len(candles),
                'candles': candles,
            })
        except Exception as e:
            logger.error(f"Historical data fetch failed: {e}")
            return Response(
                {'error': f'Failed to fetch historical data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def compare(self, request):
        """Compare multiple backtest results side by side."""
        ids = request.query_params.get('ids', '')
        if not ids:
            # Get last 5 backtests
            results = BacktestResult.objects.all()[:5]
        else:
            id_list = [i.strip() for i in ids.split(',') if i.strip()]
            results = BacktestResult.objects.filter(id__in=id_list)

        return Response({
            'backtests': BacktestResultSerializer(results, many=True).data,
            'count': results.count(),
        })
