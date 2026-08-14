# ══════════════════════════════════════════════════════════════════════
# AI-Trading Platform — Complete API Reference
# ══════════════════════════════════════════════════════════════════════

**Base URL:** `http://localhost:8000/api`

**Interactive Docs:** `http://localhost:8000/api/docs/` (Swagger UI)

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Users & Profile](#2-users--profile)
3. [Market Data](#3-market-data)
4. [Signals](#4-signals)
5. [AI Engine](#5-ai-engine)
6. [Trading Skills](#6-trading-skills)
7. [Technical Analysis](#7-technical-analysis)
8. [Sentiment](#8-sentiment)
9. [News](#9-news)
10. [Portfolio](#10-portfolio)
11. [Journal](#11-journal)
12. [Feedback & Learning](#12-feedback--learning)
13. [Forecast](#13-forecast)
14. [Social](#14-social)
15. [Arbitrage](#15-arbitrage)
16. [Notifications](#16-notifications)
17. [Health & Monitoring](#17-health--monitoring)

---

## 1. Authentication

All authenticated endpoints require a JWT token in the `Authorization` header:

```
Authorization: Bearer <your-access-token>
```

### POST `/api/auth/login/`

Login and receive JWT tokens.

**Request:**
```json
{
  "username": "myazdanpanah",
  "password": "123456"
}
```

**Response (200):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "myazdanpanah",
    "email": "user@example.com"
  }
}
```

### POST `/api/auth/refresh/`

Refresh an expired access token.

**Request:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs..."
}
```

### POST `/api/auth/register/`

Register a new user account.

**Request:**
```json
{
  "username": "newuser",
  "email": "new@example.com",
  "password": "securepass123",
  "password_confirm": "securepass123"
}
```

### POST `/api/auth/logout/`

Blacklist the refresh token.

**Request:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

### POST `/api/auth/change-password/`

Change the authenticated user's password.

**Request:**
```json
{
  "old_password": "currentpass",
  "new_password": "newsecurepass"
}
```

### GET `/api/auth/profile/`

Get the authenticated user's profile.

### PUT `/api/auth/profile/update/`

Update the authenticated user's profile.

**Request:**
```json
{
  "email": "updated@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

---

## 2. Users & Profile

### GET `/api/users/profile/`

Get the user's profile.

### PUT `/api/users/profile/`

Update the user's profile.

### GET `/api/users/watchlist/`

Get the user's watchlist.

### POST `/api/users/watchlist/`

Add a symbol to the watchlist.

**Request:**
```json
{
  "symbol": "BTCUSDT",
  "name": "Bitcoin"
}
```

### DELETE `/api/users/watchlist/{id}/`

Remove a symbol from the watchlist.

---

## 3. Market Data

### GET `/api/market/status/`

Get data source status (Binance, CoinGecko, etc.).

**Response (200):**
```json
{
  "primary_source": "binance",
  "fallback_source": "coingecko",
  "last_update": "2026-08-14T12:00:00Z",
  "sources_available": {
    "binance": true,
    "coingecko": true
  }
}
```

### GET `/api/market/ticker/?symbol=BTC`

Quick ticker price for a symbol.

**Response (200):**
```json
{
  "symbol": "BTCUSDT",
  "price": 113500.00,
  "change_24h": 2.5,
  "volume_24h": 28500000000,
  "high_24h": 115000.00,
  "low_24h": 111000.00
}
```

### GET `/api/market/candles/live/?symbol=BTCUSDT&interval=1h&limit=100`

Fetch live candle data.

**Response (200):**
```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "candles": [
    {
      "time": 1692000000,
      "open": 113000.00,
      "high": 114000.00,
      "low": 112500.00,
      "close": 113500.00,
      "volume": 1250.5
    }
  ]
}
```

### GET `/api/market/candles/`

List stored candles (paginated).

### GET `/api/market/orderbook/`

List order book snapshots.

### GET `/api/market/derivatives/`

List derivatives data (funding, OI, liquidations).

---

## 4. Signals

### Core Signal Operations

#### GET `/api/signals/signals/`

List all signals (paginated, filterable).

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `symbol` | string | Filter by symbol (e.g., `BTCUSDT`) |
| `direction` | string | `buy`, `sell`, `hold` |
| `timeframe` | string | `1m`, `5m`, `15m`, `1h`, `4h`, `1d` |
| `is_active` | boolean | Filter active signals |
| `ordering` | string | `-created_at`, `confidence` |

**Response (200):**
```json
{
  "count": 49,
  "results": [
    {
      "id": "3bfb9eb0-3c7b-4cd8-bc08-da7c8d4011d9",
      "symbol": "BTCUSDT",
      "direction": "buy",
      "confidence": 75,
      "risk_score": 35,
      "entry_price": 113500.00,
      "stop_loss": 110000.00,
      "take_profit": [118000.00, 122000.00],
      "timeframe": "1h",
      "technical_score": 72,
      "sentiment_score": 65,
      "news_score": 58,
      "macro_score": 55,
      "composite_score": 68.5,
      "is_active": true,
      "created_at": "2026-08-14T12:00:00Z"
    }
  ]
}
```

#### POST `/api/signals/signals/generate/`

Generate a new trading signal using the full AI pipeline.

**Request:**
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "current_price": 113500
}
```

**Response (201):**
```json
{
  "signal": {
    "id": "3bfb9eb0-3c7b-4cd8-bc08-da7c8d4011d9",
    "symbol": "BTCUSDT",
    "direction": "hold",
    "confidence": 85,
    "entry_price": 113500.00,
    "stop_loss": 110000.00,
    "take_profit": [118000.00],
    "composite_score": 50.0
  },
  "details": {
    "direction": "hold",
    "confidence": 85,
    "quant_composite_score": 50.0,
    "factor_scores": {
      "technical": 50.0,
      "sentiment": 50.0,
      "news": 50.0,
      "macro": 50.0,
      "derivatives": 50.0,
      "market_structure": 50.0,
      "order_book": 50.0,
      "portfolio_context": 50.0
    },
    "regime": "sideways",
    "agent_ensemble": {
      "verdict": "modify",
      "adjusted_confidence": 70,
      "agents_succeeded": 5,
      "total_latency_ms": 95531,
      "model": "gemma4:latest",
      "agent_analyses": {
        "technical_analyst": { "direction": "neutral", "confidence": 20 },
        "news_analyst": { "sentiment": "neutral", "impact": "low" },
        "market_analyst": { "regime_assessment": "range", "risk_level": "medium" },
        "risk_analyst": { "risk_level": "medium", "position_sizing": "moderate" },
        "final_validator": { "verdict": "modify", "adjusted_confidence": 70 }
      }
    }
  }
}
```

#### GET `/api/signals/signals/{id}/`

Get a specific signal.

#### GET `/api/signals/signals/latest/?symbol=BTCUSDT`

Get latest active signals.

#### POST `/api/signals/signals/evaluate/`

Evaluate pending signals and record outcomes.

**Request:**
```json
{
  "min_age_hours": 4
}
```

**Response (200):**
```json
{
  "evaluated": 12,
  "wins": 7,
  "losses": 5,
  "accuracy": 58.33
}
```

### Lineage & Versioning

#### GET `/api/signals/signals/{id}/lineage/`

Get full data lineage for a signal (versions, snapshots, AI output).

**Response (200):**
```json
{
  "signal_id": "3bfb9eb0-3c7b-4cd8-bc08-da7c8d4011d9",
  "lineage": {
    "strategy_version": "2.0",
    "feature_version": "1.2",
    "ensemble_version": "1.0",
    "regime": "sideways",
    "regime_confidence": 100.0,
    "factor_scores": { "technical": 50.0, "sentiment": 50.0 },
    "weights_snapshot": { "technical": 0.3738, "sentiment": 0.0935 },
    "market_snapshot": { "current_price": 113500.00, "candles_used": 50 },
    "ensemble_output": { "verdict": "modify", "model": "gemma4:latest" }
  },
  "explanation": "Signal: BTCUSDT HOLD with 65% confidence\nTimeframe: 1h\n..."
}
```

#### GET `/api/signals/signals/versions/`

Get current system versions.

**Response (200):**
```json
{
  "strategy": "2.0",
  "features": "1.2",
  "regime": "1.0",
  "risk": "1.0",
  "calibration": "1.0",
  "ensemble": "1.0",
  "backtester": "1.0",
  "walk_forward": "1.0"
}
```

### Calibration

#### GET `/api/signals/signals/calibration/?symbol=BTC&limit=500`

Get calibration analysis (Brier Score, ECE, reliability curve).

**Response (200):**
```json
{
  "total_signals": 49,
  "brier_score": 0.2892,
  "ece": 0.2355,
  "mce": 0.2980,
  "calibration_quality": "uncalibrated",
  "diagnosis": "OVERCONFIDENT",
  "reliability_curve": [
    { "range": "50%-60%", "predicted": 53.1, "actual": 41.2, "count": 17 },
    { "range": "60%-70%", "predicted": 64.1, "actual": 34.4, "count": 32 }
  ],
  "by_symbol": {
    "BTC": { "accuracy": 33.3, "brier": 0.2905, "count": 12 },
    "ETH": { "accuracy": 44.4, "brier": 0.2524, "count": 9 }
  }
}
```

#### POST `/api/signals/signals/adjust_confidence/`

Adjust a confidence score using the calibration curve.

**Request:**
```json
{
  "confidence": 80,
  "symbol": "BTC"
}
```

**Response (200):**
```json
{
  "raw_confidence": 80,
  "adjusted_confidence": 68.5,
  "calibration_quality": "fair",
  "ece": 0.2355,
  "brier_score": 0.2892
}
```

### Paper Trading

#### GET `/api/signals/signals/paper_status/`

Get paper trading account status.

**Response (200):**
```json
{
  "initial_capital": 10000.00,
  "cash_balance": 8500.00,
  "equity": 9200.00,
  "used_margin": 1500.00,
  "open_positions_count": 1,
  "total_trades": 5,
  "winning_trades": 3,
  "losing_trades": 2,
  "win_rate": 60.0,
  "total_return_pct": -8.0,
  "max_drawdown": 12.5,
  "open_positions": [
    {
      "id": "PAPER-000001",
      "symbol": "BTCUSDT",
      "side": "long",
      "quantity": 0.03,
      "entry_price": 50000.00,
      "current_price": 52000.00,
      "unrealized_pnl": 60.00,
      "unrealized_pnl_pct": 4.0
    }
  ],
  "recent_trades": [...]
}
```

#### POST `/api/signals/signals/paper_open/`

Open a paper trading position.

**Request:**
```json
{
  "symbol": "BTCUSDT",
  "side": "long",
  "entry_price": 50000,
  "stop_loss": 49000,
  "take_profit": 52000,
  "signal_confidence": 75
}
```

**Response (201):**
```json
{
  "success": true,
  "position": {
    "id": "PAPER-000001",
    "symbol": "BTCUSDT",
    "side": "long",
    "quantity": 0.04,
    "entry_price": 50025.00,
    "fees_paid": 2.00,
    "slippage_cost": 1.00
  }
}
```

#### POST `/api/signals/signals/paper_close/`

Close a paper trading position.

**Request:**
```json
{
  "position_id": "PAPER-000001",
  "exit_price": 52000,
  "reason": "take_profit"
}
```

**Response (200):**
```json
{
  "success": true,
  "trade": {
    "id": "TRADE-000001",
    "pnl": 78.50,
    "pnl_pct": 3.14,
    "holding_period_seconds": 3600
  }
}
```

#### POST `/api/signals/signals/paper_update_prices/`

Update prices for all paper positions.

**Request:**
```json
{
  "prices": { "BTCUSDT": 51000, "ETHUSDT": 3200 }
}
```

#### GET `/api/signals/signals/paper_performance/`

Get paper trading performance metrics.

#### POST `/api/signals/signals/paper_reset/`

Reset paper trading account.

**Request:**
```json
{ "initial_capital": 10000 }
```

### Shadow Trading

#### GET `/api/signals/signals/shadow_status/`

Get shadow trading account status.

#### POST `/api/signals/signals/shadow_signal/`

Record a shadow trade.

**Request:**
```json
{
  "symbol": "BTCUSDT",
  "side": "long",
  "signal_confidence": 75,
  "expected_entry": 50000,
  "expected_exit": 52000,
  "current_price": 50050
}
```

#### GET `/api/signals/signals/shadow_quality/`

Get shadow trading execution quality report.

### Live Execution

#### GET `/api/signals/signals/live_status/`

Get live execution account status.

#### POST `/api/signals/signals/live_order/`

Place a live order (requires risk approval).

**Request:**
```json
{
  "symbol": "BTCUSDT",
  "side": "buy",
  "type": "market",
  "quantity": 0.001,
  "risk_approved": true
}
```

#### POST `/api/signals/signals/live_cancel/`

Cancel a live order.

**Request:**
```json
{ "order_id": "LIVE-000001" }
```

#### GET `/api/signals/signals/live_open_orders/`

Get all open live orders.

### Factor Weights

#### GET `/api/signals/factor-weights/`

List all factor weights.

#### POST `/api/signals/factor-weights/adjust/`

Auto-adjust weights based on signal performance.

#### POST `/api/signals/factor-weights/reset/`

Reset weights to defaults.

#### GET `/api/signals/factor-weights/current/`

Get current weights with performance data.

### Risk Engine

#### GET `/api/signals/risk-engine/`

List risk engine configurations.

### Alerts

#### GET `/api/signals/alerts/`

List alert rules.

#### POST `/api/signals/alerts/`

Create an alert rule.

**Request:**
```json
{
  "symbol": "BTCUSDT",
  "condition": "price_above",
  "threshold": 120000,
  "notification": true
}
```

---

## 5. AI Engine

### Providers & Models

#### GET `/api/ai/providers/`

List configured AI providers.

#### GET `/api/ai/models/`

List available AI models.

**Response (200):**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "name": "gemma4:latest",
      "provider": "ollama",
      "status": "available",
      "capabilities": ["chat", "analysis"]
    }
  ]
}
```

### Agent Ensemble

#### GET `/api/ai/ensemble/`

Get agent ensemble status and configuration.

#### POST `/api/ai/ensemble/run/`

Run the agent ensemble on a signal context.

**Request:**
```json
{
  "symbol": "BTCUSDT",
  "quant_composite_score": 68,
  "direction": "buy",
  "confidence": 75,
  "regime": "bull_trend",
  "technical_score": 72,
  "sentiment_score": 65
}
```

**Response (200):**
```json
{
  "verdict": "validate",
  "adjusted_confidence": 78,
  "agents_succeeded": 5,
  "total_latency_ms": 95531,
  "agent_analyses": {
    "technical_analyst": { "direction": "bullish", "confidence": 75 },
    "news_analyst": { "sentiment": "positive", "impact": "medium" },
    "market_analyst": { "regime_assessment": "uptrend", "risk_level": "low" },
    "risk_analyst": { "risk_level": "low", "position_sizing": "aggressive" },
    "final_validator": { "verdict": "validate", "adjusted_confidence": 78 }
  }
}
```

### Chat

#### POST `/api/skills/chat/`

Chat with the AI about a specific symbol or general market questions.

**Request:**
```json
{
  "message": "Should I buy BTC now?",
  "symbol": "BTCUSDT",
  "language": "en"
}
```

**Response (200):**
```json
{
  "response": "Based on current technical analysis, BTC is showing...",
  "model": "gemma4:latest",
  "confidence": 72,
  "recommendation": "hold",
  "latency_ms": 14000
}
```

### Workflows

#### GET `/api/ai/workflows/`

List AI workflows.

#### GET `/api/ai/agents/`

List agent definitions.

#### GET `/api/ai/agent-executions/`

List agent execution history.

---

## 6. Trading Skills

#### GET `/api/skills/skills/`

List all available trading skills.

#### POST `/api/skills/technical-analysis/`

Run technical analysis on a symbol.

**Request:**
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "indicators": ["RSI", "MACD", "Bollinger", "VWAP", "Ichimoku"]
}
```

#### POST `/api/skills/candlestick-analysis/`

Analyze candlestick patterns.

#### POST `/api/skills/regime-analysis/`

Analyze market regime.

#### POST `/api/skills/position-sizer/`

Calculate optimal position size.

**Request:**
```json
{
  "symbol": "BTCUSDT",
  "entry_price": 50000,
  "stop_loss": 49000,
  "risk_percent": 2,
  "portfolio_value": 10000
}
```

#### POST `/api/skills/full-analysis/`

Run complete analysis combining all skills.

**Response (200):**
```json
{
  "symbol": "BTCUSDT",
  "technical": { "rsi": 62, "macd": "bullish", "trend": "uptrend" },
  "regime": { "type": "bull_trend", "confidence": 0.85 },
  "candlestick": { "pattern": "engulfing", "bias": "bullish" },
  "position_size": { "quantity": 0.04, "risk_amount": 200 },
  "recommendation": "BUY",
  "confidence": 75
}
```

### Signal Reviews

#### GET `/api/skills/signal-reviews/`

List signal reviews (AI feedback on past signals).

#### GET `/api/skills/regime-history/`

List regime analysis history.

---

## 7. Technical Analysis

### Indicators

#### GET `/api/technical-analysis/indicators/`

List calculated technical indicators.

### Patterns

#### GET `/api/technical-analysis/patterns/`

List detected candlestick patterns.

### Support & Resistance

#### GET `/api/technical-analysis/support-resistance/`

List support/resistance levels.

### Trends

#### GET `/api/technical-analysis/trends/`

List trend analyses.

### Smart Money

#### GET `/api/technical-analysis/smart-money/`

List smart money events.

---

## 8. Sentiment

### Fear & Greed Index

#### GET `/api/sentiment/fear-greed/`

Get Fear & Greed Index data.

**Response (200):**
```json
{
  "value": 65,
  "classification": "Greed",
  "timestamp": "2026-08-14T12:00:00Z"
}
```

### Social Sentiment

#### GET `/api/sentiment/social/`

Get social sentiment data.

### Whale Activity

#### GET `/api/sentiment/whale/`

List whale activity events.

### Influencer Sentiment

#### GET `/api/sentiment/influencer/`

List influencer sentiment data.

### Aggregated Sentiment

#### GET `/api/sentiment/aggregated/`

Get aggregated market sentiment.

**Response (200):**
```json
{
  "overall_sentiment": 65,
  "fear_greed": 65,
  "social": 60,
  "news": 55,
  "whale": 70,
  "classification": "Greed"
}
```

### Sentiment Alerts

#### GET `/api/sentiment/alerts/`

List sentiment alerts.

---

## 9. News

### Sources

#### GET `/api/news/sources/`

List configured news sources.

**Response (200):**
```json
{
  "count": 15,
  "results": [
    {
      "id": 1,
      "name": "CoinDesk",
      "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
      "category": "crypto_news",
      "reliability": 85,
      "is_active": true
    }
  ]
}
```

#### POST `/api/news/sources/`

Add a new news source.

**Request:**
```json
{
  "name": "Reuters Crypto",
  "url": "https://www.reuters.com/arc/outboundfeeds/rss/",
  "category": "macro_news",
  "reliability": 90
}
```

### Articles

#### GET `/api/news/articles/`

List news articles (paginated, filterable by symbol, sentiment).

#### GET `/api/news/entities/`

List news entities (mentioned coins, people, events).

---

## 10. Portfolio

### Portfolios

#### GET `/api/portfolio/portfolios/`

List portfolios.

#### POST `/api/portfolio/portfolios/`

Create a portfolio.

**Request:**
```json
{
  "name": "Main Portfolio",
  "initial_capital": 10000
}
```

### Allocations

#### GET `/api/portfolio/allocations/`

List portfolio allocations.

#### POST `/api/portfolio/allocations/`

Create an allocation.

### Tax

#### GET `/api/portfolio/tax-lots/`

List tax lots.

#### GET `/api/portfolio/tax-reports/`

Generate tax reports.

### Rebalance

#### GET `/api/portfolio/rebalance-history/`

List rebalance history.

---

## 11. Journal

### Entries

#### GET `/api/journal/entries/`

List journal entries (paginated, filterable).

**Response (200):**
```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "symbol": "BTCUSDT",
      "title": "BTC consolidation analysis",
      "content": "BTC is showing consolidation patterns...",
      "mood": "neutral",
      "tags": ["technical", "consolidation"],
      "created_at": "2026-08-14T12:00:00Z"
    }
  ]
}
```

#### POST `/api/journal/entries/`

Create a journal entry.

**Request:**
```json
{
  "symbol": "BTCUSDT",
  "title": "BTC breakout analysis",
  "content": "BTC has broken above the $115K resistance...",
  "mood": "bullish",
  "tags": ["breakout", "technical"]
}
```

#### GET `/api/journal/insights/`

List AI-generated journal insights.

### Market Context

#### GET `/api/journal/context/`

Get current market context for journaling.

**Response (200):**
```json
{
  "btc_price": 113500.00,
  "eth_price": 4200.00,
  "fear_greed": 65,
  "regime": "sideways",
  "active_signals": 3,
  "recent_news": ["BTC consolidates near $113K...", "..."]
}
```

### News Sources

#### GET `/api/journal/sources/`

List news sources configured in the journal.

---

## 12. Feedback & Learning

### Market Memories

#### GET `/api/feedback/market-memories/`

List market memories (what the system learned).

### Signal Memories

#### GET `/api/feedback/signal-memories/`

List signal memories (outcome data for calibration).

### Pattern Memories

#### GET `/api/feedback/pattern-memories/`

List pattern memories.

### Learning Insights

#### GET `/api/feedback/insights/`

List AI-generated learning insights.

### Feedback Cycles

#### GET `/api/feedback/cycles/`

List feedback cycle runs.

### Performance Analysis

#### GET `/api/feedback/analysis/`

Get comprehensive performance analysis.

---

## 13. Forecast

### Forecasts

#### GET `/api/forecast/forecasts/`

List price forecasts.

### Cycles

#### GET `/api/forecast/cycles/`

List forecast cycles.

### Forecast Operations

#### POST `/api/forecast/run/`

Run a price forecast.

**Request:**
```json
{
  "symbol": "BTCUSDT",
  "horizon_hours": 24,
  "method": "ensemble"
}
```

#### POST `/api/forecast/verify/`

Verify past forecasts against actual prices.

#### POST `/api/forecast/learn/`

Run a learning cycle to improve forecast accuracy.

#### GET `/api/forecast/accuracy/`

Get forecast accuracy statistics.

**Response (200):**
```json
{
  "total_forecasts": 150,
  "accuracy_1h": 62.5,
  "accuracy_4h": 58.3,
  "accuracy_24h": 52.1,
  "avg_error_pct": 3.2,
  "best_symbol": "BTCUSDT",
  "worst_symbol": "DOGEUSDT"
}
```

---

## 14. Social

### Traders

#### GET `/api/social/traders/`

List traders to follow.

### Follows

#### GET `/api/social/follows/`

List follow relationships.

### Copy Trading

#### GET `/api/social/copy-trades/`

List copy trade configurations.

### Trader Signals

#### GET `/api/social/signals/`

List signals from followed traders.

### Comments

#### GET `/api/social/comments/`

List social comments.

---

## 15. Arbitrage

### Opportunities

#### GET `/api/arbitrage/opportunities/`

List arbitrage opportunities.

### Configurations

#### GET `/api/arbitrage/configs/`

List arbitrage configurations.

### Executions

#### GET `/api/arbitrage/executions/`

List arbitrage execution history.

---

## 16. Notifications

#### GET `/api/notifications/`

List user notifications.

#### POST `/api/notifications/`

Create a notification.

---

## 17. Health & Monitoring

### Health Checks

#### GET `/health/`

Basic health check.

**Response (200):**
```json
{ "status": "ok" }
```

#### GET `/health/detailed/`

Detailed health check with component status.

**Response (200):**
```json
{
  "status": "healthy",
  "components": {
    "database": { "status": "ok", "latency_ms": 5 },
    "redis": { "status": "ok", "latency_ms": 1 },
    "ollama": { "status": "ok", "models": 5 }
  },
  "uptime_seconds": 86400
}
```

#### GET `/health/ready/`

Readiness probe (for Kubernetes).

#### GET `/health/live/`

Liveness probe (for Kubernetes).

#### GET `/metrics/`

Prometheus metrics endpoint.

### API Documentation

#### GET `/api/docs/`

Swagger UI (interactive API explorer).

#### GET `/api/redoc/`

ReDoc (alternative API documentation).

#### GET `/api/schema/`

OpenAPI schema (JSON).

---

## Rate Limits

| Tier | Limit | Window |
|------|-------|--------|
| Anonymous | 100 requests | per hour |
| Authenticated | 1,000 requests | per hour |
| Signal Generation | 10 requests | per minute |

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid input",
  "details": { "symbol": ["This field is required."] }
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 429 Too Many Requests
```json
{
  "detail": "Request was throttled. Expected available in 60 seconds."
}
```

### 500 Internal Server Error
```json
{
  "error": "An error occurred during signal generation: ..."
}
```

---

*Last updated: August 2026*
*Total endpoints: 100+*
