# QuantWave Architecture

## Overview

This document describes the refactored QuantWave architecture, inspired by the Career-Ops project structure. The goal is to create a modular, scalable, and maintainable trading automation system.

## Key Principles from Career-Ops

1. **Clear Separation of Concerns**: System files vs User data
2. **Modular Design**: Modes/Cores for different functionalities
3. **Configuration Management**: YAML-based profiles with validation
4. **Pipeline Tracking**: Structured tracking of all activities
5. **Workflow Orchestration**: Batch processing and automation
6. **Data Contract**: Explicit rules for file management
7. **Health Monitoring**: Verification and diagnostic scripts

## Directory Structure

```
QuantWave/
├── ARCHITECTURE.md           # This file - system documentation
├── DATA_CONTRACT.md          # Data separation rules
├── README.md                 # User documentation
├── config/
│   ├── trading_profile.yml   # User trading profile (USER LAYER)
│   └── settings.yml          # System settings (SYSTEM LAYER)
├── core/                     # Core workflow modules
│   ├── __init__.py
│   ├── pipeline.py          # Workflow orchestration
│   ├── tracker.py           # Trading activity tracking
│   ├── metrics.py           # Performance metrics
│   ├── scheduler.py         # Job scheduling
│   ├── retry.py             # Retry mechanisms
│   └── state_machine.py     # Trading state management
├── data/                     # User data (USER LAYER - gitignored)
│   ├── trades.md            # Trade history tracker
│   ├── positions.md         # Active positions log
│   ├── signals.md           # Signal history
│   └── scan_history.tsv     # Market scan history
├── api/                      # API clients
│   ├── __init__.py
│   ├── client.py            # Fyers client
│   ├── market_data.py       # Market data endpoints
│   ├── orders.py            # Order management
│   └── funds.py             # Account/funds info
├── strategies/               # Trading strategies
│   ├── __init__.py
│   ├── base.py              # Base classes (Pattern, Signal, Detector, Scanner)
│   ├── mss_detector.py      # Market Structure Shift detector
│   ├── harmonic_detector.py # Harmonic pattern detection engine
│   ├── harmonic_scanner.py  # Harmonic pattern scanner with async/caching
│   ├── harmonic_reporter.py # Pattern export and reporting
│   ├── validators.py       # Data, pattern, API, duplicate validators
│   ├── signal_generator.py  # Signal generation
│   ├── risk_manager.py      # Risk controls
│   ├── order_executor.py    # Order execution
│   └── ...                  # Individual strategies
├── utils/                    # Utilities
│   ├── __init__.py
│   ├── config.py            # Configuration loader
│   ├── logger.py            # Structured logging
│   ├── exporter.py          # Data export
│   └── helpers.py           # Helper functions
├── auth/                     # Authentication
│   ├── __init__.py
│   └── token_manager.py     # Token management
├── cli/                      # Command-line interface
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   └── commands.py          # CLI commands
├── scripts/                  # Automation scripts
│   ├── health_check.py      # System verification
│   ├── daily_report.py      # Daily P&L reports
│   ├── batch_trader.py      # Batch trading operations
│   └── verify_pipeline.py   # Pipeline integrity check
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_pipeline.py
│   └── test_tracker.py
├── logs/                     # Log files (USER LAYER - gitignored)
├── output/                   # Generated outputs (USER LAYER - gitignored)
└── tmp/                      # Temporary files (gitignored)
```

## Core Components

### 1. Pipeline (core/pipeline.py)

Orchestrates the complete trading workflow:
- Signal generation
- Risk validation
- Order execution
- Position tracking
- Exit monitoring

### 2. Tracker (core/tracker.py)

Maintains structured records of all trading activities:
- Trade history with P&L
- Signal performance analysis
- Position lifecycle tracking
- Daily/weekly/monthly summaries

### 3. Metrics (core/metrics.py)

Collects and reports performance metrics:
- Win/loss ratios
- Sharpe ratio
- Maximum drawdown
- Trade frequency
- Signal accuracy

### 4. Scheduler (core/scheduler.py)

Manages background jobs and timing:
- Market open/close detection
- Periodic scanning intervals
- Daily reset operations
- Scheduled reporting

### 5. Retry (core/retry.py)

Implements robust retry mechanisms:
- Exponential backoff for API calls
- Circuit breaker pattern
- Rate limiting compliance

## Data Contract

### User Layer (Never Auto-Updated)

Files that contain personal configuration and trading history:
- `config/trading_profile.yml` - Your trading preferences and identity
- `data/trades.md` - Your complete trade history
- `data/positions.md` - Your active and closed positions
- `data/signals.md` - Signal history with outcomes
- `logs/*.log` - Your trading logs
- `output/*` - Generated reports and exports

### System Layer (Auto-Updatable)

Files that contain system logic and can be updated:
- `core/*.py` - Core workflow modules
- `strategies/*.py` - Trading strategy implementations
- `api/*.py` - API client code
- `utils/*.py` - Utility functions
- `scripts/*.py` - Automation scripts
- `tests/*.py` - Test suite

## Configuration System

Following Career-Ops pattern:

1. **YAML-based**: Human-readable, structured configuration
2. **Profile-based**: Separate identity/configuration from code
3. **Validation**: Schema validation on load
4. **Environment Override**: Support for environment variables

## Workflow Patterns

### Trading Pipeline

```
Market Data → Signal Generation → Risk Check → Order Placement → 
Position Tracking → Exit Monitoring → P&L Recording → Metrics Update
```

### Batch Operations

Support for batch processing:
- Multi-symbol scanning
- Bulk order placement
- Batch position updates
- Aggregate reporting

### State Management

Trading state machine:
- `IDLE` → Waiting for market open
- `SCANNING` → Analyzing market data
- `SIGNAL_FOUND` → Valid signal detected
- `ORDER_PENDING` → Order submitted
- `POSITION_OPEN` → Active position
- `EXIT_PENDING` → Exit order submitted
- `POSITION_CLOSED` → Trade completed

## Harmonic Scanner Integration

### Overview

The Harmonic Scanner is a pattern detection system integrated into the Gemini CLI workflow for identifying harmonic trading patterns (Gartley, Butterfly, Bat, Crab) using Fibonacci ratio validation.

### Harmonic Scanner Workflow

```
User Command
    ↓
Gemini CLI (harmonic-scan, harmonic-live, harmonic-pattern)
    ↓
Command Parser
    ↓
Configuration Loader (trading_profile.yml)
    ↓
Market Data Fetcher (api/market_data.py)
    ↓
Data Validation Layer (validators.py)
    ↓
Harmonic Pattern Scanner (harmonic_scanner.py)
    ↓
Pattern Detection Engine (harmonic_detector.py)
    ├─ MSS Detector (mss_detector.py) - Swing point identification
    ├─ Fibonacci Ratio Calculation
    └─ Pattern Validation
    ↓
Pattern Validation Engine (validators.py)
    ├─ Ratio validation
    ├─ Confidence scoring
    ├─ Duplicate filtering
    └─ Risk/reward validation
    ↓
Signal Generator (harmonic_scanner.py)
    ↓
Risk Management (config/trading_profile.yml)
    ↓
Trade Execution / Paper Trading
    ↓
Report Generator (harmonic_reporter.py)
    ├─ CSV export
    ├─ JSON export
    └─ Markdown reports
    ↓
Logs + Database Storage
```

### Harmonic Scanner Components

#### 1. Base Classes (strategies/base.py)

- **Pattern**: Base class for all detected patterns
- **Signal**: Trading signal representation
- **PatternDetector**: Abstract base for pattern detectors
- **SignalGenerator**: Abstract base for signal generators
- **Scanner**: Abstract base for market scanners

#### 2. MSS Detector (strategies/mss_detector.py)

- **SwingPoint**: Dataclass for swing high/low points
- **MSSDetector**: Identifies market structure shifts using configurable lookback

#### 3. Harmonic Detector (strategies/harmonic_detector.py)

- **HarmonicPattern**: Pattern dataclass with Fibonacci ratios, PRZ, entry/SL/TP
- **HarmonicDetector**: Pattern detection engine
  - Detects Gartley, Butterfly, Bat, Crab patterns
  - Fibonacci ratio validation with configurable tolerance
  - Confidence scoring based on ratio proximity
  - Potential Reversal Zone (PRZ) calculation

#### 4. Harmonic Scanner (strategies/harmonic_scanner.py)

- **HarmonicScanner**: Multi-symbol scanner with:
  - Async/parallel scanning support
  - Data caching (configurable TTL)
  - Pattern caching
  - Duplicate pattern filtering
  - Input validation
  - Rate limiting awareness
  - Watchlist scanning with ranking

#### 5. Validators (strategies/validators.py)

- **DataValidator**: DataFrame, symbol, timeframe validation
- **PatternValidator**: Ratio, confidence, risk/reward validation
- **APIValidator**: Rate limiting, response validation
- **DuplicateValidator**: Time-window based duplicate filtering

#### 6. Harmonic Reporter (strategies/harmonic_reporter.py)

- **HarmonicReporter**: Export and reporting
  - CSV export
  - JSON export
  - Markdown reports
  - Signal history tracking

### CLI Commands

#### harmonic-scan

Scan single or multiple symbols for harmonic patterns.

```bash
# Single symbol
trading-bot harmonic-scan --symbol "NSE:RELIANCE-EQ" --timeframe D

# Multiple symbols
trading-bot harmonic-scan --symbols "NSE:RELIANCE-EQ,NSE:TCS-EQ" --timeframe 5m

# Index group
trading-bot harmonic-scan --index NIFTY50 --timeframe D

# With export
trading-bot harmonic-scan --index NIFTY50 --export
```

#### harmonic-live

Continuous live scanning for harmonic patterns.

```bash
trading-bot harmonic-live --symbols "NSE:RELIANCE-EQ,NSE:TCS-EQ" --timeframe 5m --interval 60
```

#### harmonic-pattern

Detailed pattern analysis for a single symbol.

```bash
trading-bot harmonic-pattern --symbol "NSE:RELIANCE-EQ" --timeframe D
```

### Configuration

In `config/trading_profile.yml`:

```yaml
strategies:
  enabled:
    - "harmonic"
  
  harmonic:
    enabled: true
    swing_lookback: 5
    min_confidence: 0.70
    tolerance: 0.15
    patterns:
      - "Gartley"
      - "Butterfly"
      - "Bat"
      - "Crab"
    stop_loss_pct: 1.0
    take_profit_pct: 2.0
    min_risk_reward: 2.0
```

### Performance Optimizations

1. **Caching**: Data and pattern caching with configurable TTL (default 60s)
2. **Parallel Scanning**: ThreadPoolExecutor for multi-symbol scans
3. **Async Support**: Async methods for non-blocking operations
4. **Duplicate Filtering**: Time-window based duplicate pattern filtering
5. **Rate Limiting**: API rate limit awareness and compliance

### Error Handling Strategy

1. **Structured Logging**: JSON format for machine parsing
2. **Graceful Degradation**: Continue operation on non-critical errors
3. **Retry with Backoff**: For transient failures
4. **Circuit Breaker**: Stop operations on persistent failures
5. **Alert System**: Notify on critical errors

## Monitoring & Observability

1. **Health Checks**: `scripts/health_check.py`
2. **Pipeline Verification**: `scripts/verify_pipeline.py`
3. **Daily Reports**: Automated P&L summaries
4. **Metrics Export**: Prometheus/Grafana compatible

## Migration Notes

### What Changed from Original QuantWave

1. **Config System**: Moved from INI to YAML with profile separation
2. **Logging**: Added structured JSON logging
3. **Tracking**: Added comprehensive trade/position/signal tracking
4. **Workflow**: Pipeline-based orchestration
5. **Metrics**: Performance analytics
6. **Testing**: Added health checks and verification scripts

### Backward Compatibility

- Original `main.py` functionality preserved
- Existing strategies work without modification
- API clients remain compatible
- Config can be migrated automatically
