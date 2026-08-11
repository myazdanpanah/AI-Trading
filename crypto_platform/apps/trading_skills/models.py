"""Models for trading skill results and history."""
import uuid
from django.db import models


class RegimeAnalysis(models.Model):
    """Store crypto regime analysis results."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    composite_score = models.FloatField(null=True, blank=True)
    zone = models.CharField(max_length=20)  # RISK_ON, NEUTRAL, RISK_OFF, UNKNOWN
    guidance = models.TextField(blank=True)
    components = models.JSONField(default=dict)
    exposure_posture = models.JSONField(default=dict)
    universe_size = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'regime_analysis'
        ordering = ['-created_at']

    def __str__(self):
        return f"Regime: {self.zone} ({self.composite_score}/100) @ {self.created_at}"


class SignalReview(models.Model):
    """Store signal postmortem reviews."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    signal_id = models.CharField(max_length=100, blank=True)
    symbol = models.CharField(max_length=20)
    direction = models.CharField(max_length=10)  # buy/sell
    entry_price = models.DecimalField(max_digits=20, decimal_places=8)
    exit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    pnl_pct = models.FloatField(null=True, blank=True)
    lesson_learned = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'signal_reviews'
        ordering = ['-created_at']

    def __str__(self):
        return f"Review: {self.symbol} {self.direction} @ {self.created_at}"


class SkillUsageLog(models.Model):
    """Track which skills are used and when."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    skill_name = models.CharField(max_length=100)
    input_params = models.JSONField(default=dict)
    output_summary = models.JSONField(default=dict)
    execution_time_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'skill_usage_log'
        ordering = ['-created_at']
