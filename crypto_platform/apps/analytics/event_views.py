"""Views for global events."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .global_events import (
    EconomicEvent, RegulatoryEvent, GeopoliticalEvent,
    BlockchainEvent, GlobalEventImpact
)
from .event_serializers import (
    EconomicEventSerializer, RegulatoryEventSerializer,
    GeopoliticalEventSerializer, BlockchainEventSerializer,
    GlobalEventImpactSerializer
)
from .event_tasks import (
    fetch_economic_calendar, get_upcoming_events,
    get_event_summary, analyze_event_impact
)


class EconomicEventViewSet(viewsets.ModelViewSet):
    """Manage economic events."""
    queryset = EconomicEvent.objects.all()
    serializer_class = EconomicEventSerializer
    filterset_fields = ['event_type', 'country', 'impact_level', 'is_released']
    ordering_fields = ['scheduled_date']
    ordering = ['scheduled_date']

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming events."""
        hours = int(request.query_params.get('hours', 24))
        from .services.economic_calendar import EconomicCalendarService
        import asyncio
        service = EconomicCalendarService()
        events = asyncio.run(service.get_upcoming_events(hours))
        return Response(events)

    @action(detail=False, methods=['post'])
    def fetch_calendar(self, request):
        """Trigger calendar fetch."""
        days = int(request.data.get('days_ahead', 7))
        task = fetch_economic_calendar.delay(days)
        return Response({
            'task_id': task.id,
            'message': 'Calendar fetch started'
        }, status=status.HTTP_202_ACCEPTED)


class RegulatoryEventViewSet(viewsets.ModelViewSet):
    """Manage regulatory events."""
    queryset = RegulatoryEvent.objects.all()
    serializer_class = RegulatoryEventSerializer
    filterset_fields = ['event_type', 'jurisdiction']
    search_fields = ['title', 'summary']
    ordering_fields = ['event_date']
    ordering = ['-event_date']


class GeopoliticalEventViewSet(viewsets.ModelViewSet):
    """Manage geopolitical events."""
    queryset = GeopoliticalEvent.objects.all()
    serializer_class = GeopoliticalEventSerializer
    filterset_fields = ['event_type', 'region']
    search_fields = ['title', 'summary']
    ordering_fields = ['event_date']
    ordering = ['-event_date']


class BlockchainEventViewSet(viewsets.ModelViewSet):
    """Manage blockchain events."""
    queryset = BlockchainEvent.objects.all()
    serializer_class = BlockchainEventSerializer
    filterset_fields = ['event_type', 'blockchain']
    search_fields = ['title', 'summary']
    ordering_fields = ['event_date']
    ordering = ['-event_date']

    @action(detail=False, methods=['get'])
    def recent_hacks(self, request):
        """Get recent security incidents."""
        from datetime import timedelta
        from django.utils import timezone

        days = int(request.query_params.get('days', 30))
        cutoff = timezone.now() - timedelta(days=days)

        hacks = BlockchainEvent.objects.filter(
            event_type__in=['hack', 'exploit', 'bridge_hack'],
            event_date__gte=cutoff
        ).order_by('-severity')[:20]

        serializer = self.get_serializer(hacks, many=True)
        return Response(serializer.data)


class GlobalEventImpactViewSet(viewsets.ModelViewSet):
    """Manage event impacts."""
    queryset = GlobalEventImpact.objects.all()
    serializer_class = GlobalEventImpactSerializer
    filterset_fields = ['event_type', 'symbol']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get event impact summary."""
        hours = int(request.query_params.get('hours', 24))
        from .services.event_analyzer import GlobalEventAnalyzer
        import asyncio
        analyzer = GlobalEventAnalyzer()
        summary = asyncio.run(analyzer.get_event_summary(hours))
        return Response(summary)
