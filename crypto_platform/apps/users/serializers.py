"""User serializers."""
from rest_framework import serializers
from .models import User, UserProfile, UserWatchlist


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'avatar', 'preferred_ai_provider', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'risk_level', 'favorite_symbols', 'notification_settings', 'timezone']


class UserWatchlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWatchlist
        fields = ['id', 'symbol', 'display_name', 'coin_id', 'order', 'is_favorite', 'price_alert_above', 'price_alert_below', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserWatchlistCreateSerializer(serializers.Serializer):
    """Batch create/update watchlist."""
    symbols = serializers.ListField(child=serializers.DictField(), write_only=True)
    # Each dict: {symbol, display_name, coin_id, is_favorite, order}

