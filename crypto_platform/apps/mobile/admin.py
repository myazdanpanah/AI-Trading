from django.contrib import admin
from .models import DeviceToken, MobileAlert, MobileWidget


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'device_name', 'is_active', 'last_used']
    list_filter = ['platform', 'is_active']
    search_fields = ['user__username', 'device_name']


@admin.register(MobileAlert)
class MobileAlertAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'symbol', 'alert_type', 'is_active', 'triggered_count']
    list_filter = ['alert_type', 'is_active']
    search_fields = ['name', 'symbol']


@admin.register(MobileWidget)
class MobileWidgetAdmin(admin.ModelAdmin):
    list_display = ['widget_type', 'user', 'position', 'is_visible']
    list_filter = ['widget_type', 'is_visible']
