"""Celery tasks for global event monitoring."""
from celery import shared_task
from celery.utils.log import get_task_logger
import asyncio

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3)
def fetch_economic_calendar(self, days_ahead: int = 7):
    """Fetch economic calendar events."""
    from .services.economic_calendar import EconomicCalendarService

    async def _fetch():
        service = EconomicCalendarService()
        try:
            events = await service.fetch_events(days_ahead)
            stored = await service.store_events(events)
            return {'fetched': len(events), 'stored': stored}
        finally:
            await service.close()

    try:
        result = asyncio.run(_fetch())
        logger.info(f"Economic calendar fetch completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Economic calendar fetch failed: {e}")
        raise self.retry(exc=e, countdown=300)


@shared_task
def get_upcoming_events(hours: int = 24):
    """Get upcoming events summary."""
    from .services.economic_calendar import EconomicCalendarService

    async def _get():
        service = EconomicCalendarService()
        try:
            return await service.get_upcoming_events(hours)
        finally:
            pass

    return asyncio.run(_get())


@shared_task
def analyze_event_impact(event_type: str, event_id: str, symbol: str, price_before: float):
    """Analyze impact of a global event."""
    from .services.event_analyzer import GlobalEventAnalyzer
    from decimal import Decimal

    async def _analyze():
        analyzer = GlobalEventAnalyzer()
        return await analyzer.analyze_event_impact(
            event_type, event_id, symbol, Decimal(str(price_before))
        )

    return asyncio.run(_analyze())


@shared_task
def get_event_summary(hours: int = 24):
    """Get event summary for the given time period."""
    from .services.event_analyzer import GlobalEventAnalyzer

    async def _get():
        analyzer = GlobalEventAnalyzer()
        return await analyzer.get_event_summary(hours)

    return asyncio.run(_get())


@shared_task
def cleanup_old_events(days: int = 90):
    """Clean up old events."""
    from .global_events import EconomicEvent, GlobalEventImpact
    from datetime import timedelta
    from django.utils import timezone

    cutoff = timezone.now() - timedelta(days=days)
    deleted = GlobalEventImpact.objects.filter(created_at__lt=cutoff).delete()[0]
    logger.info(f"Cleaned up {deleted} old event impacts")
    return {'deleted': deleted}
