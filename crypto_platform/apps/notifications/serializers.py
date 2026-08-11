"""Notification serializers including webhook configuration."""
from rest_framework import serializers
from .models import (
    NotificationChannel, NotificationRule, Notification,
    WebhookConfiguration, WebhookLog
)


class NotificationChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationChannel
        fields = '__all__'


class NotificationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationRule
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


class WebhookConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for webhook configuration."""
    last_triggered = serializers.DateTimeField(read_only=True)
    trigger_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = WebhookConfiguration
        fields = [
            'id', 'name', 'url', 'provider', 'is_active',
            'notify_signals', 'notify_trades', 'notify_risk', 'notify_performance',
            'min_confidence', 'priority_threshold',
            'last_triggered', 'trigger_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'last_triggered', 'trigger_count', 'created_at', 'updated_at']
    
    def validate_url(self, value):
        """Validate webhook URL."""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(value)
            if parsed.scheme not in ('http', 'https'):
                raise serializers.ValidationError('URL must use http or https scheme')
            return value
        except Exception:
            raise serializers.ValidationError('Invalid URL format')


class WebhookLogSerializer(serializers.ModelSerializer):
    """Serializer for webhook logs."""
    configuration_name = serializers.CharField(source='configuration.name', read_only=True)
    
    class Meta:
        model = WebhookLog
        fields = [
            'id', 'configuration', 'configuration_name', 'event_type',
            'status', 'status_code', 'error_message', 'created_at',
        ]
        read_only_fields = fields


class WebhookTestSerializer(serializers.Serializer):
    """Serializer for testing webhook delivery."""
    url = serializers.URLField()
    provider = serializers.ChoiceField(choices=['slack', 'discord', 'telegram', 'custom'])
    message = serializers.CharField(max_length=500, default='Test webhook from Crypto AI Platform')
