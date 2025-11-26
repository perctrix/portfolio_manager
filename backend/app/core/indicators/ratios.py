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

def calculate_treynor_ratio(returns: pd.Series, beta: float, risk_free_rate: float = 0.0) -> float:
    """Calculate Treynor Ratio = (annual_return - rf) / beta

    Args:
        returns: Daily returns series
        beta: Portfolio beta relative to benchmark
        risk_free_rate: Annual risk-free rate

    Returns:
        Treynor ratio (excess return per unit of systematic risk)
    """
    if returns.empty or beta == 0:
        return 0.0

    annual_return = calculate_annualized_return(returns)
    treynor = (annual_return - risk_free_rate) / beta
    return float(treynor)

def calculate_omega_ratio(returns: pd.Series, threshold: float = 0.0) -> float:
    """Calculate Omega Ratio = probability weighted gains / probability weighted losses

    Args:
        returns: Daily returns series
        threshold: Minimum acceptable return (default 0.0)

    Returns:
        Omega ratio (>1 indicates good risk-adjusted performance)
    """
    if returns.empty:
        return 0.0

    excess_returns = returns - threshold
    gains = excess_returns[excess_returns > 0].sum()
    losses = -excess_returns[excess_returns < 0].sum()

    if losses == 0:
        return float('inf') if gains > 0 else 0.0

    omega = gains / losses
    return float(omega)

def calculate_m2_measure(returns: pd.Series, benchmark_returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Calculate M2 Measure (Modigliani-Modigliani measure)

    Returns the portfolio's risk-adjusted return scaled to match benchmark volatility,
    expressed as a percentage difference from the benchmark.

    Args:
        returns: Portfolio daily returns
        benchmark_returns: Benchmark daily returns
        risk_free_rate: Annual risk-free rate

    Returns:
        M2 measure in percentage points
    """
    if returns.empty or benchmark_returns.empty:
        return 0.0

    portfolio_return = calculate_annualized_return(returns)
    portfolio_vol = calculate_annualized_volatility(returns)
    benchmark_vol = calculate_annualized_volatility(benchmark_returns)
    benchmark_return = calculate_annualized_return(benchmark_returns)

    if portfolio_vol == 0:
        return 0.0

    sharpe = (portfolio_return - risk_free_rate) / portfolio_vol
    m2 = risk_free_rate + sharpe * benchmark_vol - benchmark_return

    return float(m2)

def calculate_gain_to_pain_ratio(returns: pd.Series) -> float:
    """Calculate Gain-to-Pain Ratio = sum(positive returns) / abs(sum(negative returns))

    Args:
        returns: Daily returns series

    Returns:
        Gain-to-pain ratio (higher is better)
    """
    if returns.empty:
        return 0.0

    gains = returns[returns > 0].sum()
    pains = abs(returns[returns < 0].sum())

    if pains == 0:
        return float('inf') if gains > 0 else 0.0

    ratio = gains / pains
    return float(ratio)

def calculate_ulcer_performance_index(nav: pd.Series, returns: pd.Series, risk_free_rate: float = 0.0, window: int = 14) -> float:
    """Calculate Ulcer Performance Index = (return - rf) / Ulcer Index

    Args:
        nav: NAV time series
        returns: Daily returns series
        risk_free_rate: Annual risk-free rate
        window: Lookback period for Ulcer Index (default 14)

    Returns:
        Ulcer Performance Index (higher is better)
    """
    if returns.empty or nav.empty:
        return 0.0

    from .drawdown import calculate_ulcer_index

    annual_return = calculate_annualized_return(returns)
    ulcer = calculate_ulcer_index(nav, window=window)

    if ulcer == 0:
        return 0.0

    upi = (annual_return - risk_free_rate) / ulcer
    return float(upi)
