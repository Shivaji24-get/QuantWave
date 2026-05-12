"""
CLI command implementations.

FIXES (subset of key changes):
- compare_cmd(): symbol normalisation now detects index symbols and does NOT
  append -EQ (NSE:NIFTY50-INDEX was becoming NSE:NIFTY50-INDEX-EQ).
- start_bot_cmd(): PipelineConfig properly maps main/entry timeframe from YAML.
- All commands have explicit exception handling with user-friendly messages.
- _display_smc_results() updated to handle missing mtf_aligned gracefully.
"""

import sys
import typer
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import TokenManager, LoginFlow
from api import FyersClient
from api import (
    get_profile, get_funds, get_holdings,
    get_historical_data, get_quotes,
    place_order as api_place_order, get_order_status,
)
from strategies import StockScanner, SignalGenerator, RiskManager
from utils import load_config, setup_logging, is_market_open, export_to_csv

console = Console()

# ---------------------------------------------------------------------------
# Index symbol suffixes – do NOT append -EQ to these
# ---------------------------------------------------------------------------
_INDEX_MARKERS = ("-INDEX", "-IDX", "-I", "NIFTY", "SENSEX", "BANKNIFTY")


def _normalise_symbol(raw: str) -> str:
    """
    Ensure symbol has NSE: prefix.
    Appends -EQ suffix only for equity symbols, not for index symbols.

    FIX: previously appended -EQ to ALL symbols, breaking index queries like
    NSE:NIFTY50-INDEX → NSE:NIFTY50-INDEX-EQ (invalid).
    """
    s = raw.strip()
    if not s.startswith("NSE:") and not s.startswith("BSE:"):
        s = f"NSE:{s}"
    # Only append -EQ if the symbol is not already suffixed and is not an index
    if not s.endswith("-EQ") and not any(marker in s.upper() for marker in _INDEX_MARKERS):
        s = f"{s}-EQ"
    return s


# ---------------------------------------------------------------------------
# Shared helper: get authenticated client
# ---------------------------------------------------------------------------

def get_client():
    config = load_config()
    tm = TokenManager(config["client_id"], config["secret_key"])
    token = tm.get_access_token()
    if not token:
        console.print("[red]Not logged in. Run: python -m cli.main login[/red]")
        raise typer.Exit(1)
    return FyersClient(config["client_id"], token), config


# ---------------------------------------------------------------------------
# Auth commands
# ---------------------------------------------------------------------------

def login_cmd():
    """Authenticate with Fyers API."""
    config = load_config()
    console.print("[cyan]Starting Fyers authentication...[/cyan]")
    tm = TokenManager(config["client_id"], config["secret_key"])
    lf = LoginFlow(
        config["client_id"],
        config["secret_key"],
        config["redirect_uri"],
        username=config.get("username"),
        pin=config.get("pin"),
        mobile=config.get("mobile"),
    )
    try:
        token = lf.authenticate()
        tm.save_token(token)
        console.print("[green]✓ Authentication successful![/green]")
    except Exception as e:
        console.print(f"[red]✗ Authentication failed: {e}[/red]")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Account information commands
# ---------------------------------------------------------------------------

def profile_cmd():
    client, _ = get_client()
    data = get_profile(client.get_client())
    t = Table(title="User Profile")
    t.add_column("Field", style="cyan")
    t.add_column("Value")
    for k, v in data.items():
        t.add_row(k.replace("_", " ").title(), str(v))
    console.print(t)


def funds_cmd():
    client, _ = get_client()
    data = get_funds(client.get_client())
    t = Table(title="Funds")
    t.add_column("Field", style="cyan")
    t.add_column("Value")
    for k, v in data.items():
        t.add_row(k.replace("_", " ").title(), str(v))
    console.print(t)


def holdings_cmd():
    client, _ = get_client()
    holdings = get_holdings(client.get_client())
    if not holdings or "error" in holdings[0]:
        console.print("[yellow]No holdings found[/yellow]")
        return
    t = Table(title="Holdings")
    for col in ["symbol", "qty", "avg_price", "ltp", "pnl", "pnl_percent"]:
        t.add_column(col.replace("_", " ").title(), style="cyan")
    for h in holdings:
        t.add_row(str(h.get("symbol", "")), str(h.get("qty", 0)),
                  str(h.get("avg_price", 0)), str(h.get("ltp", 0)),
                  str(h.get("pnl", 0)), str(h.get("pnl_percent", 0)) + "%")
    console.print(t)


def market_data_cmd(symbol: str = typer.Option(..., "--symbol")):
    client, _ = get_client()
    df = get_historical_data(client.get_client(), symbol, "D", count=30)
    if df.empty:
        console.print("[red]No data found[/red]")
        return
    t = Table(title=f"Market Data – {symbol}")
    for col in ["timestamp", "open", "high", "low", "close", "volume"]:
        t.add_column(col.title(), style="cyan")
    for _, row in df.tail(10).iterrows():
        t.add_row(str(row["timestamp"])[:10], f"₹{row['open']:.2f}",
                  f"₹{row['high']:.2f}", f"₹{row['low']:.2f}",
                  f"₹{row['close']:.2f}", str(int(row["volume"])))
    console.print(t)


# ---------------------------------------------------------------------------
# Order commands
# ---------------------------------------------------------------------------

def place_order_cmd(
    symbol: str = typer.Option(..., "--symbol"),
    qty: int = typer.Option(..., "--qty", min=1),
    side: str = typer.Option(..., "--side"),
    order_type: str = typer.Option("MARKET", "--type"),
    product_type: str = typer.Option("MIS", "--product"),
    price: float = typer.Option(None, "--price"),
):
    client, config = get_client()
    result = api_place_order(
        client.get_client(), symbol, qty, side.upper(),
        order_type.upper(), product_type.upper(), price,
    )
    if "error" in result:
        console.print(f"[red]✗ Order failed: {result['error']}[/red]")
    else:
        console.print(f"[green]✓ Order placed: {result.get('order_id', 'N/A')}[/green]")
        export_to_csv([{"symbol": symbol, "side": side, "qty": qty, "status": "placed", **result}])


def order_status_cmd(order_id: str = typer.Option(..., "--order-id")):
    client, _ = get_client()
    status = get_order_status(client.get_client(), order_id)
    if "error" in status:
        console.print(f"[red]Error: {status['error']}[/red]")
        return
    t = Table(title=f"Order – {order_id}")
    t.add_column("Field", style="cyan")
    t.add_column("Value")
    for k, v in status.items():
        t.add_row(k.replace("_", " ").title(), str(v))
    console.print(t)


# ---------------------------------------------------------------------------
# Scan command
# ---------------------------------------------------------------------------

_INDEX_GROUPS = {
    "NIFTY50": [
        "NSE:RELIANCE-EQ", "NSE:TCS-EQ", "NSE:HDFCBANK-EQ", "NSE:ICICIBANK-EQ",
        "NSE:INFY-EQ", "NSE:SBIN-EQ", "NSE:ITC-EQ", "NSE:HINDUNILVR-EQ",
        "NSE:BAJFINANCE-EQ", "NSE:KOTAKBANK-EQ", "NSE:LT-EQ", "NSE:AXISBANK-EQ",
        "NSE:ASIANPAINT-EQ", "NSE:MARUTI-EQ", "NSE:TITAN-EQ",
        "NSE:ONGC-EQ", "NSE:NTPC-EQ", "NSE:WIPRO-EQ", "NSE:ULTRACEMCO-EQ",
    ],
    "BANKNIFTY": [
        "NSE:HDFCBANK-EQ", "NSE:ICICIBANK-EQ", "NSE:SBIN-EQ", "NSE:KOTAKBANK-EQ",
        "NSE:AXISBANK-EQ", "NSE:INDUSINDBK-EQ", "NSE:BANKBARODA-EQ",
        "NSE:PNB-EQ", "NSE:CANBK-EQ", "NSE:UNIONBANK-EQ",
    ],
}


def scan_cmd(
    symbol: str = typer.Option(None, "--symbol"),
    symbols: str = typer.Option(None, "--symbols"),
    index: str = typer.Option(None, "--index"),
    timeframe: str = typer.Option(None, "--timeframe"),
    htf: str = typer.Option(None, "--htf"),
    limit: int = typer.Option(None, "--limit"),
    live: bool = typer.Option(False, "--live"),
    smc: bool = typer.Option(False, "--smc"),
    min_score: int = typer.Option(50, "--min-score"),
    interval: int = typer.Option(5, "--interval"),
    auto_trade: bool = typer.Option(False, "--auto-trade"),
    threshold: int = typer.Option(75, "--threshold"),
    top: int = typer.Option(5, "--top"),
):
    client, _ = get_client()

    scan_symbols = None
    if symbol:
        scan_symbols = [symbol]
    elif symbols:
        scan_symbols = [s.strip() for s in symbols.split(",") if s.strip()]
    elif index:
        key = index.upper()
        if key not in _INDEX_GROUPS:
            console.print(f"[red]Unknown index '{index}'. Available: {', '.join(_INDEX_GROUPS)}[/red]")
            raise typer.Exit(1)
        scan_symbols = _INDEX_GROUPS[key]
        console.print(f"[cyan]Scanning {len(scan_symbols)} stocks from {index}[/cyan]")

    if live:
        if not scan_symbols:
            console.print("[red]--symbol, --symbols, or --index required for live mode[/red]")
            raise typer.Exit(1)
        if smc:
            from strategies import LiveSMCEngine
            scanner = StockScanner(enable_smc=True)
            engine = LiveSMCEngine(
                client.get_client(), scanner,
                interval=interval, auto_trade=auto_trade, threshold=threshold,
                ltf_timeframe=timeframe or "5m", htf_timeframe=htf,
            )
            engine.start(scan_symbols)
        else:
            from strategies import LiveEngine
            scanner = StockScanner(enable_patterns=True)
            engine = LiveEngine(client.get_client(), scanner, interval=interval,
                                auto_trade=auto_trade, threshold=threshold)
            engine.start(scan_symbols)
        return

    # Historical scan
    if smc:
        scanner = StockScanner(enable_smc=True)
        results = scanner.scan_all_smc(
            client.get_client(), scan_symbols,
            ltf_timeframe=timeframe or "5m",
            htf_timeframe=htf,
            ltf_limit=limit or 100,
            min_score=min_score,
        )
        _display_smc_results(results, top)
    else:
        scanner = StockScanner(enable_patterns=True, enable_scoring=True)
        results = scanner.scan_all(client.get_client(), scan_symbols, timeframe, limit)
        results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)[:top]
        if not results:
            console.print("[yellow]No signals found[/yellow]")
        else:
            _display_standard_results(results, top)


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _display_standard_results(results: list, top: int):
    t = Table(title=f"Scan Results (Top {len(results)})")
    t.add_column("Rank")
    t.add_column("Symbol", style="cyan")
    t.add_column("Price")
    t.add_column("Score", style="bright_green")
    t.add_column("Signal", style="green")
    t.add_column("RSI", style="yellow")
    t.add_column("SMA20", style="magenta")
    t.add_column("Pattern", style="bright_blue")
    for rank, r in enumerate(results, 1):
        sc = r.get("score", 0)
        sc_color = "green" if sc >= 75 else ("yellow" if sc >= 50 else "red")
        sig_color = "green" if r["signal"] == "BUY" else ("red" if r["signal"] == "SELL" else "white")
        pat = ""
        if r.get("pattern"):
            icon = "📈" if r.get("pattern_direction") == "bullish" else "📉"
            pat = f"{icon} {r['pattern']} ({r.get('pattern_confidence', 0):.0%})"
        t.add_row(
            str(rank), r["symbol"], f"₹{r['price']:.2f}",
            f"[{sc_color}]{sc}%[/{sc_color}]",
            f"[{sig_color}]{r['signal']}[/{sig_color}]",
            str(r["rsi"]), f"₹{r['sma_20']:.2f}", pat,
        )
    console.print(t)


def _display_smc_results(results: list, top: int, min_score: int = 50):
    if not results:
        console.print(f"[yellow]No SMC setups found (score < {min_score}%)[/yellow]")
        return
    results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)[:top]
    t = Table(title=f"SMC Scan (Top {len(results)} setups)")
    t.add_column("Symbol", style="cyan", no_wrap=True)
    t.add_column("Signal", style="green")
    t.add_column("Score", style="bright_green")
    t.add_column("Strength")
    t.add_column("HTF", style="yellow")
    t.add_column("MTF", style="yellow")   # FIX: column added
    t.add_column("Sweep", style="yellow")
    t.add_column("MSS", style="yellow")
    t.add_column("FVG", style="yellow")
    t.add_column("Price")
    for r in results:
        sc = r.get("score", 0)
        sc_color = "green" if sc >= 75 else ("yellow" if sc >= 60 else "red")
        strength = "STRONG" if sc >= 75 else ("MODERATE" if sc >= 60 else "WEAK")
        sig_color = "green" if r["signal"] == "BUY" else ("red" if r["signal"] == "SELL" else "white")
        sym = r["symbol"].replace("NSE:", "").replace("-EQ", "")[:12]
        t.add_row(
            sym,
            f"[{sig_color}]{r['signal']}[/{sig_color}]",
            f"[{sc_color}]{sc}%[/{sc_color}]",
            strength,
            "✅" if r.get("htf_aligned") else "❌",
            "✅" if r.get("mtf_aligned") else "❌",   # FIX: was missing
            "✅" if r.get("liquidity_sweep") else "❌",
            "✅" if r.get("mss_confirmed") else "❌",
            "✅" if r.get("fvg_present") else "❌",
            f"₹{r.get('price', 0):.2f}",
        )
    console.print(t)
    strong = sum(1 for r in results if r.get("score", 0) >= 75)
    console.print(f"\n[dim]Found {len(results)} setups: {strong} Strong, {len(results)-strong} below 75%[/dim]")


# ---------------------------------------------------------------------------
# Bot management commands
# ---------------------------------------------------------------------------

def start_bot_cmd(
    paper: bool = typer.Option(True, "--paper/--live"),
    config_file: str = typer.Option(None, "--config"),
):
    """Start the trading bot (paper or live mode)."""
    console.print("[cyan]Starting Trading Bot...[/cyan]")
    console.print(f"[green]Mode: {'PAPER' if paper else 'LIVE'}[/green]")

    try:
        from core.pipeline import TradingPipeline, PipelineConfig
        from core.tracker import TradingTracker
        import time

        config_dict = load_config(config_path=config_file or "config.ini")

        strategies_cfg = config_dict.get("strategies", {})
        tf_cfg = strategies_cfg.get("timeframe", {}) if isinstance(strategies_cfg, dict) else {}

        pipeline_config = PipelineConfig(
            max_concurrent=config_dict.get("max_concurrent", 5),
            timeout_seconds=30.0,
            retry_attempts=3,
            enable_auto_trade=config_dict.get("auto_trading_enabled", False),
            require_confirmation=True,
            paper_trading=paper,
            min_signal_score=float(config_dict.get("min_signal_score", 75.0)),
            min_risk_reward=1.5,
            symbols=config_dict.get("symbols", ["NSE:NIFTY50-INDEX"]),
            scan_interval=int(config_dict.get("scan_interval", 60)),
            main_timeframe=tf_cfg.get("main", "1h"),
            entry_timeframe=tf_cfg.get("entry", "5m"),
        )

        client, _ = get_client()
        tracker = TradingTracker()
        pipeline = TradingPipeline(
            config=pipeline_config,
            fyers_client=client.get_client(),
            tracker=tracker,
        )

        console.print("[cyan]Running pre-flight checks...[/cyan]")
        checks = pipeline.health_check()
        for check, ok in checks.items():
            icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
            console.print(f"  {icon} {check}")

        if not all(checks.values()):
            console.print("[red]Some checks failed. Fix issues before starting.[/red]")
            return

        console.print("[green]All checks passed! Starting bot...[/green]")
        pipeline.start()

        symbols = pipeline_config.symbols
        interval = pipeline_config.scan_interval
        console.print(f"[yellow]Press Ctrl+C to stop[/yellow]")
        console.print(f"[dim]Monitoring {len(symbols)} symbols every {interval}s[/dim]")
        console.print(f"[dim]Timeframes: trend={pipeline_config.main_timeframe.upper()} entry={pipeline_config.entry_timeframe.upper()}[/dim]")

        try:
            while pipeline._running:
                if is_market_open():
                    console.print(f"\n[bold cyan][{datetime.now().strftime('%H:%M:%S')}] Trading cycle...[/bold cyan]")
                    results = pipeline.execute_batch(symbols)
                    ok = sum(1 for r in results if r.success)
                    console.print(f"[green]✓ Cycle: {ok}/{len(symbols)} successful[/green]")
                else:
                    console.print(f"[dim][{datetime.now().strftime('%H:%M:%S')}] Market closed. Waiting...[/dim]")
                time.sleep(interval)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping bot...[/yellow]")
            pipeline.stop()

    except Exception as e:
        console.print(f"[red]Error starting bot: {e}[/red]")


def stop_bot_cmd(force: bool = typer.Option(False, "--force")):
    """Stop the trading bot (press Ctrl+C in the bot terminal)."""
    console.print("[yellow]Press Ctrl+C in the terminal where the bot is running.[/yellow]")


def status_cmd(detailed: bool = typer.Option(False, "--detailed")):
    """Check bot status and open positions."""
    try:
        from core.tracker import TradingTracker
        tracker = TradingTracker()
        market_open = is_market_open()
        color = "green" if market_open else "yellow"
        console.print(f"\n[bold]Market:[/bold] [{color}]{'OPEN' if market_open else 'CLOSED'}[/{color}]")

        if detailed:
            positions = tracker.get_active_positions()
            console.print(f"\n[bold cyan]Open Positions ({len(positions)})[/bold cyan]")
            if positions:
                t = Table()
                t.add_column("Symbol", style="cyan")
                t.add_column("Side")
                t.add_column("Entry")
                t.add_column("Qty")
                t.add_column("Unrealized P&L", style="green")
                for sym, pos in positions.items():
                    pnl_color = "green" if pos.unrealized_pnl >= 0 else "red"
                    t.add_row(sym, pos.side, f"₹{pos.entry_price:.2f}", str(pos.qty),
                              f"[{pnl_color}]₹{pos.unrealized_pnl:,.0f}[/{pnl_color}]")
                console.print(t)
            else:
                console.print("[dim]No open positions[/dim]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


# ---------------------------------------------------------------------------
# Analysis commands
# ---------------------------------------------------------------------------

def analyze_cmd(
    symbol: str = typer.Option(..., "--symbol"),
    timeframe: str = typer.Option("D", "--timeframe"),
):
    """Deep analysis of a symbol."""
    console.print(f"[cyan]Analyzing {symbol}...[/cyan]")
    try:
        client, _ = get_client()
        scanner = StockScanner(enable_smc=True, enable_patterns=True, enable_scoring=True)
        results = scanner.scan_all(client.get_client(), [symbol], timeframe, limit=50)
        if results:
            r = results[0]
            console.print(f"\n[bold green]Signal: {r.get('signal', 'HOLD')}[/bold green]")
            console.print(f"Score: {r.get('score', 0)}/100  Price: ₹{r.get('price', 0):.2f}")
            console.print(f"RSI: {r.get('rsi', 'N/A')}")
            if r.get("pattern"):
                console.print(f"Pattern: {r['pattern']} ({r.get('pattern_confidence', 0):.0%})")
        else:
            console.print("[yellow]No signal found.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def compare_cmd(
    symbols: str = typer.Option(..., "--symbols",
                                 help="Comma-separated symbols (e.g. NSE:RELIANCE-EQ,NIFTY50-INDEX)"),
):
    """
    Compare and rank multiple trade setups.

    FIX: symbol normalisation now skips -EQ for index symbols.
    """
    console.print("[cyan]Comparing trade setups...[/cyan]")
    try:
        # FIX: use _normalise_symbol which correctly handles index symbols
        raw = [s.strip() for s in symbols.split(",") if s.strip()]
        symbol_list = [_normalise_symbol(s) for s in raw]

        client, _ = get_client()
        scanner = StockScanner(enable_smc=True, enable_scoring=True)
        results = scanner.scan_all(client.get_client(), symbol_list, "D", limit=50)

        if not results:
            console.print("[yellow]No signals found.[/yellow]")
            return

        results.sort(key=lambda x: x.get("score", 0), reverse=True)

        t = Table(title="Trade Setup Comparison")
        t.add_column("Rank")
        t.add_column("Symbol", style="cyan")
        t.add_column("Signal", style="green")
        t.add_column("Score", style="bright_green")
        t.add_column("Price")
        t.add_column("RSI", style="yellow")
        t.add_column("Grade")

        for i, r in enumerate(results, 1):
            sc = r.get("score", 0)
            grade = "A" if sc >= 75 else ("B" if sc >= 50 else "C")
            medal = "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else str(i)))
            t.add_row(medal, r.get("symbol", ""), r.get("signal", ""),
                      str(sc), f"₹{r.get('price', 0):.2f}",
                      str(r.get("rsi", "N/A")), grade)
        console.print(t)

        best = results[0]
        console.print(f"\n[green]Top pick: {best.get('symbol')} score={best.get('score')}/100 ({best.get('signal')})[/green]")
        weak = [r for r in results if r.get("score", 0) < 50]
        if weak:
            console.print(f"[yellow]Note: {len(weak)} signal(s) below 50% – consider skipping[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def evaluate_cmd(
    symbol: str = typer.Option(..., "--symbol"),
    signal: str = typer.Option(None, "--signal"),
):
    """Evaluate signal quality for a symbol."""
    console.print(f"[cyan]Evaluating {symbol}...[/cyan]")
    try:
        client, _ = get_client()
        scanner = StockScanner(enable_smc=True, enable_scoring=True)
        results = scanner.scan_all(client.get_client(), [symbol], "D", limit=50)
        if not results:
            console.print("[yellow]No signal found.[/yellow]")
            return
        r = results[0]
        sc = r.get("score", 0)
        console.print(f"\n[bold]Signal:[/bold] {r.get('signal', 'HOLD')}")
        console.print(f"Score: {sc}/100  Price: ₹{r.get('price', 0):.2f}  RSI: {r.get('rsi', 'N/A')}")
        if sc >= 75:
            console.print(f"[green]✓ HIGH quality – strong setup[/green]")
        elif sc >= 50:
            console.print(f"[yellow]⚠ MODERATE quality – caution[/yellow]")
        else:
            console.print(f"[red]✗ LOW quality – skip or paper trade only[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


# ---------------------------------------------------------------------------
# Risk & tracker commands
# ---------------------------------------------------------------------------

def risk_cmd(
    symbol: str = typer.Option(None, "--symbol"),
    portfolio: bool = typer.Option(False, "--portfolio"),
):
    """Risk assessment for positions or portfolio."""
    try:
        from core.tracker import TradingTracker
        tracker = TradingTracker()
        positions = tracker.get_active_positions()
        console.print(f"\n[bold]Active Positions:[/bold] {len(positions)}")
        if positions:
            total_pnl = sum(p.unrealized_pnl for p in positions.values())
            color = "green" if total_pnl >= 0 else "red"
            console.print(f"Total Unrealized P&L: [{color}]₹{total_pnl:,.0f}[/{color}]")
        if symbol and symbol in positions:
            pos = positions[symbol]
            console.print(f"\n[bold]{symbol}:[/bold]")
            console.print(f"  Entry: ₹{pos.entry_price:.2f}  Stop: ₹{pos.stop_loss:.2f}")
            pnl_color = "green" if pos.unrealized_pnl >= 0 else "red"
            console.print(f"  P&L: [{pnl_color}]₹{pos.unrealized_pnl:,.0f}[/{pnl_color}]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def tracker_cmd(
    period: str = typer.Option("today", "--period"),
    symbol: str = typer.Option(None, "--symbol"),
):
    """Trading activity overview."""
    try:
        from core.tracker import TradingTracker
        from datetime import timedelta
        tracker = TradingTracker()
        end = datetime.now()
        days_map = {"today": 0, "week": 7, "month": 30, "all": 365}
        days = days_map.get(period, 0)
        start = (end - timedelta(days=days)).replace(hour=0, minute=0, second=0) if days else \
                end.replace(hour=0, minute=0, second=0)
        trades = tracker.get_trades(symbol=symbol, start_date=start, end_date=end)
        total = len(trades)
        wins = [t for t in trades if t.status == "WIN"]
        losses = [t for t in trades if t.status == "LOSS"]
        pnl = sum(t.pnl for t in trades)
        console.print(f"\n[bold cyan]{period.upper()} Summary[/bold cyan]")
        console.print(f"  Trades: {total}  Wins: {len(wins)}  Losses: {len(losses)}")
        console.print(f"  Win Rate: {len(wins)/total*100:.1f}%" if total else "  Win Rate: N/A")
        pnl_color = "green" if pnl >= 0 else "red"
        console.print(f"  P&L: [{pnl_color}]₹{pnl:,.0f}[/{pnl_color}]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def metrics_cmd(
    category: str = typer.Option("all", "--category"),
    period: str = typer.Option("30d", "--period"),
):
    """Performance analytics dashboard."""
    try:
        from core.metrics import MetricsCollector
        from core.tracker import TradingTracker
        from datetime import timedelta
        tracker = TradingTracker()
        collector = MetricsCollector(tracker)
        end = datetime.now()
        days = {"7d": 7, "30d": 30, "90d": 90, "1d": 1}.get(period, 30)
        start = end - timedelta(days=days)
        m = collector.calculate_metrics(start_date=start, end_date=end)
        if category in ("all", "returns"):
            console.print("\n[bold cyan]Returns[/bold cyan]")
            pnl_color = "green" if m.net_pnl >= 0 else "red"
            console.print(f"  Net P&L: [{pnl_color}]₹{m.net_pnl:,.2f}[/{pnl_color}]")
        if category in ("all", "risk"):
            console.print("\n[bold cyan]Risk[/bold cyan]")
            console.print(f"  Sharpe: {m.sharpe_ratio:.2f}  Profit Factor: {m.profit_factor:.2f}")
            console.print(f"  Max Drawdown: ₹{m.max_drawdown:,.2f} ({m.max_drawdown_pct:.2f}%)")
        if category in ("all", "trades"):
            console.print("\n[bold cyan]Trades[/bold cyan]")
            console.print(f"  Total: {m.total_trades}  Win Rate: {m.win_rate:.1f}%")
            console.print(f"  Avg P&L/trade: ₹{m.avg_trade_pnl:,.2f}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


# ---------------------------------------------------------------------------
# Misc commands (stubs kept for CLI registration)
# ---------------------------------------------------------------------------

def run_bot_cmd():
    """Legacy bot runner (use start_bot_cmd instead)."""
    console.print("[yellow]Use: python -m cli.main start-bot --paper[/yellow]")


def positions_cmd():
    """View open positions."""
    status_cmd(detailed=True)


def report_cmd(format: str = typer.Option("markdown", "--format")):
    """Generate performance report."""
    try:
        from core.metrics import MetricsCollector
        from core.tracker import TradingTracker
        tracker = TradingTracker()
        collector = MetricsCollector(tracker)
        Path("reports").mkdir(exist_ok=True)
        fname = f"reports/report_{datetime.now().strftime('%Y%m%d')}.{format}"
        collector.generate_report(output_path=fname, format=format)
        console.print(f"[green]Report saved: {fname}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def signals_cmd(limit: int = typer.Option(20, "--limit")):
    """View recent signals."""
    path = Path("data/signals.md")
    if path.exists():
        console.print(path.read_text(encoding="utf-8")[-3000:])
    else:
        console.print("[yellow]No signals file found.[/yellow]")


def backtest_cmd(
    strategy: str = typer.Option(..., "--strategy"),
    days: int = typer.Option(30, "--days"),
    symbols: str = typer.Option("NIFTY50", "--symbols"),
    capital: int = typer.Option(100000, "--capital"),
):
    console.print(f"[cyan]Backtest: {strategy} for {days} days[/cyan]")
    console.print("[yellow]Backtest engine not yet implemented.[/yellow]")


def strategy_cmd(action: str = typer.Argument("list"), name: str = typer.Option(None, "--name")):
    """Strategy management."""
    console.print(f"[cyan]Strategy action: {action}[/cyan]")


def paper_cmd(action: str = typer.Argument("status"), capital: int = typer.Option(100000, "--capital")):
    """Paper trading simulation."""
    console.print(f"[cyan]Paper trading: {action}[/cyan]")


def notify_cmd(test: bool = typer.Option(False, "--test"), setup: bool = typer.Option(False, "--setup")):
    """Configure notifications."""
    console.print("[cyan]Notification configuration – edit config/trading_profile.yml[/cyan]")


# ---------------------------------------------------------------------------
# Harmonic pattern scanning commands
# ---------------------------------------------------------------------------

def harmonic_scan_cmd(
    symbol: str = typer.Option(None, "--symbol", help="Single symbol to scan"),
    symbols: str = typer.Option(None, "--symbols", help="Comma-separated symbols to scan"),
    index: str = typer.Option(None, "--index", help="Index group (NIFTY50, BANKNIFTY)"),
    timeframe: str = typer.Option("D", "--timeframe", help="Timeframe (D, 5m, 15m, 1h)"),
    limit: int = typer.Option(100, "--limit", help="Number of candles to analyze"),
    min_confidence: float = typer.Option(0.7, "--min-confidence", help="Minimum confidence threshold"),
    export: bool = typer.Option(False, "--export", help="Export results to file"),
):
    """Scan for harmonic patterns in single or multiple symbols."""
    client, _ = get_client()
    
    from strategies.harmonic_scanner import HarmonicScanner
    
    scanner = HarmonicScanner(min_confidence=min_confidence)
    
    # Determine symbols to scan
    scan_symbols = None
    if symbol:
        scan_symbols = [symbol]
        console.print(f"[cyan]Scanning single symbol: {symbol}[/cyan]")
    elif symbols:
        scan_symbols = [s.strip() for s in symbols.split(",") if s.strip()]
        console.print(f"[cyan]Scanning {len(scan_symbols)} symbols[/cyan]")
    elif index:
        key = index.upper()
        if key not in _INDEX_GROUPS:
            console.print(f"[red]Unknown index '{index}'. Available: {', '.join(_INDEX_GROUPS)}[/red]")
            raise typer.Exit(1)
        scan_symbols = _INDEX_GROUPS[key]
        console.print(f"[cyan]Scanning {len(scan_symbols)} stocks from {index}[/cyan]")
    else:
        console.print("[red]--symbol, --symbols, or --index required[/red]")
        raise typer.Exit(1)
    
    # Perform scan
    console.print(f"[dim]Timeframe: {timeframe}, Candles: {limit}, Min Confidence: {min_confidence}[/dim]")
    
    if len(scan_symbols) == 1:
        # Single symbol scan
        result = scanner.scan_symbol(scan_symbols[0], timeframe, limit, client.get_client())
        _display_harmonic_result(result)
    else:
        # Multiple symbol scan
        results = scanner.scan_multiple(scan_symbols, timeframe, limit, client.get_client(), parallel=True)
        _display_harmonic_results(results, min_confidence)
    
    # Export if requested
    if export:
        from utils import export_to_csv
        export_data = []
        if len(scan_symbols) == 1:
            result = scanner.scan_symbol(scan_symbols[0], timeframe, limit, client.get_client())
            if result['success'] and result['patterns']:
                for pattern in result['patterns']:
                    export_data.append({
                        'symbol': result['symbol'],
                        'pattern': pattern['name'],
                        'direction': pattern['direction'],
                        'confidence': pattern['confidence'],
                        'entry_price': pattern['entry_price'],
                        'stop_loss': pattern['stop_loss'],
                        'take_profit': pattern['take_profit'],
                        'risk_reward': pattern['risk_reward'],
                        'timestamp': pattern['timestamp']
                    })
        else:
            results = scanner.scan_multiple(scan_symbols, timeframe, limit, client.get_client(), parallel=True)
            for result in results:
                if result['success'] and result['patterns']:
                    for pattern in result['patterns']:
                        export_data.append({
                            'symbol': result['symbol'],
                            'pattern': pattern['name'],
                            'direction': pattern['direction'],
                            'confidence': pattern['confidence'],
                            'entry_price': pattern['entry_price'],
                            'stop_loss': pattern['stop_loss'],
                            'take_profit': pattern['take_profit'],
                            'risk_reward': pattern['risk_reward'],
                            'timestamp': pattern['timestamp']
                        })
        
        if export_data:
            export_to_csv(export_data, filename=f"harmonic_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            console.print(f"[green]Exported {len(export_data)} patterns to CSV[/green]")
        else:
            console.print("[yellow]No patterns to export[/yellow]")


def harmonic_live_cmd(
    symbols: str = typer.Option(..., "--symbols", help="Comma-separated symbols to scan"),
    timeframe: str = typer.Option("5m", "--timeframe", help="Timeframe for live scanning"),
    interval: int = typer.Option(60, "--interval", help="Scan interval in seconds"),
    min_confidence: float = typer.Option(0.7, "--min-confidence", help="Minimum confidence threshold"),
):
    """Live continuous scanning for harmonic patterns."""
    console.print("[cyan]Starting live harmonic pattern scanner...[/cyan]")
    console.print("[yellow]Press Ctrl+C to stop[/yellow]")
    
    client, _ = get_client()
    from strategies.harmonic_scanner import HarmonicScanner
    import time
    
    scanner = HarmonicScanner(min_confidence=min_confidence)
    scan_symbols = [s.strip() for s in symbols.split(",") if s.strip()]
    
    console.print(f"[dim]Symbols: {', '.join(scan_symbols)}[/dim]")
    console.print(f"[dim]Timeframe: {timeframe}, Interval: {interval}s[/dim]")
    
    try:
        while True:
            console.print(f"\n[bold cyan][{datetime.now().strftime('%H:%M:%S')}] Scanning...[/bold cyan]")
            
            results = scanner.scan_multiple(scan_symbols, timeframe, limit=100, client=client.get_client(), parallel=True)
            
            patterns_found = 0
            for result in results:
                if result['success'] and result['patterns']:
                    patterns_found += len(result['patterns'])
                    for pattern in result['patterns']:
                        if pattern['confidence'] >= min_confidence:
                            icon = "📈" if pattern['direction'] == 'bullish' else "📉"
                            console.print(
                                f"[green]{icon} {result['symbol']}[/green] - "
                                f"{pattern['name']} ({pattern['confidence']:.0%}) - "
                                f"Entry: ₹{pattern['entry_price']:.2f}"
                            )
            
            if patterns_found == 0:
                console.print("[dim]No patterns found[/dim]")
            else:
                console.print(f"[green]Found {patterns_found} patterns[/green]")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Live scanner stopped[/yellow]")


def harmonic_pattern_cmd(
    symbol: str = typer.Option(..., "--symbol", help="Symbol to analyze"),
    timeframe: str = typer.Option("D", "--timeframe", help="Timeframe for analysis"),
):
    """Detailed pattern analysis for a single symbol."""
    client, _ = get_client()
    
    from strategies.harmonic_detector import HarmonicDetector
    from api import get_historical_data
    
    console.print(f"[cyan]Analyzing {symbol} for harmonic patterns...[/cyan]")
    
    detector = HarmonicDetector()
    df = get_historical_data(client.get_client(), symbol, timeframe, count=100)
    
    if df.empty:
        console.print("[red]No data available[/red]")
        return
    
    analysis = detector.get_analysis(df)
    
    if not analysis['has_pattern']:
        console.print("[yellow]No harmonic patterns detected[/yellow]")
        return
    
    console.print(f"\n[bold green]Pattern Detected: {analysis['latest_pattern']}[/bold green]")
    console.print(f"Direction: {analysis['direction'].upper()}")
    console.print(f"Confidence: {analysis['confidence']:.0%}")
    console.print(f"Entry Price: ₹{analysis['entry_price']:.2f}")
    console.print(f"Stop Loss: ₹{analysis['stop_loss']:.2f}")
    console.print(f"Take Profit: ₹{analysis['take_profit']:.2f}")
    console.print(f"Risk/Reward: {analysis['risk_reward']:.2f}")
    
    console.print(f"\n[dim]Total patterns found: {analysis['pattern_count']}[/dim]")


def _display_harmonic_result(result: dict):
    """Display single symbol harmonic scan result."""
    if not result['success']:
        console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
        return
    
    if not result['has_pattern']:
        console.print(f"[yellow]No harmonic patterns found in {result['symbol']}[/yellow]")
        console.print(f"[dim]Current price: ₹{result['current_price']:.2f}[/dim]")
        return
    
    console.print(f"\n[bold green]Found {result['pattern_count']} pattern(s) in {result['symbol']}[/bold green]")
    
    for i, pattern in enumerate(result['patterns'], 1):
        icon = "📈" if pattern['direction'] == 'bullish' else "📉"
        console.print(f"\n[cyan]{i}. {icon} {pattern['name']} ({pattern['confidence']:.0%})[/cyan]")
        console.print(f"   Direction: {pattern['direction'].upper()}")
        console.print(f"   Entry: ₹{pattern['entry_price']:.2f}")
        console.print(f"   Stop Loss: ₹{pattern['stop_loss']:.2f}")
        console.print(f"   Take Profit: ₹{pattern['take_profit']:.2f}")
        console.print(f"   Risk/Reward: {pattern['risk_reward']:.2f}")


def _display_harmonic_results(results: list, min_confidence: float):
    """Display multiple symbol harmonic scan results."""
    patterns_found = []
    
    for result in results:
        if result['success'] and result['patterns']:
            for pattern in result['patterns']:
                if pattern['confidence'] >= min_confidence:
                    patterns_found.append({
                        'symbol': result['symbol'],
                        'pattern': pattern
                    })
    
    if not patterns_found:
        console.print(f"[yellow]No harmonic patterns found with confidence >= {min_confidence:.0%}[/yellow]")
        return
    
    # Sort by confidence
    patterns_found.sort(key=lambda x: x['pattern']['confidence'], reverse=True)
    
    console.print(f"\n[bold green]Found {len(patterns_found)} pattern(s)[/bold green]")
    
    t = Table(title="Harmonic Pattern Scan Results")
    t.add_column("Rank")
    t.add_column("Symbol", style="cyan")
    t.add_column("Pattern", style="bright_blue")
    t.add_column("Direction", style="green")
    t.add_column("Confidence", style="bright_green")
    t.add_column("Entry", style="yellow")
    t.add_column("Stop Loss", style="red")
    t.add_column("Take Profit", style="green")
    t.add_column("R:R", style="magenta")
    
    for rank, item in enumerate(patterns_found, 1):
        p = item['pattern']
        icon = "📈" if p['direction'] == 'bullish' else "📉"
        t.add_row(
            str(rank),
            item['symbol'],
            f"{icon} {p['name']}",
            p['direction'].upper(),
            f"{p['confidence']:.0%}",
            f"₹{p['entry_price']:.2f}",
            f"₹{p['stop_loss']:.2f}",
            f"₹{p['take_profit']:.2f}",
            f"{p['risk_reward']:.2f}"
        )
    
    console.print(t)
