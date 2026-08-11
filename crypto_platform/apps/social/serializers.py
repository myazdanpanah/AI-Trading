"""Social trading serializers."""
from rest_framework import serializers
from .models import Trader, FollowRelationship, CopyTrade, TraderSignal, SocialComment


class TraderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trader
        fields = ['id', 'display_name', 'bio', 'avatar_url', 'is_public',
                  'total_signals', 'win_rate', 'avg_return', 'sharpe_ratio',
                  'max_drawdown', 'profit_factor', 'followers_count', 
                  'following_count', 'allow_copy_trading', 'copy_trading_fee_percent',
                  'created_at']
        read_only_fields = ['id', 'total_signals', 'win_rate', 'avg_return',
                           'sharpe_ratio', 'max_drawdown', 'profit_factor',
                           'followers_count', 'following_count', 'created_at']


class FollowRelationshipSerializer(serializers.ModelSerializer):
    trader = TraderSerializer(read_only=True)
    
    class Meta:
        model = FollowRelationship
        fields = ['id', 'trader', 'copy_trading', 'copy_position_size_percent',
                  'max_copy_amount_usd', 'created_at']
        read_only_fields = ['id', 'created_at']


class CopyTradeSerializer(serializers.ModelSerializer):
    trader = TraderSerializer(read_only=True)
    
    class Meta:
        model = CopyTrade
        fields = ['id', 'trader', 'symbol', 'direction', 'quantity', 'entry_price',
                  'current_price', 'pnl', 'pnl_percent', 'status', 'fee_paid',
                  'created_at', 'closed_at']
        read_only_fields = ['id', 'current_price', 'pnl', 'pnl_percent', 
                           'fee_paid', 'created_at', 'closed_at']


class TraderSignalSerializer(serializers.ModelSerializer):
    trader = TraderSerializer(read_only=True)
    
    class Meta:
        model = TraderSignal
        fields = ['id', 'trader', 'signal', 'commentary', 'is_premium',
                  'likes_count', 'comments_count', 'created_at']
        read_only_fields = ['id', 'likes_count', 'comments_count', 'created_at']


class SocialCommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = SocialComment
        fields = ['id', 'trader_signal', 'user', 'username', 'content', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
