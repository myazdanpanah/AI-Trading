"""Feedback Loop app configuration."""
from django.apps import AppConfig


class FeedbackConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.feedback'
    verbose_name = 'Feedback Loop'
    # Explicit app_label prevents Django's module resolution issues
    # when the same module can be imported via multiple paths
    app_label = 'feedback'
