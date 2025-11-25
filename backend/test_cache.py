import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core import prices
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')

def test_cache_system():
    """Test the cache system with existing CSV files"""
    print("=" * 60)
    print("Testing Cache System")
    print("=" * 60)

    test_symbols = ['AAPL', 'GOOG', 'NVDA']

    for symbol in test_symbols:
        print(f"\nTesting {symbol}...")
        print("-" * 40)

        try:
            df = prices.get_price_history(symbol)

            if not df.empty:
                print(f"  Success: Retrieved {len(df)} rows")
                print(f"  Date range: {df.index.min()} to {df.index.max()}")
                print(f"  Columns: {list(df.columns)}")
            else:
                print(f"  No data found for {symbol}")

        except Exception as e:
            print(f"  Error: {e}")

    print("\n" + "=" * 60)
    print("Checking metadata file...")
    print("=" * 60)

    metadata_file = os.path.join(prices.storage.PRICES_DIR, "metadata.json")
    if os.path.exists(metadata_file):
        print(f"  Metadata file exists: {metadata_file}")
        with open(metadata_file, 'r') as f:
            import json
            metadata = json.load(f)
            print(f"  Version: {metadata.get('version')}")
            print(f"  Last modified: {metadata.get('last_modified')}")
            print(f"  Tickers: {len(metadata.get('tickers', {}))}")
            for ticker, info in metadata.get('tickers', {}).items():
                print(f"    {ticker}: {info.get('row_count')} rows, last_updated={info.get('last_updated')}")
    else:
        print(f"  Metadata file not found")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_cache_system()
