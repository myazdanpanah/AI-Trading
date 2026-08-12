# Development Plan

## Crypto AI Signal Platform

### Project Overview
An enterprise-grade AI-powered cryptocurrency intelligence platform with multi-agent AI architecture, real-time market analysis, and self-learning capabilities.

---

## Execution Strategy

### Parallel Development Approach
To accelerate development, we use **sub-agent delegation** for independent modules:

| Phase | Sub-Agent | Task | Dependencies |
|-------|-----------|------|--------------|
| 1.1 | Agent A | Django project + settings | None |
| 1.2 | Agent B | Database models (all apps) | Agent A |
| 1.3 | Agent C | Docker + infrastructure | Agent A |
| 1.4 | Agent D | Celery + Redis setup | Agent A |

---

## Phase 1: Foundation (Week 1-2) ✅ COMPLETE

### 1.1 Backend Architecture ✅

```
Django Project Setup
├── crypto_platform/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   ├── local.py (PostgreSQL on port 5433)
│   │   └── docker.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── core/           # Shared utilities, base models ✅
│   ├── users/          # User management ✅
│   ├── authentication/ # JWT authentication ✅
│   ├── market/         # Market data engine ✅
│   ├── news/           # News intelligence ✅
│   ├── analytics/      # Analytics engine ✅
│   ├── ai_engine/      # AI integration ✅
│   ├── signals/        # Signal generation ✅
│   ├── learning/       # Learning engine ✅
│   ├── feedback/       # AI feedback loop ✅
│   ├── notifications/  # Notifications ✅
│   ├── reports/        # Reporting ✅
│   ├── mobile/         # Mobile app API ✅
│   ├── arbitrage/      # Cross-exchange arbitrage ✅
│   ├── social/         # Social trading ✅
│   ├── portfolio/      # Portfolio management ✅
│   └── technical_analysis/ # Indicators & patterns ✅
```

### 1.2 Database Architecture ✅

```
PostgreSQL 18 (port 5433)
├── Core Tables ✅
│   ├── users
│   ├── user_preferences
│   └── audit_logs
├── Market Tables ✅
│   ├── candles
│   ├── order_books
│   └── tickers
├── Technical Tables ✅
│   ├── indicators
│   └── technical_patterns
├── News Tables ✅
│   ├── news_articles
│   └── news_sources (7 sources configured)
├── AI Tables ✅
│   ├── ai_providers
│   └── ai_models
├── Signal Tables ✅
│   ├── signals
│   ├── signal_reasons
│   ├── signal_memories
│   └── factor_weights
├── Feedback Tables ✅
│   ├── feedback_cycles
│   ├── feedback_insights
│   └── signal_performance
├── Journal Tables ✅
│   ├── journal_entries
│   └── news_sources
└── Watchlist Tables ✅
    └── watchlist (10 symbols, user-defined)
```

### 1.3 Infrastructure ✅

```
Local Development (preferred over Docker):
├── Backend: Django on port 8000 ✅
├── Frontend: Vite on port 3000 ✅
├── Database: PostgreSQL on port 5433 ✅
└── Celery: Worker + Beat (optional) ✅
```

### 1.4 Background Processing ✅

```
Celery Tasks (configured, ready to start):
├── Hourly Tasks
│   ├── signals.generate_hourly ✅
│   │   Generate signals for BTC, ETH, SOL, BNB, XRP
│   └── feedback.evaluate_signals_hourly ✅
│       Evaluate old signals, record outcomes
├── Daily Tasks
│   ├── feedback.run_daily_cycle ✅
│   │   Analyze signals, generate insights
│   └── signals.adjust_weights ✅
│       Adjust factor weights based on performance
├── Weekly Tasks
│   └── feedback.run_weekly_cycle ✅
│       Comprehensive analysis
└── Monthly Tasks
    └── feedback.cleanup_old_memories ✅
        Remove old memories
```

---

## Phase 2-8: Core Engines ✅ COMPLETE

### Market Data Engine ✅
- Binance API integration (with VPN for Iran)
- CoinGecko fallback
- OHLCV candles, order books, tickers

### News Intelligence ✅
- 7 trusted news sources configured
- RSS feed integration
- Sentiment analysis

### AI Engine ✅
- Ollama integration (gemma4:latest)
- OpenAI/Anthropic support
- Agent orchestration

### Technical Analysis ✅
- RSI, MACD, EMA, SMA
- VWAP, Ichimoku Cloud
- Bollinger Bands, ATR, Stochastic

### Sentiment Engine ✅
- Fear & Greed Index
- Social sentiment

### Signal Engine ✅
- Multi-factor scoring (5 factors)
- Configurable weights
- Entry/SL/TP calculation
- Real Binance data

---

## Phase 9-10: Learning System ✅ COMPLETE

### Learning Engine ✅
- Performance tracking
- Win rate, profit factor, Sharpe ratio

### Feedback Loop ✅
- SignalEvaluator checks price outcomes
- SignalMemory records lessons
- WeightAdjuster auto-tunes factors
- AI insights generated from patterns

---

## Phase 19: TradingView UI ✅ COMPLETE

### Trading Interface ✅
- TradingView widget for charts (direct from browser)
- Real-time order book
- Watchlist with user-defined symbols
- Portfolio tracker

### Analysis Panel ✅
- SVG gauge charts (Combined, Regime, Technical)
- Factor score bar charts
- Weight distribution visualization
- Journal summary with AI analysis
- Regime details with posture/exposure

---

## Phase 35: Real Signal Engine ✅ COMPLETE

| Component | Status | Notes |
|-----------|--------|-------|
| Live Binance data | ✅ | Real prices and candles |
| Technical indicators | ✅ | RSI, MACD, EMA, VWAP, Ichimoku |
| Sentiment analysis | ✅ | Fear & Greed Index |
| Entry/SL/TP levels | ✅ | Always calculated |
| Signal reasons | ✅ | 3-5 detailed reasons per signal |
| Percentage display | ✅ | Fixed to show 0-100% correctly |

---

## Phase 36-37: AI Feedback Loop ✅ COMPLETE

### Self-Learning Loop ✅
```
Generate Signal → Evaluate Outcome → Record Memory → Adjust Weights → Better Signals
```

### Components
- SignalEvaluator — checks price after signal
- SignalMemory — records lessons learned
- WeightAdjuster — adjusts factor weights
- Performance metrics — win rate, avg return
- FeedbackPanel UI — real-time dashboard

---

## Phase 38: Celery Automation ✅ COMPLETE

### Beat Schedule
```
Every Hour: Generate signals + Evaluate old signals
Daily 1AM: Feedback cycle + Weight adjustment
Weekly 2AM: Comprehensive analysis
Monthly 3AM: Memory cleanup
```

---

## Phase 39: Interactive Analysis Panel ✅ COMPLETE

### Features
- SVG gauge charts for scores
- Factor score bar charts
- Weight distribution visualization
- Journal summary with AI analysis
- AI weight analysis with win rates
- Regime details with posture/exposure

---

## Phase 40: Iran Timezone Support ✅ COMPLETE

- Backend: Asia/Tehran (IRST, UTC+3:30)
- All frontend timestamps display in IRST

---

## Future Enhancements

### Priority 1: Weight History Visualization
- Chart showing how weights change over time
- In Settings or Analysis panel

### Priority 2: Signal History Table
- Show all past signals with outcomes
- Sort by date, symbol, outcome

### Priority 3: Multi-Symbol Comparison
- Compare signals across BTC, ETH, SOL, etc.
- Side-by-side analysis view

### Priority 4: Score Alerts
- Alert when RSI crosses 30/70
- Alert when confidence > 80%
- Email/Telegram notifications

### Priority 5: Auto Signal Generation
- Start Celery for automatic hourly signals
- Build up learning data over time

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| API rate limits | High | Caching, respect limits, CoinGecko fallback |
| Binance blocked in Iran | Medium | Use VPN, CoinGecko as backup |
| Data quality | High | Validation pipeline |
| Model hallucination | Medium | Structured output, validation |
| Infrastructure costs | Medium | Local-first, Ollama default |

---

## Success Criteria

### Phase 1 Complete When: ✅
- [x] Django project runs locally
- [x] All apps created with models
- [x] Database migrations work
- [x] PostgreSQL running on port 5433
- [x] API endpoints accessible

### Full Project Complete When:
- [x] Real-time market data flowing
- [x] AI signals generating with real data
- [x] Dashboard displaying live data
- [x] Learning system improving accuracy
- [x] Feedback loop connected
- [x] Auto weight adjustment working
- [ ] Celery running for automatic tasks
- [ ] Weight history visualization
- [ ] Signal history table
