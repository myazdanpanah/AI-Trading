"""Celery tasks for users."""
from celery import shared_task


@shared_task
def example_task():
    """Placeholder task."""
    pass
