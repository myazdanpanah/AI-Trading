# Deployment Guide

## Crypto AI Signal Platform

This guide covers deploying the Crypto AI Signal Platform in development and production environments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Production Deployment](#production-deployment)
4. [Environment Variables](#environment-variables)
5. [Database Setup](#database-setup)
6. [Services Configuration](#services-configuration)
7. [Monitoring & Observability](#monitoring--observability)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Docker** >= 24.0
- **Docker Compose** >= 2.20
- **Git** >= 2.40

### Optional (for local development without Docker)
- **Python** >= 3.11
- **Node.js** >= 20
- **PostgreSQL** >= 16 (or TimescaleDB)
- **Redis** >= 7

---

## Development Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd crypto-platform
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your configuration
# At minimum, set DJANGO_SECRET_KEY
```

### 3. Start Services with Docker Compose

```bash
# Start all services
docker-compose up -d

# Or start with build
docker-compose up -d --build

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
```

### 4. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React dashboard |
| Backend API | http://localhost:8000/api/ | Django REST API |
| Swagger UI | http://localhost:8000/api/docs/ | API documentation |
| ReDoc | http://localhost:8000/api/redoc/ | Alternative API docs |
| Admin | http://localhost:8000/admin/ | Django admin |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache/Celery broker |
| Ollama | http://localhost:11434 | Local AI inference |
| Prometheus | http://localhost:9090 | Metrics |
| Grafana | http://localhost:3001 | Dashboards |

### 5. Initialize Database

```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Load initial data (optional)
docker-compose exec backend python manage.py loaddata initial_data
```

---

## Production Deployment

### 1. Security Configuration

Before deploying to production, update the following in `.env`:

```bash
# Generate a secure secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Set in .env
DJANGO_SECRET_KEY=<your-generated-key>

# Set allowed hosts
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Set CORS origins
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Enable SSL redirect
SECURE_SSL_REDIRECT=True

# Database credentials (use strong passwords)
DB_PASSWORD=<secure-password>
POSTGRES_PASSWORD=<secure-password>
```

### 2. Start Production Services

```bash
# Use production settings
export DJANGO_SETTINGS_MODULE=crypto_platform.settings.security

# Build and start
docker-compose -f docker-compose.yml up -d --build

# Run migrations
docker-compose exec backend python manage.py migrate --settings=crypto_platform.settings.security

# Collect static files
docker-compose exec backend python manage.py collectstatic --no-input
```

### 3. SSL/TLS Configuration

For HTTPS, configure nginx with SSL certificates:

```nginx
# docker/nginx/nginx.conf
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... rest of configuration
}
```

### 4. Backup Strategy

```bash
# Database backup
docker-compose exec postgres pg_dump -U postgres crypto_platform > backup_$(date +%Y%m%d).sql

# Restore from backup
docker-compose exec -T postgres psql -U postgres crypto_platform < backup.sql
```

---

## Environment Variables

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | `django-insecure-...` | Django secret key (REQUIRED in production) |
| `DJANGO_SETTINGS_MODULE` | `crypto_platform.settings` | Settings module |
| `DEBUG` | `False` | Debug mode (set to False in production) |

### Database Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_ENGINE` | `django.db.backends.postgresql` | Database engine |
| `DB_NAME` | `crypto_platform` | Database name |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | `postgres` | Database password |
| `DB_HOST` | `localhost` | Database host |
| `DB_PORT` | `5432` | Database port |
| `DB_SSLMODE` | `prefer` | SSL mode for database |

### Redis Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |

### AI Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API URL |
| `OPENAI_API_KEY` | - | OpenAI API key (optional) |
| `ANTHROPIC_API_KEY` | - | Anthropic API key (optional) |

### Security Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins |
| `SECURE_SSL_REDIRECT` | `False` | Redirect HTTP to HTTPS |

---

## Database Setup

### PostgreSQL with TimescaleDB

The platform uses TimescaleDB for time-series data optimization:

```bash
# TimescaleDB is included in docker-compose.yml
# No additional setup required
```

### Manual PostgreSQL Setup

If not using Docker:

```sql
-- Create database
CREATE DATABASE crypto_platform;

-- Enable TimescaleDB (if installed)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create user
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE crypto_platform TO postgres;
```

---

## Services Configuration

### Celery Worker & Beat

The platform uses Celery for background tasks:

```bash
# Celery worker processes tasks
docker-compose exec celery-worker celery -A crypto_platform worker -l info

# Celery beat schedules periodic tasks
docker-compose exec celery-beat celery -A crypto_platform beat -l info
```

### Ollama (Local AI)

Ollama provides local AI inference without external API costs:

```bash
# Pull a model
docker-compose exec ollama ollama pull llama2

# Or use a smaller model
docker-compose exec ollama ollama pull mistral
```

---

## Monitoring & Observability

### Prometheus

Metrics are collected at http://localhost:9090

Key metrics to monitor:
- `django_http_requests_total` - Total HTTP requests
- `django_http_response_status_codes` - Response status codes
- `celery_task_duration_seconds` - Celery task execution time

### Grafana

Dashboards are available at http://localhost:3001

Default credentials:
- Username: `admin`
- Password: `admin` (change on first login)

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U postgres -d crypto_platform
```

#### 2. Redis Connection Errors

```bash
# Check if Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
```

#### 3. Migration Errors

```bash
# Check migration status
docker-compose exec backend python manage.py showmigrations

# Apply pending migrations
docker-compose exec backend python manage.py migrate

# Reset migrations (CAUTION: destroys data)
docker-compose exec backend python manage.py migrate --zero
```

#### 4. Static Files Not Loading

```bash
# Collect static files
docker-compose exec backend python manage.py collectstatic --no-input

# Check static files directory
ls -la staticfiles/
```

### Logs

```bash
# View all logs
docker-compose logs

# View specific service
docker-compose logs backend
docker-compose logs celery-worker
docker-compose logs nginx

# Follow logs in real-time
docker-compose logs -f backend
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Restart services
docker-compose restart

# Full rebuild
docker-compose down
docker-compose up -d --build
```

---

## Updating

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Run migrations
docker-compose exec backend python manage.py migrate

# Collect static files
docker-compose exec backend python manage.py collectstatic --no-input
```

---

## Support

For issues and support:
- Check the [Troubleshooting](#troubleshooting) section
- Review logs for error messages
- Ensure all environment variables are properly configured
