<div align="center">

# 🚀 AI-Trading

### Enterprise-Grade AI-Powered Cryptocurrency Intelligence Platform

**Real-time market analysis • Multi-agent AI signals • Self-learning system • Social trading**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/django-5.0+-green.svg)](https://djangoproject.com)
[![React](https://img.shields.io/badge/react-18+-61dafb.svg)](https://reactjs.org)
[![React Native](https://img.shields.io/badge/react--native-0.73+-61dafb.svg)](https://reactnative.dev)
[![PostgreSQL](https://img.shields.io/badge/postgresql-16-blue.svg)](https://postgresql.org)

---

</div>

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Dashboard](#-dashboard)
- [AI Learning Loop](#-ai-learning-loop)
- [API Documentation](#-api-documentation)
- [Configuration](#%EF%B8%8F-configuration)
- [Development](#-development)
- [Deployment](#-deployment)
- [Roadmap](#-roadmap)
- [License](#-license)

---

## 🌟 Overview

AI-Trading is a full-stack cryptocurrency trading platform that combines **multi-agent AI architecture**, **real-time market analysis**, **self-learning capabilities**, and **social trading** to generate intelligent trading signals.

### What Makes It Special

- **🤖 Self-Learning AI** — The system learns from past signals, automatically adjusting weights based on what actually works
- **📊 Real Data** — Live Binance prices, CoinGecko fallback, TradingView charts
- **🧠 Feedback Loop** — AI generates signals, evaluates outcomes, records lessons, and improves over time
- **📈 TradingView UI** — Professional dark-theme interface with real-time charts
- **🌐 Iran-Optimized** — Timezone support (IRST), VPN-friendly architecture

---

## 🎯 Key Features

### 📈 Trading Interface
- **TradingView Widget** — Professional candlestick charts with indicators
- **Real-time Order Book** — Live bid/ask display
- **Watchlist** — User-defined cryptocurrency pairs with live prices
- **Portfolio Tracker** — Position tracking with P&L

### 🎯 Signal Engine
- **Multi-Factor Scoring** — 5 factors: Technical, Sentiment, News, AI, Macro
- **Configurable Weights** — Auto-adjusted based on performance
- **Entry/SL/TP Levels** — Always calculated, even for HOLD signals
- **Detailed Reasons** — 3-5 reasons explaining every signal

### 🧠 AI Self-Learning Loop
```
┌─────────────────────────────────────────────────────────────────┐
│                    AI FEEDBACK LOOP                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. GENERATE SIGNAL (Signals tab)                               │
│     BTC HOLD @ $63,550 | Confidence: 52%                       │
│     Technical: 48% | Sentiment: 60%                             │
│                                                                 │
│  2. EVALUATE SIGNAL (Feedback tab)                              │
│     Check: what happened to BTC price?                          │
│     Result: BTC went to $63,538 (-0.02%)                        │
│                                                                 │
│  3. RECORD OUTCOME (SignalMemory)                               │
│     Signal: BTC HOLD | Result: LOSS -0.02%                      │
│     Lesson: "technical was misleading (48)"                     │
│                                                                 │
│  4. AI ANALYZES PATTERNS                                        │
│     "When technical score is 48%, HOLD signals lose money"      │
│                                                                 │
│  5. ADJUST WEIGHTS (WeightAdjuster)                             │
│     Reduce technical weight, increase sentiment weight          │
│                                                                 │
│  6. NEXT SIGNALS BENEFIT                                        │
│     AI adjusts weights based on what actually worked            │
│     Win rate improves over time                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 📊 Interactive Analysis Panel
- **SVG Gauge Charts** — Visual scores for Combined, Regime, Technical
- **Factor Score Bars** — Bar charts for all 5 factors
- **Weight Distribution** — Visual weight visualization
- **Journal Summary** — Latest AI analysis with findings/risks
- **Regime Details** — Market regime with posture/exposure

### 🔄 Automated Tasks (Celery)
| Task | Frequency | Description |
|------|-----------|-------------|
| Generate Signals | Every hour | BTC, ETH, SOL, BNB, XRP |
| Evaluate Signals | Every hour | Check 1+ hour old signals |
| Feedback Cycle | Daily 1 AM | Analyze patterns, generate insights |
| Weight Adjustment | Daily 2 AM | Adjust factor weights |
| Weekly Analysis | Sunday 2 AM | Comprehensive review |
| Memory Cleanup | Monthly | Remove 90+ day old memories |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (:3000)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Trading  │ │ Signals  │ │ Analysis │ │ Journal  │          │
│  │  Tab     │ │   Tab    │ │   Tab    │ │   Tab    │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                      │
│  │ Feedback │ │ Settings │ │ Chatbot  │                      │
│  │   Tab    │ │   Tab    │ │ (Floating)│                      │
│  └──────────┘ └──────────┘ └──────────┘                      │
│  TradingView Widget | Recharts | React Contexts                │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/WebSocket
┌───────────────────────────┴─────────────────────────────────────┐
│                     DJANGO BACKEND (:8000)                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│  │   Market   │ │  Signals   │ │     AI     │ │  Learning  │  │
│  │   Engine   │ │   Engine   │ │   Engine   │ │   Engine   │  │
│  │ (Binance)  │ │ (5-factor) │ │ (Ollama)   │ │ (Feedback) │  │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│  │    News    │ │ Sentiment  │ │ Technical  │ │  Journal   │  │
│  │  Sources   │ │  (F&G)     │ │ (RSI/MACD) │ │  (LLM)     │  │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                 │
│  │  Feedback  │ │  Weight    │ │   Celery   │                 │
│  │  Evaluator │ │  Adjuster  │ │   Worker   │                 │
│  └────────────┘ └────────────┘ └────────────┘                 │
└───────┬────────────┬────────────┬────────────┬─────────────────┘
        │            │            │            │
┌───────┴──────┐┌────┴────┐┌─────┴─────┐┌─────┴─────┐
│  PostgreSQL  ││  Redis  ││  Ollama   ││  APIs     │
│  Port 5433   ││  Cache  ││  gemma4   ││ Binance   │
│  30+ tables  ││ Broker  ││  :latest  ││ CoinGecko │
└──────────────┘└─────────┘└───────────┘└───────────┘
```

---

## 🛠️ Tech Stack

### Backend
| Component | Technology |
|-----------|-----------|
| Framework | Django 5.0 + Django REST Framework |
| Database | PostgreSQL 18 (port 5433) |
| Cache/Broker | Redis 7 |
| Task Queue | Celery 5.3 |
| AI | Ollama (gemma4:latest), OpenAI, Anthropic |
| Market Data | Binance API, CoinGecko API |
| API Docs | drf-spectacular (OpenAPI/Swagger) |

### Frontend
| Component | Technology |
|-----------|-----------|
| Framework | React 18 + TypeScript |
| Build Tool | Vite 5 |
| Styling | TailwindCSS 3 |
| Charts | Recharts, TradingView Widget |
| State | React Contexts |
| Language | English / Persian (فارسی) |

### Infrastructure
| Component | Technology |
|-----------|-----------|
| Database | PostgreSQL 18 |
| Timezone | Asia/Tehran (IRST, UTC+3:30) |
| CI/CD | GitHub Actions |
| Code Quality | Black, isort, Ruff, ESLint |

---

## 🚀 Quick Start

### Prerequisites

- **Python** 3.11+
- **Node.js** 20+
- **PostgreSQL** 16+ (port 5433)
- **Redis** 7+ (optional, for Celery)

### 1. Clone & Setup

```bash
git clone https://github.com/myazdanpanah/AI-Trading.git
cd AI-Trading
```

### 2. PostgreSQL Setup

```bash
# Create database
PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -c "CREATE DATABASE crypto_platform;"

# Run migrations
DJANGO_SETTINGS_MODULE=crypto_platform.settings.local python manage.py migrate

# Create user
DJANGO_SETTINGS_MODULE=crypto_platform.settings.local python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='myazdanpanah').exists():
    User.objects.create_user('myazdanpanah', password='123456')
"
```

### 3. Backend

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run server
DJANGO_SETTINGS_MODULE=crypto_platform.settings.local python manage.py runserver
# → http://localhost:8000
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### 5. Login

```
URL:      http://localhost:3000
Username: myazdanpanah
Password: 123456
```

### 6. (Optional) Start Celery for Auto Tasks

```bash
# Terminal 1: Worker
celery -A crypto_platform worker -l info

# Terminal 2: Beat (Scheduler)
celery -A crypto_platform beat -l info
```

---

## 📊 Dashboard

### Tabs Overview

| Tab | Description |
|-----|-------------|
| 📈 **Trading** | Live TradingView chart, Order Book, Watchlist, Portfolio |
| 🔔 **Signals** | Generate trading signals with multi-factor analysis |
| 📊 **Analysis** | Interactive gauges, charts, regime analysis, journal summary |
| 📝 **Journal** | AI-generated journal entries with news sources |
| 🧠 **Feedback** | Performance metrics, AI insights, learning cycles |
| ⚙️ **Settings** | AI models, news sources, user settings |

### Signal Example

```
Symbol: BTC | Direction: HOLD | Confidence: 52%
Entry: $63,550 | SL: $61,039 | TP: $66,060, $67,315

Reasons:
  [technical] Mixed signals (score: 48) - no clear direction
  [technical] RSI neutral (47) - no momentum signal
  [technical] VWAP bearish - price below VWAP
  [sentiment] Fear dominant (F&G: 27) - market cautious

Factor Scores:
  Technical: 48% | Sentiment: 60% | News: 50%
  AI: 50% | Macro: 50%
```

### Analysis Panel

```
┌──────────────────────────────────────────────────────────┐
│  FINAL VERDICT: HOLD                                     │
│  Posture: MODERATE | Max Exposure: 15%                   │
│                                                          │
│    ╭───╮      ╭───╮      ╭───╮                          │
│   │ 49 │     │ 65 │     │ 48 │   ← SVG Gauges          │
│   ╰───╯      ╰───╯      ╰───╯                          │
│  Combined  Regime   Technical                            │
└──────────────────────────────────────────────────────────┘

Factor Scores:          Weight Distribution:
Tech: 48 ▓▓▓▓░░        technical 32%
Sent: 60 ▓▓▓▓▓▓        sentiment 20%
News: 50 ▓▓▓▓░░        news 14% | ai 20% | macro 14%
AI:   50 ▓▓▓▓░░
Macro:50 ▓▓▓▓░░
```

---

## 🧠 AI Learning Loop

### How the AI Improves Over Time

```
Hour 1: Generate 5 signals → Evaluate 0 (too new)
Hour 2: Generate 5 signals → Evaluate 5 (from Hour 1) → Record outcomes
Hour 3: Generate 5 signals → Evaluate 5 (from Hour 2) → Record outcomes
...
Daily: Analyze all outcomes → Generate insights → Adjust weights
```

### Factor Weight Adjustment

| Factor | Initial Weight | After Learning | Change |
|--------|---------------|----------------|--------|
| Technical | 0.30 | 0.316 | +5.3% |
| Sentiment | 0.20 | 0.200 | — |
| News | 0.15 | 0.142 | -5.3% |
| AI | 0.20 | 0.200 | — |
| Macro | 0.15 | 0.142 | -5.3% |

### Performance Tracking

- **Win Rate** — Percentage of profitable signals
- **Avg Return** — Average return per signal
- **Profit Factor** — Gross profit / gross loss
- **Sharpe Ratio** — Risk-adjusted return
- **Per-Factor Analysis** — Which factors contribute most to wins

---

## 📡 API Documentation

### Authentication

```bash
# Login (get JWT tokens)
POST /api/auth/login/
{
  "username": "myazdanpanah",
  "password": "123456"
}
# Returns: { "access": "...", "refresh": "..." }

# Use token in requests
Authorization: Bearer <access_token>
```

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login/` | Login, get JWT tokens |
| `GET` | `/api/users/users/` | User profile |
| `GET` | `/health/` | Health check |
| `GET` | `/api/docs/` | Swagger UI |

### Market Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/market/data/status/` | Data source status |
| `GET` | `/api/market/data/ticker/?symbol=BTCUSDT` | Quick ticker |
| `GET` | `/api/market/data/candles/live/` | Live candles |

### Signals

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/signals/signals/latest/` | Recent signals |
| `POST` | `/api/signals/signals/generate/` | Generate new signal |
| `POST` | `/api/signals/signals/evaluate/` | Evaluate past signals |
| `GET` | `/api/signals/factor-weights/` | Factor weights |
| `POST` | `/api/signals/factor-weights/adjust/` | Auto-adjust weights |
| `POST` | `/api/signals/factor-weights/reset/` | Reset to defaults |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/signals/analysis/full/?symbol=BTCUSDT` | Full market analysis |
| `GET` | `/api/signals/analysis/regime/?symbol=BTCUSDT` | Regime analysis |

### Journal

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/journal/entries/` | Journal entries |
| `POST` | `/api/journal/entries/generate/` | Generate journal entry |
| `GET` | `/api/journal/sources/` | News sources |
| `GET` | `/api/journal/user-watchlist/` | User watchlist |

### Feedback

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/feedback/signal-memories/` | Signal memories |
| `POST` | `/api/feedback/cycles/run_cycle/` | Run feedback cycle |
| `GET` | `/api/feedback/cycles/` | Feedback cycle history |
| `GET` | `/api/feedback/insights/` | AI insights |

### Watchlist

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/journal/user-watchlist/` | Get watchlist |
| `POST` | `/api/journal/user-watchlist/` | Add symbol |
| `DELETE` | `/api/journal/user-watchlist/{id}/` | Remove symbol |
| `GET` | `/api/journal/user-watchlist/search/?q=BTC` | Search symbols |

### Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/ai/providers/` | AI providers |
| `GET` | `/api/journal/news-sources/` | News sources |

> 📖 **Full API docs**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)

---

## ⚙️ Configuration

### Database

```python
# crypto_platform/settings/local.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'crypto_platform',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5433',  # Custom port
    }
}
```

### Timezone

```python
# Asia/Tehran (IRST, UTC+3:30)
TIME_ZONE = 'Asia/Tehran'
USE_TZ = True
```

### AI Provider (Ollama)

```python
# Default: Ollama (local, free)
OLLAMA_BASE_URL = 'http://localhost:11434'
DEFAULT_MODEL = 'gemma4:latest'
```

### Exchange API

```bash
# Binance (requires VPN in Iran)
BINANCE_API_KEY=your-key
BINANCE_API_SECRET=your-secret

# CoinGecko (no key needed, works in Iran)
COINGECKO_API_KEY=your-key (optional)
```

---

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
python manage.py test

# Run specific app
python manage.py test apps.signals
python manage.py test apps.feedback

# With coverage
pytest --cov=apps --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm test
npm run lint
```

### Manual Testing

```bash
# Test login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"myazdanpanah","password":"123456"}'

# Test signal generation
TOKEN=<access_token>
curl -X POST http://localhost:8000/api/signals/signals/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSDT","timeframe":"1h"}'

# Test analysis
curl "http://localhost:8000/api/signals/analysis/full/?symbol=BTCUSDT" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🚢 Deployment

### Production Checklist

- [ ] Set `DJANGO_SECRET_KEY` to secure random value
- [ ] Set `DJANGO_SETTINGS_MODULE=crypto_platform.settings.production`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set `DEBUG=False`
- [ ] Configure SSL/TLS certificates
- [ ] Set up database backups
- [ ] Configure monitoring alerts
- [ ] Start Celery worker + beat

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | (must set) |
| `DJANGO_SETTINGS_MODULE` | Settings module | `crypto_platform.settings.local` |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5433` |
| `DB_NAME` | Database name | `crypto_platform` |
| `OLLAMA_BASE_URL` | Ollama API URL | `http://localhost:11434` |

---

## 🗺️ Roadmap

### ✅ Completed

| Phase | Name | Status |
|-------|------|--------|
| 1-7 | Foundation & Core | ✅ |
| 8 | Signals | ✅ |
| 9-10 | Learning & Feedback | ✅ |
| 12-33 | Production & Features | ✅ |
| 34 | PostgreSQL Database | ✅ |
| 35 | Real Signal Engine | ✅ |
| 36 | AI Feedback Loop | ✅ |
| 37 | Auto Weight Adjustment | ✅ |
| 38 | Celery Automation | ✅ |
| 39 | Interactive Analysis Panel | ✅ |
| 40 | Iran Timezone Support | ✅ |

### 🔜 Next

- [ ] Weight History Chart — Visualize weight changes over time
- [ ] Signal History Table — Show all past signals with outcomes
- [ ] Multi-Symbol Comparison — Compare signals side by side
- [ ] Score Alerts — Alert when scores cross thresholds
- [ ] Celery Auto-Start — Automatic signal generation on startup

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Django](https://www.djangoproject.com/) — The web framework
- [React](https://reactjs.org/) — The UI library
- [TradingView](https://www.tradingview.com/) — Charting widgets
- [Binance](https://www.binance.com/) — Market data API
- [CoinGecko](https://www.coingecko.com/) — Fallback data API
- [Ollama](https://ollama.ai/) — Local AI inference
- [PostgreSQL](https://www.postgresql.org/) — Database

---

<div align="center">

**Built with ❤️ by the AI-Trading Team**

[⬆ Back to Top](#-ai-trading)

</div>
