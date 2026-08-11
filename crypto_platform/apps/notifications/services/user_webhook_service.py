"""User webhook service for managing and triggering configured webhooks."""
import logging
from typing import Dict, Any, List, Optional
from django.utils import timezone
from django.db.models import Q

from apps.notifications.models import WebhookConfiguration, WebhookLog
from apps.notifications.services.webhook_service import (
    WebhookService, WebhookProvider, WebhookMessage, WebhookPriority
)

logger = logging.getLogger(__name__)


class UserWebhookService:
    """Service for managing user-configured webhooks."""
    
    def __init__(self):
        self.webhook_service = WebhookService()
    
    def get_user_webhooks(
        self,
        user,
        active_only: bool = True
    ) -> List[WebhookConfiguration]:
        """Get all webhooks for a user."""
        queryset = WebhookConfiguration.objects.filter(user=user)
        if active_only:
            queryset = queryset.filter(is_active=True)
        return list(queryset)
    
    def create_webhook(
        self,
        user,
        name: str,
        url: str,
        provider: str = 'custom',
        **kwargs
    ) -> WebhookConfiguration:
        """Create a new webhook configuration."""
        return WebhookConfiguration.objects.create(
            user=user,
            name=name,
            url=url,
            provider=provider,
            **kwargs
        )
    
    def update_webhook(
        self,
        webhook_id: str,
        user,
        **kwargs
    ) -> Optional[WebhookConfiguration]:
        """Update a webhook configuration."""
        try:
            webhook = WebhookConfiguration.objects.get(id=webhook_id, user=user)
            for key, value in kwargs.items():
                setattr(webhook, key, value)
            webhook.save()
            return webhook
        except WebhookConfiguration.DoesNotExist:
            return None
    
    def delete_webhook(self, webhook_id: str, user) -> bool:
        """Delete a webhook configuration."""
        try:
            webhook = WebhookConfiguration.objects.get(id=webhook_id, user=user)
            webhook.delete()
            return True
        except WebhookConfiguration.DoesNotExist:
            return False
    
    def trigger_webhooks(
        self,
        event_type: str,
        data: Dict[str, Any],
        min_confidence: int = 0
    ) -> List[Dict[str, Any]]:
        """Trigger all matching webhooks for an event."""
        results = []
        
        # Get all active webhooks that subscribe to this event
        webhooks = WebhookConfiguration.objects.filter(
            is_active=True,
            **self._get_event_filter(event_type)
        )
        
        for webhook in webhooks:
            # Check confidence threshold
            if event_type == 'signal' and data.get('confidence', 0) < webhook.min_confidence:
                continue
            
            # Send webhook
            result = self._send_webhook(webhook, event_type, data)
            results.append(result)
            
            # Log the attempt
            WebhookLog.objects.create(
                configuration=webhook,
                event_type=event_type,
                status='success' if result['success'] else 'failed',
                status_code=result.get('status_code'),
                error_message=result.get('error', ''),
                payload=data,
            )
            
            # Update trigger count
            if result['success']:
                webhook.increment_trigger_count()
        
        return results
    
    def _get_event_filter(self, event_type: str) -> Q:
        """Get Q filter for event type."""
        if event_type == 'signal':
            return Q(notify_signals=True)
        elif event_type == 'trade':
            return Q(notify_trades=True)
        elif event_type == 'risk':
            return Q(notify_risk=True)
        elif event_type == 'performance':
            return Q(notify_performance=True)
        return Q()
    
    def _send_webhook(
        self,
        webhook: WebhookConfiguration,
        event_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send webhook to configured URL."""
        # Create message based on event type
        message = self._create_message(event_type, data, webhook.priority_threshold)
        
        # Get provider
        provider = WebhookProvider(webhook.provider)
        
        # Send webhook
        return self.webhook_service.send_webhook(
            url=webhook.url,
            provider=provider,
            message=message
        )
    
    def _create_message(
        self,
        event_type: str,
        data: Dict[str, Any],
        priority_threshold: str
    ) -> WebhookMessage:
        """Create webhook message based on event type."""
        priority_map = {
            'low': WebhookPriority.LOW,
            'medium': WebhookPriority.MEDIUM,
            'high': WebhookPriority.HIGH,
            'critical': WebhookPriority.CRITICAL,
        }
        
        if event_type == 'signal':
            return WebhookMessage(
                title=f"Signal: {data.get('symbol')} {data.get('direction')}",
                message=f"Confidence: {data.get('confidence')}%",
                priority=priority_map.get(data.get('priority', priority_threshold), WebhookPriority.MEDIUM),
                data=data,
            )
        elif event_type == 'trade':
            return WebhookMessage(
                title=f"Trade: {data.get('symbol')} {data.get('action')}",
                message=f"Price: {data.get('price')}",
                priority=WebhookPriority.HIGH,
                data=data,
            )
        elif event_type == 'risk':
            return WebhookMessage(
                title="Risk Alert",
                message=data.get('message', 'Risk threshold exceeded'),
                priority=WebhookPriority.CRITICAL,
                data=data,
            )
        else:
            return WebhookMessage(
                title=f"Event: {event_type}",
                message=str(data),
                priority=priority_map.get(priority_threshold, WebhookPriority.MEDIUM),
                data=data,
            )
    
    def get_webhook_logs(
        self,
        webhook_id: str,
        user,
        limit: int = 50
    ) -> List[WebhookLog]:
        """Get logs for a specific webhook."""
        return list(
            WebhookLog.objects.filter(
                configuration_id=webhook_id,
                configuration__user=user
            )[:limit]
        )
