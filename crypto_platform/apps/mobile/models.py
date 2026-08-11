"""Mobile app models - Push notifications and mobile-specific features."""
import uuid
from django.db import models
from django.conf import settings


class DeviceToken(models.Model):
    """Mobile device push notification token."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='device_tokens')
    token = models.CharField(max_length=500, unique=True)
    platform = models.CharField(max_length=20, choices=[
        ('ios', 'iOS'),
        ('android', 'Android'),
    ])
    device_name = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'device token'
        verbose_name_plural = 'device tokens'
        db_table = 'mobile_device_tokens'

    def __str__(self):
        return f"{self.user} - {self.platform}"


class MobileAlert(models.Model):
    """Mobile-specific alert configuration."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mobile_alerts')
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20)
    alert_type = models.CharField(max_length=30, choices=[
        ('price_above', 'Price Above'),
        ('price_below', 'Price Below'),
        ('change_pct', 'Change %'),
        ('volume_spike', 'Volume Spike'),
        ('signal_buy', 'Buy Signal'),
        ('signal_sell', 'Sell Signal'),
    ])
    threshold = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    is_active = models.BooleanField(default=True)
    triggered_count = models.IntegerField(default=0)
    last_triggered = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'mobile alert'
        verbose_name_plural = 'mobile alerts'
        db_table = 'mobile_alerts'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.symbol}"


class MobileWidget(models.Model):
    """Mobile widget configuration."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mobile_widgets')
    widget_type = models.CharField(max_length=30, choices=[
        ('price_ticker', 'Price Ticker'),
        ('portfolio_summary', 'Portfolio Summary'),
        ('signal_list', 'Signal List'),
        ('watchlist', 'Watchlist'),
    ])
    config = models.JSONField(default=dict)
    position = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'mobile widget'
        verbose_name_plural = 'mobile widgets'
        db_table = 'mobile_widgets'
        ordering = ['position']

    def __str__(self):
        return f"{self.widget_type} - {self.user}"
