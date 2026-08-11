from django.contrib import admin
from .models import Exchange, TradingPair, Candle, OrderBook, DerivativesData, WhaleAlert

@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'api_status', 'created_at']
    list_filter = ['api_status']
    search_fields = ['name']


@admin.register(TradingPair)
class TradingPairAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'exchange', 'base_asset', 'quote_asset', 'is_active']
    list_filter = ['exchange', 'is_active']
    search_fields = ['symbol']


@admin.register(Candle)
class CandleAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'timeframe', 'open', 'high', 'low', 'close', 'volume', 'timestamp']
    list_filter = ['symbol', 'timeframe']
    ordering = ['-timestamp']


@admin.register(OrderBook)
class OrderBookAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'bid_volume', 'ask_volume', 'spread', 'timestamp']
    list_filter = ['symbol']


@admin.register(DerivativesData)
class DerivativesDataAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'funding_rate', 'open_interest', 'long_short_ratio', 'timestamp']
    list_filter = ['symbol']


@admin.register(WhaleAlert)
class WhaleAlertAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'amount', 'usd_value', 'transaction_type', 'timestamp']
    list_filter = ['transaction_type']
