"""Serializers for global events."""
from rest_framework import serializers
from .global_events import (
    EconomicEvent, RegulatoryEvent, GeopoliticalEvent,
    BlockchainEvent, GlobalEventImpact
)


class EconomicEventSerializer(serializers.ModelSerializer):
    time_until = serializers.SerializerMethodField()

    class Meta:
        model = EconomicEvent
        fields = '__all__'

    def get_time_until(self, obj):
        from datetime import datetime
        if obj.scheduled_date:
            delta = obj.scheduled_date - datetime.now().replace(tzinfo=None)
            hours = delta.total_seconds() / 3600
            if hours < 0:
                return 'Passed'
            elif hours < 24:
                return f'{hours:.1f} hours'
            else:
                return f'{hours/24:.1f} days'
        return None


class RegulatoryEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegulatoryEvent
        fields = '__all__'


class GeopoliticalEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeopoliticalEvent
        fields = '__all__'


class BlockchainEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockchainEvent
        fields = '__all__'


class GlobalEventImpactSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalEventImpact
        fields = '__all__'
