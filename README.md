# Crypto AI Signal Platform

An enterprise-grade AI-powered cryptocurrency intelligence platform with multi-agent AI architecture, real-time market analysis, and self-learning capabilities.

## Features

- **Real-time Market Data**: Live prices, candles, order books, derivatives from multiple exchanges
- **Technical Analysis**: 15+ indicators, Smart Money concepts, CPR analysis
- **AI Engine**: Multi-provider support (Ollama, OpenAI, Anthropic)
- **News Intelligence**: RSS, Twitter, Reddit, Telegram integration
- **Signal Generation**: Explainable Buy/Sell/Hold signals with confidence scores
- **Self-Learning**: Continuous improvement from signal outcomes

## Tech Stack

### Backend
- Python 3.13
- Django + Django REST Framework
- Celery (Background tasks)
- PostgreSQL + TimescaleDB
- pgvector (AI memory)
- Redis (Cache)

### Frontend
- React 18
- TypeScript
- Vite
- TailwindCSS
- ECharts

### AI
- Ollama (Local)
- OpenAI
- Anthropic
- OpenRouter

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.13+
- Node.js 20+

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd crypto-platform
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Start with Docker:
```bash
docker-compose up -d
```

4. Run migrations:
```bash
docker-compose exec backend python manage.py migrate
```

5. Create superuser:
```bash
docker-compose exec backend python manage.py createsuperuser
```

### Development

1. Install backend dependencies:
```bash
pip install -r backend/requirements.txt
```

2. Install frontend dependencies:
```bash
cd frontend && npm install
```

3. Start development servers:
```bash
# Terminal 1 - Backend
cd backend && python manage.py runserver

# Terminal 2 - Frontend
cd frontend && npm run dev

# Terminal 3 - Celery Worker
cd backend && celery -A crypto_platform worker -l info

# Terminal 4 - Celery Beat
cd backend && celery -A crypto_platform beat -l info
```

## Project Structure

```
├── crypto_platform/
│   ├── apps/
│   │   ├── core/           # Shared utilities
│   │   ├── users/          # User management
│   │   ├── authentication/ # JWT auth
│   │   ├── market/         # Market data
│   │   ├── news/           # News intelligence
│   │   ├── analytics/      # Technical analysis
│   │   ├── ai_engine/      # AI integration
│   │   ├── signals/        # Signal generation
│   │   ├── learning/       # Learning engine
│   │   ├── notifications/  # Notifications
│   │   └── reports/        # Reporting
│   ├── settings/           # Django settings
│   ├── celery.py
│   └── urls.py
├── frontend/               # React frontend
├── docker/                 # Docker configs
└── scripts/                # Utility scripts
```

## API Endpoints

- `/api/auth/login/` - JWT login
- `/api/auth/refresh/` - Token refresh
- `/api/users/` - User management
- `/api/market/` - Market data
- `/api/news/` - News articles
- `/api/signals/` - Trading signals
- `/api/ai/` - AI engine
- `/api/analytics/` - Technical analysis

## Environment Variables

See `.env.example` for all required environment variables.

## License

Proprietary - All rights reserved.
