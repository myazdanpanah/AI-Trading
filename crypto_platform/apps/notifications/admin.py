"""Notification admin with webhook configuration."""
from django.contrib import admin
from .models import (
    NotificationChannel, NotificationRule, Notification,
    WebhookConfiguration, WebhookLog
)


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'channel_type', 'is_active', 'created_at']
    list_filter = ['channel_type', 'is_active']
    search_fields = ['name']


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'event_type', 'is_active', 'created_at']
    list_filter = ['event_type', 'is_active']
    search_fields = ['name']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
    search_fields = ['title', 'message']


@admin.register(WebhookConfiguration)
class WebhookConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user', 'provider', 'is_active',
        'notify_signals', 'notify_trades', 'notify_risk',
        'trigger_count', 'last_triggered',
    ]
    list_filter = ['provider', 'is_active', 'notify_signals', 'notify_trades', 'notify_risk']
    search_fields = ['name', 'url', 'user__email']
    readonly_fields = ['last_triggered', 'trigger_count', 'created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'url', 'provider', 'is_active')
        }),
        ('Event Subscriptions', {
            'fields': ('notify_signals', 'notify_trades', 'notify_risk', 'notify_performance')
        }),
        ('Thresholds', {
            'fields': ('min_confidence', 'priority_threshold')
        }),
        ('Statistics', {
            'fields': ('last_triggered', 'trigger_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ['configuration', 'event_type', 'status', 'status_code', 'created_at']
    list_filter = ['status', 'event_type', 'created_at']
    search_fields = ['configuration__name', 'error_message']
    readonly_fields = [
        'configuration', 'event_type', 'status', 'status_code',
        'response_body', 'error_message', 'payload', 'created_at',
    ]
    date_hierarchy = 'created_at'
