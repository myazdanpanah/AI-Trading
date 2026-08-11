FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from backend directory
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Set PYTHONPATH for Django imports
ENV PYTHONPATH=/app:/app/crypto_platform

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
