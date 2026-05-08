# 🚀 TradingBot - Quick Start Guide

**Get your trading bot running in 5 minutes!**

---

## 📋 What This Bot Does

TradingBot scans Indian stock markets (NSE) and automatically:
1. **Analyzes** stocks using technical indicators (RSI, patterns, volume)
2. **Generates** BUY/SELL signals with confidence scores
3. **Tracks** all trades and positions
4. **Executes** orders (in paper mode = fake money, safe for testing)

---

## ⚡ 5-Minute Setup

### Step 1: Install Requirements
```bash
pip install -r requirements.txt
```

### Step 2: Get Fyers API Access
1. Go to [Fyers API](https://myapi.fyers.in/) and create an app
2. Note your **Client ID** (looks like `XXXXXXX-100`)
3. Note your **Secret Key**
4. Set redirect URI to: `http://127.0.0.1:5000/fyers/callback`

### Step 3: Configure the Bot
```bash
# Copy example config
copy config\trading_profile.example.yml config\trading_profile.yml

# Edit with your credentials
notepad config\trading_profile.yml
```

**Find these lines and fill in your details:**
```yaml
api:
  fyers:
    client_id: "YOUR_CLIENT_ID-100"      # ← Replace this
    secret_key: "YOUR_SECRET_KEY"       # ← Replace this
    redirect_uri: "http://127.0.0.1:5000/fyers/callback"
```

### Step 4: Login to Fyers
```bash
python -m cli.main login
```
- This opens a browser
- Login with your Fyers credentials
- The token will be saved automatically

### Step 5: Start Paper Trading (Safe Mode)
```bash
python -m cli.main start-bot --paper
```

**You should see:**
```
Starting Trading Bot...
Mode: PAPER ✓ (Fake money - safe to test)
Monitoring 19 symbols: NSE:NIFTY50-INDEX, NSE:RELIANCE-EQ, ...
Timeframes: Main=1H, Entry=5M
Press Ctrl+C to stop

[09:38:23] Running trading cycle...
✓ Cycle complete: 19/19 successful
```

---

## 🎯 Common Commands

| Command | What It Does |
|---------|--------------|
| `python -m cli.main login` | Connect to Fyers API |
| `python -m cli.main start-bot --paper` | Start paper trading (safe) |
| `python -m cli.main start-bot` | Start LIVE trading ⚠️ Real money! |
| `python -m cli.main scan` | Scan all stocks once |
| `python -m cli.main status` | Check bot health |
| `python -m cli.main metrics` | View performance stats |
| `python -m cli.main positions` | See open trades |
| `python -m cli.main place-order --symbol NSE:RELIANCE-EQ --qty 10 --side BUY` | Place manual order |

---

## 📊 Understanding Output

### What "Cycle Complete" Means
```
✓ Cycle complete: 19/19 successful
```
- The bot checked 19 stocks
- Successfully fetched data for all 19
- No errors occurred

### Where Are My Signals?
Check the signals file:
```bash
type data\signals.md
```

If empty, the market conditions don't match your strategy yet.

### Viewing Trades
```bash
type data\positions.md
```

---

## ⚙️ Configuration Explained

### Key Settings in `config/trading_profile.yml`

```yaml
# Symbols to monitor (add/remove stocks here)
default_symbols:
  - "NSE:NIFTY50-INDEX"
  - "NSE:RELIANCE-EQ"

# Trading mode (keep as MIS for intraday)
trading_mode: "MIS"

# Scan every 60 seconds
scanning:
  interval_seconds: 60

# Risk settings
risk_profile:
  risk_per_trade: 0.02        # Risk 2% of capital per trade
  max_positions: 5            # Max 5 open trades
  default_stop_loss_pct: 2.0  # 2% stop loss

# Strategy settings
strategies:
  enabled:
    - "smart_money"          # SMC strategy
    - "order_block"          # Order block detection
  smart_money:
    confidence_threshold: 0.60  # 60% confidence needed
```

---

## 🆘 Troubleshooting

### "Error: Could not load configuration"
**Fix:** Make sure `config/trading_profile.yml` exists
```bash
copy config\trading_profile.example.yml config\trading_profile.yml
```

### "Error: Not authenticated"
**Fix:** Login again
```bash
python -m cli.main login
```

### "No module named 'cli.main'"
**Fix:** Run from project root directory
```bash
cd C:\TradingBot
python -m cli.main login
```

### "Invalid symbol provided"
**Fix:** Check symbol format. Should be:
- Indices: `NSE:NIFTY50-INDEX`, `NSE:NIFTYBANK-INDEX`
- Stocks: `NSE:RELIANCE-EQ`, `NSE:TCS-EQ`

### Bot runs but no signals
**Possible reasons:**
1. Market is closed (9:15 AM - 3:30 PM IST only)
2. Strategy confidence too high (lower in config)
3. No valid patterns detected (normal in sideways markets)

---

## 🔄 Daily Workflow

### Morning (Before Market Opens)
```bash
# 1. Check if logged in
python -m cli.main status

# 2. If not logged in, login
python -m cli.main login

# 3. Start paper trading to test
python -m cli.main start-bot --paper
```

### During Market Hours
```bash
# Let bot run in background
# Check signals periodically
type data\signals.md

# Check positions
type data\positions.md
```

### Evening (After Market Closes)
```bash
# Stop bot (Ctrl+C if running)

# View daily report
python -m cli.main metrics --category all --period 1d
```

---

## 🎓 Learning Path

### Week 1: Paper Trading
- Run bot in `--paper` mode
- Watch signals but don't trade
- Understand the patterns

### Week 2: Manual Trading
- Use bot for signals only
- Manually place orders via Fyers app
- Compare bot signals with your analysis

### Week 3: Auto Trading (Optional)
- Enable auto_trading in config
- Start with small quantities
- Monitor closely

---

## 📞 Need Help?

1. Check `logs/` folder for error details
2. Review this guide again
3. Check ARCHITECTURE.md for technical details
4. Check SKILL.md for feature documentation

---

## ⚠️ Important Safety Notes

1. **Always start with `--paper`** mode first
2. **Never** enable auto_trading until you understand the signals
3. **Test** with 1-2 stocks before adding more
4. **Monitor** the bot - don't leave it unattended for days
5. **Have stop losses** - the bot uses them but you should too

---

## ✅ Next Steps

After this guide:
1. [ ] Run `python -m cli.main login`
2. [ ] Run `python -m cli.main start-bot --paper`
3. [ ] Watch it for 30 minutes
4. [ ] Check `data/signals.md`
5. [ ] Read `USAGE_GUIDE.md` for advanced features

**Happy Trading! 📈**
