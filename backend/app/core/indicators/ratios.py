import pandas as pd
import numpy as np
from .risk import calculate_annualized_volatility, calculate_downside_volatility
from .returns import calculate_annualized_return
from .drawdown import calculate_max_drawdown

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Calculate Sharpe Ratio = (annual_return - rf) / annual_volatility"""
    if returns.empty:
        return 0.0

    annual_return = calculate_annualized_return(returns)
    annual_vol = calculate_annualized_volatility(returns)

    if annual_vol == 0:
        return 0.0

    sharpe = (annual_return - risk_free_rate) / annual_vol
    return float(sharpe)

def calculate_rolling_sharpe(returns: pd.Series, window: int = 252, risk_free_rate: float = 0.0) -> pd.Series:
    """Calculate rolling Sharpe ratio"""
    if returns.empty:
        return pd.Series()

    def sharpe_window(window_returns: pd.Series) -> float:
        if len(window_returns) < 10:
            return np.nan

        mean_ret = window_returns.mean() * 252
        std_ret = window_returns.std() * np.sqrt(252)

        if std_ret == 0:
            return 0.0

        return (mean_ret - risk_free_rate) / std_ret

    rolling_sharpe = returns.rolling(window=window).apply(sharpe_window, raw=False)
    return rolling_sharpe

def calculate_sortino_ratio(returns: pd.Series, target_return: float = 0.0, risk_free_rate: float = 0.0) -> float:
    """Calculate Sortino Ratio = (annual_return - rf) / downside_volatility"""
    if returns.empty:
        return 0.0

    annual_return = calculate_annualized_return(returns)
    downside_vol = calculate_downside_volatility(returns, target_return=target_return, annualize=True)

    if downside_vol == 0:
        return 0.0

    sortino = (annual_return - risk_free_rate) / downside_vol
    return float(sortino)

def calculate_calmar_ratio(nav: pd.Series, returns: pd.Series) -> float:
    """Calculate Calmar Ratio = annual_return / abs(max_drawdown)"""
    if returns.empty or nav.empty:
        return 0.0

    annual_return = calculate_annualized_return(returns)
    max_dd = calculate_max_drawdown(nav)

    if max_dd == 0:
        return 0.0

    calmar = annual_return / abs(max_dd)
    return float(calmar)
