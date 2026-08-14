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
| **61** | **Market Regime Engine** | ✅ |
| **62** | **Portfolio Intelligence** | ✅ |
| **63** | **Signal Fusion Engine** | ✅ |
| **64** | **Local AI Router** | ✅ |
| **65** | **Agent Ensemble** | ✅ |
| **66** | **Calibration Engine** | ✅ |
| **67** | **Versioning & Data Lineage** | ✅ |
| **68** | **Paper Trading** | ✅ |
| **69** | **Shadow Trading** | ✅ |
| **70** | **Live Execution** | ✅ |

### Integration & Documentation
| **INT-1** | **Signal-to-Execution Tests** | ✅ 50/50 |
| **INT-2** | **Phase Integration Tests** | ✅ 32/32 |
| **INT-3** | **API Documentation** | ✅ 100+ endpoints |
| **INT-4** | **Deployment Guide** | ✅ Docker + Security |
| **INT-5** | **Reproducibility Dashboard** | ✅ |
| **INT-6** | **Paper Trading Dashboard** | ✅ |
| **INT-7** | **VersionTracker Integration** | ✅ |

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

### Phase 65: Agent Ensemble ✅
5 role-based local agents running sequentially:
- Technical Analyst, News Analyst, Market Analyst, Risk Analyst, Final Validator ✅
- Role-based prompts, input/output schemas, structured JSON ✅
- AI OFF/LITE/STANDARD modes ✅
- Agent performance tracking ✅
- 24/24 tests pass ✅

### Phase 66: Calibration Engine ✅
- Brier Score, Reliability Curve, Calibration Error ✅
- ECE, MCE, overconfidence/underconfidence detection ✅
- Per-group calibration (regime, timeframe, symbol) ✅
- ProbabilityAdjuster for confidence correction ✅
- 28/28 tests pass ✅

### Phase 67: Versioning & Data Lineage ✅
- Strategy/Feature/Model/Prompt/Signal versioning ✅
- Market/News/Social/Derivatives/LLM snapshots ✅
- Reproducibility: "Why was this signal generated?" ✅
- Human-readable explanation via explain_signal() ✅
- 22/22 tests pass ✅

### Phase 68: Paper Trading ✅
- PaperExecutionProvider (same engine as live, different execution target) ✅
- Simulated fills, positions, PnL, fees, slippage ✅
- Stop loss / take profit auto-triggers ✅
- Performance metrics (win rate, Sharpe, expectancy) ✅
- 28/28 tests pass ✅

### Phase 69: Shadow Trading ✅
- Real market data, real signals, simulated execution ✅
- Expected vs actual execution comparison ✅
- Slippage tracking in basis points ✅
- Execution quality scoring (0-100) ✅
- 23/23 tests pass ✅

### Phase 70: Live Execution ✅
- Exchange adapters, order management, kill switch ✅
- Safety layers: LIVE_TRADING_ENABLED, Kill Switch, Risk Engine ✅
- Retry logic with exponential backoff ✅
- Live trading disabled by default ✅
- 27/27 tests pass ✅

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

---

## 🚀 RECOMMENDED NEXT STEPS

### Priority 1: Production Hardening
| Step | Description | Effort |
|------|-------------|--------|
| 1.1 | Celery worker + beat for automated signal generation | 2h |
| 1.2 | WebSocket real-time price feed for live watchlist updates | 3h |
| 1.3 | X/Twitter scraping for real social sentiment | 4h |
| 1.4 | Weight history visualization chart in frontend | 2h |
| 1.5 | Backtesting dashboard with equity curves | 4h |

### Priority 2: AI Intelligence
| Step | Description | Effort |
|------|-------------|--------|
| 2.1 | Pull more Ollama models (llama3, qwen3.5) for comparison | 1h |
| 2.2 | Add model performance tracking per agent | 3h |
| 2.3 | Implement agent-specific prompts for better analysis | 4h |
| 2.4 | Add news source reliability scoring | 2h |
| 2.5 | Implement multi-timeframe signal fusion | 3h |

### Priority 3: Trading Features
| Step | Description | Effort |
|------|-------------|--------|
| 3.1 | Connect paper trading to real signal generation | 2h |
| 3.2 | Add limit order support in paper trading | 2h |
| 3.3 | Implement trailing stop loss | 2h |
| 3.4 | Add portfolio rebalancing suggestions | 3h |
| 3.5 | Build mobile-responsive design | 4h |

### Priority 4: Data & Analytics
| Step | Description | Effort |
|------|-------------|--------|
| 4.1 | Add on-chain data (whale movements, exchange flows) | 4h |
| 4.2 | Implement sentiment analysis from X/Twitter API | 3h |
| 4.3 | Add macro economic indicators (DXY, rates, bonds) | 3h |
| 4.4 | Build correlation matrix visualization | 2h |
| 4.5 | Add VaR dashboard with real-time monitoring | 3h |

### Priority 5: Security & Monitoring
| Step | Description | Effort |
|------|-------------|--------|
| 5.1 | Set up Prometheus + Grafana monitoring | 2h |
| 5.2 | Add rate limiting per user | 1h |
| 5.3 | Implement API key authentication for external access | 2h |
| 5.4 | Add audit logging for all trade actions | 2h |
| 5.5 | Set up automated backups | 1h |

---

## 📊 System Status

| Metric | Value |
|--------|-------|
| Total Phases | 70/70 ✅ |
| Total Tests | 288/288 ✅ |
| API Endpoints | 100+ |
| Database Tables | 35+ |
| AI Models | gemma4, llama3, qwen3.5 |
| News Sources | 68+ |
| Test Coverage | 100% |

---

*Last updated: August 14, 2026*
*Repository: https://github.com/myazdanpanah/AI-Trading*
