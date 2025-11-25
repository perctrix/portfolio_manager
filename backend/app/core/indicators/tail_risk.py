import pandas as pd
import numpy as np
from scipy import stats

def calculate_var(returns: pd.Series, confidence_level: float = 0.95) -> float:
    """Calculate Value at Risk (VaR) using historical method

    Args:
        returns: Daily returns series
        confidence_level: Confidence level (default 0.95 for 95% VaR)

    Returns:
        VaR value (negative number representing potential loss)
    """
    if returns.empty:
        return 0.0

    percentile = (1 - confidence_level) * 100
    var = np.percentile(returns, percentile)

    return float(var)

def calculate_cvar(returns: pd.Series, confidence_level: float = 0.95) -> float:
    """Calculate Conditional Value at Risk (CVaR) / Expected Shortfall

    Args:
        returns: Daily returns series
        confidence_level: Confidence level (default 0.95)

    Returns:
        CVaR value (average of losses beyond VaR)
    """
    if returns.empty:
        return 0.0

    var = calculate_var(returns, confidence_level)
    cvar = returns[returns <= var].mean()

    return float(cvar)

def calculate_skewness(returns: pd.Series) -> float:
    """Calculate skewness of returns distribution

    Positive skew: more extreme positive returns
    Negative skew: more extreme negative returns
    """
    if returns.empty:
        return 0.0

    skew = returns.skew()
    return float(skew)

def calculate_kurtosis(returns: pd.Series, excess: bool = True) -> float:
    """Calculate kurtosis of returns distribution

    Args:
        returns: Daily returns series
        excess: If True, return excess kurtosis (kurtosis - 3)

    Returns:
        Kurtosis value (higher = fatter tails)
    """
    if returns.empty:
        return 0.0

    if excess:
        kurt = returns.kurtosis()
    else:
        kurt = returns.kurtosis() + 3

    return float(kurt)
