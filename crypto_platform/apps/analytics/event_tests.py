"""Tests for global events."""
from django.test import TestCase
from datetime import datetime, timedelta
from decimal import Decimal
from .models import (
    EconomicEvent, RegulatoryEvent, GeopoliticalEvent,
    BlockchainEvent, GlobalEventImpact
)


class EconomicEventTest(TestCase):
    def test_create_economic_event(self):
        event = EconomicEvent.objects.create(
            name='FOMC Meeting',
            event_type='fomc',
            country='US',
            impact_level='high',
            scheduled_date=datetime.now() + timedelta(days=1),
            forecast_value='5.25%',
            previous_value='5.50%'
        )
        self.assertEqual(event.name, 'FOMC Meeting')
        self.assertEqual(event.impact_level, 'high')

    def test_create_regulatory_event(self):
        event = RegulatoryEvent.objects.create(
            title='SEC ETF Decision',
            event_type='etf_approval',
            jurisdiction='US',
            severity=90,
            direction='bullish',
            source='SEC',
            summary='Bitcoin ETF decision pending',
            event_date=datetime.now()
        )
        self.assertEqual(event.title, 'SEC ETF Decision')
        self.assertEqual(event.severity, 90)

    def test_create_geopolitical_event(self):
        event = GeopoliticalEvent.objects.create(
            title='Trade War Escalation',
            event_type='trade_war',
            region='Global',
            severity=70,
            direction='bearish',
            source='Reuters',
            summary='US-China tensions rise',
            event_date=datetime.now()
        )
        self.assertEqual(event.title, 'Trade War Escalation')

    def test_create_blockchain_event(self):
        event = BlockchainEvent.objects.create(
            title='Ethereum Upgrade',
            event_type='upgrade',
            blockchain='Ethereum',
            severity=75,
            direction='bullish',
            source='Ethereum Foundation',
            summary='Network upgrade completed',
            event_date=datetime.now()
        )
        self.assertEqual(event.blockchain, 'Ethereum')

    def test_create_event_impact(self):
        impact = GlobalEventImpact.objects.create(
            event_type='economic',
            event_id='test-id',
            symbol='BTCUSDT',
            price_before=Decimal('50000'),
            analysis='Expected bullish impact'
        )
        self.assertEqual(impact.symbol, 'BTCUSDT')
        self.assertEqual(impact.price_before, Decimal('50000'))


class EventAnalyzerTest(TestCase):
    def test_severity_map(self):
        from .services.event_analyzer import GlobalEventAnalyzer
        analyzer = GlobalEventAnalyzer()
        self.assertEqual(analyzer.SEVERITY_MAP['interest_rate'], 90)
        self.assertEqual(analyzer.SEVERITY_MAP['etf_approval'], 95)

    def test_impact_weights(self):
        from .services.event_analyzer import GlobalEventAnalyzer
        analyzer = GlobalEventAnalyzer()
        self.assertEqual(analyzer.IMPACT_WEIGHTS['regulatory'], 0.35)
        self.assertEqual(analyzer.IMPACT_WEIGHTS['economic'], 0.25)
