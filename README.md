<div align="center">

# 🚀 AI-Trading

### Enterprise-Grade AI-Powered Cryptocurrency Intelligence Platform

**Real-time market analysis • Multi-agent AI signals • Self-learning system • Social trading**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/django-5.0+-green.svg)](https://djangoproject.com)
[![React](https://img.shields.io/badge/react-18+-61dafb.svg)](https://reactjs.org)
[![React Native](https://img.shields.io/badge/react--native-0.73+-61dafb.svg)](https://reactnative.dev)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://docker.com)
[![CI/CD](https://img.shields.io/badge/github--actions-passing-brightgreen.svg)](https://github.com/actions)

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
- [Mobile App](#-mobile-app)
- [Infrastructure](#-infrastructure)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

AI-Trading is a full-stack cryptocurrency trading platform that combines **multi-agent AI architecture**, **real-time market analysis**, **self-learning capabilities**, and **social trading** to generate intelligent trading signals. The platform integrates with major exchanges (Binance, Bybit, OKX), uses local AI models via Ollama for privacy-first analysis, and supports cross-exchange arbitrage opportunities.

### Key Highlights

- **🤖 Multi-Agent AI System** — Coordinated AI agents (Market Analyst, Technical Analyst, Sentiment Analyst, Risk Analyst) work together to generate comprehensive trading signals
- **📊 Multi-Factor Scoring** — Combines technical analysis, sentiment, news, AI predictions, and macro factors with configurable weights
- **🧠 Self-Learning** — The system learns from past signals, adjusting weights and strategies based on performance
- **📈 TradingView-Grade UI** — Professional dark-theme interface with real-time charts, order book, and portfolio tracking
- **🔄 Real-time Streaming** — WebSocket-powered live data feeds for prices, order book, and signal updates
- **💰 Arbitrage Detection** — Cross-exchange arbitrage opportunity detection and auto-execution
- **👥 Social Trading** — Follow top traders, copy trades, and share signals
- **📱 Mobile App** — React Native companion app with real-time alerts
- **🛡️ Production-Ready** — Docker deployment with monitoring, alerting, and security hardening

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ React Web UI │ │ React Native │ │   Trading    │ │   Social     │      │
│  │  (TradingView)│ │   Mobile App │ │   Backtester │ │   Trading    │      │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘      │
│                              WebSocket Client                              │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴─────────────────────────────────────────┐
│                        NGINX REVERSE PROXY (:80)                            │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴─────────────────────────────────────────┐
│                         DJANGO BACKEND (:8000)                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐│
│  │   Market   │ │  Signals   │ │     AI     │ │  Learning  │ │  Feedback  ││
│  │   Engine   │ │   Engine   │ │   Engine   │ │   Engine   │ │    Loop    ││
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘│
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐│
│  │    News    │ │ Sentiment  │ │ Technical  │ │  Notifi-   │ │  Reports   ││
│  │ Intelligence│ │  Analysis  │ │  Analysis  │ │  cations   │ │            ││
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘│
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │ Arbitrage  │ │   Social   │ │  Portfolio  │ │   Mobile   │              │
│  │  Detector  │ │  Trading   │ │ Management │ │     API    │              │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘              │
│                            WebSocket Server                                │
└───────┬────────────┬────────────┬────────────┬────────────┬────────────────┘
        │            │            │            │            │
┌───────┴──────┐┌────┴────┐┌─────┴─────┐┌─────┴─────┐┌─────┴─────┐
│  PostgreSQL  ││  Redis  ││  Celery   ││  Ollama   ││  Other    │
│ +TimescaleDB ││  Cache  ││  Workers  ││  (Local   ││   APIs    │
│  +pgvector   ││ Broker  ││   Beat    ││    AI)    ││           │
└──────────────┘└─────────┘└───────────┘└───────────┘└───────────┘
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
- **Strategy Engine** — Advanced AI strategies with multi-agent coordination
- **Memory System** — Vector embeddings for similarity search and learning
- **Prompt Versioning** — Track and version AI prompts

### 💰 Arbitrage
- **Cross-Exchange Detection** — Monitor Binance, Bybit, OKX for opportunities
- **Auto-Execution** — Automatically execute profitable arbitrage trades
- **Risk Scoring** — Evaluate opportunity risk before execution
- **Fee Calculation** — Account for exchange fees in profit calculations

### 👥 Social Trading
- **Trader Profiles** — Public profiles with performance metrics
- **Follow System** — Follow top traders
- **Copy Trading** — Automatically copy trades from followed traders
- **Leaderboard** — Rank traders by win rate, profit factor, Sharpe ratio
- **Signal Sharing** — Share and like trading signals

### 📱 Mobile App
- **Real-time Prices** — Live price tracking with WebSocket
- **Signal Alerts** — Push notifications for new signals
- **Portfolio Tracking** — View positions on the go
- **Price Alerts** — Configure custom price alerts

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

### 💼 Portfolio Management
- **Multi-Portfolio Support** — Manage multiple portfolios
- **Automated Rebalancing** — AI-driven portfolio rebalancing
- **Tax Optimization** — Tax-loss harvesting and cost basis tracking
- **Tax Reports** — Generate tax reports with FIFO/LIFO/HIFO

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
| WebSocket | Native WebSocket API |

### Mobile
| Component | Technology |
|-----------|-----------|
| Framework | React Native 0.73 |
| Navigation | React Navigation 6 |
| State | React Hooks |
| HTTP | Axios with auth interceptor |
| Storage | AsyncStorage |

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
git clone https://github.com/myazdanpanah/AI-Trading.git
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
# Grafana: http://localhost:3001
```

### Option 2: Local Development

```bash
# Clone the repository
git clone https://github.com/myazdanpanah/AI-Trading.git
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

# --- Mobile App Setup (optional) ---
cd mobile
npm install
npm start
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
│   ├── apps/                   # Django applications (19 apps)
│   │   ├── core/              # Shared utilities, health checks
│   │   ├── users/             # User management
│   │   ├── authentication/    # JWT authentication
│   │   ├── market/            # Market data engine + exchanges
│   │   ├── ai_engine/         # AI integration + strategy engine
│   │   ├── signals/           # Signal generation + backtester
│   │   ├── technical_analysis/ # Indicators & patterns
│   │   ├── sentiment/         # Sentiment analysis
│   │   ├── news/              # News intelligence
│   │   ├── analytics/         # Event tracking & CPR
│   │   ├── learning/          # Performance tracking
│   │   ├── feedback/          # AI memory & self-improvement
│   │   ├── notifications/     # Alerts & webhooks
│   │   ├── reports/           # Report generation
│   │   ├── mobile/            # Mobile app API
│   │   ├── arbitrage/         # Cross-exchange arbitrage
│   │   ├── social/            # Social trading
│   │   └── portfolio/         # Portfolio management
│   ├── urls.py                # URL routing
│   ├── ws_urls.py             # WebSocket URL routing
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
│   │   │   ├── social/        # Leaderboard, copy trading
│   │   │   └── settings/      # API settings
│   │   └── utils/
│   │       ├── api.ts         # API client with auth & mock fallback
│   │       └── websocket.ts   # WebSocket utility
│   ├── Dockerfile
│   └── package.json
├── mobile/                     # React Native mobile app
│   ├── src/
│   │   ├── screens/           # Home, Signals, Portfolio, Alerts, Settings
│   │   ├── components/        # PriceCard, MiniChart
│   │   └── services/          # API, Auth services
│   ├── App.tsx
│   └── package.json
├── docker/                     # Docker configurations
│   ├── nginx/                 # Nginx reverse proxy
│   ├── prometheus/            # Prometheus metrics
│   └── grafana/               # Grafana dashboards
├── scripts/                    # Utility scripts
│   └── init-db.sql            # Database initialization
├── docker-compose.yml          # Docker Compose orchestration
├── docker-compose.prod.yml     # Production override
├── .github/workflows/ci.yml    # GitHub Actions CI/CD
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

### Arbitrage

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/arbitrage/opportunities/` | Arbitrage opportunities |
| `POST` | `/api/arbitrage/opportunities/scan/` | Scan for opportunities |
| `GET` | `/api/arbitrage/configs/` | Arbitrage configuration |

### Social Trading

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/social/traders/` | Trader profiles |
| `GET` | `/api/social/traders/leaderboard/` | Top traders |
| `POST` | `/api/social/follows/` | Follow/unfollow traders |
| `GET` | `/api/social/copy-trades/` | Copy trade history |

### Portfolio

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/portfolio/portfolios/` | Portfolios |
| `POST` | `/api/portfolio/portfolios/` | Create portfolio |
| `POST` | `/api/portfolio/portfolios/{id}/rebalance/` | Rebalance portfolio |
| `GET` | `/api/portfolio/tax-lots/` | Tax lots |
| `POST` | `/api/portfolio/tax-reports/generate/` | Generate tax report |

### Learning & Feedback

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/learning/results/performance/` | Performance metrics |
| `GET` | `/api/feedback/analysis/insights/` | Learning insights |
| `POST` | `/api/feedback/cycles/run_cycle/` | Run feedback cycle |

### Mobile

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/mobile/devices/register/` | Register device |
| `GET` | `/api/mobile/alerts/` | Mobile alerts |
| `GET` | `/api/mobile/widgets/` | Mobile widgets |

> 📖 **Full API documentation**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)

---

## 📱 Mobile App

### Features
- **Home Screen** — Real-time price tracking, portfolio summary, watchlist
- **Signals Screen** — AI-generated signals with confidence scores
- **Portfolio Screen** — Position tracking with P&L
- **Alerts Screen** — Price and signal alert configuration
- **Settings Screen** — App configuration and account management

### Setup

```bash
cd mobile
npm install
npm start

# Scan QR code with Expo Go app (iOS/Android)
```

### Screenshots
The mobile app features a TradingView-inspired dark theme with real-time updates.

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

### Grafana Dashboards

- **System Overview** — API requests, response times, error rates
- **Trading Signals** — Signal generation, win rate, latency
- **Arbitrage** — Opportunities, execution, profit tracking
- **Portfolio** — Value, P&L, allocation

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
python manage.py test apps.arbitrage
python manage.py test apps.social
python manage.py test apps.portfolio

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

### Mobile Tests

```bash
cd mobile
npm test
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

### ✅ Completed (Phases 1-33)

| Phase | Name | Status |
|-------|------|--------|
| 1-7 | Foundation & Core | ✅ COMPLETE |
| 8 | Signals | ✅ COMPLETE |
| 9 | Learning | ✅ COMPLETE |
| 10 | Feedback Loop | ✅ COMPLETE |
| 12 | Docker Deployment | ✅ COMPLETE |
| 13 | Testing & QA | ✅ COMPLETE |
| 14 | Security Hardening | ✅ COMPLETE |
| 15 | Performance Optimization | ✅ COMPLETE |
| 15.5 | OpenAPI Documentation | ✅ COMPLETE |
| 16 | Monitoring & Observability | ✅ COMPLETE |
| 17 | CI/CD & Developer Experience | ✅ COMPLETE |
| 18 | Advanced Analytics & Reporting | ✅ COMPLETE |
| 18.5 | Frontend Enhancement | ✅ COMPLETE |
| 19 | TradingView UI | ✅ COMPLETE |
| 20 | Backtester | ✅ COMPLETE |
| 21 | Portfolio Tracker | ✅ COMPLETE |
| 22 | Ollama Integration | ✅ COMPLETE |
| 23 | WebSocket Streaming | ✅ COMPLETE |
| 24 | Mobile App API | ✅ COMPLETE |
| 25 | Advanced AI Strategies | ✅ COMPLETE |
| 26 | Multi-exchange Arbitrage | ✅ COMPLETE |
| 27 | Social Trading | ✅ COMPLETE |
| 28 | Advanced Portfolio Management | ✅ COMPLETE |
| 29 | Production Hardening | ✅ COMPLETE |
| 30 | Arbitrage Execution | ✅ COMPLETE |
| 31 | AI Strategy Engine | ✅ COMPLETE |
| 32 | Social Trading Frontend | ✅ COMPLETE |
| 33 | Enhanced Monitoring | ✅ COMPLETE |

### 🔜 Future Enhancements

- **Advanced AI Strategies** — More debate/consensus patterns
- **Multi-exchange Arbitrage** — Auto-execute arbitrage
- **Social Trading Frontend** — Web UI for social features
- **Production Monitoring** — Enhanced Grafana dashboards

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
- [React Native](https://reactnative.dev/) — Mobile framework
- [CCXT](https://github.com/ccxt/ccxt) — Cryptocurrency exchange library
- [Ollama](https://ollama.ai/) — Local AI inference
- [TimescaleDB](https://www.timescale.com/) — Time-series database
- [TradingView](https://www.tradingview.com/) — UI inspiration

---

<div align="center">

**Built with ❤️ by the AI-Trading Team**

[⬆ Back to Top](#-ai-trading)

</div>
