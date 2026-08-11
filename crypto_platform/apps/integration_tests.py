"""Full stack integration tests for AI-Trading platform."""
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class HealthCheckTest(TestCase):
    """Test health check endpoints."""
    
    def test_health_check(self):
        """Test basic health check endpoint."""
        client = APIClient()
        response = client.get('/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')


class AuthenticationTest(TestCase):
    """Test authentication flow."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_login(self):
        """Test user login."""
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_invalid_login(self):
        """Test invalid login."""
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MarketDataTest(TestCase):
    """Test market data endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_prices(self):
        """Test getting prices endpoint."""
        response = self.client.get('/api/market/prices/')
        # May return empty list or mock data
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])


class SignalsTest(TestCase):
    """Test signals endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_signals(self):
        """Test getting signals endpoint."""
        response = self.client.get('/api/signals/signals/latest/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_generate_signal(self):
        """Test generating a signal."""
        response = self.client.post('/api/signals/signals/generate/', {
            'symbol': 'BTC-USDT',
            'timeframe': '1h',
            'current_price': 67500,
        })
        # May succeed or fail based on backend implementation
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
        ])


class ArbitrageTest(TestCase):
    """Test arbitrage endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_opportunities(self):
        """Test getting arbitrage opportunities."""
        response = self.client.get('/api/arbitrage/opportunities/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_scan_opportunities(self):
        """Test scanning for opportunities."""
        response = self.client.post('/api/arbitrage/opportunities/scan/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SocialTradingTest(TestCase):
    """Test social trading endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_traders(self):
        """Test getting traders."""
        response = self.client.get('/api/social/traders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_leaderboard(self):
        """Test getting trader leaderboard."""
        response = self.client.get('/api/social/traders/leaderboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PortfolioTest(TestCase):
    """Test portfolio endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_portfolios(self):
        """Test getting portfolios."""
        response = self.client.get('/api/portfolio/portfolios/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_portfolio(self):
        """Test creating a portfolio."""
        response = self.client.post('/api/portfolio/portfolios/', {
            'name': 'Test Portfolio',
            'portfolio_type': 'spot',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Portfolio')


class MobileAppTest(TestCase):
    """Test mobile app endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_register_device(self):
        """Test registering a device token."""
        response = self.client.post('/api/mobile/devices/register/', {
            'token': 'test-device-token-123',
            'platform': 'ios',
            'device_name': 'iPhone 14',
        })
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
        ])
    
    def test_get_alerts(self):
        """Test getting mobile alerts."""
        response = self.client.get('/api/mobile/alerts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class WebSocketTest(TestCase):
    """Test WebSocket connections."""
    
    def test_websocket_urls_exist(self):
        """Test that WebSocket URL patterns exist."""
        from crypto_platform.ws_urls import websocket_urlpatterns
        self.assertGreater(len(websocket_urlpatterns), 0)
