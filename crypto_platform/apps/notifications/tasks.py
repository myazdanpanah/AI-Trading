"""Celery tasks for webhook delivery."""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_webhook_task(
    self,
    url: str,
    provider: str,
    title: str,
    message: str,
    priority: str = 'medium',
    data: dict = None
):
    """Send webhook asynchronously with retry logic."""
    from apps.notifications.services.webhook_service import (
        WebhookService, WebhookProvider, WebhookMessage, WebhookPriority
    )
    
    try:
        service = WebhookService()
        
        # Create message
        webhook_message = WebhookMessage(
            title=title,
            message=message,
            priority=WebhookPriority(priority),
            data=data,
        )
        
        # Get provider enum
        provider_enum = WebhookProvider(provider)
        
        # Send webhook
        result = service.send_webhook(url, provider_enum, webhook_message)
        
        if not result['success']:
            # Retry on failure
            raise Exception(result.get('error', 'Unknown error'))
        
        logger.info(f"Webhook sent successfully to {provider}: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Webhook failed: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def send_signal_alert_task(url: str, provider: str, signal_data: dict):
    """Send signal alert webhook."""
    from apps.notifications.services.webhook_service import WebhookService, WebhookProvider
    
    service = WebhookService()
    provider_enum = WebhookProvider(provider)
    
    return service.send_signal_alert(url, provider_enum, signal_data)


@shared_task
def send_trade_alert_task(url: str, provider: str, trade_data: dict):
    """Send trade execution alert."""
    from apps.notifications.services.webhook_service import WebhookService, WebhookProvider
    
    service = WebhookService()
    provider_enum = WebhookProvider(provider)
    
    return service.send_trade_alert(url, provider_enum, trade_data)


@shared_task
def send_risk_alert_task(url: str, provider: str, risk_data: dict):
    """Send risk alert."""
    from apps.notifications.services.webhook_service import WebhookService, WebhookProvider
    
    service = WebhookService()
    provider_enum = WebhookProvider(provider)
    
    return service.send_risk_alert(url, provider_enum, risk_data)


@shared_task
def batch_send_webhooks_task(webhooks: list):
    """Send multiple webhooks in batch."""
    from apps.notifications.services.webhook_service import WebhookService
    
    service = WebhookService()
    results = []
    
    for webhook in webhooks:
        try:
            result = service.send_webhook(
                url=webhook['url'],
                provider=webhook['provider'],
                message=webhook['message'],
            )
            results.append(result)
        except Exception as e:
            results.append({'success': False, 'error': str(e)})
    
    return results
