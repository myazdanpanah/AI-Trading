"""Tests for market app."""
from django.test import TestCase
from .models import Exchange, TradingPair, Candle
from decimal import Decimal
from datetime import datetime


class MarketModelsTest(TestCase):
    def setUp(self):
        self.exchange = Exchange.objects.create(
            name='Binance',
            slug='binance'
        )
        self.pair = TradingPair.objects.create(
            exchange=self.exchange,
            symbol='BTCUSDT',
            base_asset='BTC',
            quote_asset='USDT'
        )

    def test_exchange_creation(self):
        self.assertEqual(self.exchange.name, 'Binance')
        self.assertEqual(self.exchange.api_status, 'active')

    def test_trading_pair_creation(self):
        self.assertEqual(self.pair.symbol, 'BTCUSDT')
        self.assertEqual(self.pair.exchange, self.exchange)

    def test_candle_creation(self):
        candle = Candle.objects.create(
            symbol='BTCUSDT',
            timeframe='1h',
            open=Decimal('50000.00000000'),
            high=Decimal('51000.00000000'),
            low=Decimal('49000.00000000'),
            close=Decimal('50500.00000000'),
            volume=Decimal('1000.00000000'),
            timestamp=datetime.now()
        )
        self.assertEqual(candle.symbol, 'BTCUSDT')
        self.assertEqual(candle.timeframe, '1h')
