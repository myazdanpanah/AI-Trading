"""Notification views including webhook configuration."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import (
    NotificationChannel, NotificationRule, Notification,
    WebhookConfiguration, WebhookLog
)
from .serializers import (
    NotificationChannelSerializer, NotificationRuleSerializer, NotificationSerializer,
    WebhookConfigurationSerializer, WebhookLogSerializer, WebhookTestSerializer
)
from .services.user_webhook_service import UserWebhookService
from .services.webhook_service import WebhookService, WebhookProvider, WebhookMessage


@extend_schema_view(
    list=extend_schema(tags=['Notifications'], summary='List notification channels'),
    create=extend_schema(tags=['Notifications'], summary='Create notification channel'),
    retrieve=extend_schema(tags=['Notifications'], summary='Get notification channel'),
    update=extend_schema(tags=['Notifications'], summary='Update notification channel'),
    partial_update=extend_schema(tags=['Notifications'], summary='Partial update notification channel'),
    destroy=extend_schema(tags=['Notifications'], summary='Delete notification channel'),
)
class NotificationChannelViewSet(viewsets.ModelViewSet):
    queryset = NotificationChannel.objects.all()
    serializer_class = NotificationChannelSerializer


@extend_schema_view(
    list=extend_schema(tags=['Notifications'], summary='List notification rules'),
    create=extend_schema(tags=['Notifications'], summary='Create notification rule'),
    retrieve=extend_schema(tags=['Notifications'], summary='Get notification rule'),
    update=extend_schema(tags=['Notifications'], summary='Update notification rule'),
    partial_update=extend_schema(tags=['Notifications'], summary='Partial update notification rule'),
    destroy=extend_schema(tags=['Notifications'], summary='Delete notification rule'),
)
class NotificationRuleViewSet(viewsets.ModelViewSet):
    queryset = NotificationRule.objects.all()
    serializer_class = NotificationRuleSerializer


@extend_schema_view(
    list=extend_schema(tags=['Notifications'], summary='List notifications'),
    create=extend_schema(tags=['Notifications'], summary='Create notification'),
    retrieve=extend_schema(tags=['Notifications'], summary='Get notification'),
    update=extend_schema(tags=['Notifications'], summary='Update notification'),
    partial_update=extend_schema(tags=['Notifications'], summary='Partial update notification'),
    destroy=extend_schema(tags=['Notifications'], summary='Delete notification'),
)
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer


@extend_schema_view(
    list=extend_schema(tags=['Webhooks'], summary='List your webhook configurations'),
    create=extend_schema(tags=['Webhooks'], summary='Create a webhook configuration'),
    retrieve=extend_schema(tags=['Webhooks'], summary='Get webhook configuration details'),
    update=extend_schema(tags=['Webhooks'], summary='Update webhook configuration'),
    partial_update=extend_schema(tags=['Webhooks'], summary='Partial update webhook configuration'),
    destroy=extend_schema(tags=['Webhooks'], summary='Delete webhook configuration'),
    test=extend_schema(tags=['Webhooks'], summary='Test webhook delivery'),
    logs=extend_schema(tags=['Webhooks'], summary='Get webhook delivery logs'),
)
class WebhookConfigurationViewSet(viewsets.ModelViewSet):
    serializer_class = WebhookConfigurationSerializer
    
    def get_queryset(self):
        """Return only current user's webhooks."""
        return WebhookConfiguration.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set user on creation."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test webhook delivery."""
        webhook = self.get_object()
        
        service = WebhookService()
        provider = WebhookProvider(webhook.provider)
        
        message = WebhookMessage(
            title='Test Webhook',
            message='This is a test webhook from Crypto AI Platform',
            data={'test': True, 'timestamp': str(webhook.created_at)},
        )
        
        result = service.send_webhook(webhook.url, provider, message)
        
        return Response({
            'success': result.get('success', False),
            'status_code': result.get('status_code'),
            'error': result.get('error'),
        })
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get webhook delivery logs."""
        webhook = self.get_object()
        logs = WebhookLog.objects.filter(configuration=webhook)[:50]
        serializer = WebhookLogSerializer(logs, many=True)
        return Response(serializer.data)


@extend_schema(tags=['Webhooks'], summary='Test webhook delivery')
class WebhookTestViewSet(viewsets.ViewSet):
    """ViewSet for testing webhooks without saving configuration."""
    
    @action(detail=False, methods=['post'])
    def test(self, request):
        """Test webhook delivery with provided URL."""
        serializer = WebhookTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        service = WebhookService()
        provider = WebhookProvider(data['provider'])
        
        message = WebhookMessage(
            title='Test Webhook',
            message=data['message'],
            data={'test': True},
        )
        
        result = service.send_webhook(data['url'], provider, message)
        
        return Response(result)
