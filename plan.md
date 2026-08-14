# Development Plan

## Crypto AI Signal Platform

### Project Overview
An enterprise-grade AI-powered cryptocurrency intelligence platform with multi-agent AI architecture, real-time market analysis, and self-learning capabilities.

---

## Completed Phases (1-57)

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
| 41 | News & Social Media Settings | ✅ |
| 42 | Candle Data & AI Training | ✅ |
| 43 | Multi-Symbol Comparison | ✅ |
| 44 | Score Alert System | ✅ |
| 45 | Real-Time Price Chart | ✅ |
| 46 | Auto Journal Generation | ✅ |
| 47 | ChatBot Fixes & Context | ✅ |
| 48 | Comprehensive News Sources | ✅ |
| 49 | Chatbot Persian Language | ✅ |
| 50 | Signal Data Enricher | ✅ |
| 51 | WebSocket Live Prices | ✅ |
| 52 | X/Twitter Scraping | ✅ |
| 53 | Weight History Chart | ✅ |
| 54 | News Source Seeding | ✅ |
| 55 | 6-Hour BTC Feedback Loop | ✅ |
| 56 | Security Hardening | ✅ |
| **57** | **Quant Research Engine** | ✅ |
| **58** | **Walk-Forward Validation** | ✅ |
| **59** | **Risk Engine** | ✅ |
| **60** | **Derivatives Intelligence** | ✅ |

---

## 🔜 NEXT STEPS (from AI-Trading-Implementation-Plan.md)

### Phase 58: Walk-Forward Validation ✅
Prevent strategy overfitting with train/validate/test splits.
- Training window, validation window, test window ✅
- Rolling windows support ✅
- Freeze optimized parameters before OOS ✅
- Store each run, compare windows ✅
- Detect leakage ✅

### Phase 59: Risk Engine
Independent risk-control layer — the critical safety gate.
- Position sizing
- Maximum risk enforcement
- Portfolio exposure limits
- Drawdown limits
- Daily loss limit
- Kill switch
- **Rule: Signal → Risk → Execution (never LLM → Order)**

### Phase 60: Derivatives Intelligence
- Funding Rate, Open Interest, Liquidations
- Long/Short Ratio, Basis
- Options IV, Put/Call Ratio
- Feature generation for signal engine

### Phase 61: Market Regime Engine
- 10 regimes: Bull/Bear/Sideways/High Vol/Low Vol/Breakout/Accumulation/Distribution/Capitulation/Recovery
- Regime-conditioned signal weights
- Strategy selection by regime

### Phase 62: Portfolio Intelligence
Extend existing Portfolio Tracker with:
- Correlation, Beta, Concentration
- BTC/Stablecoin exposure
- VaR, Max Drawdown, Effective Exposure

### Phase 63: Signal Fusion Engine
Upgrade existing 5-factor composite to regime-aware fusion.
- Remove AI from pre-fusion weighted input (move to post-fusion validator)
- Add Market Structure, Derivatives, Order Book as first-class factors
- Regime-conditioned weights
- Per-component contribution stored

### Phase 64: Local AI Router
- LLMProvider abstraction (Ollama, llama.cpp, Cloud)
- Model discovery, health checks, structured output
- AI OFF / AI LITE / AI STANDARD / AI CLOUD modes

### Phase 65: Agent Ensemble
- Technical Analyst, News Analyst, Market Analyst, Risk Analyst, Final Validator
- Role-based prompts, input/output schemas
- Agent performance tracking

### Phase 66: Calibration Engine
- Brier Score, Reliability Curve, Calibration Error
- Calibrated probability for future signals

### Phase 67: Versioning & Data Lineage
- Strategy/Feature/Model/Prompt/Signal versioning
- Market/News/Social/LLM snapshots
- Reproducibility: "Why was this signal generated?"

### Phase 68: Paper Trading
- PaperExecutionProvider (same engine as live, different execution target)
- Simulated fills, positions, PnL, fees, slippage

### Phase 69: Shadow Trading
- Real market data, real signals, simulated execution
- Expected vs actual execution comparison

### Phase 70: Live Execution
- Exchange adapters, order management, kill switch
- **Requires explicit production-readiness review**

---

## Architecture Decisions

### What's Working Well
- ✅ PostgreSQL with 35+ tables
- ✅ Django REST Framework with JWT auth
- ✅ React frontend with TailwindCSS
- ✅ TradingView widget integration
- ✅ Multi-factor signal scoring (5 factors with REAL data)
- ✅ AI feedback loop with 6-hour BTC cycle
- ✅ Comprehensive news source configuration (68+ sources)
- ✅ X/Twitter scraping via Nitter RSS
- ✅ Tab-aware chatbot with Persian/English
- ✅ Iran timezone (Asia/Tehran) support
- ✅ WebSocket live prices via Daphne
- ✅ Security hardened (restricted hosts, CORS, JWT)
- ✅ Backtesting engine with fees, slippage, full metrics
- ✅ Historical data ingestion from CoinGecko

### Key Architecture Rule (from Implementation Plan)
```
LLM must NEVER directly execute trades.

Required flow:
Data → Understanding → Regime → Quant Prediction → Multi-Factor Signal → Local AI Reasoning → Risk Control → Execution → Measurement → Calibration → Learning

Forbidden:
LLM → BUY → Exchange Order
```

---

## Commands to Run

```bash
# Start backend
cd /c/Trading
DJANGO_SETTINGS_MODULE=crypto_platform.settings.local python manage.py runserver 8000

# Start frontend
cd /c/Trading/frontend
npm run dev

# Start WebSocket server
cd /c/Trading
set DJANGO_SETTINGS_MODULE=crypto_platform.settings.local
daphne -b 0.0.0.0 -p 8001 crypto_platform.asgi:application

# Start scheduler
python scripts/scheduler.py

# Run tests
python run_tests.py apps.signals.tests

# Run backtest via API
curl -X POST http://localhost:8000/api/signals/backtests/run/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "sma_crossover",
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-02-01T00:00:00Z",
    "initial_capital": 10000,
    "fee_rate": 0.001,
    "slippage_rate": 0.0005
  }'
```
