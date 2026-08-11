"""Feedback Loop serializers."""
from rest_framework import serializers
from .models import MarketMemory, SignalMemory, PatternMemory, LearningInsight, FeedbackCycle


class MarketMemorySerializer(serializers.ModelSerializer):
    """Serializer for MarketMemory."""
    class Meta:
        model = MarketMemory
        fields = '__all__'


class SignalMemorySerializer(serializers.ModelSerializer):
    """Serializer for SignalMemory."""
    signal_symbol = serializers.CharField(source='signal.symbol', read_only=True)
    signal_direction_display = serializers.CharField(source='signal.direction', read_only=True)
    
    class Meta:
        model = SignalMemory
        fields = '__all__'


class PatternMemorySerializer(serializers.ModelSerializer):
    """Serializer for PatternMemory."""
    class Meta:
        model = PatternMemory
        fields = '__all__'


class LearningInsightSerializer(serializers.ModelSerializer):
    """Serializer for LearningInsight."""
    class Meta:
        model = LearningInsight
        fields = '__all__'


class FeedbackCycleSerializer(serializers.ModelSerializer):
    """Serializer for FeedbackCycle."""
    win_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = FeedbackCycle
        fields = '__all__'
    
    def get_win_rate(self, obj):
        if obj.signals_evaluated > 0:
            return round(obj.signals_correct / obj.signals_evaluated * 100, 2)
        return 0


class SimilaritySearchInputSerializer(serializers.Serializer):
    """Input serializer for similarity search."""
    symbol = serializers.CharField(max_length=20)
    timeframe = serializers.CharField(max_length=10, default='1h')
    price = serializers.DecimalField(max_digits=20, decimal_places=8)
    price_change_1h = serializers.FloatField(default=0)
    price_change_24h = serializers.FloatField(default=0)
    price_change_7d = serializers.FloatField(default=0)
    volume_ratio = serializers.FloatField(default=1.0)
    rsi = serializers.FloatField(default=50)
    macd_signal = serializers.FloatField(default=0)
    ema_trend = serializers.FloatField(default=0)
    adx = serializers.FloatField(default=25)
    fear_greed_index = serializers.FloatField(default=50)
    social_sentiment = serializers.FloatField(default=0)
    atr_percent = serializers.FloatField(default=2.0)
    limit = serializers.IntegerField(default=5, min_value=1, max_value=20)
    min_similarity = serializers.FloatField(default=0.7, min_value=0, max_value=1)


class SignalPredictionInputSerializer(serializers.Serializer):
    """Input serializer for signal prediction based on similarity."""
    symbol = serializers.CharField(max_length=20)
    timeframe = serializers.CharField(max_length=10, default='1h')
    price = serializers.DecimalField(max_digits=20, decimal_places=8)
    signal_direction = serializers.ChoiceField(
        choices=['buy', 'strong_buy', 'sell', 'strong_sell', 'hold']
    )
    price_change_1h = serializers.FloatField(default=0)
    price_change_24h = serializers.FloatField(default=0)
    volume_ratio = serializers.FloatField(default=1.0)
    rsi = serializers.FloatField(default=50)
    macd_signal = serializers.FloatField(default=0)
    ema_trend = serializers.FloatField(default=0)
    fear_greed_index = serializers.FloatField(default=50)


class PerformanceAnalysisInputSerializer(serializers.Serializer):
    """Input serializer for performance analysis."""
    lookback_days = serializers.IntegerField(default=30, min_value=1, max_value=365)
    symbol = serializers.CharField(max_length=20, required=False)
    min_signals = serializers.IntegerField(default=10, min_value=5, max_value=100)


class FeedbackCycleInputSerializer(serializers.Serializer):
    """Input serializer for running a feedback cycle."""
    cycle_type = serializers.ChoiceField(
        choices=['daily', 'weekly', 'signal_based', 'regime_change', 'manual'],
        default='daily'
    )
    lookback_days = serializers.IntegerField(default=1, min_value=1, max_value=30)
    symbol = serializers.CharField(max_length=20, required=False)


class RecordSignalOutcomeInputSerializer(serializers.Serializer):
    """Input serializer for recording a signal outcome for learning."""
    signal_id = serializers.UUIDField()
    exit_price = serializers.DecimalField(max_digits=20, decimal_places=8)
    profit_loss_percent = serializers.DecimalField(max_digits=10, decimal_places=4)
    holding_period_hours = serializers.IntegerField(default=0)
    market_condition = serializers.CharField(max_length=50, required=False, default='')
    notes = serializers.CharField(required=False, default='')
