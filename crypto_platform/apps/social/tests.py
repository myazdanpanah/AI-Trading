"""Tests for social trading app."""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Trader, FollowRelationship, CopyTrade, TraderSignal, SocialComment
from .services.copy_trader import CopyTrader

User = get_user_model()


class CopyTraderTest(TestCase):
    """Tests for CopyTrader service."""
    
    def setUp(self):
        self.copy_trader = CopyTrader()
    
    def test_should_copy_high_confidence_signal(self):
        """Test copying a high confidence signal."""
        signal = {
            'symbol': 'BTC/USDT',
            'direction': 'buy',
            'confidence': 85,
            'risk_score': 35,
            'entry_price': 67500,
            'stop_loss': 65000,
            'take_profit': [72000, 75000],
        }
        
        follow_config = {
            'copy_position_size_percent': 10,
            'max_copy_amount_usd': 1000,
        }
        
        result = self.copy_trader.should_copy_signal(
            signal,
            follow_config,
            Decimal('50000'),
        )
        
        self.assertTrue(result['should_copy'])
        self.assertGreater(result['quantity'], 0)
        self.assertGreater(result['estimated_cost_usd'], 0)
    
    def test_should_not_copy_low_confidence(self):
        """Test not copying a low confidence signal."""
        signal = {
            'symbol': 'BTC/USDT',
            'direction': 'buy',
            'confidence': 50,  # Below threshold
            'risk_score': 35,
            'entry_price': 67500,
        }
        
        follow_config = {
            'copy_position_size_percent': 10,
            'max_copy_amount_usd': 1000,
        }
        
        result = self.copy_trader.should_copy_signal(
            signal,
            follow_config,
            Decimal('50000'),
        )
        
        self.assertFalse(result['should_copy'])
        self.assertIn('confidence', result['reason'])
    
    def test_should_not_copy_high_risk(self):
        """Test not copying a high risk signal."""
        signal = {
            'symbol': 'BTC/USDT',
            'direction': 'buy',
            'confidence': 85,
            'risk_score': 80,  # Above threshold
            'entry_price': 67500,
        }
        
        follow_config = {
            'copy_position_size_percent': 10,
            'max_copy_amount_usd': 1000,
        }
        
        result = self.copy_trader.should_copy_signal(
            signal,
            follow_config,
            Decimal('50000'),
        )
        
        self.assertFalse(result['should_copy'])
        self.assertIn('Risk', result['reason'])
    
    def test_trader_score(self):
        """Test trader score calculation."""
        trader_data = {
            'win_rate': 70,
            'profit_factor': 2.0,
            'sharpe_ratio': 1.5,
            'followers_count': 500,
        }
        
        score = self.copy_trader.get_trader_score(trader_data)
        
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_copy_fee_calculation(self):
        """Test copy fee calculation."""
        fee = self.copy_trader.calculate_copy_fee(
            trade_value=Decimal('1000'),
            fee_percent=Decimal('5'),
        )
        
        self.assertEqual(fee, Decimal('50'))


class SocialModelTest(TestCase):
    """Tests for social trading models."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testtrader',
            email='testtrader@test.com',
            password='testpass123'
        )
    
    def test_create_trader(self):
        """Test creating a trader profile."""
        trader = Trader.objects.create(
            user=self.user,
            display_name='Test Trader',
            bio='Professional trader',
            is_public=True,
            win_rate=Decimal('65.5'),
            profit_factor=Decimal('1.8'),
        )
        
        self.assertEqual(trader.display_name, 'Test Trader')
        self.assertTrue(trader.is_public)
        self.assertEqual(str(trader), 'Test Trader (65.5% win rate)')
    
    def test_follow_relationship(self):
        """Test follow relationship."""
        trader = Trader.objects.create(
            user=self.user,
            display_name='Test Trader',
        )
        
        follower = User.objects.create_user(
            username='follower',
            email='follower@test.com',
            password='testpass123'
        )
        
        follow = FollowRelationship.objects.create(
            follower=follower,
            trader=trader,
            copy_trading=True,
            copy_position_size_percent=Decimal('10'),
            max_copy_amount_usd=Decimal('500'),
        )
        
        self.assertTrue(follow.copy_trading)
        self.assertEqual(follow.max_copy_amount_usd, Decimal('500'))
    
    def test_copy_trade(self):
        """Test copy trade creation."""
        trader = Trader.objects.create(
            user=self.user,
            display_name='Test Trader',
        )
        
        follower = User.objects.create_user(
            username='follower2',
            email='follower2@test.com',
            password='testpass123'
        )
        
        copy_trade = CopyTrade.objects.create(
            follower=follower,
            trader=trader,
            symbol='BTC/USDT',
            direction='buy',
            quantity=Decimal('0.1'),
            entry_price=Decimal('67500'),
            status='open',
        )
        
        self.assertEqual(copy_trade.symbol, 'BTC/USDT')
        self.assertEqual(copy_trade.status, 'open')
