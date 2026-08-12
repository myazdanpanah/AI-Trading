FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install core Python dependencies (lightweight)
COPY backend/requirements-core.txt .
RUN pip install --no-cache-dir -r requirements-core.txt

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser

# Copy application code
COPY . .

# Set PYTHONPATH for Django imports
ENV PYTHONPATH=/app:/app/crypto_platform

# Run migrations and collect static
RUN python manage.py migrate --no-input 2>/dev/null || true
RUN python manage.py collectstatic --noinput 2>/dev/null || true

USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')"

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
