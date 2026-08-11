"""Integration tests for Signal Generation Engine - full flow testing."""
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase
from django.test import RequestFactory
from rest_framework.test import APIClient
from rest_framework import status

from .models import (
    Signal, SignalReason, SignalGenerationRequest,
    FactorWeight, RiskProfile, PortfolioPosition,
    SignalPerformance, BacktestResult,
)
from .services import SignalGenerator, RiskManager, PortfolioTracker, SignalBacktester
from .views import SignalViewSet


class SignalGenerationIntegrationTest(TestCase):
    """Integration tests for the full signal generation flow."""

    def setUp(self):
        self.factory = RequestFactory()
        self.client = APIClient()
        
        # Create default factor weights
        self.weights = []
        for name, weight in [
            ('technical', 0.30), ('sentiment', 0.20),
            ('news', 0.15), ('ai', 0.20), ('macro', 0.15),
        ]:
            w = FactorWeight.objects.create(
                name=name, weight=weight, is_active=True
            )
            self.weights.append(w)
        
        # Create default risk profile
        self.risk_profile = RiskProfile.objects.create(
            name='Test Profile',
            max_portfolio_risk=Decimal('4.0'),
            max_position_size=Decimal('10.0'),
            risk_per_trade=Decimal('1.0'),
        )

    def test_signal_generation_creates_records(self):
        """Test that signal generation creates all required database records."""
        generator = SignalGenerator()
        generator.load_weights(self.weights)
        
        result = generator.generate_signal(
            symbol='BTC/USDT',
            timeframe='1h',
            technical_data={'rsi': 25, 'macd_signal': 'bullish_crossover', 'trend': 'uptrend'},
            sentiment_data={'fear_greed_index': 20, 'whale_signal': 'accumulation'},
            current_price=Decimal('50000'),
        )
        
        # Create signal record
        signal = Signal.objects.create(
            symbol=result['symbol'],
            direction=result['direction'],
            confidence=result['confidence'],
            risk_score=result['risk_score'],
            entry_price=result['entry_price'] or 50000,
            stop_loss=result['stop_loss'],
            take_profit=result['take_profit'],
            timeframe=result['timeframe'],
            technical_score=result['factor_scores'].get('technical', 0),
            sentiment_score=result['factor_scores'].get('sentiment', 0),
            news_score=result['factor_scores'].get('news', 0),
            ai_score=result['factor_scores'].get('ai', 0),
            macro_score=result['factor_scores'].get('macro', 0),
            composite_score=result['composite_score'],
        )
        
        # Create signal reasons
        for reason in result.get('reasons', []):
            SignalReason.objects.create(
                signal=signal,
                reason_type=reason['type'],
                description=reason['description'],
                confidence=reason['confidence'],
            )
        
        # Create generation request
        request = SignalGenerationRequest.objects.create(
            symbol=result['symbol'],
            timeframe=result['timeframe'],
            input_data={'technical_data': {'rsi': 25}},
            weights_used=result['weights_used'],
            status='completed',
        )
        
        # Verify all records exist
        self.assertEqual(Signal.objects.count(), 1)
        self.assertEqual(SignalReason.objects.filter(signal=signal).count(), len(result.get('reasons', [])))
        self.assertEqual(SignalGenerationRequest.objects.count(), 1)
        
        # Verify signal fields
        db_signal = Signal.objects.first()
        self.assertEqual(db_signal.symbol, 'BTC/USDT')
        self.assertIn(db_signal.direction, ['buy', 'strong_buy', 'hold', 'sell', 'strong_sell'])
        self.assertGreater(db_signal.confidence, 0)

    def test_risk_management_integration(self):
        """Test risk management integration with position sizing."""
        risk_manager = RiskManager(self.risk_profile)
        
        # Calculate position size
        result = risk_manager.calculate_position_size(
            account_balance=Decimal('10000'),
            entry_price=Decimal('50000'),
            stop_loss=Decimal('49000'),
            signal_confidence=70,
            signal_direction='buy',
        )
        
        self.assertGreater(result['position_size'], 0)
        self.assertIn('risk_amount', result)
        self.assertIn('within_limits', result)
        
        # Create portfolio position
        position = PortfolioPosition.objects.create(
            symbol='BTC/USDT',
            side='long',
            quantity=Decimal(str(result['position_size'])),
            entry_price=Decimal('50000'),
            stop_loss=Decimal('49000'),
            risk_amount=Decimal(str(result['risk_amount'])),
        )
        
        self.assertEqual(PortfolioPosition.objects.count(), 1)
        self.assertEqual(position.symbol, 'BTC/USDT')

    def test_portfolio_tracking_integration(self):
        """Test portfolio tracking integration."""
        tracker = PortfolioTracker(initial_capital=Decimal('10000'))
        
        # Open position
        position_data = tracker.open_position(
            symbol='BTC/USDT',
            side='long',
            quantity=Decimal('0.1'),
            entry_price=Decimal('50000'),
            stop_loss=Decimal('49000'),
        )
        
        # Update price
        updated = tracker.update_position_price(
            position=position_data,
            current_price=Decimal('52000'),
        )
        
        self.assertGreater(updated['unrealized_pnl'], 0)
        
        # Close position
        closed = tracker.close_position(
            position=updated,
            close_price=Decimal('52000'),
            reason='take_profit',
        )
        
        self.assertFalse(closed['is_active'])
        self.assertGreater(closed['unrealized_pnl'], 0)

    def test_backtest_integration(self):
        """Test backtesting integration."""
        backtester = SignalBacktester(initial_capital=Decimal('10000'))
        
        result = backtester.run_backtest(
            strategy_name='integration_test',
            symbol='BTC/USDT',
            timeframe='1h',
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 2, 1),
        )
        
        # Verify result structure
        self.assertIn('total_return_percent', result)
        self.assertIn('win_rate', result)
        self.assertIn('sharpe_ratio', result)
        self.assertIn('equity_curve', result)
        self.assertIn('trades', result)
        
        # Save backtest result
        backtest = BacktestResult.objects.create(
            strategy_name=result['strategy_name'],
            symbol=result['symbol'],
            timeframe=result['timeframe'],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 2, 1),
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
        
        self.assertEqual(BacktestResult.objects.count(), 1)


class SignalAPIIntegrationTest(TestCase):
    """Integration tests for Signal API endpoints."""

    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create default factor weights
        for name, weight in [
            ('technical', 0.30), ('sentiment', 0.20),
            ('news', 0.15), ('ai', 0.20), ('macro', 0.15),
        ]:
            FactorWeight.objects.create(
                name=name, weight=weight, is_active=True
            )

    def test_generate_signal_endpoint(self):
        """Test the signal generation API endpoint."""
        response = self.client.post(
            '/api/signals/signals/generate/',
            {
                'symbol': 'BTC/USDT',
                'timeframe': '1h',
                'technical_data': {'rsi': 25, 'trend': 'uptrend'},
                'sentiment_data': {'fear_greed_index': 20},
                'current_price': 50000,
            },
            format='json',
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('signal', response.data)
        self.assertIn('details', response.data)
        
        # Verify database records
        self.assertEqual(Signal.objects.count(), 1)
        self.assertEqual(SignalReason.objects.count(), 1)  # At least one reason
        self.assertEqual(SignalGenerationRequest.objects.count(), 1)

    def test_latest_signals_endpoint(self):
        """Test the latest signals API endpoint."""
        # Create some signals
        for i in range(5):
            Signal.objects.create(
                symbol='BTC/USDT',
                direction='buy' if i % 2 == 0 else 'sell',
                confidence=60 + i,
                entry_price=50000 + i * 1000,
                timeframe='1h',
            )
        
        response = self.client.get('/api/signals/signals/latest/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_factor_weights_endpoint(self):
        """Test factor weights CRUD endpoint."""
        # List weights
        response = self.client.get('/api/signals/factor-weights/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
        
        # Update a weight
        weight = FactorWeight.objects.first()
        response = self.client.patch(
            f'/api/signals/factor-weights/{weight.id}/',
            {'weight': 0.35},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_risk_profiles_endpoint(self):
        """Test risk profiles CRUD endpoint."""
        response = self.client.get('/api/signals/risk-profiles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class EndToEndSignalFlowTest(TestCase):
    """End-to-end test of the complete signal generation flow."""

    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(
            email='e2e@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create factor weights
        for name, weight in [
            ('technical', 0.30), ('sentiment', 0.20),
            ('news', 0.15), ('ai', 0.20), ('macro', 0.15),
        ]:
            FactorWeight.objects.create(
                name=name, weight=weight, is_active=True
            )

    def test_complete_signal_lifecycle(self):
        """Test complete signal lifecycle from generation to tracking."""
        # 1. Generate signal via API
        response = self.client.post(
            '/api/signals/signals/generate/',
            {
                'symbol': 'ETH/USDT',
                'timeframe': '4h',
                'technical_data': {'rsi': 30, 'trend': 'uptrend', 'macd_signal': 'bullish_crossover'},
                'sentiment_data': {'fear_greed_index': 25, 'whale_signal': 'accumulation'},
                'current_price': 3000,
            },
            format='json',
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        signal_data = response.data['signal']
        
        # 2. Verify signal was created
        signal = Signal.objects.get(id=signal_data['id'])
        self.assertEqual(signal.symbol, 'ETH/USDT')
        self.assertGreater(signal.confidence, 0)
        
        # 3. Verify reasons were created
        reasons = SignalReason.objects.filter(signal=signal)
        self.assertGreater(reasons.count(), 0)
        
        # 4. Verify generation request was logged
        request = SignalGenerationRequest.objects.get(symbol='ETH/USDT')
        self.assertEqual(request.status, 'completed')
        
        # 5. Verify factor weights were used
        self.assertIn('weights_used', response.data['details'])
