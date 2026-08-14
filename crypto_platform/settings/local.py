"""Local development settings - no Docker needed."""
from .base import *

DEBUG = True

# ASGI for WebSocket support
ASGI_APPLICATION = 'crypto_platform.asgi.application'

# Insert daphne at the top of INSTALLED_APPS
if 'daphne' not in INSTALLED_APPS:
    INSTALLED_APPS = ['daphne'] + INSTALLED_APPS

# Iran Standard Time (IRST / UTC+3:30)
TIME_ZONE = 'Asia/Tehran'

# PostgreSQL database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'crypto_platform'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5433'),
    }
}

# Localhost only
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Disable Redis-dependent features for local dev
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

# Use in-memory cache instead of Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Use InMemoryChannelLayer instead of Redis
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# AI Settings - local Ollama
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
AI_MODE = os.environ.get('AI_MODE', 'off')  # off, lite, standard, cloud

# CORS
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

# JWT Security - shorter lifetimes for dev
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=30)
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=1)
SIMPLE_JWT['ROTATE_REFRESH_TOKENS'] = True
SIMPLE_JWT['BLACKLIST_AFTER_ROTATION'] = True
