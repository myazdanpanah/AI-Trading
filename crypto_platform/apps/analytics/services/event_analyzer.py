"""Global event impact analyzer."""
import asyncio
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from ..models import (
    EconomicEvent, RegulatoryEvent, GeopoliticalEvent,
    BlockchainEvent, GlobalEventImpact
)
import logging

logger = logging.getLogger(__name__)


class GlobalEventAnalyzer:
    """Analyzes impact of global events on crypto markets."""

    # Impact weights by event type
    IMPACT_WEIGHTS = {
        'economic': 0.25,
        'regulatory': 0.35,
        'geopolitical': 0.20,
        'blockchain': 0.20,
    }

    # Severity mapping for event types
    SEVERITY_MAP = {
        'interest_rate': 90,
        'cpi': 80,
        'fomc': 85,
        'gdp': 70,
        'nonfarm': 75,
        'etf_approval': 95,
        'sec_decision': 85,
        'hack': 80,
        'war': 90,
        'sanctions': 85,
        'election': 70,
    }

    async def analyze_event_impact(
        self,
        event_type: str,
        event_id: str,
        symbol: str,
        price_before: Decimal
    ) -> Dict:
        """Analyze impact of a single event."""
        # Get event details
        event = await self._get_event(event_type, event_id)
        if not event:
            return {'error': 'Event not found'}

        # Calculate expected impact
        severity = self._get_severity(event_type, event)
        direction = self._predict_direction(event_type, event)

        # Create impact record
        impact = await asyncio.to_thread(
            GlobalEventImpact.objects.create,
            event_type=event_type,
            event_id=event_id,
            symbol=symbol,
            price_before=price_before,
            analysis=f"Expected {direction} impact with severity {severity}/100"
        )

        return {
            'impact_id': str(impact.id),
            'event_type': event_type,
            'severity': severity,
            'direction': direction,
            'symbol': symbol,
        }

    async def update_impact_after_event(
        self,
        impact_id: str,
        price_after_1h: Decimal,
        price_after_24h: Decimal
    ) -> Dict:
        """Update impact record with actual price changes."""
        def _get_impact():
            return GlobalEventImpact.objects.get(id=impact_id)

        impact = await asyncio.to_thread(_get_impact)

        # Calculate changes
        if impact.price_before > 0:
            change_1h = ((price_after_1h - impact.price_before) / impact.price_before) * 100
            change_24h = ((price_after_24h - impact.price_before) / impact.price_before) * 100
        else:
            change_1h = Decimal('0')
            change_24h = Decimal('0')

        # Update record
        def _update():
            impact.price_after_1h = price_after_1h
            impact.price_after_24h = price_after_24h
            impact.price_change_1h_percent = change_1h
            impact.price_change_24h_percent = change_24h
            impact.save()

        await asyncio.to_thread(_update)

        return {
            'impact_id': str(impact.id),
            'change_1h_percent': float(change_1h),
            'change_24h_percent': float(change_24h),
        }

    async def get_event_summary(self, hours: int = 24) -> Dict:
        """Get summary of events and their impacts."""
        now = datetime.now()
        since = now - timedelta(hours=hours)

        def _get_summary():
            economic = EconomicEvent.objects.filter(
                scheduled_date__gte=since
            ).count()
            regulatory = RegulatoryEvent.objects.filter(
                event_date__gte=since
            ).count()
            geopolitical = GeopoliticalEvent.objects.filter(
                event_date__gte=since
            ).count()
            blockchain = BlockchainEvent.objects.filter(
                event_date__gte=since
            ).count()
            impacts = GlobalEventImpact.objects.filter(
                created_at__gte=since
            )

            avg_impact_1h = impacts.filter(
                price_change_1h_percent__isnull=False
            ).values_list('price_change_1h_percent', flat=True)

            return {
                'total_events': economic + regulatory + geopolitical + blockchain,
                'by_type': {
                    'economic': economic,
                    'regulatory': regulatory,
                    'geopolitical': geopolitical,
                    'blockchain': blockchain,
                },
                'impacts_recorded': impacts.count(),
                'avg_impact_1h': sum(avg_impact_1h) / len(avg_impact_1h) if avg_impact_1h else 0,
            }

        return await asyncio.to_thread(_get_summary)

    async def _get_event(self, event_type: str, event_id: str):
        """Get event by type and ID."""
        model_map = {
            'economic': EconomicEvent,
            'regulatory': RegulatoryEvent,
            'geopolitical': GeopoliticalEvent,
            'blockchain': BlockchainEvent,
        }
        model = model_map.get(event_type)
        if not model:
            return None

        def _fetch():
            return model.objects.get(id=event_id)

        try:
            return await asyncio.to_thread(_fetch)
        except model.DoesNotExist:
            return None

    def _get_severity(self, event_type: str, event) -> int:
        """Calculate event severity."""
        # Check for specific severity in event
        if hasattr(event, 'severity'):
            return event.severity
        if hasattr(event, 'impact_level'):
            impact_map = {'critical': 90, 'high': 75, 'medium': 50, 'low': 25}
            return impact_map.get(event.impact_level, 50)

        # Use default severity
        return self.SEVERITY_MAP.get(event_type, 50)

    def _predict_direction(self, event_type: str, event) -> str:
        """Predict market direction based on event."""
        if hasattr(event, 'direction'):
            return event.direction

        # Default prediction based on event type
        bullish_types = ['etf_approval', 'crypto_legalization', 'partnership', 'upgrade']
        bearish_types = ['hack', 'exploit', 'crypto_ban', 'enforcement']

        if event_type in bullish_types:
            return 'bullish'
        elif event_type in bearish_types:
            return 'bearish'

        return 'neutral'
