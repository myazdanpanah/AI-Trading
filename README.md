<div align="center">

# 🚀 AI-Trading

### Enterprise-Grade AI-Powered Cryptocurrency Intelligence Platform

**Real-time market analysis • Multi-agent AI signals • Self-learning system**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/django-5.0+-green.svg)](https://djangoproject.com)
[![React](https://img.shields.io/badge/react-18+-61dafb.svg)](https://reactjs.org)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://docker.com)

---

</div>

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Configuration](#%EF%B8%8F-configuration)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [Frontend Components](#-frontend-components)
- [Backend Services](#-backend-services)
- [Infrastructure](#-infrastructure)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

AI-Trading is a full-stack cryptocurrency trading platform that combines **multi-agent AI architecture**, **real-time market analysis**, and **self-learning capabilities** to generate intelligent trading signals. The platform integrates with major exchanges (Binance, Bybit, OKX) and uses local AI models via Ollama for privacy-first analysis.

### Key Highlights

- **🤖 Multi-Agent AI System** — Coordinated AI agents (Market Analyst, Technical Analyst, Sentiment Analyst, Risk Analyst) work together to generate comprehensive trading signals
- **📊 Multi-Factor Scoring** — Combines technical analysis, sentiment, news, AI predictions, and macro factors with configurable weights
- **🧠 Self-Learning** — The system learns from past signals, adjusting weights and strategies based on performance
- **📈 TradingView-Grade UI** — Professional dark-theme interface with real-time charts, order book, and portfolio tracking
- **🔄 Real-time Streaming** — WebSocket-powered live data feeds for prices, order book, and signal updates
- **🛡️ Production-Ready** — Docker deployment with monitoring, alerting, and security hardening

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │ Trading  │ │ Signals  │ │Analysis  │ │ Backtest │ │ Settings ││
│  │  View    │ │  Panel   │ │  Panel   │ │  Engine  │ │  Config  ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘│
│                          WebSocket Client                         │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────┴────────────────────────────────────┐
│                     NGINX REVERSE PROXY (:80)                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────┴────────────────────────────────────┐
│                       DJANGO BACKEND (:8000)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │  Market  │ │ Signals  │ │    AI    │ │ Learning │ │ Feedback ││
│  │  Engine  │ │  Engine  │ │  Engine  │ │  Engine  │ │  Loop    ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘│
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │  News    │ │Sentiment │ │Technical │ │Notifi-   │ │ Reports  ││
│  │  Intel   │ │ Analysis │ │ Analysis │ │cations   │ │          ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘│
│                          WebSocket Server                         │
└────┬──────────┬──────────┬──────────┬──────────┬──────────────────┘
     │          │          │          │          │
┌────┴────┐┌────┴────┐┌────┴────┐┌────┴────┐┌────┴────┐
│PostgreSQL││  Redis  ││  Celery ││ Ollama  ││  Other  │
│TimescaleDB││  Cache  ││ Workers ││ (Local  ││  APIs   │
│ pgvector ││  Broker ││  Beat   ││   AI)   ││         │
└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘
```

---

## ✨ Features

### 📈 Trading Interface
- **TradingView-Style Charts** — Candlestick charts with SMA, EMA, Bollinger Bands overlays
- **Real-time Order Book** — Live bid/ask display with depth visualization
- **Watchlist** — 10 cryptocurrency pairs with live prices and sorting
- **Portfolio Tracker** — Real-time position tracking with P&L and allocation pie chart
- **Drawing Tools** — Trend lines, horizontal lines, Fibonacci retracement, rectangles

### 🎯 Signal Engine
- **Multi-Factor Scoring** — Combines 5 factors (Technical, Sentiment, News, AI, Macro)
- **Configurable Weights** — Adjust factor weights via API or UI
- **Risk Management** — Kelly criterion, position sizing, max drawdown limits
- **Signal Reasons** — Human-readable explanations for every signal

### 🤖 AI Engine
- **Multi-Provider Support** — Ollama (local), OpenAI, Anthropic, OpenRouter
- **Agent Orchestration** — Pipeline, parallel, consensus, and debate patterns
- **Memory System** — Vector embeddings for similarity search and learning
- **Prompt Versioning** — Track and version AI prompts

### 📊 Analytics
- **Technical Indicators** — RSI, MACD, Bollinger, ATR, Stochastic, EMA/SMA
- **Pattern Detection** — Head & Shoulders, Double Top/Bottom, Triangles, Flags
- **Smart Money Concepts** — Order blocks, FVG, liquidity sweeps, BOS/CHoCH
- **CPR Analysis** — Central Pivot Range with breakout/reversal probability

### 🧠 Learning System
- **Performance Tracking** — Win rate, Sharpe ratio, profit factor per strategy
- **Weight Optimization** — Adaptive factor weights based on historical performance
- **Pattern Memory** — Store and recall successful/failed patterns
- **Feedback Cycles** — Daily and weekly review cycles with AI insights

### 📰 Intelligence
- **News Crawling** — RSS feeds, Reddit, Twitter/X monitoring
- **Sentiment Analysis** — Fear & Greed index, social sentiment, whale tracking
- **Entity Recognition** — Extract crypto entities and sentiment from news
- **Event Impact Scoring** — Rate news impact on specific assets

### 🔔 Notifications
- **Multi-Channel** — Email, Telegram, Discord, Slack, SMS, Webhooks
- **Smart Rules** — Configure conditions for each notification type
- **Rate Limiting** — Prevent notification storms
- **Webhook Logs** — Full delivery tracking and retry logic

### 🔬 Backtester
- **Strategy Testing** — SMA Crossover, RSI Reversal, Bollinger Bounce, MACD
- **Performance Metrics** — Return, win rate, Sharpe ratio, max drawdown
- **Equity Curve** — Visual equity curve with trade markers
- **Trade History** — Detailed trade log with P&L

---

## 🛠️ Tech Stack

### Backend
| Component | Technology |
|-----------|-----------|
| Framework | Django 5.0 + Django REST Framework |
| Database | PostgreSQL 16 + TimescaleDB + pgvector |
| Cache/Broker | Redis 7 |
| Task Queue | Celery 5.3 |
| AI | Ollama (local), OpenAI, Anthropic |
| Market Data | CCXT (Binance, Bybit, OKX) |
| API Docs | drf-spectacular (OpenAPI/Swagger) |
| Monitoring | Prometheus + Grafana |

### Frontend
| Component | Technology |
|-----------|-----------|
| Framework | React 18 + TypeScript |
| Build Tool | Vite 5 |
| Styling | TailwindCSS 3 |
| Charts | Recharts |
| State | React Hooks (useState, useEffect, useMemo) |
| HTTP | Fetch API with auth interceptor |

### Infrastructure
| Component | Technology |
|-----------|-----------|
| Containers | Docker + Docker Compose |
| Reverse Proxy | Nginx |
| CI/CD | GitHub Actions |
| Linting | Black, isort, Ruff, ESLint |
| Testing | pytest, React Testing Library |
| Pre-commit | pre-commit hooks |

---

## 🚀 Quick Start

### Prerequisites

- **Docker** 24.0+ and **Docker Compose** v2.20+
- **Python** 3.11+ (for local development)
- **Node.js** 20+ and **npm** (for local development)
- **PostgreSQL** 16+ with TimescaleDB (if running locally)
- **Redis** 7+ (if running locally)

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/AI-Trading.git
cd AI-Trading

# Copy environment variables
cp .env.example .env
# Edit .env with your settings

# Start all services
docker-compose up -d

# Apply database migrations
docker-compose exec backend python manage.py migrate

# Create a superuser
docker-compose exec backend python manage.py createsuperuser

# Access the platform
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/api/docs/
# Admin: http://localhost:8000/admin/
```

### Option 2: Local Development

```bash
# Clone the repository
git clone https://github.com/your-username/AI-Trading.git
cd AI-Trading

# --- Backend Setup ---
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

# Set environment variables
export DJANGO_SETTINGS_MODULE=crypto_platform.settings.development
export DB_HOST=localhost
export REDIS_URL=redis://localhost:6379/0

# Apply migrations
python manage.py migrate
python manage.py createsuperuser

# Start the backend
python manage.py runserver

# --- Frontend Setup (new terminal) ---
cd frontend
npm install
npm run dev
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | (must set) |
| `DJANGO_SETTINGS_MODULE` | Settings module | `crypto_platform.settings.development` |
| `DB_NAME` | PostgreSQL database name | `crypto_platform` |
| `DB_USER` | PostgreSQL username | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | `postgres` |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `OLLAMA_BASE_URL` | Ollama API URL | `http://localhost:11434` |
| `OPENAI_API_KEY` | OpenAI API key | (optional) |
| `ANTHROPIC_API_KEY` | Anthropic API key | (optional) |

### Exchange Configuration

Configure exchange API keys via the Settings page in the UI or through the API:

```
POST /api/market/exchanges/configure/
{
  "exchange": "binance",
  "api_key": "your-api-key",
  "api_secret": "your-api-secret",
  "testnet": true
}
```

### AI Provider Configuration

```python
# Ollama (default, local)
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI (optional)
OPENAI_API_KEY=sk-...

# Anthropic (optional)
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 📁 Project Structure

```
AI-Trading/
├── backend/                    # Backend Dockerfile & requirements
│   ├── Dockerfile
│   └── requirements.txt
├── crypto_platform/            # Django project
│   ├── settings/               # Environment-specific settings
│   │   ├── base.py            # Base settings (shared)
│   │   ├── development.py     # Local development
│   │   ├── production.py      # Production settings
│   │   └── docker.py          # Docker settings
│   ├── apps/                   # Django applications
│   │   ├── core/              # Shared utilities, health checks
│   │   ├── users/             # User management
│   │   ├── authentication/    # JWT authentication
│   │   ├── market/            # Market data engine
│   │   │   └── exchanges/     # Exchange adapters (CCXT)
│   │   ├── ai_engine/         # AI integration
│   │   │   ├── providers/     # Ollama, OpenAI, Anthropic
│   │   │   └── services/      # Orchestrator, gateway
│   │   ├── signals/           # Signal generation
│   │   │   └── services/      # Generator, risk manager, backtester
│   │   ├── technical_analysis/ # Indicators & patterns
│   │   │   └── services/      # RSI, MACD, Bollinger, etc.
│   │   ├── sentiment/         # Sentiment analysis
│   │   │   └── services/      # Fear/Greed, whale tracker
│   │   ├── news/              # News intelligence
│   │   │   └── crawlers/      # RSS, Reddit crawlers
│   │   ├── analytics/         # Event tracking & CPR
│   │   ├── learning/          # Performance tracking
│   │   ├── feedback/          # AI memory & self-improvement
│   │   ├── notifications/     # Alerts & webhooks
│   │   └── reports/           # Report generation
│   ├── urls.py                # URL routing
│   ├── celery_app.py          # Celery configuration
│   └── asgi.py                # ASGI (WebSocket support)
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/          # Login form
│   │   │   ├── dashboard/     # Main dashboard, signals, analysis
│   │   │   ├── trading/       # Chart, order book, portfolio, backtester
│   │   │   ├── charts/        # Reusable chart components
│   │   │   ├── feedback/      # Learning insights
│   │   │   └── settings/      # API settings
│   │   └── utils/
│   │       └── api.ts         # API client with auth & mock fallback
│   ├── Dockerfile
│   └── package.json
├── docker/                     # Docker configurations
│   ├── nginx/                 # Nginx reverse proxy
│   ├── prometheus/            # Prometheus metrics
│   └── grafana/               # Grafana dashboards
├── scripts/                    # Utility scripts
│   └── init-db.sql            # Database initialization
├── docker-compose.yml          # Docker Compose orchestration
├── manage.py                   # Django management
├── plan.md                     # Development plan
├── progress.md                 # Progress tracker
├── changelog.md                # Changelog
└── README.md                   # This file
```

---

## 📡 API Documentation

### Authentication

```bash
# Login (get JWT tokens)
POST /api/auth/login/
{
  "username": "admin",
  "password": "your-password"
}
# Returns: { "access": "...", "refresh": "..." }

# Use token in requests
Authorization: Bearer <access_token>
```

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health/` | Health check |
| `GET` | `/health/detailed/` | Detailed health check |
| `GET` | `/metrics/` | Prometheus metrics |
| `GET` | `/api/docs/` | Swagger UI |
| `GET` | `/api/redoc/` | ReDoc documentation |
| `GET` | `/api/schema/` | OpenAPI schema |

### Market Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/market/prices/` | Current prices |
| `GET` | `/api/market/candles/` | OHLCV candle data |
| `GET` | `/api/market/orderbook/` | Order book snapshot |
| `GET` | `/api/market/tickers/` | All tickers |

### Signals

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/signals/signals/latest/` | Recent signals |
| `POST` | `/api/signals/signals/generate/` | Generate new signal |
| `GET` | `/api/signals/factor-weights/` | Factor weights |
| `POST` | `/api/signals/backtest/` | Run backtest |

### AI Engine

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/ai/providers/` | AI providers |
| `POST` | `/api/ai/analyze/` | AI market analysis |
| `GET` | `/api/ai/workflows/` | Agent workflows |

### Learning & Feedback

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/learning/results/performance/` | Performance metrics |
| `GET` | `/api/feedback/analysis/insights/` | Learning insights |
| `POST` | `/api/feedback/cycles/run_cycle/` | Run feedback cycle |

> 📖 **Full API documentation**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)

---

## 🖥️ Frontend Components

### Trading Tab
- **TradingViewChart** — Interactive candlestick chart with technical indicators
- **Watchlist** — Live cryptocurrency pair prices with sorting and favorites
- **OrderBook** — Real-time bid/ask display with depth visualization
- **PortfolioTracker** — Position tracking with P&L and allocation pie chart

### Signals Tab
- **SignalsPanel** — Generate and view trading signals
- **Signal Table** — Direction, confidence, risk score, entry/exit levels

### Analysis Tab
- **AnalysisPanel** — Performance metrics dashboard
- **CandlestickChart** — Daily/weekly/monthly price charts
- **PerformanceChart** — Win rate and return trends
- **FactorBarChart** — Factor contribution visualization

### Backtest Tab
- **Backtester** — Strategy backtesting with equity curves

### Feedback Tab
- **LearningInsights** — AI-generated insights and recommendations
- **Feedback Cycles** — Run daily/weekly review cycles

### Settings Tab
- **APISettings** — AI provider and exchange configuration

---

## 🔧 Backend Services

### Exchange Connectors
- **BinanceAdapter** — Spot and futures via CCXT
- **BybitAdapter** — Spot and derivatives
- **OKXAdapter** — Spot, futures, and options
- **CCXTExchange** — Base class for all CCXT-based adapters

### AI Providers
- **OllamaProvider** — Local AI inference (default)
- **OpenAIProvider** — GPT-4, GPT-3.5
- **AnthropicProvider** — Claude models
- **ProviderManager** — Provider selection and fallback

### Signal Generation
- **SignalGenerator** — Multi-factor scoring engine
- **RiskManager** — Position sizing and risk limits
- **CachedSignalGenerator** — Redis-cached signal generation

### Technical Analysis
- **IndicatorEngine** — RSI, MACD, Bollinger, ATR, Stochastic, EMA/SMA
- **PatternDetector** — Chart pattern recognition
- **SmartMoneyAnalyzer** — Order blocks, FVG, liquidity analysis
- **SRAnalyzer** — Support and resistance levels
- **TrendAnalyzer** — Trend direction and strength

---

## 🐳 Infrastructure

### Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `backend` | 8000 | Django application |
| `frontend` | 3000 | React application |
| `postgres` | 5432 | PostgreSQL + TimescaleDB + pgvector |
| `redis` | 6379 | Cache and message broker |
| `celery-worker` | — | Background task processing |
| `celery-beat` | — | Periodic task scheduling |
| `ollama` | 11434 | Local AI inference |
| `nginx` | 80 | Reverse proxy |
| `prometheus` | 9090 | Metrics collection |
| `grafana` | 3001 | Dashboard visualization |

### Monitoring

- **Prometheus** — Collects metrics from Django and Celery
- **Grafana** — Pre-configured dashboards for system monitoring
- **Health Checks** — `/health/`, `/health/detailed/`, `/health/ready/`, `/health/live/`
- **Structured Logging** — JSON-formatted logs with correlation IDs

---

## 👨‍💻 Development

### Code Quality

```bash
# Backend
black .
isort .
ruff check .
mypy .

# Frontend
cd frontend
npm run lint
npm run type-check
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Database Migrations

```bash
# Create migration
python manage.py makemigrations <app_name>

# Apply migrations
python manage.py migrate

# Show migrations
python manage.py showmigrations
```

---

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.signals
python manage.py test apps.technical_analysis

# With coverage
pytest --cov=apps --cov-report=html

# Run integration tests
pytest -m integration
```

### Frontend Tests

```bash
cd frontend
npm test
npm run test:coverage
```

### Docker Tests

```bash
# Run tests in Docker
docker-compose exec backend python manage.py test

# Run specific test
docker-compose exec backend python manage.py test apps.signals.tests.SignalGeneratorTest
```

---

## 🚢 Deployment

### Production Checklist

- [ ] Set `DJANGO_SECRET_KEY` to a secure random value
- [ ] Set `DJANGO_SETTINGS_MODULE=crypto_platform.settings.production`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set `DEBUG=False`
- [ ] Configure SSL/TLS certificates
- [ ] Set up database backups
- [ ] Configure monitoring alerts
- [ ] Set up log aggregation

### Docker Production

```bash
# Build for production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Environment-Specific Settings

| Setting | Development | Production |
|---------|-------------|------------|
| `DEBUG` | `True` | `False` |
| `ALLOWED_HOSTS` | `['*']` | `['yourdomain.com']` |
| `DATABASE` | SQLite/PostgreSQL | PostgreSQL |
| `CACHE` | Local memory | Redis |
| `STATIC_FILES` | Auto-served | Collected & served by Nginx |

---

## 🗺️ Roadmap

### ✅ Completed (Phases 1-22)

- [x] **Foundation** — Django project, models, auth, database
- [x] **Market Engine** — Exchange connectors, data collection, normalization
- [x] **News Intelligence** — RSS crawlers, Reddit, sentiment extraction
- [x] **AI Engine** — Multi-provider support, agent orchestration, memory
- [x] **Technical Analysis** — 15+ indicators, patterns, smart money
- [x] **Sentiment Engine** — Fear & Greed, social, whale tracking
- [x] **Signal Engine** — Multi-factor scoring, risk management
- [x] **Learning System** — Performance tracking, weight optimization
- [x] **Feedback Loop** — AI memory, similarity search, self-improvement
- [x] **Docker Deployment** — Full stack containerization
- [x] **Testing & QA** — Unit and integration tests
- [x] **Security Hardening** — SSRF prevention, rate limiting, input validation
- [x] **Performance** — Query optimization, caching, connection pooling
- [x] **OpenAPI Documentation** — drf-spectacular integration
- [x] **Monitoring** — Prometheus, Grafana, health checks
- [x] **CI/CD** — GitHub Actions pipeline
- [x] **Analytics** — Event tracking, CPR analysis, global events
- [x] **Frontend Enhancement** — Charts, real-time updates, demo mode
- [x] **TradingView UI** — Professional dark-theme interface
- [x] **Backtester** — Strategy backtesting with equity curves
- [x] **Portfolio Tracker** — Position tracking and allocation
- [x] **Ollama Integration** — Local AI model management

### 🔜 In Progress

- [ ] **WebSocket Streaming** — Real-time price and signal updates
- [ ] **Production Hardening** — SSL, backups, alerting

### 📅 Planned (Phases 24-28)

- [ ] **Mobile App** — React Native companion app
- [ ] **Advanced AI Strategies** — Multi-agent debate/consensus
- [ ] **Multi-exchange Arbitrage** — Cross-exchange opportunity detection
- [ ] **Social Trading** — Follow top traders, copy trading

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for all React components
- Write tests for new features
- Update documentation for API changes
- Use conventional commit messages

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Django](https://www.djangoproject.com/) — The web framework
- [React](https://reactjs.org/) — The UI library
- [CCXT](https://github.com/ccxt/ccxt) — Cryptocurrency exchange library
- [Ollama](https://ollama.ai/) — Local AI inference
- [TimescaleDB](https://www.timescale.com/) — Time-series database
- [TradingView](https://www.tradingview.com/) — UI inspiration

---

<div align="center">

**Built with ❤️ by the AI-Trading Team**

[⬆ Back to Top](#-ai-trading)

</div>
