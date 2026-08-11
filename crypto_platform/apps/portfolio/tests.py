"""Tests for portfolio app."""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Portfolio, PortfolioAllocation, TaxLot, TaxReport
from .services.rebalancer import PortfolioRebalancer
from .services.tax_optimizer import TaxOptimizer

User = get_user_model()


class PortfolioRebalancerTest(TestCase):
    """Tests for PortfolioRebalancer service."""
    
    def setUp(self):
        self.rebalancer = PortfolioRebalancer()
    
    def test_calculate_rebalance_trades(self):
        """Test calculating rebalance trades."""
        current_holdings = {
            'BTC': Decimal('50000'),
            'ETH': Decimal('30000'),
            'SOL': Decimal('20000'),
        }
        
        target_allocation = {
            'BTC': Decimal('40'),  # 40%
            'ETH': Decimal('35'),  # 35%
            'SOL': Decimal('25'),  # 25%
        }
        
        trades = self.rebalancer.calculate_rebalance_trades(
            current_holdings,
            target_allocation,
            Decimal('100000'),
        )
        
        self.assertGreater(len(trades), 0)
        
        # Verify trades have required fields
        for trade in trades:
            self.assertIn('symbol', trade)
            self.assertIn('action', trade)
            self.assertIn('trade_value_usd', trade)
            self.assertIn(trade['action'], ['buy', 'sell'])
    
    def test_check_rebalance_needed(self):
        """Test checking if rebalance is needed."""
        current = {
            'BTC': Decimal('50'),
            'ETH': Decimal('30'),
            'SOL': Decimal('20'),
        }
        
        target = {
            'BTC': Decimal('40'),
            'ETH': Decimal('35'),
            'SOL': Decimal('25'),
        }
        
        needs_rebalance, drifted = self.rebalancer.check_rebalance_needed(
            current,
            target,
            threshold_percent=Decimal('5'),
        )
        
        self.assertTrue(needs_rebalance)
        self.assertGreater(len(drifted), 0)
    
    def test_no_rebalance_needed(self):
        """Test when no rebalance is needed."""
        current = {
            'BTC': Decimal('40'),
            'ETH': Decimal('35'),
            'SOL': Decimal('25'),
        }
        
        target = {
            'BTC': Decimal('40'),
            'ETH': Decimal('35'),
            'SOL': Decimal('25'),
        }
        
        needs_rebalance, drifted = self.rebalancer.check_rebalance_needed(
            current,
            target,
            threshold_percent=Decimal('5'),
        )
        
        self.assertFalse(needs_rebalance)
        self.assertEqual(len(drifted), 0)
    
    def test_optimize_allocation(self):
        """Test allocation optimization."""
        historical_returns = {
            'BTC': [0.01, 0.02, -0.01, 0.03, 0.015],
            'ETH': [0.02, 0.03, -0.02, 0.04, 0.025],
            'SOL': [0.03, 0.04, -0.03, 0.05, 0.035],
        }
        
        allocation = self.rebalancer.optimize_allocation(
            historical_returns,
            risk_tolerance='moderate',
        )
        
        self.assertEqual(len(allocation), 3)
        # Allocation should sum to approximately 100
        total = sum(allocation.values())
        self.assertAlmostEqual(float(total), 100, places=0)


class TaxOptimizerTest(TestCase):
    """Tests for TaxOptimizer service."""
    
    def setUp(self):
        self.optimizer = TaxOptimizer()
    
    def test_calculate_tax_lots_fifo(self):
        """Test FIFO tax lot calculation."""
        transactions = [
            {'type': 'buy', 'date': '2024-01-01', 'symbol': 'BTC', 'quantity': 1, 'price': 40000},
            {'type': 'buy', 'date': '2024-02-01', 'symbol': 'BTC', 'quantity': 1, 'price': 50000},
            {'type': 'sell', 'date': '2024-03-01', 'symbol': 'BTC', 'quantity': 1, 'price': 60000},
        ]
        
        tax_lots = self.optimizer.calculate_tax_lots(transactions, method='fifo')
        
        self.assertEqual(len(tax_lots), 1)
        self.assertEqual(tax_lots[0]['cost_basis'], 40000)
        self.assertEqual(tax_lots[0]['proceeds'], 60000)
        self.assertEqual(tax_lots[0]['gain_loss'], 20000)
    
    def test_calculate_tax_lots_lifo(self):
        """Test LIFO tax lot calculation."""
        transactions = [
            {'type': 'buy', 'date': '2024-01-01', 'symbol': 'BTC', 'quantity': 1, 'price': 40000},
            {'type': 'buy', 'date': '2024-02-01', 'symbol': 'BTC', 'quantity': 1, 'price': 50000},
            {'type': 'sell', 'date': '2024-03-01', 'symbol': 'BTC', 'quantity': 1, 'price': 60000},
        ]
        
        tax_lots = self.optimizer.calculate_tax_lots(transactions, method='lifo')
        
        self.assertEqual(len(tax_lots), 1)
        self.assertEqual(tax_lots[0]['cost_basis'], 50000)  # Last in
        self.assertEqual(tax_lots[0]['gain_loss'], 10000)
    
    def test_tax_loss_harvesting(self):
        """Test tax-loss harvesting opportunities."""
        holdings = {
            'BTC': {
                'quantity': 1,
                'cost_basis': 70000,
                'current_price': 67000,
            },
            'ETH': {
                'quantity': 10,
                'cost_basis': 4000,
                'current_price': 3500,
            },
        }
        
        opportunities = self.optimizer.find_tax_loss_harvesting_opportunities(holdings)
        
        self.assertGreater(len(opportunities), 0)
        for opp in opportunities:
            self.assertIn('estimated_tax_savings', opp)
            self.assertGreater(opp['estimated_tax_savings'], 0)
    
    def test_generate_tax_report(self):
        """Test tax report generation."""
        tax_lots = [
            {
                'disposition_date': '2024-06-01',
                'proceeds': 60000,
                'cost_basis': 40000,
                'gain_loss': 20000,
                'is_long_term': False,
            },
            {
                'disposition_date': '2024-07-01',
                'proceeds': 40000,
                'cost_basis': 30000,
                'gain_loss': 10000,
                'is_long_term': True,
            },
        ]
        
        report = self.optimizer.generate_tax_report(tax_lots, tax_year=2024)
        
        self.assertEqual(report['tax_year'], 2024)
        self.assertEqual(report['total_gain_loss'], 30000)
        self.assertEqual(report['short_term_gain_loss'], 20000)
        self.assertEqual(report['long_term_gain_loss'], 10000)
        self.assertGreater(report['total_estimated_tax'], 0)


class PortfolioModelTest(TestCase):
    """Tests for portfolio models."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_create_portfolio(self):
        """Test creating a portfolio."""
        portfolio = Portfolio.objects.create(
            user=self.user,
            name='My Portfolio',
            portfolio_type='spot',
            total_value_usd=Decimal('100000'),
        )
        
        self.assertEqual(portfolio.name, 'My Portfolio')
        self.assertEqual(portfolio.total_value_usd, Decimal('100000'))
    
    def test_create_allocation(self):
        """Test creating portfolio allocation."""
        portfolio = Portfolio.objects.create(
            user=self.user,
            name='Test Portfolio',
        )
        
        allocation = PortfolioAllocation.objects.create(
            portfolio=portfolio,
            symbol='BTC',
            target_percent=Decimal('40'),
            current_percent=Decimal('35'),
        )
        
        self.assertEqual(allocation.symbol, 'BTC')
        self.assertEqual(allocation.target_percent, Decimal('40'))
    
    def test_create_tax_lot(self):
        """Test creating a tax lot."""
        portfolio = Portfolio.objects.create(
            user=self.user,
            name='Test Portfolio',
        )
        
        tax_lot = TaxLot.objects.create(
            portfolio=portfolio,
            symbol='BTC',
            acquisition_date='2024-01-01',
            quantity=Decimal('1'),
            cost_basis_usd=Decimal('40000'),
            cost_basis_per_unit=Decimal('40000'),
            remaining_quantity=Decimal('1'),
            source='purchase',
        )
        
        self.assertEqual(tax_lot.symbol, 'BTC')
        self.assertEqual(tax_lot.quantity, Decimal('1'))
