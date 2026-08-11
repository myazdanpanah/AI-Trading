# Changelog

All notable changes to the Crypto AI Signal Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased] - 2026-08-11

### Added
- **TradingView Replica UI**
  - TradingView-style dark theme (TradingView colors: #131722, #1e1e2e, #2a2a3e)
  - Real-time candlestick chart with OHLCV data
  - Technical indicators overlay (SMA, EMA, Bollinger Bands)
  - Drawing tools toolbar (Trend Line, Horizontal, Fibonacci, Rectangle, Text)
  - Timeframe selector (1m to 1W)
  - Volume bars with color-coded candles

- **Order Book**
  - Real-time bid/ask display with depth visualization
  - Color-coded volume bars (red for asks, green for bids)
  - Spread calculation and display
  - Auto-updates every 1.5 seconds

- **Watchlist**
  - 10 cryptocurrency pairs with live prices
  - Sortable by change or volume
  - Favorite/star functionality
  - Compact, non-overlapping layout

- **Backtester**
  - Strategy selection (SMA Crossover, RSI, Bollinger, MACD)
  - Configurable parameters (capital, date range)
  - Equity curve visualization
  - Trade history with P&L
  - Performance metrics (Return, Win Rate, Sharpe, Drawdown)

- **Portfolio Tracker**
  - Real-time position tracking
  - P&L calculation with percentage
  - Pie chart allocation visualization
  - Total balance and buying power display

- **Ollama Integration**
  - Display installed local models
  - Pull new models (Gemma2, Llama3, Mistral, etc.)
  - Model selection and activation
  - Connection status indicator

- **API Settings Page**
  - AI provider configuration (Ollama, OpenAI, Anthropic)
  - Exchange API key management (Binance, Bybit, OKX)
  - General settings (trading pair, risk level, auto-trading)

- **Backend Fixes**
  - Fixed missing drf-spectacular dependency
  - Added missing NotificationChannel, NotificationRule, Notification models
  - Fixed analytics event imports (global_events)
  - Renamed celery.py to celery_app.py to avoid package conflict
  - Fixed sentiment/technical_analysis app name mismatches
  - Resolved duplicate db_table names across apps
  - Created all missing migrations
  - Fixed healthcheck URL in docker-compose.yml

- **Infrastructure**
  - Vite proxy configured for backend API
  - Frontend binding to 0.0.0.0 for Docker accessibility
  - Mock data fallback for offline testing

### Fixed
- LoginForm endpoint corrected to /api/auth/login/
- Auth token header now included in all API requests
- Backend health check now uses /health/ endpoint
- All Django migrations successfully applied

---

## Development Log

### 2026-08-11
- Rebuilt Docker images with all fixes
- Enhanced frontend with charts and real-time updates
- Added demo mode for testing without backend
- Verified full stack connectivity
- Updated documentation

### 2026-08-03
- Implemented Phase 18: Advanced Analytics & Reporting
- Created webhook service with multi-provider support
- Added async Celery tasks for webhook delivery
- Updated documentation with Phase 18 completion
