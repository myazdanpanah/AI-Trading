"""Learning serializers - Enhanced with input validation."""
from rest_framework import serializers
from .models import SignalResult, ModelPerformance, StrategyWeight, BacktestResult


class SignalResultSerializer(serializers.ModelSerializer):
    signal_symbol = serializers.CharField(source='signal.symbol', read_only=True)
    signal_direction = serializers.CharField(source='signal.direction', read_only=True)

    class Meta:
        model = SignalResult
        fields = '__all__'


class ModelPerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelPerformance
        fields = '__all__'


class StrategyWeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategyWeight
        fields = '__all__'


class BacktestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = BacktestResult
        fields = '__all__'


class RecordOutcomeInputSerializer(serializers.Serializer):
    """Input serializer for recording signal outcomes."""
    signal_id = serializers.UUIDField()
    exit_price = serializers.DecimalField(max_digits=20, decimal_places=8)
    profit_loss = serializers.DecimalField(max_digits=10, decimal_places=4, default=0)
    profit_loss_percent = serializers.DecimalField(max_digits=10, decimal_places=4, default=0)
    success = serializers.BooleanField(default=False)
    duration_hours = serializers.IntegerField(default=0)
    market_condition = serializers.CharField(max_length=50, required=False, default='')
    notes = serializers.CharField(required=False, default='')


class OptimizeWeightsInputSerializer(serializers.Serializer):
    """Input serializer for weight optimization."""
    window_days = serializers.IntegerField(default=30, min_value=7, max_value=365)
    min_signals = serializers.IntegerField(default=10, min_value=5, max_value=100)


class PredictQualityInputSerializer(serializers.Serializer):
    """Input serializer for quality prediction."""
    symbol = serializers.CharField(max_length=20, required=False)
    timeframe = serializers.CharField(max_length=10, required=False)
    direction = serializers.CharField(max_length=20, required=False)
    confidence = serializers.IntegerField(default=50, min_value=0, max_value=100)
