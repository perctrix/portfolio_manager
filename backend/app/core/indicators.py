import pandas as pd
import numpy as np
import talib as ta
from scipy.fft import fft, ifft, fftfreq

def rolling_normalize(series: pd.Series, window=21) -> pd.Series:
    """Apply rolling window normalization to a time series"""
    rolling_mean = series.rolling(window=window, min_periods=1).mean()
    rolling_std = series.rolling(window=window, min_periods=1).std()
    eps = 1e-8
    normalized = (series - rolling_mean) / (rolling_std + eps)
    normalized = normalized.ffill().bfill()
    return normalized

def calculate_connors_rsi(data: pd.DataFrame, rsi_period=3, streak_period=2, rank_period=100) -> pd.Series:
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

def apply_kalman_filter(data: pd.DataFrame, measurement_noise=0.1, process_noise=0.01):
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

def apply_fft_filter_rolling(data: pd.DataFrame, cutoff_period, window_size=252) -> pd.Series:
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

def calculate_basic_metrics(nav_series: pd.Series):
    """Calculate basic performance metrics"""
    if nav_series.empty:
        return {}
        
    daily_returns = nav_series.pct_change().dropna()
    
    total_return = (nav_series.iloc[-1] / nav_series.iloc[0]) - 1
    
    # Annualized Return (assuming daily data)
    days = (nav_series.index[-1] - nav_series.index[0]).days
    if days > 0:
        cagr = (nav_series.iloc[-1] / nav_series.iloc[0]) ** (365.0 / days) - 1
    else:
        cagr = 0
        
    # Volatility
    volatility = daily_returns.std() * np.sqrt(252)
    
    # Sharpe (Rf=0)
    sharpe = (cagr / volatility) if volatility != 0 else 0
    
    # Max Drawdown
    rolling_max = nav_series.cummax()
    drawdown = (nav_series - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    
    
    return {
        "total_return": float(total_return),
        "cagr": float(cagr),
        "volatility": float(volatility),
        "sharpe": float(sharpe),
        "max_drawdown": float(max_drawdown)
    }

def calculate_risk_metrics(returns_series: pd.Series, risk_free_rate: float = 0.0) -> dict:
    """Calculate advanced risk metrics"""
    if returns_series.empty:
        return {}
        
    # Sortino Ratio
    target_return = 0.0
    downside_returns = returns_series[returns_series < target_return]
    downside_std = downside_returns.std() * np.sqrt(252)
    
    annualized_return = returns_series.mean() * 252
    sortino = (annualized_return - risk_free_rate) / downside_std if downside_std != 0 else 0
    
    # Calmar Ratio
    # We need max drawdown for Calmar. 
    # Assuming returns_series is daily returns, we reconstruct a cumulative series for MDD.
    cum_returns = (1 + returns_series).cumprod()
    rolling_max = cum_returns.cummax()
    drawdown = (cum_returns - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    
    calmar = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
    
    # VaR (95%) - Historical Method
    var_95 = np.percentile(returns_series, 5)
    
    # CVaR (95%) - Expected Shortfall
    cvar_95 = returns_series[returns_series <= var_95].mean()
    
    # Skewness & Kurtosis
    skew = returns_series.skew()
    kurt = returns_series.kurtosis()
    
    return {
        "sortino": float(sortino),
        "calmar": float(calmar),
        "var_95": float(var_95),
        "cvar_95": float(cvar_95),
        "skewness": float(skew),
        "kurtosis": float(kurt)
    }

def calculate_allocation_metrics(weights: dict) -> dict:
    """Calculate allocation metrics like HHI"""
    if not weights:
        return {}
        
    w_series = pd.Series(weights)
    # Normalize weights to sum to 1 (just in case)
    total_weight = w_series.sum()
    if total_weight == 0:
        return {}
    w_norm = w_series / total_weight
    
    # HHI
    hhi = (w_norm ** 2).sum()
    
    # Top 5 Concentration
    top_5 = w_norm.nlargest(5).sum()
    
    return {
        "hhi": float(hhi),
        "top_5_concentration": float(top_5)
    }

def calculate_risk_contribution(weights: dict, price_history: pd.DataFrame) -> dict:
    """
    Calculate Marginal Contribution to Risk (MCTR) and Total Risk Contribution.
    price_history: DataFrame with columns as symbols, index as date.
    """
    if not weights or price_history.empty:
        return {}
        
    # Align weights and prices
    symbols = [s for s in weights.keys() if s in price_history.columns]
    if not symbols:
        return {}
        
    w = np.array([weights[s] for s in symbols])
    # Normalize weights
    w = w / np.sum(w)
    
    returns = price_history[symbols].pct_change().dropna()
    if returns.empty:
        return {}
        
    cov_matrix = returns.cov() * 252 # Annualized
    
    # Portfolio Volatility
    port_vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
    
    # Marginal Contribution to Risk (MCTR)
    # MCTR = (Cov * w) / port_vol
    mctr = np.dot(cov_matrix, w) / port_vol
    
    # Absolute Risk Contribution = w * MCTR
    risk_contrib = w * mctr
    
    # Percent Risk Contribution
    pct_risk_contrib = risk_contrib / port_vol
    
    result = {}
    for i, sym in enumerate(symbols):
        result[sym] = {
            "mctr": float(mctr[i]),
            "risk_contribution": float(risk_contrib[i]),
            "pct_risk_contribution": float(pct_risk_contrib[i])
        }
        
    return {
        "portfolio_volatility": float(port_vol),
        "risk_decomposition": result
    }
