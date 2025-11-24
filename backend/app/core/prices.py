import yfinance as yf
import pandas as pd
import numpy as np
import os
import talib as ta
from app.core import storage
from app.core.indicators import (
    calculate_connors_rsi, 
    apply_kalman_filter, 
    apply_fft_filter_rolling, 
    rolling_normalize
)

def fetch_price_data(symbol: str, start_date: str = '2020-01-01', interval: str = '1d') -> pd.DataFrame:
    """
    Download and prepare stock data.
    """
    # Download stock data
    # Note: yfinance might return MultiIndex if multiple tickers, but here we fetch one.
    stock = yf.download(symbol, start=start_date, interval=interval, progress=False)
    
    if isinstance(stock.columns, pd.MultiIndex):
        # Handle case where yf returns MultiIndex even for single ticker
        try:
            stock = stock.xs(symbol, level=1, axis=1)
        except KeyError:
            pass # Might not be MultiIndex in some versions or if structure differs

    if stock.empty:
        # Try fetching without start date (max history) if empty
        stock = yf.download(symbol, period="max", interval=interval, progress=False)
        if stock.empty:
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
            stock['MA5'] = ta.SMA(stock['Close'].values, timeperiod=5)
            stock['MA20'] = ta.SMA(stock['Close'].values, timeperiod=20)
            stock['MACD'], stock['MACD_Signal'], stock['MACD_Hist'] = ta.MACD(stock['Close'].values)
            stock['RSI'] = ta.RSI(stock['Close'].values)
            stock['Upper'], stock['Middle'], stock['Lower'] = ta.BBANDS(stock['Close'].values)
            
            if 'Volume' in stock.columns:
                stock['Volume_MA5'] = ta.SMA(stock['Volume'].values, timeperiod=5)
            
            stock['CRSI'] = calculate_connors_rsi(stock)
            stock['Kalman_Price'], stock['Kalman_Trend'] = apply_kalman_filter(stock)
            stock['FFT_21'] = apply_fft_filter_rolling(stock, 21)
            stock['FFT_63'] = apply_fft_filter_rolling(stock, 63)
            
            # Normalization (optional, maybe not for storage but for analysis? 
            # User script did it. We will store raw + indicators. 
            # Normalization might be better done on the fly or stored in separate columns if needed.
            # For now, let's keep the user's logic of adding normalized columns? 
            # Actually, user script REPLACED columns with normalized versions in `download_and_prepare_data`?
            # Wait, user script: `stock[col] = rolling_normalize(stock[col]...)`
            # If we normalize the PRICES, we lose the actual price levels for NAV calculation!
            # CRITICAL: We must NOT normalize the Close price if we want to calculate NAV.
            # User's script seemed to be for ML/Analysis where normalization is key.
            # For a Portfolio Manager, we need ABSOLUTE prices.
            # I will SKIP normalization for the stored CSV, or store it in separate columns.
            # I will store the absolute values because NAV depends on them.
        except Exception as e:
            print(f"Warning: Failed to calculate some indicators for {symbol}: {e}")

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
    return df
