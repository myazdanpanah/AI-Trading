"""Economic calendar service for tracking macro events."""
import asyncio
from typing import List, Dict
from datetime import datetime, timedelta
import httpx
import logging

logger = logging.getLogger(__name__)


class EconomicCalendarService:
    """Service for fetching and managing economic calendar events."""

    BASE_URL = 'https://nfs.faireconomy.media/ff_calendar_thisweek.json'

    EVENT_TYPE_MAP = {
        'Interest Rate Decision': 'interest_rate',
        'CPI': 'cpi',
        'Core CPI': 'cpi',
        'PPI': 'ppi',
        'GDP': 'gdp',
        'Non-Farm Payrolls': 'nonfarm',
        'Unemployment Rate': 'employment',
        'Retail Sales': 'retail_sales',
        'PMI': 'pmi',
        'FOMC': 'fomc',
        'Consumer Sentiment': 'consumer_sentiment',
    }

    COUNTRY_MAP = {
        'USD': 'US',
        'EUR': 'EU',
        'GBP': 'UK',
        'JPY': 'JP',
        'CNY': 'CN',
        'CAD': 'CA',
        'AUD': 'AU',
        'CHF': 'CH',
    }

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_events(self, days_ahead: int = 7) -> List[Dict]:
        """Fetch economic events from calendar API."""
        try:
            response = await self.client.get(self.BASE_URL)
            response.raise_for_status()
            data = response.json()

            events = []
            now = datetime.now()
            cutoff = now + timedelta(days=days_ahead)

            for event in data:
                try:
                    event_date = datetime.strptime(
                        f"{event.get('date', '')} {event.get('time', '')}".strip(),
                        '%Y-%m-%d %H:%M'
                    ) if event.get('date') else None

                    if event_date and now <= event_date <= cutoff:
                        events.append({
                            'name': event.get('title', ''),
                            'event_type': self._map_event_type(event.get('title', '')),
                            'country': self._map_country(event.get('country', '')),
                            'impact_level': self._map_impact(event.get('impact', '')),
                            'scheduled_date': event_date,
                            'forecast_value': event.get('forecast', ''),
                            'previous_value': event.get('previous', ''),
                            'actual_value': event.get('actual', ''),
                            'source': 'faireconomy',
                        })
                except Exception as e:
                    logger.warning(f"Error parsing event: {e}")
                    continue

            logger.info(f"Fetched {len(events)} economic events")
            return events

        except Exception as e:
            logger.error(f"Error fetching economic calendar: {e}")
            return []

    def _map_event_type(self, title: str) -> str:
        title_lower = title.lower()
        for key, value in self.EVENT_TYPE_MAP.items():
            if key.lower() in title_lower:
                return value
        return 'other'

    def _map_country(self, country_code: str) -> str:
        return self.COUNTRY_MAP.get(country_code, country_code)

    def _map_impact(self, impact: str) -> str:
        impact_lower = impact.lower()
        if 'high' in impact_lower or '3' in impact:
            return 'high'
        elif 'medium' in impact_lower or '2' in impact:
            return 'medium'
        elif 'low' in impact_lower or '1' in impact:
            return 'low'
        return 'medium'

    async def store_events(self, events: List[Dict]) -> int:
        """Store events in database."""
        from ..global_events import EconomicEvent

        stored_count = 0
        for event_data in events:
            try:
                def _create():
                    return EconomicEvent.objects.get_or_create(
                        name=event_data['name'],
                        scheduled_date=event_data['scheduled_date'],
                        defaults=event_data
                    )
                event, created = await asyncio.to_thread(_create)
                if created:
                    stored_count += 1
            except Exception as e:
                logger.error(f"Error storing event: {e}")

        return stored_count

    async def get_upcoming_events(self, hours: int = 24) -> List[Dict]:
        """Get upcoming events."""
        from ..global_events import EconomicEvent

        now = datetime.now()
        future = now + timedelta(hours=hours)

        def _fetch():
            return list(EconomicEvent.objects.filter(
                scheduled_date__gte=now,
                scheduled_date__lte=future,
                is_released=False
            ).order_by('scheduled_date')[:20])

        events = await asyncio.to_thread(_fetch)
        return [
            {
                'id': str(e.id),
                'name': e.name,
                'event_type': e.event_type,
                'country': e.country,
                'impact_level': e.impact_level,
                'scheduled_date': e.scheduled_date.isoformat(),
                'forecast_value': e.forecast_value,
                'previous_value': e.previous_value,
            }
            for e in events
        ]

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
