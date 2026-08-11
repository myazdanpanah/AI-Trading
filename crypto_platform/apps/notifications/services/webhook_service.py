"""Webhook service for external integrations."""
import logging
import json
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


class WebhookProvider(str, Enum):
    """Supported webhook providers."""
    SLACK = 'slack'
    DISCORD = 'discord'
    TELEGRAM = 'telegram'
    CUSTOM = 'custom'


class WebhookPriority(str, Enum):
    """Webhook priority levels."""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


@dataclass
class WebhookMessage:
    """Webhook message format."""
    title: str
    message: str
    priority: WebhookPriority = WebhookPriority.MEDIUM
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class WebhookFormatter:
    """Format messages for different providers."""
    
    @staticmethod
    def format_slack(message: WebhookMessage) -> Dict[str, Any]:
        """Format message for Slack."""
        color_map = {
            WebhookPriority.LOW: '#36a64f',
            WebhookPriority.MEDIUM: '#ff9900',
            WebhookPriority.HIGH: '#ff0000',
            WebhookPriority.CRITICAL: '#990000',
        }
        
        return {
            'attachments': [{
                'color': color_map.get(message.priority, '#ff9900'),
                'title': message.title,
                'text': message.message,
                'fields': [
                    {
                        'title': 'Priority',
                        'value': message.priority.value,
                        'short': True,
                    },
                    {
                        'title': 'Time',
                        'value': message.timestamp.isoformat(),
                        'short': True,
                    }
                ] if message.data else [],
                'data': message.data or {},
            }]
        }
    
    @staticmethod
    def format_discord(message: WebhookMessage) -> Dict[str, Any]:
        """Format message for Discord."""
        color_map = {
            WebhookPriority.LOW: 0x36a64f,
            WebhookPriority.MEDIUM: 0xff9900,
            WebhookPriority.HIGH: 0xff0000,
            WebhookPriority.CRITICAL: 0x990000,
        }
        
        embed = {
            'title': message.title,
            'description': message.message,
            'color': color_map.get(message.priority, 0xff9900),
            'timestamp': message.timestamp.isoformat(),
            'fields': [],
        }
        
        if message.data:
            for key, value in message.data.items():
                embed['fields'].append({
                    'name': key,
                    'value': str(value),
                    'inline': True,
                })
        
        return {'embeds': [embed]}
    
    @staticmethod
    def format_telegram(message: WebhookMessage) -> Dict[str, Any]:
        """Format message for Telegram."""
        priority_emoji = {
            WebhookPriority.LOW: 'ℹ️',
            WebhookPriority.MEDIUM: '⚠️',
            WebhookPriority.HIGH: '🚨',
            WebhookPriority.CRITICAL: '🔥',
        }
        
        text = f"{priority_emoji.get(message.priority, 'ℹ️')} *{message.title}*\n\n{message.message}"
        
        if message.data:
            text += "\n\n📊 Data:\n"
            for key, value in message.data.items():
                text += f"  • {key}: {value}\n"
        
        return {
            'text': text,
            'parse_mode': 'Markdown',
        }
    
    @staticmethod
    def format_custom(message: WebhookMessage) -> Dict[str, Any]:
        """Format message for custom webhook."""
        return {
            'title': message.title,
            'message': message.message,
            'priority': message.priority.value,
            'timestamp': message.timestamp.isoformat(),
            'data': message.data or {},
        }


class WebhookService:
    """Service for sending webhooks to external providers."""
    
    def __init__(self):
        self.formatter = WebhookFormatter()
        self.timeout = 10
        self._last_send_times: Dict[str, datetime] = {}
        self._rate_limit_seconds = 1  # Minimum time between sends to same URL
    
    def _validate_url(self, url: str) -> bool:
        """Validate webhook URL to prevent SSRF attacks."""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                return False
            # Block internal/private IPs
            hostname = parsed.hostname or ''
            blocked_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '::1']
            for blocked in blocked_hosts:
                if hostname == blocked:
                    return False
            # Block private IP ranges (10.x.x.x, 192.168.x.x, 172.16-31.x.x)
            parts = hostname.split('.')
            if len(parts) == 4:
                try:
                    first = int(parts[0])
                    second = int(parts[1])
                    if first == 10:
                        return False
                    if first == 192 and second == 168:
                        return False
                    if first == 172 and 16 <= second <= 31:
                        return False
                except ValueError:
                    pass
            return True
        except Exception:
            return False
    
    def _check_rate_limit(self, url: str) -> bool:
        """Check if we should rate limit this URL."""
        now = datetime.now()
        last_send = self._last_send_times.get(url)
        if last_send and (now - last_send).total_seconds() < self._rate_limit_seconds:
            return False
        return True
    
    def send_webhook(
        self,
        url: str,
        provider: WebhookProvider,
        message: WebhookMessage,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Send webhook to specified URL."""
        # Validate URL
        if not self._validate_url(url):
            return {'success': False, 'error': 'Invalid URL', 'provider': provider.value}
        
        # Check rate limit
        if not self._check_rate_limit(url):
            return {'success': False, 'error': 'Rate limited', 'provider': provider.value}
        
        try:
            # Format message based on provider
            formatter_method = getattr(
                self.formatter, 
                f'format_{provider.value}',
                self.formatter.format_custom
            )
            payload = formatter_method(message)
            
            # Set appropriate headers
            if headers is None:
                headers = {}
            
            if provider == WebhookProvider.SLACK:
                headers['Content-Type'] = 'application/json'
            elif provider == WebhookProvider.DISCORD:
                headers['Content-Type'] = 'application/json'
            elif provider == WebhookProvider.TELEGRAM:
                headers['Content-Type'] = 'application/json'
            
            # Send request
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            # Update rate limit timestamp
            self._last_send_times[url] = datetime.now()
            
            return {
                'success': True,
                'status_code': response.status_code,
                'provider': provider.value,
            }
            
        except requests.RequestException as e:
            logger.error(f"Webhook failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': provider.value,
            }
    
    def send_signal_alert(
        self,
        url: str,
        provider: WebhookProvider,
        signal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send signal alert webhook."""
        message = WebhookMessage(
            title=f"Signal: {signal_data.get('symbol')} {signal_data.get('direction')}",
            message=f"Confidence: {signal_data.get('confidence')}%",
            priority=WebhookPriority.HIGH if signal_data.get('confidence', 0) > 70 else WebhookPriority.MEDIUM,
            data=signal_data,
        )
        return self.send_webhook(url, provider, message)
    
    def send_trade_alert(
        self,
        url: str,
        provider: WebhookProvider,
        trade_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send trade execution alert."""
        message = WebhookMessage(
            title=f"Trade: {trade_data.get('symbol')} {trade_data.get('action')}",
            message=f"Price: {trade_data.get('price')}",
            priority=WebhookPriority.HIGH,
            data=trade_data,
        )
        return self.send_webhook(url, provider, message)
    
    def send_risk_alert(
        self,
        url: str,
        provider: WebhookProvider,
        risk_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send risk alert."""
        message = WebhookMessage(
            title="Risk Alert",
            message=risk_data.get('message', 'Risk threshold exceeded'),
            priority=WebhookPriority.CRITICAL,
            data=risk_data,
        )
        return self.send_webhook(url, provider, message)
