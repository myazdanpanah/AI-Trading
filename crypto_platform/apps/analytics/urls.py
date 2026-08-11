from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .event_urls import urlpatterns as event_urlpatterns

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('', include(event_urlpatterns)),
]
