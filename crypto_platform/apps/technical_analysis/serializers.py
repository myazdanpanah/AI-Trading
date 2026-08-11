"""Technical Analysis serializers."""
from rest_framework import serializers
from .models import (
    TechnicalIndicator, TechnicalPattern, SupportResistance,
    TrendAnalysis, SmartMoneyEvent, TechnicalAnalysisResult
)


class TechnicalIndicatorSerializer(serializers.ModelSerializer):
    """Serializer for Technical Indicator."""
    class Meta:
        model = TechnicalIndicator
        fields = '__all__'


class TechnicalPatternSerializer(serializers.ModelSerializer):
    """Serializer for Technical Pattern."""
    class Meta:
        model = TechnicalPattern
        fields = '__all__'


class SupportResistanceSerializer(serializers.ModelSerializer):
    """Serializer for Support/Resistance levels."""
    class Meta:
        model = SupportResistance
        fields = '__all__'


class TrendAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for Trend Analysis."""
    class Meta:
        model = TrendAnalysis
        fields = '__all__'


class SmartMoneyEventSerializer(serializers.ModelSerializer):
    """Serializer for Smart Money Event."""
    class Meta:
        model = SmartMoneyEvent
        fields = '__all__'


class TechnicalAnalysisResultSerializer(serializers.ModelSerializer):
    """Serializer for combined Technical Analysis Result."""
    class Meta:
        model = TechnicalAnalysisResult
        fields = '__all__'


class AnalysisRequestSerializer(serializers.Serializer):
    """Serializer for analysis request."""
    symbol = serializers.CharField(max_length=20)
    timeframe = serializers.ChoiceField(
        choices=['1m', '5m', '15m', '1h', '4h', '1d', '1w']
    )
    indicators = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=['rsi', 'macd', 'bollinger_bands', 'ema']
    )
    include_patterns = serializers.BooleanField(default=True)
    include_sr = serializers.BooleanField(default=True)
    include_trend = serializers.BooleanField(default=True)
    include_smart_money = serializers.BooleanField(default=True)



