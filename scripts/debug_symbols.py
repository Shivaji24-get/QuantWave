import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from api import get_historical_data
from auth import TokenManager
from api import FyersClient
from utils import load_config

def test_symbols():
    config = load_config()
    tm = TokenManager(config["client_id"], config["secret_key"])
    token = tm.get_access_token()
    
    if not token:
        print("Not logged in.")
        return
        
    client = FyersClient(config["client_id"], token).get_client()
    symbols = config.get("symbols", [])
    
    print(f"Testing {len(symbols)} symbols...")
    for symbol in symbols:
        try:
            df = get_historical_data(client, symbol, "D", count=1)
            if not df.empty:
                print(f"[OK] {symbol}")
            else:
                print(f"[FAIL] {symbol} (Empty data)")
        except Exception as e:
            print(f"[ERROR] {symbol}: {e}")

if __name__ == "__main__":
    test_symbols()
