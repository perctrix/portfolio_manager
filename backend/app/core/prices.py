import pandas as pd
import numpy as np
import os
import sys
from app.core import storage
from app.core.indicators.technical import calculate_technical_indicators_batch

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from data.fetch_data import get_historical_close

def fetch_price_data(symbol: str, start_date: str = '2020-01-01', interval: str = '1d') -> pd.DataFrame:
    """
    Download and prepare stock data.
    """
    stock = get_historical_close(symbol, start_date=start_date, interval=interval)

    if stock is None or (isinstance(stock, pd.DataFrame) and stock.empty):
        raise ValueError(f"No data found for {symbol}")

    # Ensure columns exist and are float
    price_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    # Filter only existing columns
    existing_cols = [c for c in price_columns if c in stock.columns]
    stock = stock[existing_cols].copy()
    
    for col in existing_cols:
        stock[col] = stock[col].astype(np.float64)

    # Calculate indicators (enrichment)
    # We only calculate if we have enough data
    if len(stock) > 20:
        try:
            stock = calculate_technical_indicators_batch(stock)
        except Exception as e:
            print(f"Warning: Failed to calculate indicators for {symbol}: {e}")

    return stock

def update_price_cache(symbol: str):
    """Fetch data and save to CSV"""
    try:
        df = fetch_price_data(symbol)
        file_path = os.path.join(storage.PRICES_DIR, f"{symbol}.csv")
        df.to_csv(file_path)
        return True
    except Exception as e:
        print(f"Error updating {symbol}: {e}")
        return False

def get_price_history(symbol: str) -> pd.DataFrame:
    """Load price history from CSV"""
    file_path = os.path.join(storage.PRICES_DIR, f"{symbol}.csv")
    if not os.path.exists(file_path):
        # Try to fetch if not exists
        if not update_price_cache(symbol):
            return pd.DataFrame()

    df = pd.read_csv(file_path, index_col=0, parse_dates=True)
    if not df.empty and hasattr(df.index, 'normalize'):
        df.index = df.index.normalize()
    return df
