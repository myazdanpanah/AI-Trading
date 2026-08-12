"""Forecast serializers."""
from rest_framework import serializers
from .models import PriceForecast, ForecastCycle, ModelWeight


class PriceForecastSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceForecast
        fields = '__all__'


class ForecastCycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForecastCycle
        fields = '__all__'


class ModelWeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelWeight
        fields = '__all__'


class RunForecastInputSerializer(serializers.Serializer):
    symbols = serializers.ListField(
        child=serializers.CharField(max_length=10),
        default=['BTC', 'ETH', 'SOL', 'BNB', 'XRP'],
        help_text='List of symbols to forecast',
    )


class AccuracyStatsSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10, required=False)
    days = serializers.IntegerField(default=30, min_value=1, max_value=365)
