"""Report models."""
import uuid
from django.db import models


class Report(models.Model):
    """Generated reports."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(
        max_length=30,
        choices=[
            ('daily_market', 'Daily Market Report'),
            ('weekly_ai', 'Weekly AI Report'),
            ('signal_performance', 'Signal Performance'),
            ('portfolio', 'Portfolio Report'),
            ('learning', 'Learning Report'),
        ]
    )
    title = models.CharField(max_length=200)
    content = models.JSONField(default=dict)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    generated_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'report'
        verbose_name_plural = 'reports'
        db_table = 'reports'
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.report_type} - {self.generated_at}"
