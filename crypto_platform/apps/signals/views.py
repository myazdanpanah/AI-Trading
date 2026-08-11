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
)
from .serializers import (
    SignalSerializer, SignalReasonSerializer,
    SignalGenerationRequestSerializer, FactorWeightSerializer,
    RiskProfileSerializer, PortfolioPositionSerializer,
    SignalPerformanceSerializer, BacktestResultSerializer,
    SignalGenerationInputSerializer, RiskCalculationInputSerializer,
    BacktestInputSerializer,
)
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

        try:
            generator = SignalGenerator()

            # Load configurable weights
            factor_weights = FactorWeight.objects.filter(is_active=True)
            if factor_weights.exists():
                generator.load_weights(factor_weights)

            # Generate signal
            result = generator.generate_signal(
                symbol=data['symbol'],
                timeframe=data['timeframe'],
                technical_data=data.get('technical_data', {}),
                sentiment_data=data.get('sentiment_data', {}),
                news_data=data.get('news_data', {}),
                ai_data=data.get('ai_data', {}),
                macro_data=data.get('macro_data', {}),
                current_price=data.get('current_price'),
            )

            # Create signal record
            with transaction.atomic():
                signal = Signal.objects.create(
                    symbol=result['symbol'],
                    direction=result['direction'],
                    confidence=result['confidence'],
                    risk_score=result['risk_score'],
                    entry_price=result['entry_price'] or 0,
                    stop_loss=result['stop_loss'],
                    take_profit=result['take_profit'],
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
                        reason_type=reason['type'],
                        description=reason['description'],
                        confidence=reason['confidence'],
                    )

                # Create generation request record
                SignalGenerationRequest.objects.create(
                    symbol=result['symbol'],
                    timeframe=result['timeframe'],
                    input_data=data,
                    weights_used=result['weights_used'],
                    status='completed',
                )

            return Response({
                'signal': SignalSerializer(signal).data,
                'details': result,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            return Response(
                {'error': 'An error occurred during signal generation. Please try again later.'},
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
    """ViewSet for FactorWeight CRUD."""
    queryset = FactorWeight.objects.all()
    serializer_class = FactorWeightSerializer


@extend_schema_view(
    list=extend_schema(tags=['Signals'], summary='List risk profiles'),
    create=extend_schema(tags=['Signals'], summary='Create risk profile'),
    retrieve=extend_schema(tags=['Signals'], summary='Get risk profile'),
    update=extend_schema(tags=['Signals'], summary='Update risk profile'),
    partial_update=extend_schema(tags=['Signals'], summary='Partial update risk profile'),
    destroy=extend_schema(tags=['Signals'], summary='Delete risk profile'),
)
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
class BacktestResultViewSet(viewsets.ModelViewSet):
    """ViewSet for BacktestResult CRUD."""
    queryset = BacktestResult.objects.all()
    serializer_class = BacktestResultSerializer

    @action(detail=False, methods=['post'])
    def run(self, request):
        """Run a backtest."""
        serializer = BacktestInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            backtester = SignalBacktester(
                initial_capital=data.get('initial_capital', 10000)
            )

            result = backtester.run_backtest(
                strategy_name=data['strategy_name'],
                symbol=data['symbol'],
                timeframe=data['timeframe'],
                start_date=data['start_date'],
                end_date=data['end_date'],
            )

            # Save backtest result
            backtest = BacktestResult.objects.create(
                strategy_name=result['strategy_name'],
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
                win_rate=result['win_rate'],
                total_trades=result['total_trades'],
                winning_trades=result['winning_trades'],
                losing_trades=result['losing_trades'],
                avg_win=result['avg_win'],
                avg_loss=result['avg_loss'],
                profit_factor=result['profit_factor'],
                trades_data=result['trades'],
                equity_curve=result['equity_curve'],
            )

            return Response(
                BacktestResultSerializer(backtest).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            return Response(
                {'error': 'An error occurred during backtesting. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
