"""Mobile app serializers."""
from rest_framework import serializers
from .models import DeviceToken, MobileAlert, MobileWidget


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['id', 'token', 'platform', 'device_name', 'is_active', 'last_used']
        read_only_fields = ['id', 'last_used']


class MobileAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileAlert
        fields = ['id', 'name', 'symbol', 'alert_type', 'threshold', 'is_active', 
                  'triggered_count', 'last_triggered', 'created_at']
        read_only_fields = ['id', 'triggered_count', 'last_triggered', 'created_at']


class MobileWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileWidget
        fields = ['id', 'widget_type', 'config', 'position', 'is_visible', 'created_at']
        read_only_fields = ['id', 'created_at']
