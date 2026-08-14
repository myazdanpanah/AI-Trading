# ══════════════════════════════════════════════════════════════════════
# Backend Dockerfile — Multi-stage build for production
# ══════════════════════════════════════════════════════════════════════

# ── Stage 1: Build dependencies ─────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements-core.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements-core.txt

# ── Stage 2: Production image ───────────────────────────────────────
FROM python:3.12-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/crypto_platform

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user
RUN addgroup --system appuser && \
    adduser --system --ingroup appuser appuser && \
    mkdir -p /app /app/staticfiles /app/logs && \
    chown -R appuser:appuser /app

WORKDIR /app

# Copy application code
COPY crypto_platform/ /app/crypto_platform/
COPY manage.py /app/

# Collect static files
RUN DJANGO_SETTINGS_MODULE=crypto_platform.settings.production \
    python manage.py collectstatic --noinput 2>/dev/null || true

# Switch to non-root user
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Production server: Gunicorn with async workers
CMD ["gunicorn", "crypto_platform.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
