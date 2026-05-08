"""
Test each symbol individually to identify which ones fail.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import get_historical_data
from auth import TokenManager
from api import FyersClient
from utils import load_config

def test_all_symbols():
    config = load_config()
    symbols = config.get("symbols", [])
    
    print(f"Testing {len(symbols)} symbols...\n")
    
    # Get client
    tm = TokenManager(config["client_id"], config["secret_key"])
    token = tm.get_access_token()
    
    if not token:
        print("Not logged in. Run: python -m cli.main login")
        return
    
    client = FyersClient(config["client_id"], token).get_client()
    
    failed_symbols = []
    passed_symbols = []
    
    for symbol in symbols:
        try:
            df = get_historical_data(client, symbol, "D", count=5)
            if not df.empty:
                print(f"✓ {symbol} - OK ({len(df)} candles)")
                passed_symbols.append(symbol)
            else:
                print(f"✗ {symbol} - Empty data")
                failed_symbols.append(symbol)
        except Exception as e:
            print(f"✗ {symbol} - ERROR: {str(e)[:50]}")
            failed_symbols.append(symbol)
    
    print(f"\n{'='*60}")
    print(f"PASSED: {len(passed_symbols)}/{len(symbols)}")
    print(f"FAILED: {len(failed_symbols)}/{len(symbols)}")
    
    if failed_symbols:
        print(f"\nFailed symbols:")
        for s in failed_symbols:
            print(f"  - {s}")
            # Try to suggest fix
            if "NIFTY50" in s and "-INDEX" in s:
                print(f"    → Try: NSE:NIFTY50 (without -INDEX)")
            elif "NIFTYBANK" in s and "-INDEX" in s:
                print(f"    → Try: NSE:NIFTYBANK (without -INDEX)")
            elif "-EQ" not in s and "NIFTY" not in s:
                print(f"    → Try: {s}-EQ (add -EQ suffix)")

if __name__ == "__main__":
    test_all_symbols()
