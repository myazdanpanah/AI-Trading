# Changelog

All notable changes to the Crypto AI Signal Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased] - 2026-08-11

### Added
- **WebSocket Real-time Streaming (Phase 23)**
  - PriceConsumer for real-time price updates (1s interval)
  - OrderBookConsumer for live order book streaming (1.5s interval)
  - SignalConsumer for trading signal notifications
  - WebSocket URL routing with authentication middleware
  - Frontend WebSocket utility with reconnection logic
  - OrderBook component now uses WebSocket for live data
  - Watchlist component streams real-time prices via WebSocket

- **Backend Improvements**
  - Created missing `base.py` exchange adapter (BaseExchange, OHLCV, OrderBook dataclasses)
  - Added CORS configuration to Django settings
  - Added rate limiting (100/hour anonymous, 1000/hour authenticated)
  - Added Django Channels for WebSocket support
  - Updated ASGI configuration for ProtocolTypeRouter
  - Added `channels` and `channels-redis` to requirements

- **Infrastructure**
  - Nginx WebSocket proxy configuration with upgrade headers
  - Nginx security headers (X-Frame-Options, X-Content-Type-Options, etc.)
  - Nginx rate limiting zone (10r/s with burst)
  - Vite WebSocket proxy for development

- **Documentation**
  - Comprehensive README.md with architecture diagram
  - Full API documentation with endpoints table
  - Project structure documentation
  - Quick start guide for Docker and local development

### Changed
- OrderBook component now connects to WebSocket instead of polling
- Watchlist component streams prices via WebSocket connections
- ASGI application now uses ProtocolTypeRouter for HTTP/WebSocket

### Fixed
- Missing `base.py` exchange adapter that `ccxt_base.py` was importing
- CORS not configured in Django settings
- No rate limiting on API endpoints

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
