# ══════════════════════════════════════════════════════════════════════
# AI-Trading Platform — Production Deployment Guide
# ══════════════════════════════════════════════════════════════════════

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Quick Start](#2-quick-start)
3. [Environment Variables](#3-environment-variables)
4. [Docker Deployment](#4-docker-deployment)
5. [Security Checklist](#5-security-checklist)
6. [Database Setup](#6-database-setup)
7. [AI / LLM Configuration](#7-ai--llm-configuration)
8. [Monitoring & Logging](#8-monitoring--logging)
9. [Backup & Recovery](#9-backup--recovery)
10. [Performance Tuning](#10-performance-tuning)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Prerequisites

### System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Storage | 50 GB SSD | 100+ GB SSD |
| GPU | None | NVIDIA (for Ollama) |

### Software Requirements

- **Docker** 24.0+ with Docker Compose v2
- **Git** 2.30+
- **PostgreSQL** 15+ (or use Docker)
- **Redis** 7+ (or use Docker)

### Install Docker (Ubuntu)

```bash
# Add Docker's official GPG key
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
```

---

## 2. Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/myazdanpanah/AI-Trading.git
cd AI-Trading

# 2. Create .env file
cp .env.example .env
# Edit .env with your settings (see Section 3)

# 3. Start all services
docker compose up -d

# 4. Run migrations
docker compose exec backend python manage.py migrate

# 5. Create admin user
docker compose exec backend python manage.py createsuperuser

# 6. Pull AI model into Ollama
docker compose exec ollama ollama pull gemma4:latest

# 7. Access the platform
# Frontend: http://localhost:80
# Backend API: http://localhost:8000/api/
# Admin: http://localhost:8000/admin/
# Grafana: http://localhost:3001
```

---

## 3. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key (50+ chars) | `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DB_PASSWORD` | PostgreSQL password | `your-secure-password` |
| `ALLOWED_HOSTS` | Comma-separated domains | `yourdomain.com,www.yourdomain.com` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_MODE` | `standard` | `off` / `lite` / `standard` / `cloud` |
| `LIVE_TRADING_ENABLED` | `False` | Enable real trading (DANGEROUS) |
| `SECURE_SSL_REDIRECT` | `False` | Force HTTPS |

---

## 4. Docker Deployment

### Development Mode

```bash
# Start with hot-reload
docker compose up -d

# View logs
docker compose logs -f backend

# Stop
docker compose down
```

### Production Mode

```bash
# Build production images
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify health
docker compose ps
curl http://localhost:8000/health/
```

### Service Architecture

```
                    ┌─────────────┐
                    │   Nginx     │
                    │   (Port 80) │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼───┐ ┌─────▼─────┐
        │ Frontend  │ │  API  │ │  Static   │
        │ (React)   │ │ Proxy │ │  Files    │
        └───────────┘ └───┬───┘ └───────────┘
                          │
                    ┌─────▼─────┐
                    │  Django   │
                    │ (Gunicorn)│
                    └─────┬─────┘
                          │
           ┌──────────────┼──────────────┐
           │              │              │
     ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
     │ PostgreSQL│ │   Redis   │ │  Ollama   │
     │  (Data)   │ │ (Cache)   │ │  (LLM)   │
     └───────────┘ └───────────┘ └───────────┘
           │              │
     ┌─────▼─────┐ ┌─────▼─────┐
     │  Celery   │ │  Celery   │
     │  Worker   │ │   Beat    │
     └───────────┘ └───────────┘
```

---

## 5. Security Checklist

### ✅ Pre-Deployment

- [ ] **SECRET_KEY**: Generated unique 50+ character key
- [ ] **DEBUG**: Set to `False`
- [ ] **ALLOWED_HOSTS**: Configured with actual domain(s)
- [ ] **Database password**: Strong, unique password
- [ ] **Redis password**: Set if exposed
- [ ] **SSL/TLS**: Configured (Let's Encrypt or Cloudflare)

### ✅ Authentication & Authorization

- [ ] **JWT tokens**: Short-lived (15 min access, 1 day refresh)
- [ ] **Token rotation**: Enabled (`ROTATE_REFRESH_TOKENS=True`)
- [ ] **Blacklist**: Enabled after rotation
- [ ] **Rate limiting**: Configured (100/hr anonymous, 1000/hr authenticated)
- [ ] **Admin access**: Restricted to specific IPs

### ✅ Network Security

- [ ] **Firewall**: Only ports 80/443 open
- [ ] **Database**: Not exposed to internet (internal only)
- [ ] **Redis**: Not exposed to internet (internal only)
- [ ] **Ollama**: Not exposed to internet (internal only)
- [ ] **VPN**: Required for admin access

### ✅ Data Security

- [ ] **HTTPS**: Enforced (`SECURE_SSL_REDIRECT=True`)
- [ ] **HSTS**: Enabled (1 year)
- [ ] **CORS**: Restricted to specific origins
- [ ] **CSRF**: Cookie secure
- [ ] **XSS protection**: Enabled
- [ ] **Content-Type sniff**: Blocked

### ✅ Trading Security

- [ ] **LIVE_TRADING_ENABLED**: Set to `False` unless ready
- [ ] **Exchange testnet**: Enabled by default
- [ ] **Kill switch**: Configured and tested
- [ ] **Position limits**: Set maximum exposure
- [ ] **Alerts**: Configured for unusual activity

---

## 6. Database Setup

### Initial Setup

```bash
# Create database
docker compose exec postgres psql -U postgres -c "CREATE DATABASE crypto_platform;"

# Run migrations
docker compose exec backend python manage.py migrate

# Create superuser
docker compose exec backend python manage.py createsuperuser
```

### Backup Script

```bash
#!/bin/bash
# scripts/backup-db.sh

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

mkdir -p $BACKUP_DIR

docker compose exec -T postgres pg_dump -U postgres crypto_platform | gzip > $FILE

# Keep last 30 backups
ls -t $BACKUP_DIR/backup_*.sql.gz | tail -n +31 | xargs rm -f 2>/dev/null

echo "Backup completed: $FILE"
```

### Restore Script

```bash
#!/bin/bash
# scripts/restore-db.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

gunzip -c $BACKUP_FILE | docker compose exec -T postgres psql -U postgres crypto_platform
echo "Restore completed from $BACKUP_FILE"
```

---

## 7. AI / LLM Configuration

### Local Ollama (Recommended)

```bash
# Pull model
docker compose exec ollama ollama pull gemma4:latest

# Test connection
curl http://localhost:11434/api/tags

# Configure in .env
AI_MODE=standard
OLLAMA_BASE_URL=http://ollama:11434
```

### Cloud LLM (Optional)

```bash
# Add to .env
AI_MODE=cloud
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
```

### Model Selection

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `gemma4:latest` | 8B | Fast | Good | Default |
| `llama3:latest` | 8B | Fast | Good | Alternative |
| `qwen3.5:latest` | 8B | Fast | Good | Persian |

---

## 8. Monitoring & Logging

### Prometheus + Grafana

```bash
# Access Grafana
open http://localhost:3001
# Login: admin / admin (change on first login)

# Access Prometheus
open http://localhost:9090
```

### Application Logs

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f backend
docker compose logs -f celery-worker

# View last 100 lines
docker compose logs --tail 100 backend
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health/

# Database health
docker compose exec postgres pg_isready -U postgres

# Redis health
docker compose exec redis redis-cli ping

# Ollama health
curl http://localhost:11434/api/tags
```

---

## 9. Backup & Recovery

### Automated Backups (Cron)

```bash
# Add to crontab
0 2 * * * /path/to/scripts/backup-db.sh >> /var/log/backup.log 2>&1
```

### Full Backup Script

```bash
#!/bin/bash
# scripts/backup-full.sh

BACKUP_DIR="/backups/ai-trading"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
docker compose exec -T postgres pg_dump -U postgres crypto_platform | gzip > "$BACKUP_DIR/db_$TIMESTAMP.sql.gz"

# Media files backup
tar -czf "$BACKUP_DIR/media_$TIMESTAMP.tar.gz" media/

# Configuration backup
tar -czf "$BACKUP_DIR/config_$TIMESTAMP.tar.gz" .env docker-compose*.yml

echo "Full backup completed: $BACKUP_DIR"
```

---

## 10. Performance Tuning

### PostgreSQL Tuning

```sql
-- Check current settings
SHOW shared_buffers;
SHOW effective_cache_size;
SHOW work_mem;

-- Recommended for 16GB RAM
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
ALTER SYSTEM SET max_connections = 200;

-- Reload
SELECT pg_reload_conf();
```

### Redis Tuning

```bash
# Check memory usage
docker compose exec redis redis-cli info memory

# Recommended settings in docker-compose.prod.yml
command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### Celery Tuning

```bash
# Increase concurrency for CPU-bound tasks
docker compose exec celery-worker celery -A crypto_platform worker -l info --concurrency=8

# For I/O-bound tasks
docker compose exec celery-worker celery -A crypto_platform worker -l info --concurrency=16 -P gevent
```

---

## 11. Troubleshooting

### Common Issues

#### Backend won't start

```bash
# Check logs
docker compose logs backend

# Common fix: migrate database
docker compose exec backend python manage.py migrate

# Common fix: collect static files
docker compose exec backend python manage.py collectstatic --noinput
```

#### Database connection refused

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check credentials
docker compose exec postgres psql -U postgres -c "\l"

# Reset database
docker compose down -v
docker compose up -d postgres
docker compose exec backend python manage.py migrate
```

#### Ollama not responding

```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Pull model if missing
docker compose exec ollama ollama pull gemma4:latest

# Check logs
docker compose logs ollama
```

#### Frontend not loading

```bash
# Rebuild frontend
docker compose build frontend --no-cache

# Check nginx config
docker compose exec frontend nginx -t

# View logs
docker compose logs frontend
```

### Useful Commands

```bash
# Restart a specific service
docker compose restart backend

# Rebuild a specific service
docker compose build backend --no-cache
docker compose up -d backend

# Enter a running container
docker compose exec backend bash

# Check resource usage
docker stats

# Clean up unused resources
docker system prune -a
```

---

## Production Checklist

Before going live:

- [ ] All environment variables configured
- [ ] SSL certificate installed
- [ ] Database backups scheduled
- [ ] Monitoring dashboards configured
- [ ] Alert rules set up (Prometheus/Grafana)
- [ ] Kill switch tested
- [ ] Rate limiting configured
- [ ] CORS restricted to production domain
- [ ] Debug mode disabled
- [ ] Secret key is unique and secure
- [ ] Database password is strong
- [ ] Redis is not exposed to internet
- [ ] Ollama is not exposed to internet
- [ ] Firewall configured
- [ ] VPN access for admin panel

---

*Last updated: August 2026*
