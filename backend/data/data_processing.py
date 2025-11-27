import logging

import numpy as np
import pandas as pd
import talib as ta
import yfinance as yf
from scipy.fft import fft, fftfreq, ifft
from tqdm import tqdm

logger: logging.Logger = logging.getLogger(__name__)

def rolling_normalize(series, window=21):
    """
    Apply rolling window normalization to a time series
    
    Parameters:
    series (pd.Series): Input time series
    window (int): Size of rolling window
    
    Returns:
    pd.Series: Normalized series
    """
    rolling_mean = series.rolling(window=window, min_periods=1).mean()
    rolling_std = series.rolling(window=window, min_periods=1).std()
    
    # Add small constant to avoid division by zero
    eps = 1e-8
    normalized = (series - rolling_mean) / (rolling_std + eps)
    
    # Forward fill NaN values at the beginning
    normalized = normalized.ffill()
    # Backward fill any remaining NaN values
    normalized = normalized.bfill()
    
    return normalized

def calculate_connors_rsi(data, rsi_period=3, streak_period=2, rank_period=100):
    """Calculate Connors RSI"""
    # Component 1: Regular RSI on price changes
    price_rsi = pd.Series(ta.RSI(data['Close'].values, timeperiod=rsi_period), index=data.index)
    
    # Component 2: Streak RSI
    daily_returns = data['Close'].diff()
    streak = pd.Series(0.0, index=data.index)
    streak_count = 0.0
    
    for i in range(1, len(data)):
        if daily_returns.iloc[i] > 0:
            if streak_count < 0:
                streak_count = 1.0
            else:
                streak_count += 1.0
        elif daily_returns.iloc[i] < 0:
            if streak_count > 0:
                streak_count = -1.0
            else:
                streak_count -= 1.0
        else:
            streak_count = 0.0
        streak.iloc[i] = streak_count
    
    streak_values = streak.values.astype(np.float64)
    streak_rsi = pd.Series(ta.RSI(streak_values, timeperiod=streak_period), index=data.index)
    
    # Component 3: Percentage Rank (ROC)
    def percent_rank(series, period):
        return series.rolling(period).apply(
            lambda x: pd.Series(x).rank().iloc[-1] / float(period) * 100,
            raw=True
        )
    
    pct_rank = percent_rank(data['Close'], rank_period)
    
    # Combine components with equal weighting
    crsi = (price_rsi + streak_rsi + pct_rank) / 3.0
    return crsi

def apply_kalman_filter(data, measurement_noise=0.1, process_noise=0.01):
    """Apply Kalman filter to price series"""
    prices = data['Close'].values
    state = np.array([prices[0], 0])
    P = np.array([[1, 0], [0, 1]])
    
    F = np.array([[1, 1], [0, 1]])
    H = np.array([[1, 0]])
    Q = np.array([[process_noise/10, 0], [0, process_noise]])
    R = np.array([[measurement_noise]])
    
    filtered_prices = []
    trends = []
    
    for price in prices:
        # Predict
        state = np.dot(F, state)
        P = np.dot(np.dot(F, P), F.T) + Q
        
        # Update
        y = price - np.dot(H, state)
        S = np.dot(np.dot(H, P), H.T) + R
        K = np.dot(np.dot(P, H.T), np.linalg.inv(S))
        
        state = state + np.dot(K, y)
        P = P - np.dot(np.dot(K, H), P)
        
        filtered_prices.append(state[0])
        trends.append(state[1])
    
    return pd.Series(filtered_prices, index=data.index), pd.Series(trends, index=data.index)

def apply_fft_filter_rolling(data, cutoff_period, window_size=252):
    """
    Apply FFT filtering with a rolling window approach to avoid look-ahead bias
    
    Parameters:
    data (pd.DataFrame/Series): DataFrame with stock data or price Series
    cutoff_period (int): The cutoff period for the low-pass filter
    window_size (int): Size of the rolling window to use
    
    Returns:
    pd.Series: Series of filtered prices with the same index as input data
    """
    # Get the price series (handle both DataFrame and Series inputs)
    if isinstance(data, pd.DataFrame) and 'Close' in data.columns:
        prices = data['Close'].values.astype(np.float64)
        index = data.index
    else:
        prices = data.values.astype(np.float64) if isinstance(data, pd.Series) else np.array(data, dtype=np.float64)
        index = data.index if isinstance(data, pd.Series) else None
    
    n = len(prices)
    filtered_prices = np.zeros(n)
    
    # For the first few points where we don't have enough history,
    # just use the original prices
    min_window = max(cutoff_period * 3, 20)  # Ensure enough data for FFT
    for i in range(min(min_window, n)):
        filtered_prices[i] = prices[i]
    
    # Process each point using only historical data
    for i in range(min_window, n):
        # Define the historical window (current point and earlier)
        start_idx = max(0, i - window_size + 1)
        window_data = prices[start_idx:i+1]
        window_len = len(window_data)
        
        # Detrend the window data to reduce edge effects
        # Only use data within the window for the trend
        trend = np.linspace(window_data[0], window_data[-1], window_len)
        detrended = window_data - trend
        
        # Perform FFT on the window
        fft_result = fft(detrended)
        freqs = fftfreq(window_len, d=1)
        
        # Create low-pass filter
        filter_threshold = 1/cutoff_period
        filter_mask = np.abs(freqs) < filter_threshold
        fft_result_filtered = fft_result * filter_mask
        
        # Inverse FFT and add trend back
        filtered_detrended = np.real(ifft(fft_result_filtered))
        filtered_window = filtered_detrended + trend
        
        # Only use the last value (current time point)
        filtered_prices[i] = filtered_window[-1]
    
    # Return as a pandas Series with the original index
    if index is not None:
        return pd.Series(filtered_prices, index=index)
    else:
        return filtered_prices

def download_and_prepare_data(symbol: str, start_date: str, end_date: str, 
                              window=21, *, interval: str = '1d'):
    """
    Download and prepare stock data with rolling window normalization
    
    Parameters:
    symbol (str): Stock symbol
    start_date (str): Start date
    end_date (str): End date
    window (int): Size of rolling window for normalization
    """
    # Download stock data
    stock = yf.download(symbol, start=start_date, end=end_date, interval=interval, progress=False)

    if isinstance(stock.columns, pd.MultiIndex):
        stock = stock.xs(symbol, level=1, axis=1) if symbol in stock.columns.levels[1] else stock
    
    # Ensure we have data
    if stock.empty:
        raise ValueError(f"No data downloaded for {symbol}")
    
    # Convert price columns to float64
    price_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    stock = stock.astype({col: np.float64 for col in price_columns})
    
    # Create a copy to avoid SettingWithCopyWarning
    stock = stock.copy()
    
    # Calculate basic technical indicators
    stock['MA5'] = ta.SMA(stock['Close'].values, timeperiod=5)
    stock['MA20'] = ta.SMA(stock['Close'].values, timeperiod=20)
    stock['MACD'], stock['MACD_Signal'], stock['MACD_Hist'] = ta.MACD(stock['Close'].values)
    stock['RSI'] = ta.RSI(stock['Close'].values)
    stock['Upper'], stock['Middle'], stock['Lower'] = ta.BBANDS(stock['Close'].values)
    stock['Volume_MA5'] = ta.SMA(stock['Volume'].values, timeperiod=5)
    
    # Add Connors RSI
    stock['CRSI'] = calculate_connors_rsi(stock)
    
    # Add Kalman Filter estimates
    stock['Kalman_Price'], stock['Kalman_Trend'] = apply_kalman_filter(stock)
    
    # Add FFT filtered prices
    stock['FFT_21'] = apply_fft_filter_rolling(stock, 21)
    stock['FFT_63'] = apply_fft_filter_rolling(stock, 63)
    
    # Forward fill any NaN values from indicators
    stock = stock.ffill()
    
    # Backward fill any remaining NaN values at the beginning
    stock = stock.bfill()
    
    # Apply rolling window normalization to all columns
    columns_to_normalize = [
        'Open', 'High', 'Low', 'Close', 'Volume',
        'MA5', 'MA20', 'MACD', 'MACD_Signal', 'MACD_Hist',
        'RSI', 'Upper', 'Middle', 'Lower', 'Volume_MA5',
        'CRSI', 'Kalman_Price', 'Kalman_Trend',
        'FFT_21', 'FFT_63'
    ]
    
    for col in columns_to_normalize:
        if col in stock.columns:
            stock[col] = rolling_normalize(stock[col], window=window)
    
    return stock

def load_data_from_csv(file_path):
    data = pd.read_csv(file_path)

    # Support both 'Date' (daily) and 'Datetime' (hourly) column names
    if 'Datetime' in data.columns:
        data['Datetime'] = pd.to_datetime(data['Datetime'])
        data.set_index('Datetime', inplace=True)
    elif 'Date' in data.columns:
        data['Date'] = pd.to_datetime(data['Date'])
        data.set_index('Date', inplace=True)
    else:
        raise ValueError("CSV file must contain either 'Date' or 'Datetime' column")

    return data

if __name__ == "__main__":
    # Test code with error handling
    symbols = [# 科技股
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD", "INTC", "CRM", 
    "ADBE", "NFLX", "CSCO", "ORCL", "QCOM", "IBM", "AMAT", "MU", "NOW", "SNOW", "AVGO",
    
    # 金融股
    "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "AXP", "V", "MA",
    "COF", "USB", "PNC", "SCHW", "BK", "TFC", "AIG", "MET", "PRU", "ALL", "ICE", "MCO",
    
    # 医疗保健
    "JNJ", "UNH", "PFE", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY", "LLY",
    "AMGN", "GILD", "ISRG", "CVS", "CI", "HUM", "BIIB", "VRTX", "REGN", "ZTS",
    
    # 消费品
    "PG", "KO", "PEP", "WMT", "HD", "MCD", "NKE", "SBUX", "TGT", "LOW",
    "COST", "DIS", "CMCSA", "VZ", "T", "CL", "EL", "KMB", "GIS", "K", "PDD", "GOTU",
    
    # 工业
    "BA", "GE", "MMM", "CAT", "HON", "UPS", "LMT", "RTX", "DE", "EMR",
    "FDX", "NSC", "UNP", "WM", "ETN", "PH", "ROK", "CMI", "IR", "GD",
    
    # 能源
    "XOM", "CVX", "COP", "EOG", "SLB", "MPC", "PSX", "VLO", "OXY",
    "KMI", "WMB", "EP", "HAL", "DVN", "HES", "MRO", "APA", "FANG", "BKR",
    
    # 材料
    "LIN", "APD", "ECL", "SHW", "FCX", "NEM", "NUE", "VMC", "MLM", "DOW",
    "DD", "PPG", "ALB", "EMN", "CE", "CF", "MOS", "IFF", "FMC", "SEE",
    
    # 房地产
    "AMT", "PLD", "CCI", "EQIX", "PSA", "DLR", "O", "WELL", "AVB", "EQR",
    "SPG", "VTR", "BXP", "ARE", "MAA", "UDR", "HST", "KIM", "REG", "ESS",
    
    # 中概股
    "BABA", "JD", "PDD", "BIDU", "NIO", "XPEV", "LI", "TME", "BILI", "IQ",
    
    # ETF
    "SPY", "QQQ", "DIA", "IWM", "VOO", "IVV", "ARKK", "XLF", "XLK", "XLE", 
    "VNQ", "TLT", "HYG", "EEM", "GDX", "VTI", "IEMG", "XLY", "XLP", "USO",

    # 指数
    "^GSPC", "^NDX", "^DJI", "^RUT", "^VIX", 
    "^IXIC", "^HSI", "000001.SS", "^GDAXI", "^FTSE",
    ]
    # symbols = [
    #     "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD", "INTC", "CRM", 
    #     "^GSPC", "^NDX", "^DJI", "^IXIC",
    #     "UNH", "ABBV","LLY",
    #     "FANG", "DLR", "PSA", "BABA", "JD", "BIDU",
    #     "QQQ"
    # ]
    try:
        for ticker in tqdm(symbols):
            data = download_and_prepare_data(ticker, '2024-01-01', '2025-10-01', interval='1h')
            print(data.head())
            data.to_csv(f'data_hours\{ticker}.csv', index=True)
        
    except Exception as e:
        logger.error("Error occurred: %s", e)