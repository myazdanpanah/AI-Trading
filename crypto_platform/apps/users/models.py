"""User models for authentication."""
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    """Custom user model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    avatar = models.URLField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    preferred_ai_provider = models.CharField(
        max_length=50,
        choices=[
            ('ollama', 'Ollama'),
            ('openai', 'OpenAI'),
            ('anthropic', 'Anthropic'),
            ('openrouter', 'OpenRouter'),
        ],
        default='ollama'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        db_table = 'users'

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    """Extended user profile."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    risk_level = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    favorite_symbols = models.JSONField(default=list)
    notification_settings = models.JSONField(default=dict)
    timezone = models.CharField(max_length=50, default='UTC')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'user profile'
        verbose_name_plural = 'user profiles'
        db_table = 'user_profiles'

    def __str__(self):
        return f"Profile: {self.user.username}"


class UserSession(models.Model):
    """Track user sessions for security."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'user session'
        verbose_name_plural = 'user sessions'
        db_table = 'user_sessions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Session: {self.user.username} - {self.created_at}"
