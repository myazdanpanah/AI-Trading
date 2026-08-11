"""Notification and webhook configuration models."""
import uuid
from django.db import models
from django.conf import settings


class NotificationChannel(models.Model):
    """Channel configuration for notifications."""
    name = models.CharField(max_length=100)
    channel_type = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('telegram', 'Telegram'),
            ('discord', 'Discord'),
            ('slack', 'Slack'),
            ('sms', 'SMS'),
            ('webhook', 'Webhook'),
        ]
    )
    config = models.JSONField(default=dict, help_text='Channel-specific configuration')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.channel_type})"


class NotificationRule(models.Model):
    """Rules for when to send notifications."""
    name = models.CharField(max_length=100)
    event_type = models.CharField(
        max_length=50,
        choices=[
            ('signal', 'New Signal'),
            ('trade', 'Trade Execution'),
            ('risk', 'Risk Alert'),
            ('performance', 'Performance Report'),
            ('system', 'System Alert'),
        ]
    )
    is_active = models.BooleanField(default=True)
    conditions = models.JSONField(default=dict, help_text='Conditions that trigger this rule')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.event_type})"


class Notification(models.Model):
    """Individual notification instance."""
    channel = models.ForeignKey(
        NotificationChannel,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50,
        choices=[
            ('info', 'Information'),
            ('warning', 'Warning'),
            ('error', 'Error'),
            ('success', 'Success'),
        ],
        default='info'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.status}"


class WebhookConfiguration(models.Model):
    """User-configurable webhook settings."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='webhook_configs'
    )
    name = models.CharField(max_length=100, help_text='Friendly name for this webhook')
    url = models.URLField(help_text='Webhook endpoint URL')
    provider = models.CharField(
        max_length=20,
        choices=[
            ('slack', 'Slack'),
            ('discord', 'Discord'),
            ('telegram', 'Telegram'),
            ('custom', 'Custom'),
        ],
        default='custom'
    )
    is_active = models.BooleanField(default=True)
    
    # Event subscriptions
    notify_signals = models.BooleanField(default=True, help_text='Notify on new signals')
    notify_trades = models.BooleanField(default=True, help_text='Notify on trade executions')
    notify_risk = models.BooleanField(default=True, help_text='Notify on risk alerts')
    notify_performance = models.BooleanField(default=False, help_text='Notify on performance reports')
    
    # Configuration
    min_confidence = models.IntegerField(
        default=70,
        help_text='Minimum signal confidence to trigger webhook (0-100)'
    )
    priority_threshold = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium'
    )
    
    # Metadata
    last_triggered = models.DateTimeField(null=True, blank=True)
    trigger_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'webhook configuration'
        verbose_name_plural = 'webhook configurations'
        ordering = ['-created_at']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.provider}) - {'Active' if self.is_active else 'Inactive'}"
    
    def increment_trigger_count(self):
        """Increment trigger count and update last triggered time."""
        from django.utils import timezone
        self.trigger_count += 1
        self.last_triggered = timezone.now()
        self.save(update_fields=['trigger_count', 'last_triggered'])


class WebhookLog(models.Model):
    """Log of webhook deliveries."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    configuration = models.ForeignKey(
        WebhookConfiguration,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    event_type = models.CharField(max_length=50)  # signal, trade, risk, performance
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('pending', 'Pending'),
        ]
    )
    status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    payload = models.JSONField(default=dict, help_text='Webhook payload sent')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'webhook log'
        verbose_name_plural = 'webhook logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.event_type} - {self.status} at {self.created_at}"
