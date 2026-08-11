from django.contrib import admin
from .models import Trader, FollowRelationship, CopyTrade, TraderSignal, SocialComment


@admin.register(Trader)
class TraderAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'win_rate', 'profit_factor', 'followers_count', 
                    'allow_copy_trading', 'is_public']
    list_filter = ['is_public', 'allow_copy_trading']
    search_fields = ['display_name', 'user__username']


@admin.register(FollowRelationship)
class FollowRelationshipAdmin(admin.ModelAdmin):
    list_display = ['follower', 'trader', 'copy_trading', 'created_at']
    list_filter = ['copy_trading']


@admin.register(CopyTrade)
class CopyTradeAdmin(admin.ModelAdmin):
    list_display = ['follower', 'trader', 'symbol', 'direction', 'pnl', 'status']
    list_filter = ['status', 'direction']
    search_fields = ['symbol']


@admin.register(TraderSignal)
class TraderSignalAdmin(admin.ModelAdmin):
    list_display = ['trader', 'is_premium', 'likes_count', 'comments_count', 'created_at']
    list_filter = ['is_premium']


@admin.register(SocialComment)
class SocialCommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'trader_signal', 'created_at']
