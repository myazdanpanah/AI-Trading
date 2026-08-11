# Feedback Loop API Documentation

## Overview

The Feedback Loop API provides AI memory, similarity search, and self-improvement capabilities for the crypto signal platform.

## Endpoints

### Market Memories

#### POST `/api/feedback/market-memories/search_similar/`
Find similar historical market situations.

**Request Body:**
```json
{
  "symbol": "BTC-USDT",
  "timeframe": "1h",
  "price": 50000,
  "price_change_1h": 2.5,
  "price_change_24h": 5.0,
  "volume_ratio": 1.5,
  "rsi": 65,
  "macd_signal": 0.3,
  "ema_trend": 0.5,
  "adx": 30,
  "fear_greed_index": 60,
  "social_sentiment": 0.3,
  "atr_percent": 3.0,
  "limit": 5,
  "min_similarity": 0.7
}
```

**Response:**
```json
{
  "similar_memories": [
    {
      "memory_id": "uuid",
      "symbol": "BTC-USDT",
      "timeframe": "1h",
      "market_condition": "trending",
      "similarity_score": 0.85,
      "price": 48500,
      "created_at": "2024-01-15T10:30:00Z",
      "historical_outcome": {
        "total_signals": 5,
        "correct_signals": 4,
        "win_rate": 80.0,
        "avg_return_percent": 2.5
      }
    }
  ],
  "count": 1,
  "query": {
    "symbol": "BTC-USDT",
    "timeframe": "1h"
  }
}
```

#### POST `/api/feedback/market-memories/record_state/`
Record current market state for future similarity search.

**Request Body:**
```json
{
  "symbol": "BTC-USDT",
  "timeframe": "1h",
  "price": 50000,
  "volume": 1000000,
  "technical_indicators": {"rsi": 65, "macd": 0.3},
  "sentiment_data": {"fear_greed": 60},
  "market_condition": "trending",
  "dominant_factor": "technical"
}
```

---

### Signal Memories

#### POST `/api/feedback/signal-memories/record_outcome/`
Record signal outcome for learning.

**Request Body:**
```json
{
  "signal_id": "uuid",
  "exit_price": 52000,
  "profit_loss_percent": 4.0,
  "holding_period_hours": 24,
  "market_condition": "trending"
}
```

#### GET `/api/feedback/signal-memories/prediction/`
Get prediction for a signal based on historical similarity.

**Query Parameters:**
- `symbol`: Trading pair
- `timeframe`: Candle timeframe
- `price`: Current price
- `signal_direction`: buy/sell/hold

---

### Performance Analysis

#### POST `/api/feedback/analysis/analyze/`
Run comprehensive performance analysis.

**Request Body:**
```json
{
  "lookback_days": 30,
  "symbol": "BTC-USDT",
  "min_signals": 10
}
```

#### GET `/api/feedback/analysis/recommendations/`
Get improvement recommendations.

#### GET `/api/feedback/analysis/insights/`
Get all learning insights.

---

### Feedback Cycles

#### POST `/api/feedback/cycles/run_cycle/`
Execute a feedback cycle.

**Request Body:**
```json
{
  "cycle_type": "daily",
  "lookback_days": 1,
  "symbol": "BTC-USDT"
}
```

#### GET `/api/feedback/cycles/history/`
Get feedback cycle history.

---

## Celery Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `feedback.run_daily_cycle` | Daily 1:00 AM | Analyze yesterday's signals |
| `feedback.run_weekly_cycle` | Sunday 2:00 AM | Comprehensive weekly analysis |
| `feedback.cleanup_old_memories` | Monthly 1st, 3:00 AM | Remove memories older than 90 days |
| `feedback.record_signal_outcome` | On-demand | Record a signal outcome |
| `feedback.generate_market_memory` | On-demand | Generate market memory embedding |
