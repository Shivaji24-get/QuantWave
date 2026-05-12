# 📅 Daily Trading Routine - Structured Workflow

**Your complete day-by-day guide to using QuantWave**

---

## 🌅 MORNING ROUTINE (Before Market Opens)

### 8:00 AM - 8:30 AM: Pre-Market Preparation

```bash
# 1. Open terminal and navigate to project
cd C:\QuantWave

# 2. Check if bot is ready
python -m cli.main status
```

**Expected Output:**
```
✓ Config loaded
✓ Fyers API: Connected
✓ Token: Valid
```

**If NOT logged in:**
```bash
python -m cli.main login
# Browser will open - login with Fyers credentials
```

---

### 8:30 AM - 9:00 AM: Configuration Check

**Review overnight changes:**
```bash
# Check previous day's performance
type data\positions.md

# Check if any signals overnight
type data\signals.md

# Clear old logs if needed
del logs\quantwave.log
```

**Verify settings in `config/trading_profile.yml`:**
- [ ] Symbols are correct (add/remove if needed)
- [ ] Risk limits appropriate for today
- [ ] Strategies enabled/disabled as planned

---

### 9:00 AM - 9:15 AM: Final Checks

```bash
# Test market status
python -m cli.main market-status

# Test one symbol
python -m cli.main scan --symbol NSE:NIFTY50-INDEX

# Check system health
python -m cli.main health
```

**Green checklist before starting:**
- [ ] Market will open in 15 minutes
- [ ] API connection working
- [ ] At least 1 symbol test successful
- [ ] Configuration is correct

---

## 🏁 MARKET OPEN (9:15 AM)

### 9:15 AM: Start Paper Trading

```bash
# START THE BOT (Paper Mode = Safe)
python -m cli.main start-bot --paper
```

**You should see:**
```
Starting Trading Bot...
Mode: PAPER
✓ All checks passed! Starting bot...
Monitoring 19 symbols: NSE:NIFTY50-INDEX, NSE:RELIANCE-EQ, ...
Timeframes: Main=1H, Entry=5M
Scan interval: 60 seconds
Press Ctrl+C to stop

[09:15:23] Running trading cycle...
✓ Cycle complete: 19/19 successful
```

### 9:15 AM - 9:45 AM: First 30 Minutes (Watch Mode)

**DO NOT trade first 30 minutes!** Market is volatile.

**What to do:**
```bash
# In another terminal window, watch signals:
type data\signals.md

# Every 5 minutes, check:
python -m cli.main metrics --period 1d
```

**Watch for:**
- Are all symbols showing "successful"?
- Any errors in the console?
- Signals being generated?

---

## 📊 ACTIVE TRADING HOURS (9:45 AM - 3:15 PM)

### Continuous Monitoring

**The bot is running automatically now.** Your job is to monitor.

**Every 15-30 minutes, check:**

```bash
# 1. View latest signals
type data\signals.md

# 2. Check current positions
type data\positions.md

# 3. Check performance
python -m cli.main metrics --category all --period 1d

# 4. Check positions visually
python -m cli.main positions
```

### Signal Decision Tree

When you see a signal in `data/signals.md`:

```
Signal: BUY NSE:RELIANCE-EQ | Score: 82 | Price: 2450.30
```

**Decision process:**

```
Is Score >= 75?
  ├─ NO → Ignore, wait for better signal
  └─ YES → Continue
       ↓
Is it paper trading?
  ├─ YES → Bot already "traded" it, check outcome
  └─ NO (Live) → Continue
       ↓
Do you want to take this trade?
  ├─ NO → Do nothing
  └─ YES → Place order manually
       ↓
  python -m cli.main place-order --symbol NSE:RELIANCE-EQ --qty 10 --side BUY
```

### Hourly Tasks (Every Hour on the Hour)

| Time | Task | Command |
|------|------|---------|
| 10:00 AM | Check morning performance | `python -m cli.main metrics --period 1d` |
| 11:00 AM | Review signals generated | `type data\signals.md` |
| 12:00 PM | Mid-day health check | `python -m cli.main health` |
| 1:00 PM | Post-lunch check | `type data\positions.md` |
| 2:00 PM | Afternoon review | `python -m cli.main metrics` |
| 3:00 PM | Pre-close check | Check all positions |

### Lunch Break (12:00 PM - 1:00 PM)

**Bot continues running!** Just check quickly:
```bash
# Quick 2-minute check
type data\signals.md
python -m cli.main positions
```

---

## 🛑 MARKET CLOSE (3:30 PM)

### 3:30 PM: Stop the Bot

```bash
# Press Ctrl+C in the bot terminal
# Or run:
python -m cli.main stop-bot
```

**Expected output:**
```
Stopping bot gracefully...
Bot stopped. All positions saved.
```

### 3:30 PM - 4:00 PM: End-of-Day Analysis

```bash
# 1. Generate daily report
python -m cli.main report --format markdown

# 2. View final metrics
python -m cli.main metrics --category all --period 1d

# 3. Check all positions
type data\positions.md

# 4. View signals summary
type data\signals.md
```

**Calculate manually:**
- How many signals generated today?
- How many were correct (if known)?
- What was the win rate?
- Any issues/errors?

### 4:00 PM - 5:00 PM: Journaling & Planning

**Fill in your trading journal:**

```markdown
## Trading Journal - [DATE]

### Market Conditions
- NIFTY Trend: Up/Down/Sideways
- Volatility: High/Medium/Low
- News affecting market: [Any major news]

### Bot Performance
- Symbols monitored: 19
- Signals generated: X
- Trades taken: X
- Win rate: X%
- P&L: +₹X / -₹X

### What Worked
- [Strategy that performed well]
- [Good decisions made]

### What Didn't Work
- [Strategy that failed]
- [Mistakes made]

### Changes for Tomorrow
- [ ] Adjust confidence threshold
- [ ] Add/remove symbols
- [ ] Change risk settings
```

---

## 📋 DAILY CHECKLIST

### Morning (Before 9:15 AM)
- [ ] Terminal opened
- [ ] Navigated to C:\QuantWave
- [ ] Status checked (`python -m cli.main status`)
- [ ] Logged in (if needed)
- [ ] Configuration reviewed
- [ ] Market status confirmed
- [ ] Symbol test passed

### Trading Hours (9:15 AM - 3:30 PM)
- [ ] Bot started in paper mode
- [ ] First 30 minutes watched
- [ ] No major errors in console
- [ ] Signals generated
- [ ] Positions tracked
- [ ] 15-30 minute checks done
- [ ] Lunch break covered

### Evening (After 3:30 PM)
- [ ] Bot stopped (Ctrl+C)
- [ ] Daily report generated
- [ ] Metrics reviewed
- [ ] Positions closed/tracked
- [ ] Journal updated
- [ ] Tomorrow planned

---

## 🆘 TROUBLESHOOTING DURING THE DAY

### Issue: "Cycle complete: 0/19 successful"

**Fix immediately:**
```bash
# 1. Check internet
ping google.com

# 2. Check Fyers login
python -m cli.main login

# 3. Restart bot
python -m cli.main start-bot --paper
```

### Issue: "Not authenticated"

**Fix:**
```bash
python -m cli.main login
# Then restart bot
```

### Issue: Bot stops unexpectedly

**Check:**
```bash
# View error logs
type logs\errors.log

# Check if daily loss limit hit
# Check if max positions reached
```

### Issue: No signals for hours

**Possible reasons:**
1. Market is sideways (normal)
2. Confidence threshold too high
3. Strategies too strict

**Lower threshold temporarily:**
```bash
# Edit config
notepad config\trading_profile.yml
# Change: confidence_threshold: 0.60 → 0.50

# Restart bot
```

---

## 📊 WEEKLY ROUTINE

### Every Weekend (Saturday/Sunday)

```bash
# 1. Weekly performance report
python -m cli.main metrics --period 7d

# 2. Review all signals
type data\signals.md

# 3. Clean old files
del logs\*.log.old

# 4. Backup data
copy data\signals.md backup\signals_[date].md
```

### Weekly Review Questions

1. **Performance:** What was my win rate this week?
2. **Strategy:** Which strategy worked best?
3. **Risk:** Did I follow my risk rules?
4. **Emotions:** Did I panic or get greedy?
5. **Improvement:** What will I do differently next week?

---

## 🎯 SAMPLE DAY TIMELINE

```
08:00 - Wake up, coffee
08:15 - Check market news
08:30 - Start computer, open terminal
08:35 - Run: python -m cli.main status
08:40 - Review config, check symbols
08:50 - Test: python -m cli.main scan --symbol NSE:NIFTY50-INDEX
09:10 - Final checks, get ready
09:15 - MARKET OPENS
09:15 - Start bot: python -m cli.main start-bot --paper
09:15-09:45 - Watch first 30 min (NO trading)
10:00 - Check: type data\signals.md
10:30 - Check: python -m cli.main metrics
11:00 - Mid-morning check
12:00 - Lunch break check
13:00 - Post-lunch check
14:00 - Afternoon review
15:00 - Pre-close positions check
15:30 - MARKET CLOSES
15:30 - Stop bot (Ctrl+C)
15:35 - Generate report
15:45 - Review day's performance
16:00 - Update trading journal
16:30 - Done! Review tomorrow's plan
```

---

## 💡 PRO TIPS

### Do's ✅
- Start with paper trading for at least 2 weeks
- Check bot every 15-30 minutes
- Keep a trading journal
- Review performance daily
- Have a backup plan (what if bot fails?)
- Stay calm during market volatility

### Don'ts ❌
- Don't enable auto-trading immediately
- Don't leave bot unattended for hours initially
- Don't risk more than 2% per trade
- Don't trade first 30 minutes (9:15-9:45 AM)
- Don't chase losses
- Don't ignore errors in console

---

## 🔧 AUTOMATION IDEAS

Once you're comfortable:

### Schedule Daily Start
Create `start_trading.bat`:
```batch
@echo off
cd C:\QuantWave
python -m cli.main start-bot --paper
```

Double-click at 9:15 AM to start.

### Quick Check Commands
Create aliases for frequently used commands:
```bash
doskey qs=type data\signals.md
doskey qp=type data\positions.md
doskey pm=python -m cli.main metrics --period 1d
```

---

## 📞 EMERGENCY CONTACTS

**If something goes wrong:**

1. **Immediate stop:** Ctrl+C in bot terminal
2. **Check logs:** `type logs\errors.log`
3. **Check positions:** `type data\positions.md`
4. **Manual override:** Place orders via Fyers web/app

---

## ✅ SUCCESS METRICS

After 30 days of following this routine, you should have:
- [ ] 30 days of trading data
- [ ] Understanding of your win rate
- [ ] Knowledge of which strategies work
- [ ] Confidence to go live (if ready)
- [ ] Complete trading journal

---

**Remember: Consistency > Perfection**

Follow this routine daily. Some days will be profitable, some won't. What matters is following the process.

**Happy Trading! 📈**
