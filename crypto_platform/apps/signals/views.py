"""Signal views - Full CRUD + analysis endpoints."""
import logging
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
)
from .serializers import (
    SignalSerializer, SignalReasonSerializer,
    SignalGenerationRequestSerializer, FactorWeightSerializer,
    WeightHistorySerializer,
    RiskProfileSerializer, PortfolioPositionSerializer,
    SignalPerformanceSerializer, BacktestResultSerializer,
    WalkForwardRunSerializer, WalkForwardWindowSerializer,
    WalkForwardInputSerializer,
    SignalGenerationInputSerializer, RiskCalculationInputSerializer,
    BacktestInputSerializer,
    AlertRuleSerializer, AlertHistorySerializer,
)
from .models import AlertRule, AlertHistory
from .services import SignalGenerator, RiskManager, PortfolioTracker, SignalBacktester

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
        """Generate a trading signal using multi-factor scoring."""
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
            generator = SignalGenerator()

            # Load configurable weights
            try:
                factor_weights = FactorWeight.objects.filter(is_active=True)
                if factor_weights.exists():
                    generator.load_weights(factor_weights)
            except Exception:
                pass  # Use defaults if DB unavailable

            # Fetch live data and run technical analysis
            symbol = data['symbol'].upper()
            technical_data = data.get('technical_data', {})
            sentiment_data = data.get('sentiment_data', {})
            current_price = data.get('current_price')

            try:
                from apps.market.services.unified_data import fetch_market_data
                from apps.technical_analysis.services.indicator_engine import IndicatorEngine

                market = fetch_market_data(symbol)
                closes = market['closes'][-50:]
                highs = market['highs'][-50:]
                lows = market['lows'][-50:]
                volumes = market['volumes'][-50:]
                current_price = current_price or market['current_price']

                # Run indicator engine
                indicators = IndicatorEngine.calculate_all_indicators(
                    [{'close': c, 'high': h, 'low': l, 'volume': v}
                     for c, h, l, v in zip(closes, highs, lows, volumes)]
                )

                # Translate indicator engine output to signal generator format
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
                # Use defaults if live data unavailable
                current_price = current_price or 0

            # Generate signal with real data
            result = generator.generate_signal(
                symbol=symbol,
                timeframe=data['timeframe'],
                technical_data=technical_data,
                sentiment_data=sentiment_data,
                news_data=data.get('news_data', {}),
                ai_data=data.get('ai_data', {}),
                macro_data=data.get('macro_data', {}),
                current_price=current_price,
            )

            # Try to save to database (graceful fallback if DB unavailable)
            signal = None
            try:
                with transaction.atomic():
                    entry_price_val = result.get('entry_price')
                    stop_loss_val = result.get('stop_loss')
                    # Convert None to 0 for required fields
                    entry_price_float = float(entry_price_val) if entry_price_val else 0.0
                    stop_loss_float = float(stop_loss_val) if stop_loss_val else entry_price_float * 0.97

                    signal = Signal.objects.create(
                        symbol=result['symbol'],
                        direction=result['direction'],
                        confidence=result['confidence'],
                        risk_score=result['risk_score'],
                        entry_price=entry_price_float,
                        stop_loss=stop_loss_float,
                        take_profit=result.get('take_profit', []),
                        timeframe=result['timeframe'],
                        technical_score=result['factor_scores'].get('technical', 0),
                        sentiment_score=result['factor_scores'].get('sentiment', 0),
                        news_score=result['factor_scores'].get('news', 0),
                        ai_score=result['factor_scores'].get('ai', 0),
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
                        input_data=decimal_to_float(data),
                        weights_used=result.get('weights_used', {}),
                        status='completed',
                    )
            except Exception as db_err:
                logger.warning(f"DB save failed (returning result anyway): {db_err}")

            serializable_result = decimal_to_float(result)

            # Build response - use signal data if saved, otherwise from result
            if signal:
                signal_data = SignalSerializer(signal).data
            else:
                # Build fake signal data from result for display
                signal_data = {
                    'id': f"gen-{result['symbol']}-{result['timeframe']}",
                    'symbol': result['symbol'],
                    'direction': result['direction'],
                    'confidence': result['confidence'],
                    'risk_score': result['risk_score'],
                    'entry_price': result.get('entry_price', 0),
                    'stop_loss': result.get('stop_loss', 0),
                    'take_profit': result.get('take_profit', []),
                    'timeframe': result['timeframe'],
                    'technical_score': result['factor_scores'].get('technical', 0),
                    'sentiment_score': result['factor_scores'].get('sentiment', 0),
                    'news_score': result['factor_scores'].get('news', 0),
                    'ai_score': result['factor_scores'].get('ai', 0),
                    'macro_score': result['factor_scores'].get('macro', 0),
                    'composite_score': result['composite_score'],
                    'reasons': result.get('reasons', []),
                    'created_at': result['generated_at'],
                    'is_active': True,
                }

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
