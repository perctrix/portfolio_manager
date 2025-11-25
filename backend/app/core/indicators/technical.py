import pandas as pd
import numpy as np
import talib as ta
from typing import Tuple
from scipy.fft import fft, ifft, fftfreq

def calculate_sma(close: np.ndarray, period: int) -> np.ndarray:
    """Calculate Simple Moving Average"""
    return ta.SMA(close, timeperiod=period)

def calculate_ema(close: np.ndarray, period: int) -> np.ndarray:
    """Calculate Exponential Moving Average"""
    return ta.EMA(close, timeperiod=period)

def calculate_wma(close: np.ndarray, period: int) -> np.ndarray:
    """Calculate Weighted Moving Average"""
    return ta.WMA(close, timeperiod=period)

def calculate_macd(close: np.ndarray, fastperiod: int = 12, slowperiod: int = 26, signalperiod: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate MACD (Moving Average Convergence Divergence)

    Returns:
        macd, signal, histogram
    """
    return ta.MACD(close, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)

def calculate_bollinger_bands(close: np.ndarray, period: int = 20, nbdevup: int = 2, nbdevdn: int = 2) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Bollinger Bands

    Returns:
        upper, middle, lower
    """
    return ta.BBANDS(close, timeperiod=period, nbdevup=nbdevup, nbdevdn=nbdevdn)

def calculate_donchian_channel(high: np.ndarray, low: np.ndarray, period: int = 20) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Donchian Channel

    Returns:
        upper, middle, lower
    """
    upper = ta.MAX(high, timeperiod=period)
    lower = ta.MIN(low, timeperiod=period)
    middle = (upper + lower) / 2.0
    return upper, middle, lower

def calculate_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Average True Range"""
    return ta.ATR(high, low, close, timeperiod=period)

def calculate_roc(close: np.ndarray, period: int = 10) -> np.ndarray:
    """Calculate Rate of Change"""
    return ta.ROC(close, timeperiod=period)

def calculate_momentum(close: np.ndarray, period: int = 10) -> np.ndarray:
    """Calculate Momentum"""
    return ta.MOM(close, timeperiod=period)

def calculate_stochastic(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                         fastk_period: int = 14, slowk_period: int = 3, slowd_period: int = 3) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate Stochastic Oscillator

    Returns:
        slowk, slowd
    """
    return ta.STOCH(high, low, close, fastk_period=fastk_period, slowk_period=slowk_period, slowd_period=slowd_period)

def calculate_rsi(close: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Relative Strength Index"""
    return ta.RSI(close, timeperiod=period)

def calculate_cci(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Commodity Channel Index"""
    return ta.CCI(high, low, close, timeperiod=period)

def calculate_williams_r(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Williams %R"""
    return ta.WILLR(high, low, close, timeperiod=period)

def calculate_52week_high(close: pd.Series, window: int = 252) -> float:
    """Calculate 52-week (252-day) high"""
    if len(close) < window:
        return float(close.max())
    return float(close.tail(window).max())

def calculate_52week_low(close: pd.Series, window: int = 252) -> float:
    """Calculate 52-week (252-day) low"""
    if len(close) < window:
        return float(close.min())
    return float(close.tail(window).min())

def calculate_distance_from_52week_high(close: pd.Series, window: int = 252) -> float:
    """Calculate distance from 52-week high as percentage"""
    if close.empty:
        return 0.0

    current_price = close.iloc[-1]
    high_52w = calculate_52week_high(close, window)

    if high_52w == 0:
        return 0.0

    distance = (current_price - high_52w) / high_52w
    return float(distance)

def calculate_connors_rsi(data: pd.DataFrame, rsi_period: int = 3, streak_period: int = 2, rank_period: int = 100) -> pd.Series:
    """Calculate Connors RSI"""
    price_rsi = pd.Series(ta.RSI(data['Close'].values, timeperiod=rsi_period), index=data.index)

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

    def percent_rank(series: pd.Series, period: int) -> pd.Series:
        return series.rolling(period).apply(
            lambda x: pd.Series(x).rank().iloc[-1] / float(period) * 100,
            raw=True
        )

    pct_rank = percent_rank(data['Close'], rank_period)

    crsi = (price_rsi + streak_rsi + pct_rank) / 3.0
    return crsi

def apply_kalman_filter(data: pd.DataFrame, measurement_noise: float = 0.1, process_noise: float = 0.01) -> Tuple[pd.Series, pd.Series]:
    """Apply Kalman filter to price series

    Returns:
        filtered_prices, trends
    """
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
        state = np.dot(F, state)
        P = np.dot(np.dot(F, P), F.T) + Q

        y = price - np.dot(H, state)
        S = np.dot(np.dot(H, P), H.T) + R
        K = np.dot(np.dot(P, H.T), np.linalg.inv(S))

        state = state + np.dot(K, y)
        P = P - np.dot(np.dot(K, H), P)

        filtered_prices.append(state[0])
        trends.append(state[1])

    return pd.Series(filtered_prices, index=data.index), pd.Series(trends, index=data.index)

def apply_fft_filter_rolling(data: pd.DataFrame, cutoff_period: int, window_size: int = 252) -> pd.Series:
    """Apply FFT filtering with a rolling window approach"""
    if isinstance(data, pd.DataFrame) and 'Close' in data.columns:
        prices = data['Close'].values.astype(np.float64)
        index = data.index
    else:
        prices = data.values.astype(np.float64) if isinstance(data, pd.Series) else np.array(data, dtype=np.float64)
        index = data.index if isinstance(data, pd.Series) else None

    n = len(prices)
    filtered_prices = np.zeros(n)

    min_window = max(cutoff_period * 3, 20)
    for i in range(min(min_window, n)):
        filtered_prices[i] = prices[i]

    for i in range(min_window, n):
        start_idx = max(0, i - window_size + 1)
        window_data = prices[start_idx:i+1]
        window_len = len(window_data)

        trend = np.linspace(window_data[0], window_data[-1], window_len)
        detrended = window_data - trend

        fft_result = fft(detrended)
        freqs = fftfreq(window_len, d=1)

        filter_threshold = 1/cutoff_period
        filter_mask = np.abs(freqs) < filter_threshold
        fft_result_filtered = fft_result * filter_mask

        filtered_detrended = np.real(ifft(fft_result_filtered))
        filtered_window = filtered_detrended + trend

        filtered_prices[i] = filtered_window[-1]

    if index is not None:
        return pd.Series(filtered_prices, index=index)
    else:
        return filtered_prices

def calculate_technical_indicators_batch(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate all technical indicators for a stock DataFrame

    Adds columns: MA5, MA20, MA50, MA200, EMA12, EMA26,
                  MACD, MACD_Signal, MACD_Hist,
                  RSI, Upper, Middle, Lower,
                  ATR, Volume_MA5,
                  CRSI, Kalman_Price, Kalman_Trend, FFT_21, FFT_63
    """
    result = data.copy()

    if len(result) > 20:
        try:
            close = result['Close'].values
            high = result['High'].values if 'High' in result.columns else close
            low = result['Low'].values if 'Low' in result.columns else close

            result['MA5'] = calculate_sma(close, 5)
            result['MA20'] = calculate_sma(close, 20)
            result['MA50'] = calculate_sma(close, 50)
            result['MA200'] = calculate_sma(close, 200)

            result['EMA12'] = calculate_ema(close, 12)
            result['EMA26'] = calculate_ema(close, 26)

            macd, signal, hist = calculate_macd(close)
            result['MACD'] = macd
            result['MACD_Signal'] = signal
            result['MACD_Hist'] = hist

            result['RSI'] = calculate_rsi(close)

            upper, middle, lower = calculate_bollinger_bands(close)
            result['Upper'] = upper
            result['Middle'] = middle
            result['Lower'] = lower

            if 'High' in result.columns and 'Low' in result.columns:
                result['ATR'] = calculate_atr(high, low, close)

            if 'Volume' in result.columns:
                result['Volume_MA5'] = calculate_sma(result['Volume'].values, 5)

            result['CRSI'] = calculate_connors_rsi(result)

            kalman_price, kalman_trend = apply_kalman_filter(result)
            result['Kalman_Price'] = kalman_price
            result['Kalman_Trend'] = kalman_trend

            result['FFT_21'] = apply_fft_filter_rolling(result, 21)
            result['FFT_63'] = apply_fft_filter_rolling(result, 63)

        except Exception as e:
            print(f"Warning: Failed to calculate some indicators: {e}")

    return result
