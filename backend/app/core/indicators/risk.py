import pandas as pd
import numpy as np

def calculate_daily_volatility(returns: pd.Series) -> float:
    """Calculate daily volatility (standard deviation of returns)"""
    if returns.empty:
        return 0.0
    return float(returns.std())

def calculate_annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Calculate annualized volatility"""
    if returns.empty:
        return 0.0
    daily_vol = returns.std()
    return float(daily_vol * np.sqrt(periods_per_year))

def calculate_rolling_volatility(returns: pd.Series, window: int, annualize: bool = True) -> pd.Series:
    """Calculate N-day rolling volatility"""
    if returns.empty:
        return pd.Series()

    rolling_std = returns.rolling(window=window).std()

    if annualize:
        rolling_std = rolling_std * np.sqrt(252)

    return rolling_std

def calculate_upside_volatility(returns: pd.Series, annualize: bool = True) -> float:
    """Calculate upside volatility (volatility of positive returns only)"""
    if returns.empty:
        return 0.0

    upside_returns = returns[returns > 0]
    if upside_returns.empty:
        return 0.0

    vol = upside_returns.std()
    if annualize:
        vol = vol * np.sqrt(252)

    return float(vol)

def calculate_downside_volatility(returns: pd.Series, target_return: float = 0.0, annualize: bool = True) -> float:
    """Calculate downside volatility (volatility of returns below target)"""
    if returns.empty:
        return 0.0

    downside_returns = returns[returns < target_return]
    if downside_returns.empty:
        return 0.0

    vol = downside_returns.std()
    if annualize:
        vol = vol * np.sqrt(252)

    return float(vol)

def calculate_semivariance(returns: pd.Series, target_return: float = 0.0) -> float:
    """Calculate semivariance (mean of squared negative returns)"""
    if returns.empty:
        return 0.0

    downside_returns = returns[returns < target_return]
    if downside_returns.empty:
        return 0.0

    semivar = (downside_returns ** 2).mean()
    return float(semivar)
