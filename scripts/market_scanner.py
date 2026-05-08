"""
After-market automated scanner script.
Performs 3-tier MTF analysis and generates daily reports.
"""
import os
import sys
import logging
from datetime import datetime
from typing import List, Dict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import TokenManager
from api import FyersClient
from strategies.scanner import StockScanner
from utils import load_config
from utils.notifications import NotificationManager
from core.tracker import TradingTracker

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_client():
    config = load_config()
    tm = TokenManager(config["client_id"], config["secret_key"])
    token = tm.get_access_token()
    if not token:
        logger.error("Not logged in. Please run 'python -m cli.main login' first.")
        sys.exit(1)
    return FyersClient(config["client_id"], token).get_client(), config

def generate_report(results: List[Dict], date_str: str) -> str:
    """Generate markdown report from scan results."""
    report = f"# Market Scan Report - {date_str}\n\n"
    report += f"Total Symbols Scanned: {len(results)}\n"
    report += f"High-Probability Setups: {len([r for r in results if r['score'] >= 75])}\n\n"
    
    report += "| Symbol | Signal | Score | HTF | MTF | Patterns | Price |\n"
    report += "|---|---|---|---|---|---|---|\n"
    
    for r in results:
        htf = "✓" if r['htf_aligned'] else "✗"
        mtf = "✓" if r['mtf_aligned'] else "✗"
        patterns = r.get('pattern', 'None')
        report += f"| {r['symbol']} | {r['signal']} | {r['score']}% | {htf} | {mtf} | {patterns} | ₹{r['price']:.2f} |\n"
        
    return report

def main():
    logger.info("Starting After-Market Scan...")
    
    # Initialize components
    try:
        fyers_client, config = get_client()
    except Exception as e:
        logger.error(f"Failed to initialize Fyers client: {e}")
        sys.exit(1)
        
    symbols = config.get("symbols", ["NSE:RELIANCE-EQ", "NSE:TCS-EQ", "NSE:INFY-EQ"])
    
    scanner = StockScanner(enable_smc=True)
    notifier = NotificationManager(config)
    tracker = TradingTracker()
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Perform 3-tier scan
    results = scanner.scan_all_smc(
        fyers_client, 
        symbols=symbols,
        ltf_timeframe="5m",
        mtf_timeframe="15m",
        htf_timeframe="1h",
        min_score=60
    )
    
    if not results:
        logger.info("No high-probability setups found today.")
        notifier.notify("After-market scan complete. No high-probability setups found.")
        return

    # Generate and save report
    report_content = generate_report(results, date_str)
    report_path = f"reports/scan_report_{date_str}.md"
    os.makedirs("reports", exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    logger.info(f"Report generated: {report_path}")
    
    # Send notification summary
    top_setups = [r for r in results if r['score'] >= 75]
    summary = f"🚀 After-market scan complete for {date_str}.\n"
    summary += f"Found {len(results)} potential setups, {len(top_setups)} are STRONG.\n\n"
    for s in top_setups[:5]:
        summary += f"• {s['symbol']}: {s['signal']} (Score: {s['score']}%)\n"
    
    summary += f"\nDetailed report: {report_path}"
    notifier.notify(summary)
    
    # Log signals to tracker
    for r in results:
        tracker.add_signal(
            symbol=r['symbol'],
            signal=r['signal'],
            score=r['score'],
            price=r['price'],
            patterns=[r.get('pattern')] if r.get('pattern') else []
        )

if __name__ == "__main__":
    main()
