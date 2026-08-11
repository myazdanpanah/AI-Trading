"""Social trading models - Follow traders and copy trading."""
import uuid
from django.db import models
from django.conf import settings


class Trader(models.Model):
    """Trader profile for social trading."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trader_profile')
    display_name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)
    is_public = models.BooleanField(default=False)
    
    # Performance metrics
    total_signals = models.IntegerField(default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    avg_return = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    profit_factor = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    # Social metrics
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    
    # Settings
    allow_copy_trading = models.BooleanField(default=False)
    copy_trading_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'trader'
        verbose_name_plural = 'traders'
        db_table = 'social_traders'
        ordering = ['-win_rate']

    def __str__(self):
        return f"{self.display_name} ({self.win_rate}% win rate)"


class FollowRelationship(models.Model):
    """Follow relationship between users."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following')
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE, related_name='followers')
    copy_trading = models.BooleanField(default=False)
    copy_position_size_percent = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    max_copy_amount_usd = models.DecimalField(max_digits=20, decimal_places=2, default=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'follow relationship'
        verbose_name_plural = 'follow relationships'
        db_table = 'social_follows'
        unique_together = ['follower', 'trader']

    def __str__(self):
        return f"{self.follower} follows {self.trader}"


class CopyTrade(models.Model):
    """Copied trade from a followed trader."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='copy_trades')
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE, related_name='copied_trades')
    original_signal = models.ForeignKey('signals.Signal', on_delete=models.SET_NULL, null=True)
    
    symbol = models.CharField(max_length=20)
    direction = models.CharField(max_length=10)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    entry_price = models.DecimalField(max_digits=20, decimal_places=8)
    current_price = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    pnl = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    pnl_percent = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    status = models.CharField(max_length=20, choices=[
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('failed', 'Failed'),
    ], default='open')
    
    fee_paid = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'copy trade'
        verbose_name_plural = 'copy trades'
        db_table = 'social_copy_trades'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower} copied {self.trader}: {self.symbol} {self.direction}"


class TraderSignal(models.Model):
    """Public signal shared by a trader."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE, related_name='signals')
    signal = models.ForeignKey('signals.Signal', on_delete=models.CASCADE, related_name='shared_signals')
    
    commentary = models.TextField(blank=True)
    is_premium = models.BooleanField(default=False)
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'trader signal'
        verbose_name_plural = 'trader signals'
        db_table = 'social_trader_signals'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.trader}: {self.signal}"


class SocialComment(models.Model):
    """Comment on a trader signal."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trader_signal = models.ForeignKey(TraderSignal, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'social comment'
        verbose_name_plural = 'social comments'
        db_table = 'social_comments'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user}: {self.content[:50]}"
