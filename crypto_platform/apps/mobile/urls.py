"""Mobile app URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'devices', views.DeviceTokenViewSet, basename='device')
router.register(r'alerts', views.MobileAlertViewSet, basename='mobile-alert')
router.register(r'widgets', views.MobileWidgetViewSet, basename='mobile-widget')

urlpatterns = [
    path('', include(router.urls)),
]
