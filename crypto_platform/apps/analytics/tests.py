"""Tests for analytics app."""
from django.test import TestCase
from .models import Indicator, TechnicalPattern, CPRAnalysis, SmartMoneyEvent
from decimal import Decimal
from datetime import datetime


class AnalyticsModelsTest(TestCase):
    def test_indicator_creation(self):
        indicator = Indicator.objects.create(
            symbol='BTCUSDT',
            indicator_name='rsi_14',
            timeframe='1h',
            value=Decimal('65.5'),
            score=Decimal('70'),
            signal='bullish',
            timestamp=datetime.now()
        )
        self.assertEqual(indicator.symbol, 'BTCUSDT')
        self.assertEqual(indicator.indicator_name, 'rsi_14')

    def test_cpr_creation(self):
        cpr = CPRAnalysis.objects.create(
            symbol='BTCUSDT',
            timeframe='daily',
            pivot=Decimal('50000'),
            bc=Decimal('49500'),
            tc=Decimal('50500'),
            r1=Decimal('51000'),
            r2=Decimal('52000'),
            s1=Decimal('49000'),
            s2=Decimal('48000'),
            cpr_width=Decimal('1000'),
            cpr_type='narrow',
            timestamp=datetime.now()
        )
        self.assertEqual(cpr.symbol, 'BTCUSDT')
        self.assertEqual(cpr.cpr_type, 'narrow')
