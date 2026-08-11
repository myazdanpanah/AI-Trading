"""URLs for global events."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .event_views import (
    EconomicEventViewSet, RegulatoryEventViewSet,
    GeopoliticalEventViewSet, BlockchainEventViewSet,
    GlobalEventImpactViewSet
)

router = DefaultRouter()
router.register(r'economic', EconomicEventViewSet)
router.register(r'regulatory', RegulatoryEventViewSet)
router.register(r'geopolitical', GeopoliticalEventViewSet)
router.register(r'blockchain', BlockchainEventViewSet)
router.register(r'impacts', GlobalEventImpactViewSet)

urlpatterns = [
    path('events/', include(router.urls)),
]
