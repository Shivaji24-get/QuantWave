# SKILL.md — Fyers Trading Bot

---

## Project Overview

**Fyers Trading Bot** is a Python-based algorithmic trading system built for the Indian stock market (NSE/BSE). It connects to the [Fyers API v3](https://myapi.fyers.in/) to perform automated multi-stock scanning, signal generation, and intraday order execution — all controlled through a CLI interface.

The bot features a **dual-mode architecture**:
- **Legacy Mode** (`main.py`): Original monolithic implementation
- **Enhanced Mode** (`main_enhanced.py`): New modular pipeline architecture with state management, structured tracking, and extensible workflow

The enhanced architecture is designed to run during market hours (09:15–15:30 IST), poll live quotes at configurable intervals, evaluate technical signals against a scoring model, and optionally place MIS (intraday) orders when confidence thresholds are met.

> ⚠️ **Important**: As of the last run (2026-04-30), algo order placement was blocked with error code `-50`: *"Algo orders are not allowed from this app ID."* The bot's data-fetch and scanning features work correctly; only order execution requires an algo-enabled Fyers app ID.

---

## Architecture Evolution

### Legacy Architecture (main.py)
Monolithic design with tight coupling between components:
```
main.py → utils/config.py → auth/token_manager.py → api/*.py → strategies/*.py
```

### Enhanced Architecture (main_enhanced.py)
Modular pipeline architecture inspired by Career-Ops workflow patterns:
```
main_enhanced.py
├── core/
│   ├── pipeline.py      # Workflow orchestration
│   ├── tracker.py       # Trade/position/signal tracking
│   ├── metrics.py       # Performance analytics
│   ├── scheduler.py     # Market session management
│   ├── retry.py         # Resilience patterns
│   └── state_machine.py # Trading state management
├── utils/
│   ├── config.py        # YAML + INI config support
│   └── logger.py        # Structured JSON logging
└── scripts/
    ├── health_check.py  # System verification
    ├── init_tracking.py # Data file initialization
    └── daily_report.py  # Performance reports
```

---

## Features

- **Multi-stock scanning** — scan a single symbol, a comma-separated list, or a full index group (NIFTY50, BANKNIFTY)
- **Technical signal generation** — RSI, SMA20/SMA50 crossover, volume spike, and chart pattern detection (flags, triangles, pennants)
- **Weighted probability scoring** — RSI (30%) + Trend (30%) + Volume (20%) + Pattern (20%)
- **Auto-trading** — places MIS market orders when signal score meets the confidence threshold (default ≥ 75%)
- **Risk management** — position sizing by % of capital, per-trade stop-loss, max concurrent positions, max daily loss guard
- **Live polling loop** — re-scans all symbols every 60 seconds during market hours
- **Automated exit logic** — monitors open positions and places exit orders when stop-loss or take-profit levels are triggered
- **Trade logging** — all executed and exited trades are exported to CSV with full metadata
- **Dual-mode interface** — `main.py` for headless/automated runs; `cli/` module for interactive terminal use with Rich-formatted tables
- **Encrypted token management** — access tokens stored encrypted on disk; refreshed automatically via Selenium-based login flow

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.9+ |
| Broker API | Fyers API v3 (`fyers-apiv3`) |
| CLI Framework | Typer |
| Terminal UI | Rich |
| Data Processing | Pandas, NumPy |
| Auth Automation | Selenium + WebDriver Manager |
| Token Encryption | Cryptography (Fernet) |
| Scheduling | Python `time.sleep` loop + `core/scheduler.py` |
| Config | `config.ini` (INI) + `config/trading_profile.yml` (YAML) |
| Strategy Config | `strategy.json` (JSON) |
| Logging | Structured JSON logging (`utils/logger.py`) |
| Resilience | Retry, Circuit Breaker, Rate Limiter (`core/retry.py`) |
| State Management | Trading State Machine (`core/state_machine.py`) |
| Optional AI | Google Gemini CLI integration (suggested) |
| Optional Automation | OpenCode workflow automation (suggested) |

---

## Architecture / Workflow

### Enhanced Architecture (main_enhanced.py)

```
┌─────────────────────────────────────────────────────────────┐
│                     Entry Points                            │
│  main_enhanced.py    │    cli/main.py (interactive)        │
│  (Enhanced Pipeline) │    (Legacy commands)                  │
└──────────┬───────────────────────────────┬──────────────────┘
           │                               │
    ┌──────▼───────┐              ┌────────▼────────┐
    │   core/      │              │     cli/        │
    │              │              │   commands.py   │
    │ • pipeline   │              │   main.py       │
    │ • tracker    │              └─────────────────┘
    │ • scheduler  │
    │ • state      │
    │ • retry      │
    │ • metrics    │
    └──────┬───────┘
           │
    ┌──────▼───────────┐       ┌─────────────────┐
    │    utils/        │       │    scripts/     │
    │ • config (YAML)  │       │ • health_check  │
    │ • logger (JSON)  │       │ • init_tracking │
    └──────┬───────────┘       │ • daily_report  │
           │                    │ • verify_pipe   │
    ┌──────▼────────────────────┴─────────────────┐
    │                  auth/                      │
    │    TokenManager → get_access_token        │
    │    (Selenium login + Fernet encrypt)        │
    └──────────────────────┬──────────────────────┘
                           │
    ┌──────────────────────▼──────────────────────┐
    │                    api/                     │
    │     FyersClient → fyers.fyersModel          │
    │     get_historical_data / get_quotes        │
    │     get_funds / place_order                 │
    └──────────────────────┬──────────────────────┘
                           │
    ┌──────────────────────▼──────────────────────┐
    │                strategies/                │
    │     SignalGenerator.analyze(df)             │
    │       ├── indicators (RSI, SMA, Vol)        │
    │       ├── pattern_detector                  │
    │       └── signal_scorer (weighted)          │
    │     RiskManager                             │
    │       ├── can_trade()                       │
    │       ├── calculate_position_size()         │
    │       ├── add/remove_position()             │
    │       └── check_exit()                      │
    └──────────────────────┬──────────────────────┘
                           │
    ┌──────────────────────▼──────────────────────┐
    │           Data Layer (tracking)             │
    │    data/trades.md    - Completed trades     │
    │    data/positions.md - Active positions     │
    │    data/signals.md   - Signal history       │
    │    data/daily_pnl.md - Daily summaries      │
    └─────────────────────────────────────────────┘
```

**Enhanced Pipeline Flow:**
```
IDLE → SCANNING → SIGNAL_FOUND → RISK_VALIDATING → ORDER_PENDING → POSITION_OPEN → EXIT_PENDING → POSITION_CLOSED
```

**Main loop (enhanced mode):**
1. Load configuration (YAML or INI format)
2. Initialize structured logging with JSON support
3. Authenticate via `TokenManager`
4. Initialize `TradingPipeline` with `PipelineConfig`
5. State machine transitions: `IDLE` → `SCANNING` (at market open)
6. Every scan interval:
   - Pipeline executes for each symbol: market data → signal → risk → order
   - Tracker records all activities to markdown files
   - Metrics collector updates performance statistics
   - State machine tracks workflow progression
7. Graceful shutdown with state transitions and cleanup

---

## Key Modules Explanation

### `utils/`
- `load_config()` — reads `config.ini` or `config/trading_profile.yml` and returns a flat dictionary
- `validate_config()` — validates required fields and ranges
- `get_profile()` — converts config to `TradingProfile` dataclass
- `setup_logging()` — configures structured JSON logging with `TradingAdapter`
- `is_market_open()` — checks current IST time against configured open/close windows
- `export_to_csv()` — appends trade records (entry or exit) to a timestamped CSV file

**Structured Logging Features:**
- Event-type tagging (trade, signal, position, risk, metric)
- Context propagation via `logger.with_context(symbol=..., trade_id=...)`
- JSON output for machine parsing (optional)
- Helper functions: `log_trade()`, `log_signal()`, `log_position()`, `log_risk_event()`

### `auth/`
- `TokenManager` — manages the Fyers OAuth2 access token lifecycle:
  - Stores tokens encrypted on disk using `cryptography.fernet`
  - On expiry, triggers a Selenium browser session to re-authenticate
  - Exposes `get_access_token()` used by all other modules
- `login_flow.py` — Selenium automation for browser-based OAuth2 flow

### `core/` (Enhanced Architecture)

#### `pipeline.py`
- `TradingPipeline` — orchestrates the complete trading workflow:
  - `execute_single(symbol)` — run full pipeline for one symbol
  - `execute_batch(symbols)` — run pipeline for multiple symbols
  - Step handlers: market data → signal generation → risk validation → order placement → position tracking
- `PipelineConfig` — configuration dataclass for pipeline behavior
- `PipelineResult` — structured result with success/failure status and metadata

#### `tracker.py`
- `TradingTracker` — records all trading activities in markdown format (Career-Ops pattern):
  - `add_trade()` — records completed trades with P&L
  - `add_position()` — records new positions
  - `close_position()` — closes position and creates trade record
  - `add_signal()` — records generated signals with outcomes
  - `get_active_positions()` — returns dict of open positions
  - `export_to_markdown()` — persists all records to `data/*.md` files
- `TradeRecord`, `PositionRecord`, `SignalRecord` — dataclasses for structured data

#### `scheduler.py`
- `TradingScheduler` — market session management and job scheduling:
  - `get_market_status()` — returns market status dict with `is_trading_hours`, `time_until_open`, etc.
  - `is_market_open()` — boolean check for trading hours
  - `wait_for_market_open()` — blocks until market opens
  - `add_job()` — schedule periodic tasks
  - Market session awareness (pre-market, open, post-market, closed)
- `MarketSession` — configuration for market hours
- `MarketStatus` — enum for session states

#### `state_machine.py`
- `TradingStateMachine` — manages trading workflow states:
  - States: `IDLE`, `SCANNING`, `SIGNAL_FOUND`, `RISK_VALIDATING`, `ORDER_PENDING`, `POSITION_OPEN`, `EXIT_PENDING`, `POSITION_CLOSED`, `ERROR`, `STOPPED`
  - `transition(event)` — event-driven state transitions
  - `transition_to(state)` — direct state transition
  - Callback registration: `on_state_change()`, `on_transition()`
  - Transition history tracking
- `TradingState`, `TradingEvent` — enums for states and events

#### `retry.py`
- Resilience patterns for API calls:
  - `RetryHandler` — exponential backoff with jitter
  - `CircuitBreaker` — fail-fast pattern with recovery timeout
  - `RateLimiter` — throttling for API rate limits
- Decorators: `retry_with_backoff()`, `with_circuit_breaker()`, `with_rate_limit()`, `resilient()`
- `RetryConfig`, `CircuitBreakerConfig` — configuration dataclasses

#### `metrics.py`
- `MetricsCollector` — trading performance analytics:
  - `calculate_metrics()` — win rate, profit factor, Sharpe ratio, max drawdown
  - `get_daily_series()` — daily P&L time series
  - `generate_report()` — formatted performance report
  - `record_daily_snapshot()` — saves daily summary
- `TradingMetrics`, `DailySnapshot` — dataclasses for metrics data

### `scripts/`
Automation and utility scripts:
- `health_check.py` — system verification (Python version, dependencies, config, API creds, tracking files)
- `init_tracking.py` — creates initial `data/*.md` tracking files
- `daily_report.py` — generates daily/weekly trading performance reports
- `verify_pipeline.py` — validates pipeline integrity and data consistency

### `api/`
- `FyersClient` — thin wrapper around `fyers_apiv3.fyersModel`; initializes the authenticated client object
- `get_historical_data(client, symbol, resolution, count)` — fetches OHLCV candles as a Pandas DataFrame
- `get_quotes(client, symbol)` — fetches live LTP and bid/ask snapshot
- `get_funds(client)` — returns available cash and margin details
- `place_order(client, symbol, qty, side, order_type, product)` — submits an order; returns order ID on success

### `strategies/`
- `SignalGenerator` — orchestrates the full analysis pipeline:
  - Computes RSI(14), SMA20, SMA50, volume ratio
  - Calls `PatternDetector` for chart pattern recognition
  - Feeds outputs into `SignalScorer` for weighted probability scoring
  - Returns `BUY`, `SELL`, or `HOLD` with a confidence score
- `RiskManager` — stateful risk controller:
  - Tracks open positions in memory
  - `can_trade()` — enforces max position count and daily trade cap
  - `calculate_position_size()` — sizes each trade as a % of available capital
  - `check_exit()` — evaluates stop-loss and take-profit levels against current price
- `PatternDetector` — identifies flag, triangle, and pennant formations from recent candle sequences
- `indicators.py` — standalone RSI, SMA, and volume spike calculation functions

### `cli/`
- `main.py` — Typer app entry point; registers all sub-commands
- `commands.py` — implements: `login`, `scan`, `get-funds`, `get-holdings`, `get-profile`, `place-order`, `order-status`

### Config Files

#### `config.ini` (Legacy)
Primary runtime config in INI format:
```ini
[FYERS_APP]
client_id = XXXXXXXXXX-100
secret_key = YOUR_SECRET
redirect_uri = http://127.0.0.1:5000/fyers/callback
username = YOUR_USER_ID
pin = YOUR_PIN
mobile = YOUR_MOBILE

[TRADING_CONFIG]
risk_per_trade = 0.02
max_positions = 5
confidence_threshold = 0.75
stop_loss_percentage = 2.0
take_profit_percentage = 3.0
max_daily_loss = 0.05
market_open_time = 09:15
market_close_time = 15:30
symbols = NSE:NIFTY50-INDEX,NSE:BANKNIFTY-INDEX

[LOGGING]
log_level = INFO
log_file = quantwave.log
export_csv = true
```

#### `config/trading_profile.yml` (Enhanced - Career-Ops Pattern)
YAML-based user profile with structured sections:
```yaml
trader:
  name: "Your Name"
  email: "your@email.com"
  timezone: "Asia/Kolkata"

risk_profile:
  risk_per_trade: 0.02
  max_positions: 5
  max_daily_loss: 0.05
  max_trades_per_day: 10

api:
  fyers:
    client_id: "XXXXXXXXXX-100"
    redirect_uri: "http://127.0.0.1:5000/fyers/callback"
    # secret_key from env: FYERS_SECRET_KEY

# See config/trading_profile.example.yml for full template
```

#### `strategy.json`
Indicator parameters and default symbol list:
```json
{
  "indicators": {
    "rsi": { "period": 14, "oversold": 30, "overbought": 70 },
    "sma": { "short_period": 20, "long_period": 50 },
    "volume": { "threshold": 100000 }
  },
  "scoring_weights": {
    "rsi": 0.30,
    "trend": 0.30,
    "volume": 0.20,
    "pattern": 0.20
  }
}
```

#### Data Contract (`DATA_CONTRACT.md`)
User Layer (personal data, gitignored):
- `config/trading_profile.yml` — user-specific settings
- `data/*.md` — trading history and positions
- `token.enc`, `token.key` — encrypted credentials

System Layer (code, version-controlled):
- `core/`, `utils/`, `strategies/`, `api/` — all source code
- `config/trading_profile.example.yml` — template for user profile

---

## Setup Instructions

### Quick Start (Enhanced Architecture)

```bash
# 1. Clone the repository
git clone https://github.com/Shivaji24-get/QuantWave.git
cd QuantWave

# 2. Create and activate a virtual environment
python -m venv fyers-env
source fyers-env/bin/activate  # Windows: fyers-env\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize tracking files
python scripts/init_tracking.py

# 5. Create config (choose one)
# Option A: Use legacy INI format
cp "config copy.ini" config.ini
# Edit config.ini with your Fyers credentials

# Option B: Use enhanced YAML format (recommended)
cp config/trading_profile.example.yml config/trading_profile.yml
# Edit config/trading_profile.yml with your settings

# 6. Set environment variable for secret key (YAML mode)
export FYERS_SECRET_KEY="your_secret_key"  # Windows: set FYERS_SECRET_KEY=...

# 7. Authenticate (opens browser for Fyers OAuth2 login)
python -m cli.main login

# 8. Run health check
python scripts/health_check.py

# 9. Run the enhanced bot
python main_enhanced.py
```

### System Verification

```bash
# Health check - verify all components
python scripts/health_check.py

# Pipeline verification - check data integrity
python scripts/verify_pipeline.py

# Generate daily report
python scripts/daily_report.py --days 7 --format markdown
```

**Requirements:**
- Python 3.9+ (3.12 recommended)
- A Fyers trading account with API access enabled
- Chrome browser (for Selenium-based login automation)
- **An algo-trading enabled App ID** to place orders (standard app IDs will receive error code `-50`)
- Optional: `PyYAML` for YAML config support (`pip install pyyaml`)
- Optional: `python-json-logger` for structured logging (`pip install python-json-logger`)

---

## Usage Guide

### Headless Auto-Trading

#### Enhanced Mode (Recommended)
```bash
# Run with enhanced pipeline architecture
python main_enhanced.py

# Features:
# - Structured logging to logs/quantwave.log
# - Trade/position tracking in data/*.md files
# - State machine for workflow management
# - Automatic retry and circuit breaker patterns
```

#### Legacy Mode
```bash
# Run original monolithic implementation
python main.py
```

### CLI Commands

#### Scanning & Analysis
```bash
# Scan a single symbol
python -m cli.main scan --symbol NSE:SBIN-EQ

# Scan multiple symbols
python -m cli.main scan --symbols NSE:SBIN-EQ,NSE:RELIANCE-EQ,NSE:INFY-EQ

# Scan full index, show top 5 results
python -m cli.main scan --index NIFTY50 --top 5

# Live scan with auto-trading enabled at 75% threshold
python -m cli.main scan --symbol NSE:SBIN-EQ --live --auto-trade --threshold 75 --interval 5
```

#### Order Management
```bash
# Place market order
python -m cli.main place-order --symbol NSE:RELIANCE-EQ --side BUY --qty 10

# Place limit order
python -m cli.main place-order --symbol NSE:SBIN-EQ --side SELL --qty 5 --type LIMIT --price 1080.50

# Check order status
python -m cli.main order-status --order-id 230415000000001
```

#### Account Information
```bash
python -m cli.main get-funds
python -m cli.main get-holdings
python -m cli.main get-profile
```

### Automation Scripts

```bash
# Initialize tracking files (run once)
python scripts/init_tracking.py

# System health check
python scripts/health_check.py

# Verify pipeline integrity
python scripts/verify_pipeline.py

# Generate performance report
python scripts/daily_report.py --days 7 --format markdown --output report.md
```

---

## Configuration Details

### `config.ini`

```ini
[DEFAULT]
client_id        = YOUR_FYERS_APP_ID     # Format: XXXXXXXXXX-100
secret_key       = YOUR_SECRET_KEY
redirect_uri     = http://127.0.0.1:5000/fyers/callback

[FYERS_APP]
username         = YOUR_FYERS_USER_ID
pin              = YOUR_PIN
mobile           = YOUR_MOBILE_NUMBER

[TRADING_CONFIG]
risk_per_trade        = 0.02    # 2% of capital per trade
max_positions         = 5       # Max concurrent open positions
confidence_threshold  = 0.75    # Minimum score to trigger a trade (75%)
stop_loss_percentage  = 2.0     # SL at 2% below entry
take_profit_percentage= 3.0     # TP at 3% above entry
max_daily_loss        = 0.05    # Stop trading if daily loss > 5% of capital
market_open_time      = 09:15   # IST
market_close_time     = 15:30   # IST
symbols               = NSE:NIFTY50-INDEX,NSE:BANKNIFTY-INDEX

[LOGGING]
log_level  = INFO
log_file   = quantwave.log
export_csv = true
```

### `strategy.json`

```json
{
  "indicators": {
    "rsi":    { "period": 14, "oversold": 30, "overbought": 70 },
    "sma":    { "period": 20 },
    "volume": { "threshold": 100000 }
  },
  "entry": { "rsi_less_than": 30, "volume_greater_than": 100000 },
  "exit":  { "rsi_greater_than": 70 },
  "symbols": ["NSE:SBIN-EQ", "NSE:RELIANCE-EQ", "NSE:INFY-EQ"],
  "timeframe": "D",
  "limit": 30
}
```

### Scoring Weights (hardcoded in `SignalScorer`)

| Component | Weight | Signal Condition |
|---|---|---|
| RSI | 30% | < 30 → BUY signal; > 70 → SELL signal |
| Trend (SMA20 vs SMA50) | 30% | SMA20 > SMA50 → bullish |
| Volume | 20% | Current volume > 1.5× average |
| Chart Pattern | 20% | Pattern confidence score (0–100%) |

---

## Limitations / Assumptions

- **Algo order restriction**: Standard Fyers App IDs (suffix `-100`) block algorithmic order placement. An algo-enabled app ID must be obtained separately from Fyers.
- **MIS only**: All orders are placed as MIS (intraday margin). No CNC (delivery) or overnight position support.
- **No WebSocket streaming**: Live data is polled via REST every 5–60 seconds, not streamed — introduces latency.
- **Daily OHLCV for signals**: `SignalGenerator` uses daily candles (`"D"` resolution) even during intraday runs, which may not reflect intraday momentum accurately.
- **Single-threaded scanning**: All symbols are processed sequentially in the main loop; large symbol lists will have increasing per-symbol delays.
- **Selenium dependency**: Login automation requires Chrome and chromedriver — fragile in headless/server environments.

### Addressed in Enhanced Architecture
- ✅ **Persistent position tracking**: `TradingTracker` saves positions to `data/positions.md`
- ✅ **Paper trading mode**: Configurable via `paper_trading: true` in profile
- ✅ **Structured logging**: JSON-formatted logs with event categorization
- ✅ **Resilience patterns**: Retry with backoff, circuit breaker, rate limiting
- ✅ **State management**: Trading state machine tracks workflow progression
- ✅ **Health checks**: Automated system verification scripts

---

## Future Improvements & Suggested Enhancements

### High Priority

- **WebSocket integration** — replace REST polling with Fyers WebSocket for real-time tick data (reduces latency from seconds to milliseconds)
- **Intraday candles for signals** — use 5m or 15m candles for more responsive intraday signal generation
- **Async/concurrent scanning** — use `asyncio` or `ThreadPoolExecutor` to scan symbols in parallel
- **Algo app onboarding guide** — document the Fyers algo-trading app registration process to unblock order execution

### AI & Automation Integration (Suggested)

#### Google Gemini CLI Integration
Add AI-based decision support for trade signals:
```python
# Proposed: core/gemini_advisor.py
class GeminiAdvisor:
    """AI-powered trade signal explanation and validation."""
    
    def explain_signal(self, symbol: str, signal_data: dict) -> str:
        """Generate natural language explanation of why signal was generated."""
        # Use Gemini API to analyze indicators and patterns
        # Return: "BUY signal due to RSI oversold (28) + bullish flag pattern + volume spike"
    
    def validate_signal(self, signal_data: dict, market_context: dict) -> dict:
        """AI validation of signal quality with confidence score."""
        # Cross-reference with news, sector trends, market sentiment
        # Return: {"valid": true, "confidence": 0.85, "concerns": ["High market volatility"]}
    
    def suggest_position_size(self, signal_data: dict, portfolio: dict) -> int:
        """AI-optimized position sizing based on signal strength and portfolio risk."""
```

**Setup:**
```bash
# Install Gemini CLI
pip install google-generativeai

# Set API key
export GEMINI_API_KEY="your_key"

# Enable in trading_profile.yml
advanced:
  gemini_integration: true
  ai_validation_threshold: 0.80
```

#### OpenCode Workflow Automation
Automate code tasks and deployments:
```yaml
# Proposed: .windsurf/workflows/trading-deploy.md
---
description: Deploy trading bot updates
---
1. Run health checks
2. Run verify_pipeline
3. Backup data/ directory
4. Deploy new version
5. Restart bot with supervisor
```

### Monitoring & Alerting

#### Notification System
```python
# Proposed: core/notifications.py
class NotificationManager:
    """Multi-channel trade alerts."""
    
    def send_telegram(self, message: str):
        """Send alert to Telegram bot."""
    
    def send_email(self, subject: str, body: str):
        """Send email via SMTP."""
    
    def send_webhook(self, url: str, payload: dict):
        """Send to Discord/Slack webhook."""
```

**Configuration:**
```yaml
notifications:
  telegram:
    bot_token: "${TELEGRAM_BOT_TOKEN}"
    chat_id: "${TELEGRAM_CHAT_ID}"
    events: [trade_executed, position_closed, high_profit, stop_loss_hit]
  
  email:
    smtp_server: "smtp.gmail.com"
    username: "${EMAIL_USER}"
    password: "${EMAIL_PASS}"
    recipients: ["trader@example.com"]
```

#### Logging Dashboard
```bash
# Proposed: scripts/dashboard.py
python scripts/dashboard.py

# Features:
# - Real-time log tail with filtering
# - Trade performance charts
# - Active positions table
# - Signal history with outcomes
```

### Backtesting & Strategy Development

```python
# Proposed: core/backtest.py
class BacktestEngine:
    """Historical strategy validation."""
    
    def run_backtest(
        self,
        symbols: list,
        start_date: datetime,
        end_date: datetime,
        strategy_config: dict
    ) -> BacktestResult:
        """
        Replay historical data through SignalGenerator and RiskManager.
        Returns performance metrics: CAGR, Sharpe, max drawdown, win rate.
        """
    
    def optimize_parameters(self, param_grid: dict) -> OptimizedParams:
        """Grid search for optimal indicator parameters."""
```

### Performance Optimizations

- **WebSocket streaming** — real-time tick data instead of REST polling
- **Async I/O** — `aiohttp` for concurrent API calls
- **Caching layer** — Redis for market data caching
- **Database backend** — PostgreSQL for historical data and trade analytics
- **Containerization** — Docker + Docker Compose for deployment

### Security & Operations

- **Secrets management** — HashiCorp Vault or AWS Secrets Manager
- **API key rotation** — automated token refresh without browser
- **Audit logging** — immutable trade log with digital signatures
- **Health monitoring** — Prometheus metrics + Grafana dashboard
- **Circuit breaker dashboard** — real-time resilience status
