"""Tests for notifications app."""
from django.test import TestCase
from .models import NotificationChannel, NotificationRule, Notification


class NotificationModelsTest(TestCase):
    def test_channel_creation(self):
        channel = NotificationChannel.objects.create(
            name='Telegram Bot',
            channel_type='telegram',
            config={'bot_token': 'test'}
        )
        self.assertEqual(channel.name, 'Telegram Bot')
        self.assertEqual(channel.channel_type, 'telegram')

    def test_notification_creation(self):
        channel = NotificationChannel.objects.create(
            name='Email',
            channel_type='email'
        )
        notification = Notification.objects.create(
            channel=channel,
            title='Test Alert',
            message='This is a test'
        )
        self.assertEqual(notification.title, 'Test Alert')
        self.assertEqual(notification.status, 'pending')
