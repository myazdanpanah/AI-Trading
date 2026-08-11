# CRYPTO AI SIGNAL PLATFORM

## Master Architecture & Development Specification

### Version 1.0

---

# Table of Contents

* 1. Vision
* 2. Goals
* 3. Design Principles
* 4. System Overview
* 5. Core Features
* 6. Technology Stack
* 7. High Level Architecture
* 8. Multi-Agent AI Architecture
* 9. LLM Provider Manager
* 10. Development Roadmap
* 11. Phase 1 – Foundation
* 12. Phase 2 – Market Data Engine
* 13. Phase 3 – News Intelligence Engine
* 14. Phase 4 – Global Event Engine
* 15. Phase 5 – AI Engine
* 16. Phase 5.5 – AI Orchestrator
* 17. Phase 6 – Technical Analysis Engine
* 18. Phase 7 – Sentiment Engine
* 19. Phase 8 – Signal Engine
* 20. Phase 9 – Learning Engine
* 21. Phase 10 – Feedback Loop
* 22. Database Design
* 23. API
* 24. Dashboard
* 25. Deployment
* 26. Future Roadmap

---

# 1. Vision

Create an enterprise-grade AI-powered cryptocurrency intelligence platform that continuously monitors cryptocurrency markets, collects and analyzes structured and unstructured information, understands technical indicators, interprets macroeconomic events, evaluates market sentiment, and generates transparent Buy/Sell/Hold trading signals.

The platform is designed as an intelligent decision support system rather than an automated trading bot.

Every generated signal must be:

* Explainable
* Traceable
* Measurable
* Continuously evaluated
* Continuously improved

The platform must support completely local execution using Ollama while also allowing seamless switching to commercial LLM providers.

---

# 2. Goals

Primary objectives

* Real-time crypto market monitoring
* Multi-exchange support
* News intelligence
* Global event understanding
* Technical analysis
* Smart Money analysis
* CPR analysis
* AI reasoning
* Historical learning
* Self-improving scoring engine
* Modular architecture
* Enterprise scalability

---

# 3. Design Principles

The entire project follows these principles.

## AI First

Artificial intelligence is a core architectural component rather than an optional feature.

---

## Explainability

Every prediction must include:

* Why
* How
* Supporting evidence
* Confidence
* Risk

---

## Local First

Default execution

* Ollama
* PostgreSQL
* Docker

Cloud AI is optional.

---

## Modular

Every engine can be replaced independently.

---

## Event Driven

Every market event becomes a stored event.

Nothing should be discarded.

---

## Self Learning

Every signal must become future training data.

---

## Observable

Every decision

Every prompt

Every model response

Every indicator

Every score

must be logged.

---

# 4. System Overview

The platform contains multiple independent engines.

```text
Market Engine

↓

News Engine

↓

Macro Engine

↓

Technical Engine

↓

Sentiment Engine

↓

On-chain Engine

↓

AI Analysis Engine

↓

Signal Engine

↓

Risk Engine

↓

Learning Engine

↓

Performance Engine

↓

Dashboard
```

---

# 5. Core Features

## Market

* Live Prices
* Candles
* Volume
* Funding
* Liquidation
* Open Interest
* Whale Orders

---

## Technical Analysis

* Indicators
* Smart Money
* CPR
* Pattern Detection
* Trend Detection
* Multi Timeframe

---

## Artificial Intelligence

* Local Models
* GPT
* Claude
* Hybrid Routing
* Prompt Templates
* AI Reasoning
* AI Explanation

---

## News Intelligence

* RSS
* Telegram
* Twitter
* Reddit
* Official Blogs
* Exchange Announcements
* SEC
* FOMC
* ETF News

---

## Global Events

* Interest Rate
* CPI
* PPI
* War
* Elections
* Regulations
* Exchange Hacks
* Blockchain Upgrades
* Stablecoin Events

---

## Dashboard

* Market Overview
* Heatmap
* Signal Feed
* Watchlists
* Performance
* AI Insights

---

# 6. Technology Stack

## Backend

Python 3.13

Django

Django REST Framework

Celery

Redis

PostgreSQL

TimescaleDB

pgvector

SQLAlchemy (optional analytical modules)

---

## Frontend

React

TypeScript

Vite

TailwindCSS

shadcn/ui

TradingView Chart

Apache ECharts

React Query

---

## AI

Ollama

Llama

Qwen

DeepSeek

Gemma

Mistral

OpenAI

Anthropic

OpenRouter

Sentence Transformers

FAISS

LangGraph

LiteLLM

---

## Infrastructure

Docker

Docker Compose

Ubuntu Server

Nginx

Prometheus

Grafana

MinIO

GitHub Actions

---

# 7. High-Level Architecture

```text
                    +----------------------+
                    |     Crypto APIs      |
                    +----------+-----------+
                               |
                               v
                     Market Data Engine
                               |
                               v
                      Historical Database
                               |
------------------------------------------------------------
                               |
                     News Intelligence Engine
                               |
                               v
                     Global Event Engine
                               |
                               v
                     Sentiment Engine
                               |
                               v
                Technical Analysis Engine
                               |
                               v
                  Multi-Agent AI Orchestrator
                               |
                               v
                      Signal Decision Engine
                               |
                               v
                         Risk Manager
                               |
                               v
                      Learning Engine
                               |
                               v
                       Dashboard / API
```

---

# 8. Multi-Agent AI Architecture

The platform must never rely on a single reasoning agent.

Independent specialist agents produce independent analyses.

## Agents

Market Agent

Responsible for

* Price
* Volume
* Trend
* Volatility

---

News Agent

Responsible for

* News classification
* Summaries
* Relevance
* Impact

---

Macro Agent

Responsible for

* Global economy
* Interest rates
* Inflation
* Political events

---

Technical Agent

Responsible for

* Indicators
* Trend
* Pattern
* Momentum

---

CPR Specialist Agent

Responsible for

* Daily CPR
* Weekly CPR
* Monthly CPR
* Virgin CPR
* Narrow CPR
* Wide CPR
* CPR Compression
* CPR Breakout
* Multi-Timeframe CPR Alignment

---

Smart Money Agent

Responsible for

* BOS
* CHOCH
* Liquidity
* Order Blocks
* Fair Value Gap
* Premium Discount
* Mitigation Blocks

---

Sentiment Agent

Responsible for

* Fear
* Greed
* Twitter
* Reddit
* Telegram
* Funding Rate

---

Risk Agent

Responsible for

* Position sizing
* Stop Loss
* Take Profit
* Maximum Drawdown

---

Learning Agent

Responsible for

* Historical accuracy
* Model evaluation
* Weight optimization

---

Supervisor Agent

Final responsibilities

* Collect all agent outputs
* Resolve conflicts
* Ask additional LLM reasoning if needed
* Produce final signal
* Generate confidence score
* Generate explanation
* Store reasoning

---

# 9. LLM Provider Manager

The AI layer must support multiple providers.

## Local Providers

* Ollama
* LocalAI
* LM Studio
* vLLM

---

## Cloud Providers

* OpenAI API
* Anthropic API
* OpenRouter

---

## Features

Automatic Switching

Manual Switching

Fallback Providers

Cost Awareness

Latency Awareness

Capability Routing

Streaming

Caching

Prompt Versioning

Conversation Memory

Structured Output

JSON Mode

Retry Logic

Health Checks

---

## Provider Routing Example

Technical Analysis

↓

Ollama DeepSeek

---

News Summary

↓

Qwen

---

Complex Reasoning

↓

Claude

---

Portfolio Analysis

↓

GPT-5.5

---

Offline Mode

↓

Ollama

---

Provider Failover

```text
OpenAI

↓

Anthropic

↓

OpenRouter

↓

Ollama

↓

LocalAI
```

---

## Prompt Library

Every AI prompt shall be versioned.

Prompt Metadata

* Version
* Author
* Date
* Model Compatibility
* Expected JSON Schema
* Evaluation Score

Prompt Categories

* Market Analysis
* Technical Analysis
* News Summary
* CPR Interpretation
* Smart Money
* Signal Validation
* Risk Analysis
* Portfolio Review
* Learning Feedback
* Supervisor Decision

---

# 10. Development Roadmap

Phase 1

Foundation

↓

Phase 2

Market Data

↓

Phase 3

News

↓

Phase 4

Macro Events

↓

Phase 5

AI Engine

↓

Phase 5.5

AI Orchestrator

↓

Phase 6

Technical Analysis

↓

Phase 7

Sentiment

↓

Phase 8

Signals

↓

Phase 9

Learning

↓

Phase 10

Feedback

↓

Phase 11

Dashboard

↓

Phase 12

Deployment

↓

Phase 13

Production

---

# PHASE 1

# Project Foundation

## Objective

Create the base infrastructure required for all future modules.

The foundation must support:

* Web application
* REST API
* Background processing
* AI integration
* Real-time data
* Scalable database
* Monitoring

---

# 1.1 Backend Architecture

Framework:

```
Django + Django REST Framework
```

Architecture Pattern:

```
apps/

├── users
├── authentication
├── market
├── news
├── analytics
├── ai_engine
├── signals
├── learning
├── notifications
├── reports
└── core
```

---

# 1.2 Backend Services

## API Service

Responsibilities:

* Authentication
* Data access
* Dashboard APIs
* Signal APIs
* AI communication

---

## Worker Service

Technology:

Celery

Responsibilities:

* Market data collection
* News crawling
* AI jobs
* Backtesting
* Learning jobs

---

## Scheduler

Technology:

Celery Beat

Responsibilities:

Scheduled Tasks:

```
Every minute:
Update candles

Every 5 minutes:
Technical analysis

Every 15 minutes:
AI market review

Every hour:
News analysis

Daily:
Model evaluation
```

---

# 1.3 Database Architecture

Primary Database:

PostgreSQL

Extension:

TimescaleDB

Purpose:

High performance time-series storage.

---

Vector Database:

pgvector

Purpose:

AI memory.

Stores:

* News embeddings
* Market situations
* Previous signals
* Historical patterns

---

# 1.4 Docker Architecture

Production containers:

```
crypto-platform

│

├── backend

├── frontend

├── postgres

├── redis

├── celery-worker

├── celery-beat

├── ollama

├── nginx

├── prometheus

└── grafana
```

---

# PHASE 2

# Market Data Engine

## Objective

Collect all required market information in real time.

---

# 2.1 Exchange Connectors

Supported:

* Binance
* Bybit
* OKX
* Coinbase
* KuCoin

Architecture:

```
Exchange Adapter Interface

          |

+---------+---------+

Binance Adapter

Bybit Adapter

OKX Adapter

```

Adding a new exchange must not change existing code.

---

# 2.2 Market Data Types

## Price Data

Store:

```
Symbol

Open

High

Low

Close

Volume

Timestamp

Timeframe
```

---

Supported Timeframes:

```
1m

5m

15m

30m

1h

4h

12h

1D

1W

1M
```

---

## Order Book

Store:

```
Bid Price

Ask Price

Depth

Liquidity Zones

Spread
```

---

## Derivatives Data

Collect:

```
Funding Rate

Open Interest

Liquidations

Long/Short Ratio

Basis
```

---

## Whale Tracking

Detect:

* Large transfers
* Exchange inflow
* Exchange outflow
* Wallet movements

---

# 2.3 Market Processing Pipeline

```
Exchange API

↓

Collector Service

↓

Normalizer

↓

Validation

↓

Database

↓

Indicator Engine

↓

AI Analysis
```

---

# PHASE 3

# News Intelligence Engine

## Objective

Convert raw information into market intelligence.

---

# 3.1 Data Sources

Sources:

```
RSS

Crypto News Websites

Twitter/X

Reddit

Telegram

Official Blogs

GitHub

Government Sources
```

---

# 3.2 News Pipeline

```
Crawler

↓

Cleaner

↓

Duplicate Detection

↓

Language Detection

↓

Translation

↓

Entity Recognition

↓

Impact Analysis

↓

AI Interpretation

↓

Storage
```

---

# 3.3 News Database

Table:

news_articles

Fields:

```
id

title

content

source

published_at

language

sentiment

entities

impact_score

ai_summary

embedding
```

---

# 3.4 AI News Analysis

Every article receives:

```
Market Impact:

0-100


Direction:

Bullish

Neutral

Bearish


Affected Assets:

BTC

ETH

SOL

etc.


Time Horizon:

Short

Medium

Long
```

---

# PHASE 4

# Global Event Engine

## Objective

Understand macroeconomic and geopolitical events.

---

# 4.1 Event Categories

## Economic

* CPI
* PPI
* GDP
* Interest Rates
* Employment Data
* FOMC

---

## Regulation

* SEC decisions
* ETF approvals
* Exchange regulations

---

## Geopolitical

* War
* Sanctions
* Elections
* Government decisions

---

## Blockchain

* Hard Fork
* Upgrade
* Token Unlock
* Hack
* Exploit

---

# 4.2 Event Impact Model

Each event receives:

```
Severity Score

Market Direction

Affected Coins

Expected Duration

Historical Similarity

AI Explanation
```

---

Example:

```
Bitcoin ETF Approval

Severity:
95/100

Direction:
Bullish

Expected Impact:
Medium Term

Confidence:
87%
```

---

# PHASE 5

# AI Engine

## Objective

Provide reasoning capabilities.

---

# 5.1 AI Architecture

```
Application

↓

AI Gateway

↓

Provider Manager

↓

Model Selection

↓

LLM

↓

Response Validation

↓

Memory Storage
```

---

# 5.2 AI Gateway Responsibilities

Functions:

* Authentication
* Prompt Management
* Provider Selection
* Token Management
* Logging
* Evaluation

---

# 5.3 Ollama Integration

Default Local Models:

```
Qwen

DeepSeek

Llama

Mistral

Gemma
```

---

Use Cases:

Local Analysis

Private Data Processing

Offline Operation

---

# 5.4 OpenAI Integration

Capabilities:

* Advanced reasoning
* Complex market analysis
* Strategy generation

---

# 5.5 Anthropic Integration

Capabilities:

* Long context analysis
* Research
* Multi-document reasoning

---

# PHASE 5.5

# AI Orchestrator

## Objective

Coordinate all AI agents.

---

# Agent Communication

Protocol:

```
Agent Message

{

agent_name,

analysis_type,

confidence,

evidence,

recommendation

}
```

---

# Supervisor Workflow

```
Receive Agent Results

↓

Check Conflicts

↓

Request Additional Analysis

↓

Calculate Consensus

↓

Generate Final Signal

↓

Store Decision
```

---

# PHASE 6

# Technical Analysis Engine

## Objective

Create professional market analysis.

---

# 6.1 Indicator Framework

Every indicator follows:

```
Indicator

↓

Calculation

↓

Score

↓

Confidence

↓

Signal Contribution
```

---

# 6.2 Standard Indicators

Implemented:

## Trend

* EMA
* SMA
* VWAP
* ADX

---

## Momentum

* RSI
* MACD
* Stochastic
* CCI

---

## Volatility

* ATR
* Bollinger Bands
* Keltner Channel

---

## Volume

* OBV
* MFI
* Volume Profile

---

# 6.3 Smart Money Concepts

Features:

```
Market Structure

BOS

CHOCH

Liquidity Sweep

Order Blocks

Fair Value Gap

Premium/Discount Zones

Institutional Zones
```

---

# 6.4 CPR Indicator by KGS

## Purpose

Central Pivot Range based market structure analysis.

---

# CPR Calculations

Supported:

```
Daily CPR

Weekly CPR

Monthly CPR
```

---

# CPR Features

## CPR Width

Detect:

```
Narrow CPR

Normal CPR

Wide CPR
```

---

## Virgin CPR

Detect untouched CPR zones.

---

## CPR Alignment

Analyze:

```
Daily CPR

+

Weekly CPR

+

Monthly CPR
```

---

## CPR Signals

Generate:

```
CPR Breakout Probability

CPR Reversal Probability

CPR Compression Score

CPR Trend Bias

CPR Support Score

CPR Resistance Score
```

---

# CPR Integration

CPR combines with:

```
EMA

VWAP

Volume

Smart Money

Price Action

AI Reasoning
```

---

# Example

```
BTCUSDT

CPR:
Narrow

Price:
Above CPR

Volume:
Increasing

EMA:
Bullish

AI Confidence:
86%

Signal:
BUY
```

---

# 6.5 Technical Score Engine

Final technical score:

```
Trend Score

+

Momentum Score

+

Volume Score

+

Smart Money Score

+

CPR Score

+

Pattern Score

=

Technical Confidence
```

---

# PHASE 7

# Sentiment Intelligence Engine

## Objective

Analyze collective market psychology using multiple data sources.

The purpose is detecting:

* Fear
* Greed
* Euphoria
* Panic
* Accumulation
* Distribution

---

# 7.1 Sentiment Data Sources

## Social Networks

Sources:

```text
Twitter/X

Reddit

Telegram

Discord

Crypto Communities
```

---

## Market Sentiment Data

Sources:

```text
Fear & Greed Index

Funding Rate

Long/Short Ratio

Open Interest

Liquidation Data

Options Data
```

---

## News Sentiment

Input:

News Intelligence Engine

Output:

```text
Bullish

Neutral

Bearish

Impact Score
```

---

# 7.2 Sentiment Processing Pipeline

```text
Raw Data

↓

Collector

↓

Text Processing

↓

AI Sentiment Analysis

↓

Emotion Detection

↓

Asset Mapping

↓

Sentiment Score

↓

Signal Engine
```

---

# 7.3 Sentiment Scoring Model

Every asset receives:

```text
Social Score

News Score

Market Score

Whale Score

Community Score

Final Sentiment Score
```

Example:

```text
BTC

Social:
82/100

News:
75/100

Whale:
90/100

Final:
83/100

Status:
Strong Bullish
```

---

# 7.4 AI Sentiment Analysis

The LLM must detect:

## Positive Signals

* ETF approval
* Institutional buying
* Exchange listing
* Network growth

---

## Negative Signals

* Hack
* Regulation
* Exchange withdrawal issues
* Whale selling

---

## Hidden Signals

AI must detect:

* Manipulation
* Fake hype
* Coordinated campaigns
* FOMO
* Panic selling

---

# PHASE 8

# Signal Decision Engine

## Objective

Generate explainable trading signals.

---

# 8.1 Signal Types

Supported:

```text
BUY

STRONG BUY

SELL

STRONG SELL

HOLD

WAIT

EXIT

TAKE PROFIT

STOP LOSS
```

---

# 8.2 Signal Architecture

```text
Market Data

+

Technical Analysis

+

CPR Analysis

+

Smart Money

+

News

+

Macro Events

+

Sentiment

+

AI Reasoning

↓

Signal Engine

↓

Final Decision
```

---

# 8.3 Signal Scoring Model

Final Score:

```text
Technical Weight

+

News Weight

+

Macro Weight

+

Sentiment Weight

+

AI Confidence Weight

+

Historical Similarity Weight

=

Final Signal Score
```

---

# Default Weights

Configurable:

```text
Technical Analysis:
30%

AI Reasoning:
20%

Sentiment:
15%

News:
15%

Macro:
10%

Historical:
10%
```

---

# 8.4 Signal Object

Every signal must contain:

```json
{
"symbol":"BTCUSDT",

"direction":"BUY",

"confidence":86,

"risk":35,

"entry":65000,

"stop_loss":62000,

"take_profit":[68000,70000],

"timeframe":"4H",

"technical_reason":

"EMA trend + CPR breakout",

"news_reason":

"Positive ETF inflow",

"ai_explanation":

"Multi-factor bullish confirmation"
}
```

---

# 8.5 Risk Engine

Before publishing a signal:

Risk checks:

```text
Volatility

Liquidity

Market Condition

News Risk

Drawdown

Correlation
```

---

# Risk Score

```text
0-30

Low Risk


31-70

Medium Risk


71-100

High Risk
```

---

# 8.6 Multi Timeframe Confirmation

Every signal should evaluate:

```text
1 Minute

5 Minute

15 Minute

1 Hour

4 Hour

Daily

Weekly
```

Example:

```text
15M:
Bullish

1H:
Bullish

4H:
Bullish

Daily:
Neutral

Final:
Moderate Buy
```

---

# PHASE 9

# Learning Engine

## Objective

Turn every prediction into intelligence.

---

# 9.1 Signal History

Store:

```text
Signal Time

Asset

Direction

Confidence

Entry Price

Exit Price

Result

Profit/Loss

Market Condition

AI Reasoning
```

---

# 9.2 Performance Metrics

Calculate:

## Accuracy

Percentage of correct predictions.

---

## Precision

How many buy signals succeeded.

---

## Recall

How many opportunities were detected.

---

## Risk Reward

Average reward compared to risk.

---

## Drawdown

Maximum losing period.

---

# 9.3 Learning Data Pipeline

```text
Signal Created

↓

Market Moves

↓

Result Collected

↓

Performance Calculated

↓

Mistake Detection

↓

Weight Adjustment

↓

Future Improvement
```

---

# 9.4 Adaptive Weight System

The system can modify:

```text
Indicator Importance

News Importance

Sentiment Weight

CPR Weight

AI Confidence Weight
```

Example:

Before:

```text
CPR Weight:
10%
```

After successful historical results:

```text
CPR Weight:
18%
```

---

# PHASE 10

# AI Feedback Loop

## Objective

Create a self-improving intelligence cycle.

---

# Complete Cycle

```text
Observe Market

↓

Analyze

↓

Generate Signal

↓

Wait

↓

Evaluate Result

↓

Find Errors

↓

Update Knowledge

↓

Improve Future Decisions
```

---

# 10.1 Memory System

Using:

```text
PostgreSQL

+

pgvector
```

Store:

* Market situations
* Previous signals
* Similar patterns
* Successful strategies
* Failed strategies

---

# 10.2 Similarity Search

Before generating a signal:

System searches:

```text
"Have we seen this market condition before?"
```

Example:

```text
Current:

BTC

CPR Narrow

EMA Bullish

Volume Increasing


Historical Match:

92% similarity


Previous Result:

+8.4%
```

---

# 10.3 AI Learning Agent

Responsibilities:

* Analyze mistakes
* Compare predictions
* Recommend improvements
* Update prompts
* Update weights

---

# PHASE 11

# Backtesting Engine

## Objective

Validate strategies before production.

---

# 11.1 Backtesting Features

Support:

```text
Historical Data

Custom Strategies

Indicator Combinations

AI Assisted Backtest

CPR Strategies

Smart Money Strategies
```

---

# 11.2 Backtest Report

Generate:

```text
Total Trades

Winning Trades

Losing Trades

Win Rate

Profit Factor

Maximum Drawdown

Sharpe Ratio

Best Market Condition

Worst Market Condition
```

---

# 11.3 AI Backtest Analyst

AI reviews:

```text
Why did strategy fail?

Which market condition hurts performance?

Which indicators improve results?

What parameters should change?
```

---

# PHASE 12

# Portfolio Intelligence Module

## Objective

Manage user assets and risk.

---

# Features

Portfolio Tracking

Asset Allocation

Risk Exposure

Profit/Loss

Performance

AI Suggestions

---

# Portfolio AI Analysis

Example:

```text
Your portfolio:

BTC 70%

ETH 20%

ALT 10%


Risk:

High concentration


Suggestion:

Reduce BTC exposure by 10%
```

---

# PHASE 13

# Notification System

## Supported Channels

```text
Telegram

Discord

Email

Web Push

Mobile Push
```

---

# Notification Rules

Examples:

```text
Confidence > 85%

Major News

Whale Movement

Signal Change

Risk Alert

Stop Loss Trigger
```

---

# PHASE 14

# Reporting Engine

## Reports

Daily Market Report

Weekly AI Report

Signal Performance Report

Portfolio Report

Learning Report

---

# AI Generated Reports

Every report includes:

```text
Market Summary

Important Events

Technical Overview

Best Opportunities

Major Risks

AI Outlook
```

---

# PHASE 15

# Database Architecture

## Objective

Design a scalable database capable of storing:

* Real-time market data
* AI analysis
* Signals
* Learning history
* User data
* Model performance

Database:

```text
PostgreSQL + TimescaleDB + pgvector
```

---

# 15.1 Database Design Principles

Requirements:

* Time-series optimization
* Fast historical queries
* AI memory support
* Data versioning
* Auditability
* High availability

---

# 15.2 Core Database Schema

---

# Users Module

## users

```sql
id

username

email

password_hash

role

created_at

updated_at
```

---

## user_preferences

```sql
id

user_id

favorite_symbols

risk_level

notification_settings

preferred_ai_provider
```

---

# Market Module

## exchanges

```sql
id

name

api_status

created_at
```

---

## trading_pairs

```sql
id

exchange_id

symbol

base_asset

quote_asset
```

---

## candles

TimescaleDB hypertable

```sql
id

symbol

timeframe

open

high

low

close

volume

timestamp
```

---

## order_books

```sql
id

symbol

bid_volume

ask_volume

spread

timestamp
```

---

## derivatives_data

```sql
id

symbol

funding_rate

open_interest

long_short_ratio

timestamp
```

---

# Technical Analysis Module

## indicators

```sql
id

symbol

indicator_name

timeframe

value

score

timestamp
```

---

## technical_patterns

```sql
id

symbol

pattern

confidence

detected_at
```

---

## cpr_analysis

Dedicated CPR table.

```sql
id

symbol

timeframe


pivot

bc

tc


cpr_width


cpr_type


virgin_cpr


breakout_probability


reversal_probability


confidence


timestamp
```

---

# Smart Money Module

## smart_money_events

```sql
id

symbol

event_type


BOS

CHOCH

Liquidity Sweep

Order Block

FVG


price_zone

confidence

timestamp
```

---

# News Module

## news_articles

```sql
id

title

content

source

url

language

published_at


sentiment


impact_score


embedding
```

---

## news_entities

```sql
id

news_id

entity_type

entity_name
```

---

# Macro Event Module

## global_events

```sql
id

event_name

category

severity

direction

affected_assets

event_date
```

---

# AI Module

## ai_providers

```sql
id

provider_name

type


OLLAMA

OPENAI

ANTHROPIC


status

priority
```

---

## ai_models

```sql
id

provider_id

model_name

context_size

cost

speed_score
```

---

## ai_requests

```sql
id

model

prompt

response

tokens

latency

created_at
```

---

## ai_memory

Vector table:

```sql
id

content

embedding

category

metadata
```

---

# Signal Module

## signals

```sql
id

symbol


direction


confidence


risk_score


entry_price


stop_loss


take_profit


timeframe


technical_score


news_score


sentiment_score


ai_score


created_at
```

---

## signal_reasons

```sql
id

signal_id

reason_type


technical

news

macro

ai


description
```

---

# Learning Module

## signal_results

```sql
id

signal_id


exit_price


profit_loss


success


duration


evaluated_at
```

---

## model_performance

```sql
id

model_name

accuracy

precision

recall

score

date
```

---

## strategy_weights

```sql
id

component


CPR

EMA

RSI

NEWS

AI


weight

updated_at
```

---

# PHASE 16

# API Architecture

## Objective

Expose all platform capabilities through REST API.

---

# Authentication

Technology:

JWT

---

Endpoints:

```text
POST /api/auth/login

POST /api/auth/register

POST /api/auth/refresh
```

---

# Market API

```text
GET /api/market/prices

GET /api/market/candles

GET /api/market/orderbook

GET /api/market/derivatives
```

---

# Technical API

```text
GET /api/technical/indicators

GET /api/technical/patterns

GET /api/technical/cpr

GET /api/technical/smart-money
```

---

# News API

```text
GET /api/news

GET /api/news/{id}

GET /api/news/sentiment
```

---

# Signal API

```text
GET /api/signals

GET /api/signals/{id}

GET /api/signals/live
```

---

# AI API

```text
POST /api/ai/analyze

GET /api/ai/models

GET /api/ai/providers

POST /api/ai/switch-provider
```

---

# Learning API

```text
GET /api/performance

GET /api/backtest

GET /api/model-score
```

---

# PHASE 17

# Frontend Architecture

## Objective

Create a professional trading intelligence dashboard.

---

# Technology

```text
React

TypeScript

Vite

Tailwind

shadcn/ui

ECharts

TradingView Chart
```

---

# Application Structure

```text
src/

├── dashboard

├── market

├── signals

├── charts

├── news

├── ai

├── portfolio

├── settings

└── admin
```

---

# Main Dashboard

Components:

---

## Market Overview

Display:

* BTC
* ETH
* Market Cap
* Volume
* Fear & Greed

---

## AI Signal Feed

Shows:

```text
BUY BTC

Confidence:
87%

Risk:
Low


Reasons:

CPR Breakout

EMA Trend

Positive News
```

---

## Chart Intelligence

Features:

* Candlestick
* Indicators
* CPR Zones
* Order Blocks
* AI Markers

---

## News Intelligence

Display:

* Important news
* AI summary
* Impact score

---

# AI Assistant Interface

User can ask:

Examples:

```text
Why is BTC bullish?

Analyze ETH today

Compare BTC and SOL

Explain this signal
```

---

# PHASE 18

# Deployment Architecture

## Production Environment

Operating System:

Ubuntu Server 24+

---

# Server Components

```text
Nginx

↓

Frontend

↓

Django API

↓

PostgreSQL

↓

Redis

↓

Celery

↓

Ollama
```

---

# Docker Compose

Services:

```yaml
services:

backend

frontend

postgres

redis

celery

celery-beat

ollama

nginx

prometheus

grafana
```

---

# PHASE 19

# Monitoring System

## Objective

Observe system health.

---

# Metrics

Monitor:

```text
CPU

RAM

Database

API latency

AI response time

Signal generation time

Error rate
```

---

# Prometheus Metrics

Examples:

```text
signals_generated_total

ai_requests_total

market_updates_total

prediction_accuracy
```

---

# Grafana Dashboards

Create:

System Dashboard

AI Dashboard

Market Dashboard

Learning Dashboard

---

# PHASE 20

# Security Architecture

## Authentication

JWT

Refresh Tokens

2FA Optional

---

# API Security

Implement:

* Rate Limiting
* Request Validation
* Permission System
* Audit Logs

---

# Data Security

* Encryption
* Secret Management
* Environment Variables
* Database Backup

---

# PHASE 21

# Production Optimization

## Performance

Implement:

* Redis Cache
* Database Indexing
* Async Processing
* Query Optimization

---

## AI Optimization

Implement:

* Prompt caching
* Response caching
* Model routing
* Token optimization

---

# PHASE 22

# Final Production Workflow

```text
User

↓

Dashboard

↓

API

↓

Signal Engine

↓

AI Orchestrator

↓

Agents

↓

Market Data

↓

News

↓

Technical Analysis

↓

CPR

↓

Risk Engine

↓

Final Signal

↓

Learning System

↓

Improved Future Decisions
```

---

# FINAL PROJECT STATUS TARGET

After completion:

The system becomes a complete AI crypto intelligence platform capable of:

* Real-time market analysis
* Multi-source intelligence gathering
* Professional technical analysis
* CPR based trading logic
* AI reasoning
* Multi-agent collaboration
* Self evaluation
* Continuous improvement
* Local and cloud AI operation
* Enterprise deployment

---

END OF DOCUMENT