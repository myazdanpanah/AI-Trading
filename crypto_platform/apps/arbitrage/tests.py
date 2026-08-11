"""Tests for arbitrage app."""
from decimal import Decimal
from django.test import TestCase
from .models import ArbitrageOpportunity, ArbitrageConfig, ArbitrageExecution
from .services.detector import ArbitrageDetector


class ArbitrageDetectorTest(TestCase):
    """Tests for ArbitrageDetector service."""
    
    def setUp(self):
        self.detector = ArbitrageDetector(exchanges=['binance', 'bybit', 'okx'])
    
    def test_find_opportunities_with_spread(self):
        """Test finding arbitrage opportunities with valid spread."""
        prices = {
            'binance': {
                'BTC/USDT': {'bid': Decimal('67400'), 'ask': Decimal('67410'), 'volume': Decimal('50000')},
            },
            'bybit': {
                'BTC/USDT': {'bid': Decimal('67500'), 'ask': Decimal('67510'), 'volume': Decimal('50000')},
            },
        }
        
        opportunities = self.detector.find_opportunities(
            prices,
            min_spread_percent=Decimal('0.1'),
            volume_threshold=Decimal('1000'),
        )
        
        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0]['symbol'], 'BTC/USDT')
        self.assertEqual(opportunities[0]['buy_exchange'], 'binance')
        self.assertEqual(opportunities[0]['sell_exchange'], 'bybit')
        self.assertGreater(opportunities[0]['spread_percent'], 0)
    
    def test_no_opportunity_with_small_spread(self):
        """Test no opportunity when spread is too small."""
        prices = {
            'binance': {
                'BTC/USDT': {'bid': Decimal('67450'), 'ask': Decimal('67455'), 'volume': Decimal('50000')},
            },
            'bybit': {
                'BTC/USDT': {'bid': Decimal('67460'), 'ask': Decimal('67465'), 'volume': Decimal('50000')},
            },
        }
        
        opportunities = self.detector.find_opportunities(
            prices,
            min_spread_percent=Decimal('1.0'),  # 1% minimum
            volume_threshold=Decimal('1000'),
        )
        
        self.assertEqual(len(opportunities), 0)
    
    def test_no_opportunity_with_low_volume(self):
        """Test no opportunity when volume is too low."""
        prices = {
            'binance': {
                'BTC/USDT': {'bid': Decimal('67000'), 'ask': Decimal('67010'), 'volume': Decimal('100')},
            },
            'bybit': {
                'BTC/USDT': {'bid': Decimal('68000'), 'ask': Decimal('68010'), 'volume': Decimal('100')},
            },
        }
        
        opportunities = self.detector.find_opportunities(
            prices,
            min_spread_percent=Decimal('0.1'),
            volume_threshold=Decimal('1000'),
        )
        
        self.assertEqual(len(opportunities), 0)
    
    def test_multiple_symbols(self):
        """Test finding opportunities across multiple symbols."""
        prices = {
            'binance': {
                'BTC/USDT': {'bid': Decimal('67000'), 'ask': Decimal('67010'), 'volume': Decimal('50000')},
                'ETH/USDT': {'bid': Decimal('3400'), 'ask': Decimal('3405'), 'volume': Decimal('100000')},
            },
            'bybit': {
                'BTC/USDT': {'bid': Decimal('67500'), 'ask': Decimal('67510'), 'volume': Decimal('50000')},
                'ETH/USDT': {'bid': Decimal('3500'), 'ask': Decimal('3505'), 'volume': Decimal('100000')},
            },
        }
        
        opportunities = self.detector.find_opportunities(
            prices,
            min_spread_percent=Decimal('0.5'),
            volume_threshold=Decimal('1000'),
        )
        
        self.assertGreater(len(opportunities), 0)
        symbols = [opp['symbol'] for opp in opportunities]
        self.assertIn('BTC/USDT', symbols)
    
    def test_risk_score_calculation(self):
        """Test risk score calculation."""
        # Low risk: high volume, small spread
        risk = self.detector._calculate_risk_score(
            spread=Decimal('1'),
            volume=Decimal('100000'),
            exchange1='binance',
            exchange2='bybit',
        )
        self.assertLess(risk, 50)
        
        # High risk: low volume, large spread
        risk = self.detector._calculate_risk_score(
            spread=Decimal('10'),
            volume=Decimal('1000'),
            exchange1='unknown',
            exchange2='binance',
        )
        self.assertGreater(risk, 50)
    
    def test_optimal_position_size(self):
        """Test optimal position size calculation."""
        opportunity = {
            'volume_available': 50000,
            'spread_percent': 2.5,
        }
        
        size = self.detector.calculate_optimal_size(
            opportunity,
            max_position_usd=Decimal('10000'),
        )
        
        self.assertGreater(size, 0)
        self.assertLessEqual(size, Decimal('10000'))


class ArbitrageModelTest(TestCase):
    """Tests for Arbitrage models."""
    
    def test_create_opportunity(self):
        """Test creating an arbitrage opportunity."""
        opportunity = ArbitrageOpportunity.objects.create(
            symbol='BTC/USDT',
            buy_exchange='binance',
            sell_exchange='bybit',
            buy_price=Decimal('67000'),
            sell_price=Decimal('67500'),
            spread_percent=Decimal('0.75'),
            net_profit_percent=Decimal('0.55'),
            volume_available=Decimal('50000'),
            risk_score=35,
            status='active',
        )
        
        self.assertEqual(opportunity.symbol, 'BTC/USDT')
        self.assertEqual(opportunity.status, 'active')
        self.assertEqual(str(opportunity), 'BTC/USDT: binance -> bybit (0.75%)')
    
    def test_create_config(self):
        """Test creating an arbitrage config."""
        config = ArbitrageConfig.objects.create(
            name='Default Config',
            min_spread_percent=Decimal('0.5'),
            max_risk_score=70,
            enabled_exchanges=['binance', 'bybit', 'okx'],
            monitored_symbols=['BTC/USDT', 'ETH/USDT'],
            check_interval_seconds=30,
            max_position_size_usd=Decimal('10000'),
        )
        
        self.assertEqual(config.name, 'Default Config')
        self.assertTrue(config.is_active)
