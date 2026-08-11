"""Signal serializers - Full CRUD + analysis endpoints."""
from rest_framework import serializers
from .models import (
    Signal, SignalReason, SignalGenerationRequest,
    FactorWeight, RiskProfile, PortfolioPosition,
    SignalPerformance, BacktestResult,
)


class SignalReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignalReason
        fields = '__all__'


class SignalSerializer(serializers.ModelSerializer):
    reasons = SignalReasonSerializer(many=True, read_only=True)

    class Meta:
        model = Signal
        fields = '__all__'


class SignalGenerationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignalGenerationRequest
        fields = '__all__'


class FactorWeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactorWeight
        fields = '__all__'


class RiskProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskProfile
        fields = '__all__'


class PortfolioPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioPosition
        fields = '__all__'


class SignalPerformanceSerializer(serializers.ModelSerializer):
    signal_symbol = serializers.CharField(source='signal.symbol', read_only=True)
    signal_direction = serializers.CharField(source='signal.direction', read_only=True)

    class Meta:
        model = SignalPerformance
        fields = '__all__'


class BacktestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = BacktestResult
        fields = '__all__'


class SignalGenerationInputSerializer(serializers.Serializer):
    """Input serializer for signal generation endpoint."""
    symbol = serializers.CharField(max_length=20)
    timeframe = serializers.CharField(max_length=10, default='1h')
    current_price = serializers.DecimalField(max_digits=20, decimal_places=8, required=False)
    technical_data = serializers.DictField(required=False, default=dict)
    sentiment_data = serializers.DictField(required=False, default=dict)
    news_data = serializers.DictField(required=False, default=dict)
    ai_data = serializers.DictField(required=False, default=dict)
    macro_data = serializers.DictField(required=False, default=dict)


class RiskCalculationInputSerializer(serializers.Serializer):
    """Input serializer for risk calculation endpoint."""
    account_balance = serializers.DecimalField(max_digits=20, decimal_places=2)
    entry_price = serializers.DecimalField(max_digits=20, decimal_places=8)
    stop_loss = serializers.DecimalField(max_digits=20, decimal_places=8)
    signal_confidence = serializers.IntegerField(default=50)
    signal_direction = serializers.CharField(max_length=20)


class BacktestInputSerializer(serializers.Serializer):
    """Input serializer for backtest endpoint."""
    strategy_name = serializers.CharField(max_length=100)
    symbol = serializers.CharField(max_length=20)
    timeframe = serializers.CharField(max_length=10, default='1h')
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    initial_capital = serializers.DecimalField(max_digits=20, decimal_places=2, default=10000)
