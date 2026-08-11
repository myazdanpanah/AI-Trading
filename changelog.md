# Changelog

All notable changes to the Crypto AI Signal Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased] - 2026-08-11

### Added
- **Phase 24: Mobile App API**
  - DeviceToken model for push notification management
  - MobileAlert model for price and signal alerts
  - MobileWidget model for configurable home screen widgets
  - REST API endpoints with full CRUD operations
  - Device registration and deactivation endpoints

- **Phase 25: Advanced AI Strategies**
  - Enhanced multi-agent orchestration patterns
  - Agent definitions with roles and capabilities
  - Workflow engine for step-by-step execution
  - Prompt versioning for AI management

- **Phase 26: Multi-exchange Arbitrage**
  - ArbitrageOpportunity model for tracking opportunities
  - ArbitrageDetector service for cross-exchange detection
  - Exchange fee calculation and profit estimation
  - Risk scoring for arbitrage opportunities
  - ArbitrageConfig for customizable settings
  - ArbitrageExecution for tracking execution history

- **Phase 27: Social Trading**
  - Trader profile model with performance metrics
  - Follow/following relationship system
  - CopyTrade model for automatic trade copying
  - TraderSignal model for sharing signals
  - SocialComment model for discussions
  - CopyTrader service for copy trading logic
  - Trader leaderboard endpoint
  - Like and comment functionality

- **Phase 28: Advanced Portfolio Management**
  - Portfolio model with multi-portfolio support
  - PortfolioAllocation model for target allocations
  - PortfolioRebalancer service for automated rebalancing
  - TaxLot model for FIFO/LIFO/HIFO cost basis tracking
  - TaxOptimizer service for tax-loss harvesting
  - TaxReport model for generating tax reports
  - RebalanceHistory for tracking rebalance events
  - Performance metrics (Sharpe, drawdown, volatility)

- **Infrastructure**
  - Added new Django apps: mobile, arbitrage, social, portfolio
  - Added to INSTALLED_APPS in settings
  - Added URL routing for new endpoints
  - Added admin configurations for all new models
  - Created serializers for all new models

### Changed
- Updated progress.md with all completed phases
- Updated changelog.md with detailed changes

---

## Development Log

### 2026-08-11
- Implemented Phase 23: WebSocket real-time streaming
- Implemented Phase 24: Mobile App API
- Implemented Phase 25: Advanced AI Strategies
- Implemented Phase 26: Multi-exchange Arbitrage
- Implemented Phase 27: Social Trading
- Implemented Phase 28: Advanced Portfolio Management
- Production hardening with Dockerfiles and Grafana
- Comprehensive README.md documentation

### 2026-08-03
- Implemented Phase 18: Advanced Analytics & Reporting
- Created webhook service with multi-provider support
- Added async Celery tasks for webhook delivery
- Updated documentation with Phase 18 completion
