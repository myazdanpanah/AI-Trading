<div align="center">

# AI-Trading

### Enterprise-Grade AI-Powered Cryptocurrency Intelligence Platform

**Real-time market analysis • Multi-agent AI signals • Self-learning system • Social trading**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/django-5.0+-green.svg)](https://djangoproject.com)
[![React](https://img.shields.io/badge/react-18+-61dafb.svg)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/postgresql-16-blue.svg)](https://postgresql.org)

---

</div>

## Overview

AI-Trading is a full-stack cryptocurrency trading platform that combines **multi-agent AI architecture**, **real-time market analysis**, **self-learning capabilities**, and **social trading** to generate intelligent trading signals.

### What Makes It Special

- **Self-Learning AI** — The system learns from past signals, automatically adjusting weights based on what actually works
- **Real Data** — Live prices via WebSocket, TradingView charts, 68+ news sources, 30+ X/Twitter accounts
- **6-Hour Feedback Loop** — Scans news, candles, price, orderbook, social, technical, macro, and signals every 6 hours
- **TradingView UI** — Professional dark-theme interface with real-time charts
- **Bilingual** — Full English/Persian (Farsi) support throughout
- **Security Hardened** — Restricted hosts, CORS, JWT tokens, rate limiting
- **No Celery Required** — Standalone scheduler runs all tasks without Redis/Celery

---

## Key Features

### Trading Interface
- **TradingView Widget** — Professional candlestick charts with indicators
- **WebSocket Live Prices** — Real-time price updates via Daphne
- **Watchlist** — User-defined cryptocurrency pairs with live prices
- **Portfolio Tracker** — Position tracking with P&L

### Signal Engine (5 Factors with REAL Data)
```
SIGNAL GENERATION - All 5 Factors Now Use Real Data

1. TECHNICAL (35%)
   RSI, MACD, EMA, VWAP, Ichimoku, ATR
   Source: CoinGecko candles -> IndicatorEngine

2. SENTIMENT (15%)
   Fear & Greed Index + Social mentions
   Source: Alternative.me + X/Twitter via Nitter

3. NEWS (10%)
   20 recent articles, sentiment + keyword analysis
   Source: 35+ RSS feeds (CoinDesk, Reuters, BBC, etc.)

4. AI (25%)
   gemma4 LLM prediction with JSON parsing
   Source: Ollama local inference

5. MACRO (15%)
   BTC dominance, total market cap change
   Source: CoinGecko global API

Composite Score -> Direction -> Confidence -> Entry/SL/TP
```

### 6-Hour BTC Feedback Loop
```
COMPREHENSIVE FEEDBACK LOOP (Every 6 Hours)

SCANS ALL 8 DATA SOURCES:
1. NEWS       30 articles, sentiment analysis
2. CANDLES    Price changes, volume, patterns
3. PRICE      SMA/EMA, trend, support/resistance
4. ORDERBOOK  Volume, bid/ask imbalance
5. SOCIAL     Fear & Greed + X/Twitter sentiment
6. TECHNICAL  RSI, MACD, VWAP, EMA crossovers
7. MACRO      BTC dominance, market cap change
8. SIGNALS    Past signals vs actual outcomes

THEN:
- Generates actionable insights
- Adjusts factor weights based on performance
- Stores results in database
- Updates learning summary
```

### Chatbot (Bilingual)
- **Persian Support** — 99.4% Persian ratio on Farsi questions
- **Tab-Aware** — Knows which tab you're on, suggests relevant questions
- **Conversation History** — Last 10 messages sent to LLM for context
- **Analysis Integration** — Provides recommendation, confidence, risks, levels

### News & Social Media (68+ Sources)
```
NEWS SOURCES (40+):
   Crypto: CoinDesk, CoinTelegraph, The Block, Decrypt
   Finance: Bloomberg, FT, WSJ, CNBC
   Geopolitics: BBC, Al Jazeera, Guardian, DW News
   Conflict: War on Rocks, Crisis Group, Iran International
   Energy: OilPrice, Rigzone, EIA
   Central Banks: Federal Reserve, ECB

X/TWITTER ACCOUNTS (30+):
   Analysts: CryptoCapo, PlanB, WillyWoo, Hayes
   News: WatcherGuru, tier10k, WhaleAlert
   Geopolitics: sentdefender, BNONews, LiveSquawk
   Iran: IranIntl, IranIntl_En
   Macro: GoldTelegraph, SantiagoAuFund
```

### Backtesting Engine
```
BACKTESTING - Full Historical Strategy Validation

Features:
  - Configurable fees (default 0.1% per trade)
  - Configurable slippage (default 0.05%)
  - Position sizing based on risk per trade
  - Stop loss & take profit triggers
  - Multiple open positions support
  - Real historical data from CoinGecko

Metrics:
  - Total Return / CAGR
  - Sharpe Ratio (annualized)
  - Sortino Ratio (downside risk)
  - Max Drawdown
  - Win Rate / Profit Factor
  - Expectancy
  - MFE / MAE
  - Total Fees / Total Slippage

Reproducibility:
  - Strategy version tracking
  - Feature version tracking
  - Factor weight snapshots
  - Deterministic replay
  - No-look-ahead guarantee
```

### Scheduler (No Celery Required)
```
STANDALONE SCHEDULER - Backup for Celery

Runs all 10 scheduled tasks without Redis:

  news-crawl       every 30 min  - RSS feed crawling
  news-analyze     every hour    - Article sentiment analysis
  signals-generate every hour    - Signal generation (5 factors)
  signals-evaluate every hour    - Signal outcome evaluation
  candles-collect  every 4 hours - Candle data for AI training
  btc-6hour        every 6 hours - Full BTC feedback loop
  daily-feedback   daily 1 AM    - Daily analysis cycle
  weight-adjust    daily 2 AM    - Factor weight optimization
  weekly-feedback  Sunday 2 AM   - Comprehensive weekly review
  cleanup          monthly 3 AM  - Memory cleanup (90 day retention)
```

---

## Architecture

```
                    FRONTEND (:3000)
  Trading | Signals | Compare | Analysis | Journal | Feedback
  TradingView Widget | WebSocket Live Prices | Recharts

                            |
                            v HTTP + WebSocket

              DJANGO BACKEND (:8000) + DAPHNE (:8001)
  Market Engine | Signal Engine | AI Engine | Learning Engine
  News Sources | Sentiment | Technical | Journal | Feedback
  WebSocket Consumer | Weight Adjuster | Standalone Scheduler

        |            |            |            |
        v            v            v            v

  PostgreSQL    LocMem      Ollama       APIs
  Port 5433     Cache       gemma4       CoinGecko
  35+ tables                :latest      Nitter RSS
```

---

## Quick Start

### Prerequisites
- **Python** 3.11+
- **Node.js** 20+
- **PostgreSQL** 16+ (port 5433)
- **Ollama** (for AI features)

### 1. Clone & Setup
```bash
git clone https://github.com/myazdanpanah/AI-Trading.git
cd AI-Trading
```

### 2. Backend
```bash
pip install -r backend/requirements.txt
DJANGO_SETTINGS_MODULE=crypto_platform.settings.local python manage.py migrate
DJANGO_SETTINGS_MODULE=crypto_platform.settings.local python manage.py seed_news_sources
DJANGO_SETTINGS_MODULE=crypto_platform.settings.local python manage.py runserver 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
# -> http://localhost:3000
```

### 4. WebSocket Server
```bash
daphne -b 0.0.0.0 -p 8001 crypto_platform.asgi:application
```

### 5. Scheduler (No Celery Required)
```bash
# Option A: Standalone scheduler (recommended)
python scripts/scheduler.py

# Option B: Manual feedback loop
python manage.py run_feedback_loop

# Option C: Celery (if Redis available)
celery -A crypto_platform worker -l info -P solo
celery -A crypto_platform beat -l info
```

### 6. Create User
```bash
DJANGO_SETTINGS_MODULE=crypto_platform.settings.local python manage.py createsuperuser
```

---

## Dashboard Tabs

| Tab | Description |
|-----|-------------|
| **Trading** | Live TradingView chart, Order Book, Watchlist, Portfolio |
| **Signals** | Generate signals with 5-factor analysis + history |
| **Compare** | Multi-symbol comparison side by side |
| **Analysis** | Interactive gauges, charts, regime analysis, journal |
| **Journal** | AI-generated journal entries with news sources |
| **Feedback** | Performance metrics, AI insights, 6h loop status |
| **Settings** | AI models, news sources, alerts, user settings |

---

## API Endpoints

### Authentication
```bash
POST /api/auth/login/          # Login, get JWT tokens
POST /api/auth/token/refresh/  # Refresh access token
```

### Signals
```bash
GET  /api/signals/signals/              # List signals
POST /api/signals/signals/generate/     # Generate new signal
POST /api/signals/signals/evaluate/     # Evaluate past signals
GET  /api/signals/factor-weights/       # Factor weights
GET  /api/signals/weight-history/       # Weight change history
```

### Analysis
```bash
GET  /api/skills/full-analysis/?symbol=BTC  # Full market analysis
POST /api/skills/chat/                       # Chat with AI
```

### News & Journal
```bash
GET  /api/news/sources/           # News sources (68+)
GET  /api/journal/sources/        # Journal sources (69)
POST /api/journal/entries/generate/  # Generate journal entry
```

### Backtesting
```bash
POST /api/signals/backtests/run/              # Run a backtest (fees, slippage, full metrics)
GET  /api/signals/backtests/                  # List backtest results
GET  /api/signals/backtests/{id}/             # Get backtest details
GET  /api/signals/backtests/historical_data/  # Fetch OHLCV from CoinGecko
GET  /api/signals/backtests/compare/          # Compare multiple backtests
```

### Feedback
```bash
GET  /api/feedback/signal-memories/   # Signal outcomes
POST /api/feedback/cycles/run_cycle/  # Run feedback cycle
GET  /api/feedback/cycles/            # Cycle history
```

### WebSocket
```bash
ws://localhost:8001/ws/prices/   # Live price feed
```

---

## Configuration

### Database
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'crypto_platform',
        'PORT': '5433',
    }
}
```

### AI Provider (Ollama)
```python
OLLAMA_BASE_URL = 'http://localhost:11434'
DEFAULT_MODEL = 'gemma4:latest'
```

### Security
```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
CORS_ALLOWED_ORIGINS = ['http://localhost:3000']
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=30)
```

---

## Services

| Service | Port | Status |
|---------|------|--------|
| Frontend | 3000 | Running |
| Backend | 8000 | Running |
| WebSocket | 8001 | Running |
| PostgreSQL | 5433 | Running |
| Ollama | 11434 | Running |
| Scheduler | - | Running (background) |

---

## Roadmap

### Completed (59 Phases)
- Foundation, Signals, Learning, Feedback
- PostgreSQL, Real Signal Engine, AI Feedback Loop
- Celery Automation, Analysis Panel, Iran Timezone
- News & Social Settings, Candle Data, Comparison
- Alerts, Price Chart, Journal, Chatbot
- News Sources, Persian Language, Data Enricher
- WebSocket, X/Twitter, Weight History
- News Seeding, 6-Hour Feedback Loop, Security
- Standalone Scheduler (Celery backup)
- **Phase 57: Quant Research Engine** (backtesting with fees, slippage, Sortino, MFE/MAE, CAGR, deterministic replay)
- **Phase 58: Walk-Forward Validation** (rolling windows, parameter freezing, leakage detection, overfitting analysis)
- **Phase 59: Risk Engine** (independent safety gate, kill switch, position sizing, exposure limits)

### Next Steps (Implementation Plan Phases 58-70)
- [ ] Phase 58: Walk-Forward Validation (prevent overfitting)
- [ ] Phase 59: Risk Engine (independent risk control, kill switch)
- [ ] Phase 60: Derivatives Intelligence (funding, OI, liquidations)
- [ ] Phase 61: Market Regime Engine (10 regimes, regime-conditioned weights)
- [ ] Phase 62: Portfolio Intelligence (correlation, VaR, beta)
- [ ] Phase 63: Signal Fusion Engine (regime-aware, AI as post-fusion validator)
- [ ] Phase 64: Local AI Router (Ollama, llama.cpp, cloud plugins)
- [ ] Phase 65: Agent Ensemble (5 role-based local agents)
- [ ] Phase 66: Calibration Engine (Brier Score, reliability curves)
- [ ] Phase 67: Versioning & Data Lineage (reproducibility)
- [ ] Phase 68: Paper Trading
- [ ] Phase 69: Shadow Trading
- [ ] Phase 70: Live Execution (requires production review)

---

## License

This project is licensed under the **MIT License**.

---

<div align="center">

**Built with care by the AI-Trading Team**

</div>
