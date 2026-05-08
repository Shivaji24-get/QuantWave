# 📖 TradingBot - Complete Usage Guide

**Everything you need to know about using TradingBot**

---

## 📚 Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Configuration Deep Dive](#configuration-deep-dive)
3. [Running the Bot](#running-the-bot)
4. [Understanding Signals](#understanding-signals)
5. [Risk Management](#risk-management)
6. [Strategies Explained](#strategies-explained)
7. [CLI Commands Reference](#cli-commands-reference)
8. [Automation Features](#automation-features)
9. [Monitoring & Logs](#monitoring--logs)
10. [Troubleshooting](#troubleshooting)

---

## Installation & Setup

### Prerequisites

**Required Software:**
- Python 3.9 or higher
- Windows 10/11 (or Linux/Mac with modifications)
- Internet connection

**Required Accounts:**
- Fyers trading account (for live trading)
- Fyers API app (free to create)

### Step-by-Step Installation

**1. Download the Project**
```bash
git clone https://github.com/yourusername/TradingBot.git
cd TradingBot
```

**2. Create Virtual Environment (Recommended)**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# OR
source venv/bin/activate  # Linux/Mac
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Create Configuration**
```bash
# Copy example config
copy config\trading_profile.example.yml config\trading_profile.yml

# Edit the config
notepad config\trading_profile.yml
```

**5. Get Fyers API Credentials**

1. Visit [Fyers API Dashboard](https://myapi.fyers.in/)
2. Click "Create App"
3. Fill details:
   - App Name: TradingBot
   - Redirect URL: `http://127.0.0.1:5000/fyers/callback`
4. Save the **Client ID** and **Secret Key**
5. Enter them in `config/trading_profile.yml`:

```yaml
api:
  fyers:
    client_id: "ABCDE1S2F3-100"
    secret_key: "XYZ123ABC456"
    redirect_uri: "http://127.0.0.1:5000/fyers/callback"
```

---

## Configuration Deep Dive

### File: `config/trading_profile.yml`

This is your main configuration file. Let's understand each section:

#### 1. Trader Information
```yaml
trader:
  name: "Your Name"
  email: "your@email.com"
  timezone: "Asia/Kolkata"  # Important for market hours
```
**Purpose:** Identifies you in logs and reports

#### 2. Risk Profile (Most Important!)
```yaml
risk_profile:
  risk_per_trade: 0.02          # 2% of capital per trade
  max_positions: 5              # Max 5 trades at once
  max_daily_loss: 0.05            # Stop trading if down 5%
  max_trades_per_day: 10        # Max 10 trades/day
  default_stop_loss_pct: 2.0    # 2% stop loss
  default_take_profit_pct: 4.5  # 4.5% target
  min_risk_reward_ratio: 2.0    # Only 2:1 trades or better
```

**Beginner Settings:**
```yaml
risk_profile:
  risk_per_trade: 0.01          # Safer: 1% only
  max_positions: 2              # Fewer positions
  default_stop_loss_pct: 1.5    # Tighter stops
```

**Aggressive Settings:**
```yaml
risk_profile:
  risk_per_trade: 0.05          # 5% per trade
  max_positions: 10             # More positions
  default_stop_loss_pct: 3.0    # Wider stops
```

#### 3. Trading Preferences
```yaml
trading_preferences:
  default_symbols:
    - "NSE:NIFTY50-INDEX"       # Index
    - "NSE:NIFTYBANK-INDEX"     # Bank index
    - "NSE:RELIANCE-EQ"         # Stock
    - "NSE:TCS-EQ"              # Stock
```

**How to Add Stocks:**
- Find symbol on NSE website
- Format: `NSE:SYMBOLNAME-EQ`
- Examples: `NSE:INFY-EQ`, `NSE:SBIN-EQ`, `NSE:HDFCBANK-EQ`

**Market Hours:**
```yaml
  market_session:
    market_open: "09:15"        # IST
    market_close: "15:30"       # IST
```

#### 4. Auto Trading Settings
```yaml
  auto_trading:
    enabled: false               # KEEP FALSE until ready!
    confirmation_required: true  # Always confirm first
    min_signal_score: 75.0       # Only 75%+ signals
    paper_trading: true          # Safe mode
```

**⚠️ WARNING:** Only set `enabled: true` after weeks of paper trading!

#### 5. Scanning Settings
```yaml
  scanning:
    interval_seconds: 60         # Check every minute
    use_live_data: true
    historical_lookback: 50      # 50 candles of history
```

**Adjust Based on Your Style:**
- **Day Trading:** `interval_seconds: 30` (faster)
- **Swing Trading:** `interval_seconds: 300` (5 min)
- **Positional:** `interval_seconds: 1800` (30 min)

#### 6. Strategy Configuration
```yaml
strategies:
  enabled:
    - "smart_money"            # SMC strategy
    - "order_block"            # Order blocks
    - "fvg_detector"           # Fair Value Gaps
  
  smart_money:
    min_pattern_size: 3
    confidence_threshold: 0.60  # 60% confidence
    require_fvg: false          # Don't require FVG
    require_mss: false          # Don't require MSS
  
  timeframe:
    main: "1h"                  # 1-hour trend
    entry: "5m"                 # 5-minute entries
    higher: "4h"                # 4-hour context
```

**Understanding Timeframes:**
- **Main (1H):** Higher timeframe trend direction
- **Entry (5M):** Where you actually enter trades
- **Higher (4H):** Broader market context

**Strategy Toggles:**
```yaml
  fvg_detector:
    enabled: false              # Disable if hitting stop losses
    min_gap_size: 0.5
    fill_threshold: 0.3
```

---

## Running the Bot

### Three Modes of Operation

#### 1. Paper Trading Mode (Recommended for Beginners)
```bash
python -m cli.main start-bot --paper
```
**What happens:**
- Bot analyzes markets
- Generates signals
- Simulates trades (fake money)
- Tracks performance
- **NO REAL MONEY AT RISK**

**Use this for:**
- Learning the system
- Testing strategies
- Building confidence
- 2-4 weeks minimum before going live

#### 2. Live Mode with Manual Confirmation
```bash
python -m cli.main start-bot
# Then use manual order commands
python -m cli.main place-order --symbol NSE:RELIANCE-EQ --qty 10 --side BUY
```
**What happens:**
- Bot generates signals
- You decide to trade
- You place orders manually

**Use this for:**
- Validating signals with real money
- Small position sizes
- Building trust in the system

#### 3. Full Auto-Trading (Advanced Only!)
**Config:**
```yaml
auto_trading:
  enabled: true
  confirmation_required: false   # ⚠️ DANGEROUS
  min_signal_score: 85.0         # Very high threshold
```

```bash
python -m cli.main start-bot
```

**⚠️ EXTREME CAUTION:**
- Only after months of successful paper trading
- Start with 1 share per trade
- Monitor constantly
- Have kill switch ready (Ctrl+C)

---

## Understanding Signals

### Signal Format
When you check `data/signals.md`:

```markdown
| # | Date                | Symbol          | Signal | Score | Price    | Executed | Outcome | Notes              |
|---|---------------------|-----------------|--------|-------|----------|----------|---------|-------------------|
| 1 | 2024-01-15 10:30:00 | NSE:RELIANCE-EQ | BUY    | 82.5  | 2450.30  | YES      | WIN     | Breakout confirmed|
| 2 | 2024-01-15 11:15:00 | NSE:TCS-EQ      | SELL   | 45.0  | 3560.80  | NO       | -       | Score too low     |
```

### Signal Score Explained

| Score Range | Quality | Action |
|-------------|---------|--------|
| 0-50        | Poor    | Ignore |
| 50-70       | Fair    | Watch only |
| 70-85       | Good    | Consider manually |
| 85-100      | Excellent | Strong candidate |

### Signal Components

**Score Breakdown (example: 82.5):**
- RSI Contribution: 24.75 (30% weight)
- Trend Contribution: 24.75 (30% weight)
- Volume Contribution: 16.5 (20% weight)
- Pattern Contribution: 16.5 (20% weight)

**What Each Means:**
- **RSI:** Oversold (<30) or overbought (>70)
- **Trend:** Above/below moving averages
- **Volume:** Higher than average (confirms move)
- **Pattern:** Chart patterns (flags, triangles)

---

## Risk Management

### Built-In Safety Features

#### 1. Position Sizing
```python
# If you have ₹100,000 capital
# risk_per_trade = 0.02 (2%)
# Max loss per trade = ₹2,000

# For a stock at ₹500 with 2% stop loss:
# Stop distance = ₹10
# Position size = ₹2,000 / ₹10 = 200 shares
```

#### 2. Daily Loss Limit
```yaml
max_daily_loss: 0.05  # Stop if down 5%
```
Once hit, bot stops trading for the day.

#### 3. Maximum Positions
```yaml
max_positions: 5
```
Prevents over-concentration.

#### 4. Stop Loss Calculation
```python
entry_price = 1000
stop_loss_pct = 2.0

stop_loss_price = entry_price * (1 - stop_loss_pct/100)
# = 1000 * 0.98 = 980

# If stock drops to 980, exit automatically
```

### Risk Management Rules to Follow

1. **Never risk more than 2% per trade**
2. **Never have more than 5 open positions**
3. **Stop if you lose 5% in a day**
4. **Always use stop losses**
5. **Risk/Reward should be at least 1:2**

---

## Strategies Explained

### Strategy 1: Smart Money Concepts (SMC)

**What it does:**
Identifies where "smart money" (institutions) is buying/selling.

**How it works:**
1. Finds Order Blocks (areas where big players entered)
2. Detects Fair Value Gaps (FVG) - price imbalance
3. Identifies Market Structure Shifts (MSS) - trend changes
4. Combines for high-probability setups

**Best for:**
- Trending markets
- Breakout trades
- Swing trading

**Configuration:**
```yaml
smart_money:
  min_pattern_size: 3           # Minimum candles in pattern
  confidence_threshold: 0.60    # 60% confidence required
  require_fvg: true              # Must have FVG
  require_mss: true              # Must have MSS
```

### Strategy 2: Order Block Detection

**What it does:**
Finds areas on chart where institutional orders were placed.

**How it works:**
1. Looks for strong bullish/bearish candles
2. Identifies consolidation zones
3. Marks potential support/resistance
4. Trades breakouts from these zones

**Best for:**
- Support/resistance trading
- Range breakouts
- Day trading

**Configuration:**
```yaml
order_block:
  lookback_periods: 20         # Look back 20 candles
  volume_threshold: 1.5         # 1.5x average volume
```

### Strategy 3: Fair Value Gap (FVG) Detector

**What it does:**
Finds price gaps that are likely to be "filled" (price returns to gap area).

**How it works:**
1. Identifies gaps between candles
2. Measures gap size
3. Predicts if price will return to fill gap
4. Trades in direction of gap fill

**Best for:**
- Mean reversion
- Quick scalps
- After volatile moves

**⚠️ Warning:** FVG strategy can be risky in strong trends. Use with caution.

**Configuration:**
```yaml
fvg_detector:
  min_gap_size: 0.5            # Minimum gap size (%)
  fill_threshold: 0.3          # How much gap must fill
  enabled: false               # Disabled by default
```

### Multi-Timeframe Analysis

**How it works:**
```
Higher TF (4H): Bullish trend? → Only take BUY signals
Main TF (1H):   Identify setup → Pattern forming
Entry TF (5M):  Precise entry → Execute trade
```

**Why it matters:**
- Avoids trading against major trend
- Better entry points
- Higher win rate

---

## CLI Commands Reference

### Account & Authentication

```bash
# Login to Fyers
python -m cli.main login

# Check account status
python -m cli.main status

# Logout
python -m cli.main logout
```

### Trading Operations

```bash
# Start paper trading (RECOMMENDED)
python -m cli.main start-bot --paper

# Start live trading
python -m cli.main start-bot

# Place manual order
python -m cli.main place-order \
  --symbol NSE:RELIANCE-EQ \
  --qty 10 \
  --side BUY \
  --type MARKET

# Close position
python -m cli.main close-position --symbol NSE:RELIANCE-EQ

# View positions
python -m cli.main positions
```

### Market Analysis

```bash
# Scan all symbols
python -m cli.main scan

# Scan specific symbol
python -m cli.main scan --symbol NSE:TCS-EQ

# Deep analysis with AI
python -m cli.main analyze --symbol NSE:RELIANCE-EQ

# Get market data
python -m cli.main market-data --symbol NSE:SBIN-EQ
```

### Reports & Metrics

```bash
# View performance metrics
python -m cli.main metrics --category all --period 30d

# Category options: returns, risk, trades, all
# Period options: 7d, 30d, 90d, all

# Generate report
python -m cli.main report --format markdown

# Paper trading status
python -m cli.main paper status
```

### Utility Commands

```bash
# Test if market is open
python -m cli.main market-status

# Send test notification
python -m cli.main notify "Test message"

# View signals
python -m cli.main signals --limit 10

# Health check
python -m cli.main health
```

---

## Automation Features

### When Does the Bot Run?

**Automatic Triggers:**
1. **Time-based:** Every 60 seconds during market hours
2. **Event-based:** On signal generation
3. **Manual:** When you run commands

### What Trades Are Automated?

**In Paper Mode:**
- All signals are "simulated"
- No real money involved
- Tracks hypothetical P&L

**In Live Mode (Manual):**
- Bot alerts you
- You decide to trade
- You place order

**In Live Mode (Auto):**
- Bot generates signal
- Checks risk limits
- Places order automatically
- Manages position
- Exits on stop/target

### Expected Behavior

**Normal Operation:**
```
Every 60 seconds:
  1. Check if market open (9:15 - 15:30 IST)
  2. If open:
     - Fetch data for all symbols
     - Run strategies
     - Generate signals
     - Update positions
  3. If signal generated:
     - Log to signals.md
     - Send notification (if enabled)
     - Auto-trade (if enabled)
```

**Signal to Trade Flow:**
```
Signal Generated (Score: 82)
    ↓
Check Risk Limits (Pass)
    ↓
Check Auto-Trading (Enabled)
    ↓
Place Order (Paper = Simulated, Live = Real)
    ↓
Track Position
    ↓
Monitor for Exit (Stop Loss or Target)
    ↓
Record P&L
    ↓
Update Metrics
```

---

## Monitoring & Logs

### Where to Find Information

**1. Console Output**
Shows real-time status:
```
[09:38:23] Running trading cycle...
✓ Cycle complete: 19/19 successful
[09:38:25] Signal: BUY NSE:RELIANCE-EQ @ 2450.30 (Score: 82.5)
```

**2. Signals File**
Location: `data/signals.md`
Contains all signals with outcomes.

**3. Positions File**
Location: `data/positions.md`
Contains current and past trades.

**4. Log Files**
Location: `logs/`
- `trading.log` - Main trading activity
- `errors.log` - Error messages
- `api.log` - API calls

**5. Reports**
Location: `reports/`
- Daily P&L reports
- Weekly summaries
- Monthly analytics

### Understanding Log Levels

In `config/trading_profile.yml`:
```yaml
advanced:
  log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR
```

**DEBUG:** Everything (very verbose)
**INFO:** Normal operation (recommended)
**WARNING:** Only warnings and errors
**ERROR:** Only errors

### Useful Commands for Monitoring

```bash
# Watch signals in real-time
tail -f data\signals.md

# Check bot is running
python -m cli.main status

# View today's trades
type data\positions.md

# Check for errors
type logs\errors.log

# View metrics
python -m cli.main metrics --category all --period 1d
```

---

## Troubleshooting

### Common Issues & Solutions

#### Issue 1: "ModuleNotFoundError: No module named 'cli.main'"

**Cause:** Running from wrong directory

**Solution:**
```bash
cd C:\TradingBot
python -m cli.main login
```

#### Issue 2: "Error: Could not load configuration"

**Cause:** Config file missing

**Solution:**
```bash
copy config\trading_profile.example.yml config\trading_profile.yml
notepad config\trading_profile.yml
```

#### Issue 3: "Error: Not authenticated"

**Cause:** Token expired or invalid

**Solution:**
```bash
python -m cli.main login
```

#### Issue 4: "Invalid symbol provided"

**Cause:** Wrong symbol format

**Solution:**
Check format: `NSE:SYMBOL-EQ` for stocks, `NSE:INDEX-INDEX` for indices

Examples:
- ✅ `NSE:RELIANCE-EQ`
- ✅ `NSE:NIFTY50-INDEX`
- ❌ `RELIANCE`
- ❌ `NSE:RELIANCE`

#### Issue 5: "No signals generated"

**Possible Causes:**
1. Market closed (9:15-15:30 IST only)
2. Strategy confidence too high
3. No valid patterns in current market
4. Symbol format issues

**Solutions:**
```bash
# 1. Check market status
python -m cli.main market-status

# 2. Lower confidence threshold in config
smart_money:
  confidence_threshold: 0.50  # Lower from 0.70

# 3. Check symbol debug
python scripts\debug_symbols.py

# 4. Manual scan test
python -m cli.main scan --symbol NSE:RELIANCE-EQ
```

#### Issue 6: "Cycle complete: 0/19 successful"

**Cause:** Data fetch failing for all symbols

**Solutions:**
1. Check internet connection
2. Verify Fyers login: `python -m cli.main login`
3. Check API limits in `fyersApi.log`
4. Test single symbol: `python -m cli.main market-data --symbol NSE:NIFTY50-INDEX`

#### Issue 7: Bot stops after running for a while

**Possible Causes:**
1. Daily loss limit hit
2. Max positions reached
3. Error in code
4. Keyboard interrupt

**Check:**
```bash
# View logs
type logs\trading.log

# Check positions
type data\positions.md
```

#### Issue 8: "Connection timeout"

**Cause:** Slow internet or API issues

**Solution:**
Increase timeout in config:
```yaml
advanced:
  timeout: 30  # seconds
```

Or reduce symbols scanned:
```yaml
default_symbols:
  - "NSE:NIFTY50-INDEX"
  - "NSE:RELIANCE-EQ"  # Just 2 symbols for testing
```

### Getting Help

If issues persist:

1. **Check logs:** `logs/trading.log`, `logs/errors.log`
2. **Run debug:** `python scripts/debug_symbols.py`
3. **Check ARCHITECTURE.md** for technical details
4. **Check SKILL.md** for feature documentation

---

## Advanced Topics

### Adding Custom Strategies

1. Create file in `strategies/`
2. Inherit from base strategy class
3. Register in `config/trading_profile.yml`

Example template in `strategies/custom_strategy.py`

### Backtesting

```bash
python -m cli.main backtest --symbol NSE:RELIANCE-EQ --start 2024-01-01 --end 2024-01-31
```

### Custom Indicators

Add to `strategies/indicators.py`:
```python
def my_custom_indicator(df):
    # Your calculation
    return signal
```

### Webhook Integration

For external alerts:
```yaml
notifications:
  webhook_url: "https://your-webhook.com/trading-signals"
```

---

## Best Practices

### Daily Routine

**Before Market (8:30 AM):**
1. Check `python -m cli.main status`
2. If not logged in: `python -m cli.main login`
3. Review overnight news
4. Clear previous day's temporary files

**Market Open (9:15 AM):**
1. Start paper trading: `python -m cli.main start-bot --paper`
2. Monitor first 30 minutes
3. Check for signals

**During Market:**
1. Let bot run
2. Check signals every hour: `type data\signals.md`
3. Monitor positions: `python -m cli.main positions`
4. Watch for alerts

**Market Close (3:30 PM):**
1. Stop bot (Ctrl+C)
2. Generate report: `python -m cli.main metrics --period 1d`
3. Review trades
4. Update trading journal

**After Market:**
1. Analyze performance
2. Adjust strategies if needed
3. Prepare for next day

### Weekly Review

Every weekend:
1. Review all trades in `data/positions.md`
2. Check win rate: `python -m cli.main metrics --period 7d`
3. Adjust risk if needed
4. Backtest new ideas

### Monthly Review

1. Full performance analysis: `python -m cli.main metrics --period 30d`
2. Strategy effectiveness check
3. Capital allocation review
4. Goal setting for next month

---

## Frequently Asked Questions (FAQ)

**Q: Can I run this on Mac/Linux?**
A: Yes, but modify paths (use `/` instead of `\`)

**Q: How much money do I need?**
A: Paper trading = $0. Live trading = minimum ₹10,000 recommended

**Q: Is it safe?**
A: Paper mode is 100% safe. Live mode has risks - use proper position sizing.

**Q: Can I use other brokers?**
A: Currently Fyers only. Other brokers would require API modifications.

**Q: Do I need to keep my computer on?**
A: Yes, for continuous scanning. Or use a VPS/cloud server.

**Q: What if I lose internet?**
A: Bot pauses. Reconnect and restart. No trades = no losses.

**Q: Can I run multiple instances?**
A: Not recommended - will hit API rate limits.

**Q: How do I update the bot?**
A: `git pull` then restart. Check release notes first.

---

## Resources

- **Fyers API Docs:** https://myapi.fyers.in/docs
- **NSE Symbol Search:** https://www.nseindia.com/market-data/equity-derivatives-watch
- **Trading Strategies:** See `modes/` folder
- **Code Examples:** See `scripts/` folder

---

**Happy Trading! 📈**

*Remember: Past performance doesn't guarantee future results. Always trade responsibly.*
