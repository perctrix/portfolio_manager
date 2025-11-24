import os
import json
import requests
from typing import Optional
from datetime import datetime
from app.core import storage

DYNAMIC_TICKERS_FILE = os.path.join(storage.TICKERS_DIR, "dynamic.json")


def validate_ticker_via_yahoo(symbol: str) -> tuple[bool, Optional[dict]]:
    """
    Validate ticker via Yahoo Finance search API.
    Returns (is_valid, ticker_info)
    """
    symbol = symbol.upper().strip()

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
                        'name': quote.get('longname') or quote.get('shortname', ''),
                        'exchange': quote.get('exchange', 'UNKNOWN'),
                        'type': quote.get('quoteType', 'EQUITY').lower()
                    }
                    return True, info

        return False, None

    except Exception as e:
        print(f"Error validating ticker {symbol}: {e}")
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
    """
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

        os.makedirs(os.path.dirname(DYNAMIC_TICKERS_FILE), exist_ok=True)
        with open(DYNAMIC_TICKERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Added ticker {symbol} to dynamic list")
        return True

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
