import os
import json
import requests
import time
import fcntl
from typing import Optional
from datetime import datetime
from app.core import storage

DYNAMIC_TICKERS_FILE = os.path.join(storage.TICKERS_DIR, "dynamic.json")


def validate_ticker_via_yahoo(symbol: str, max_retries: int = 3) -> tuple[bool, Optional[dict]]:
    """
    Validate ticker via Yahoo Finance search API with retry mechanism.
    Returns (is_valid, ticker_info)
    """
    symbol = symbol.upper().strip()

    for attempt in range(max_retries):
        try:
            url = "https://query2.finance.yahoo.com/v1/finance/search"
            params = {
                'q': symbol,
                'quotes_count': 5,
                'news_count': 0
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                quotes = data.get('quotes', [])

                for quote in quotes:
                    if quote.get('symbol', '').upper() == symbol:
                        info = {
                            'symbol': symbol,
                            'name': quote.get('longname') or quote.get('shortname') or symbol,
                            'exchange': quote.get('exchange', 'UNKNOWN'),
                            'type': quote.get('quoteType', 'EQUITY').lower()
                        }
                        return True, info

                # Symbol not found in results
                return False, None
            else:
                print(f"Yahoo Finance API returned status code {response.status_code} for symbol {symbol}: {response.reason}")
                # For client errors (4xx), don't retry - ticker doesn't exist
                if 400 <= response.status_code < 500:
                    return False, None
                # For server errors (5xx), retry with backoff
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # exponential backoff
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                return False, None

        except requests.exceptions.Timeout:
            print(f"Timeout occurred while validating ticker {symbol}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            return False, None
        except Exception as e:
            print(f"Error validating ticker {symbol}: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            return False, None

    return False, None


def load_dynamic_tickers() -> dict:
    """Load dynamically added tickers from dynamic.json"""
    if not os.path.exists(DYNAMIC_TICKERS_FILE):
        return {}

    try:
        with open(DYNAMIC_TICKERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {t['symbol']: t for t in data.get('tickers', [])}
    except Exception as e:
        print(f"Error loading dynamic tickers: {e}")
        return {}


def add_to_dynamic_list(symbol: str, info: dict) -> bool:
    """
    Add validated ticker to dynamic.json for future use.
    Uses file locking and atomic writes to prevent race conditions and data corruption.
    """
    try:
        os.makedirs(os.path.dirname(DYNAMIC_TICKERS_FILE), exist_ok=True)
        
        # Use the data file itself for locking to ensure proper synchronization
        lock_file = DYNAMIC_TICKERS_FILE + '.lock'
        
        # Create lock file if it doesn't exist
        with open(lock_file, 'a'):
            pass
            
        with open(lock_file, 'r+') as lock_fd:
            # Acquire exclusive lock (blocks until available)
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
            
            try:
                tickers_dict = load_dynamic_tickers()

                tickers_dict[symbol] = {
                    'symbol': info['symbol'],
                    'name': info['name'],
                    'exchange': info['exchange'],
                    'type': info['type']
                }

                data = {
                    'comment': 'Dynamically added tickers validated by users',
                    'last_updated': datetime.now().isoformat(),
                    'count': len(tickers_dict),
                    'tickers': list(tickers_dict.values())
                }

                # Write to temporary file first, then atomically rename
                temp_file = DYNAMIC_TICKERS_FILE + '.tmp'
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # Atomic rename (on POSIX systems, this is atomic)
                os.replace(temp_file, DYNAMIC_TICKERS_FILE)

                print(f"Added ticker {symbol} to dynamic list")
                return True
            finally:
                # Release lock
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)

    except Exception as e:
        print(f"Error adding ticker {symbol} to dynamic list: {e}")
        return False


if __name__ == "__main__":
    test_symbols = ['AAPL', '2330.TW', 'INVALID123']

    for symbol in test_symbols:
        print(f"\nTesting {symbol}...")
        valid, info = validate_ticker_via_yahoo(symbol)

        if valid:
            print(f"  Valid: {info}")
            add_to_dynamic_list(symbol, info)
        else:
            print(f"  Invalid")
