"""Celery app configuration with beat schedule."""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crypto_platform.settings')

from celery import Celery

app = Celery('crypto_platform')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat Schedule for Feedback Loop
app.conf.beat_schedule = {
    # Daily feedback cycle - analyze yesterday's signals
    'feedback-daily-cycle': {
        'task': 'feedback.run_daily_cycle',
        'schedule': {
            'hour': 1,
            'minute': 0,
        },
        'kwargs': {'lookback_days': 1},
    },
    # Weekly comprehensive feedback cycle
    'feedback-weekly-cycle': {
        'task': 'feedback.run_weekly_cycle',
        'schedule': {
            'day_of_week': 'sunday',
            'hour': 2,
            'minute': 0,
        },
        'kwargs': {'lookback_days': 7},
    },
    # Cleanup old memories monthly
    'feedback-cleanup-monthly': {
        'task': 'feedback.cleanup_old_memories',
        'schedule': {
            'day_of_month': '1',
            'hour': 3,
            'minute': 0,
        },
        'kwargs': {'days_to_keep': 90},
    },
}
