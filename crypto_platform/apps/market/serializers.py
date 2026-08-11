"""Market serializers."""
from rest_framework import serializers
from .models import Exchange, TradingPair, Candle, OrderBook, DerivativesData, WhaleAlert


class ExchangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exchange
        fields = '__all__'


class TradingPairSerializer(serializers.ModelSerializer):
    exchange_name = serializers.CharField(source='exchange.name', read_only=True)

    class Meta:
        model = TradingPair
        fields = '__all__'


class CandleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candle
        fields = ['id', 'symbol', 'timeframe', 'open', 'high', 'low', 'close', 'volume', 'timestamp', 'created_at']
        read_only_fields = ['id', 'created_at']


class OrderBookSerializer(serializers.ModelSerializer):
    spread_display = serializers.SerializerMethodField()

    class Meta:
        model = OrderBook
        fields = '__all__'

    def get_spread_display(self, obj):
        if obj.spread:
            return f"{obj.spread:.8f}"
        return "0"


class DerivativesDataSerializer(serializers.ModelSerializer):
    funding_rate_display = serializers.SerializerMethodField()

    class Meta:
        model = DerivativesData
        fields = '__all__'

    def get_funding_rate_display(self, obj):
        return f"{obj.funding_rate * 100:.4f}%"


class WhaleAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhaleAlert
        fields = '__all__'
