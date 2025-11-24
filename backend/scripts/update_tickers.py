import os
import sys
import json
import requests
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.core import storage


def download_nasdaq_tickers() -> list[dict]:
    """
    Download ticker list from NASDAQ FTP.
    Returns list of ticker dicts.
    """
    tickers = []

    nasdaq_url = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
    try:
        print(f"Downloading NASDAQ-listed securities...")
        response = requests.get(nasdaq_url, timeout=30)

        if response.status_code == 200:
            lines = response.text.strip().split('\n')

            for line in lines[1:]:
                if not line or line.startswith('File Creation Time'):
                    continue

                fields = line.split('|')
                if len(fields) >= 2:
                    symbol = fields[0].strip()
                    name = fields[1].strip()

                    if symbol and symbol != 'Symbol':
                        tickers.append({
                            'symbol': symbol,
                            'name': name,
                            'exchange': 'NASDAQ',
                            'type': 'stock'
                        })

            print(f"  Downloaded {len(tickers)} NASDAQ tickers")

    except Exception as e:
        print(f"Error downloading NASDAQ tickers: {e}")

    other_url = "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt"
    try:
        print(f"Downloading other exchange securities...")
        response = requests.get(other_url, timeout=30)

        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            other_count = 0

            for line in lines[1:]:
                if not line or line.startswith('File Creation Time'):
                    continue

                fields = line.split('|')
                if len(fields) >= 3:
                    symbol = fields[0].strip()
                    name = fields[1].strip()
                    exchange = fields[2].strip()
                    etf = fields[4].strip() if len(fields) > 4 else 'N'

                    if symbol and symbol != 'ACT Symbol':
                        tickers.append({
                            'symbol': symbol,
                            'name': name,
                            'exchange': exchange,
                            'type': 'etf' if etf == 'Y' else 'stock'
                        })
                        other_count += 1

            print(f"  Downloaded {other_count} other exchange tickers")

    except Exception as e:
        print(f"Error downloading other exchange tickers: {e}")

    return tickers


def load_json_tickers_from_folder(folder_path: str) -> list[dict]:
    """
    Load all ticker JSON files from a folder.
    Returns combined list of ticker dicts.
    """
    all_tickers = []

    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} does not exist")
        return all_tickers

    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]

    for json_file in json_files:
        file_path = os.path.join(folder_path, json_file)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            tickers = data.get('tickers', [])
            all_tickers.extend(tickers)
            print(f"Loaded {len(tickers)} tickers from {json_file}")

        except Exception as e:
            print(f"Error loading {json_file}: {e}")

    return all_tickers


def merge_and_deduplicate(ticker_lists: list[list[dict]]) -> list[dict]:
    """
    Merge multiple ticker lists and remove duplicates.
    Priority: later lists override earlier lists for the same symbol.
    """
    ticker_dict = {}

    for ticker_list in ticker_lists:
        for ticker in ticker_list:
            symbol = ticker.get('symbol')
            if symbol:
                ticker_dict[symbol] = ticker

    return list(ticker_dict.values())


def save_to_frontend(tickers: list[dict], output_path: str) -> bool:
    """
    Save merged ticker list to frontend public data folder.
    """
    try:
        data = {
            'metadata': {
                'last_updated': datetime.now().isoformat(),
                'count': len(tickers),
                'sources': ['nasdaq', 'manual', 'dynamic']
            },
            'tickers': sorted(tickers, key=lambda x: x['symbol'])
        }

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\nSuccessfully saved {len(tickers)} tickers to {output_path}")
        return True

    except Exception as e:
        print(f"Error saving tickers to frontend: {e}")
        return False


def main():
    """
    Main function to update ticker list.
    """
    print("=" * 60)
    print("Ticker List Update Script")
    print("=" * 60)

    nasdaq_tickers = download_nasdaq_tickers()

    tickers_folder = os.path.join(os.path.dirname(__file__), '..', storage.TICKERS_DIR)
    local_tickers = load_json_tickers_from_folder(tickers_folder)

    print(f"\nMerging ticker lists...")
    print(f"  NASDAQ: {len(nasdaq_tickers)} tickers")
    print(f"  Local JSON files: {len(local_tickers)} tickers")

    all_tickers = merge_and_deduplicate([nasdaq_tickers, local_tickers])

    print(f"  Total after deduplication: {len(all_tickers)} tickers")

    frontend_data_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'frontend', 'public', 'data', 'tickers.json'
    )

    success = save_to_frontend(all_tickers, frontend_data_path)

    print("=" * 60)
    if success:
        print("Ticker list update completed successfully!")
    else:
        print("Ticker list update failed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
