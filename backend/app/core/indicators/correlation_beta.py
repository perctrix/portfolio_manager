import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, List
from scipy import stats


def calculate_correlation_to_portfolio(asset_returns: pd.Series, portfolio_returns: pd.Series) -> float:
    """Calculate correlation between single asset and portfolio

    Args:
        asset_returns: Daily returns of a single asset
        portfolio_returns: Daily returns of the portfolio

    Returns:
        Correlation coefficient (-1 to 1)
    """
    if asset_returns.empty or portfolio_returns.empty:
        return 0.0

    aligned_asset, aligned_portfolio = asset_returns.align(portfolio_returns, join='inner')

    if len(aligned_asset) < 2:
        return 0.0

    corr = aligned_asset.corr(aligned_portfolio)
    return float(corr) if not np.isnan(corr) else 0.0


def calculate_correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate correlation matrix between all assets

    Args:
        returns_df: DataFrame with columns as assets, rows as dates, values as returns

    Returns:
        Correlation matrix DataFrame
    """
    if returns_df.empty:
        return pd.DataFrame()

    corr_matrix = returns_df.corr()
    return corr_matrix


def calculate_covariance_matrix(returns_df: pd.DataFrame, annualize: bool = True) -> pd.DataFrame:
    """Calculate covariance matrix between all assets

    Args:
        returns_df: DataFrame with columns as assets, rows as dates, values as returns
        annualize: If True, annualize the covariance (multiply by 252)

    Returns:
        Covariance matrix DataFrame
    """
    if returns_df.empty:
        return pd.DataFrame()

    cov_matrix = returns_df.cov()

    if annualize:
        cov_matrix = cov_matrix * 252

    return cov_matrix


def calculate_beta(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Calculate portfolio beta relative to benchmark

    Beta = Cov(portfolio, benchmark) / Var(benchmark)

    Args:
        portfolio_returns: Daily returns of portfolio
        benchmark_returns: Daily returns of benchmark

    Returns:
        Beta coefficient
    """
    if portfolio_returns.empty or benchmark_returns.empty:
        return 0.0

    aligned_portfolio, aligned_benchmark = portfolio_returns.align(benchmark_returns, join='inner')

    if len(aligned_portfolio) < 2:
        return 0.0

    covariance = aligned_portfolio.cov(aligned_benchmark)
    variance = aligned_benchmark.var()

    if variance == 0:
        return 0.0

    beta = covariance / variance
    return float(beta)


def calculate_alpha(portfolio_returns: pd.Series, benchmark_returns: pd.Series,
                   risk_free_rate: float = 0.0) -> float:
    """Calculate Jensen's Alpha

    Alpha = portfolio_return - (risk_free_rate + beta * (benchmark_return - risk_free_rate))

    Args:
        portfolio_returns: Daily returns of portfolio
        benchmark_returns: Daily returns of benchmark
        risk_free_rate: Annual risk-free rate (default 0.0)

    Returns:
        Annualized alpha
    """
    if portfolio_returns.empty or benchmark_returns.empty:
        return 0.0

    aligned_portfolio, aligned_benchmark = portfolio_returns.align(benchmark_returns, join='inner')

    if len(aligned_portfolio) < 2:
        return 0.0

    beta = calculate_beta(aligned_portfolio, aligned_benchmark)

    portfolio_annual_return = aligned_portfolio.mean() * 252
    benchmark_annual_return = aligned_benchmark.mean() * 252

    alpha = portfolio_annual_return - (risk_free_rate + beta * (benchmark_annual_return - risk_free_rate))

    return float(alpha)


def calculate_r_squared(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Calculate R² (coefficient of determination)

    R² measures how much of portfolio's variance is explained by benchmark

    Args:
        portfolio_returns: Daily returns of portfolio
        benchmark_returns: Daily returns of benchmark

    Returns:
        R² value (0 to 1)
    """
    if portfolio_returns.empty or benchmark_returns.empty:
        return 0.0

    aligned_portfolio, aligned_benchmark = portfolio_returns.align(benchmark_returns, join='inner')

    if len(aligned_portfolio) < 2:
        return 0.0

    slope, intercept, r_value, p_value, std_err = stats.linregress(
        aligned_benchmark.values,
        aligned_portfolio.values
    )

    r_squared = r_value ** 2
    return float(r_squared)


def calculate_tracking_error(portfolio_returns: pd.Series, benchmark_returns: pd.Series,
                            annualize: bool = True) -> float:
    """Calculate tracking error (standard deviation of excess returns)

    Tracking Error = std(portfolio_returns - benchmark_returns)

    Args:
        portfolio_returns: Daily returns of portfolio
        benchmark_returns: Daily returns of benchmark
        annualize: If True, annualize the tracking error

    Returns:
        Tracking error
    """
    if portfolio_returns.empty or benchmark_returns.empty:
        return 0.0

    aligned_portfolio, aligned_benchmark = portfolio_returns.align(benchmark_returns, join='inner')

    if len(aligned_portfolio) < 2:
        return 0.0

    excess_returns = aligned_portfolio - aligned_benchmark
    tracking_error = excess_returns.std()

    if annualize:
        tracking_error = tracking_error * np.sqrt(252)

    return float(tracking_error)


def calculate_information_ratio(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Calculate Information Ratio

    Information Ratio = (portfolio_return - benchmark_return) / tracking_error

    Args:
        portfolio_returns: Daily returns of portfolio
        benchmark_returns: Daily returns of benchmark

    Returns:
        Information Ratio
    """
    if portfolio_returns.empty or benchmark_returns.empty:
        return 0.0

    aligned_portfolio, aligned_benchmark = portfolio_returns.align(benchmark_returns, join='inner')

    if len(aligned_portfolio) < 2:
        return 0.0

    excess_returns = aligned_portfolio - aligned_benchmark
    mean_excess_return = excess_returns.mean() * 252
    tracking_error = excess_returns.std() * np.sqrt(252)

    if tracking_error == 0:
        return 0.0

    information_ratio = mean_excess_return / tracking_error
    return float(information_ratio)


def calculate_all_benchmark_metrics(portfolio_returns: pd.Series, benchmark_returns: pd.Series,
                                    risk_free_rate: float = 0.0) -> Dict[str, float]:
    """Calculate all benchmark-relative metrics at once

    Args:
        portfolio_returns: Daily returns of portfolio
        benchmark_returns: Daily returns of benchmark
        risk_free_rate: Annual risk-free rate

    Returns:
        Dictionary with all metrics
    """
    if portfolio_returns.empty or benchmark_returns.empty:
        return {
            'beta': 0.0,
            'alpha': 0.0,
            'r_squared': 0.0,
            'correlation': 0.0,
            'tracking_error': 0.0,
            'information_ratio': 0.0,
            'upside_capture': 0.0,
            'downside_capture': 0.0,
            'treynor_ratio': 0.0,
            'm2_measure': 0.0
        }

    from .ratios import calculate_treynor_ratio, calculate_m2_measure

    beta = calculate_beta(portfolio_returns, benchmark_returns)

    return {
        'beta': beta,
        'alpha': calculate_alpha(portfolio_returns, benchmark_returns, risk_free_rate),
        'r_squared': calculate_r_squared(portfolio_returns, benchmark_returns),
        'correlation': calculate_correlation_to_portfolio(portfolio_returns, benchmark_returns),
        'tracking_error': calculate_tracking_error(portfolio_returns, benchmark_returns),
        'information_ratio': calculate_information_ratio(portfolio_returns, benchmark_returns),
        'upside_capture': calculate_upside_capture(portfolio_returns, benchmark_returns),
        'downside_capture': calculate_downside_capture(portfolio_returns, benchmark_returns),
        'treynor_ratio': calculate_treynor_ratio(portfolio_returns, beta, risk_free_rate),
        'm2_measure': calculate_m2_measure(portfolio_returns, benchmark_returns, risk_free_rate)
    }


def calculate_multi_benchmark_metrics(portfolio_returns: pd.Series,
                                      benchmark_returns_dict: Dict[str, pd.Series],
                                      risk_free_rate: float = 0.0) -> Dict[str, Dict[str, float]]:
    """Calculate metrics relative to multiple benchmarks

    Args:
        portfolio_returns: Daily returns of portfolio
        benchmark_returns_dict: Dict of {benchmark_name: returns_series}
        risk_free_rate: Annual risk-free rate

    Returns:
        Nested dict: {benchmark_name: {metric: value}}
    """
    results = {}

    for benchmark_name, benchmark_returns in benchmark_returns_dict.items():
        results[benchmark_name] = calculate_all_benchmark_metrics(
            portfolio_returns,
            benchmark_returns,
            risk_free_rate
        )

    return results


def calculate_mean_pairwise_correlation(returns_df: pd.DataFrame) -> float:
    """Calculate mean pairwise correlation among all assets in portfolio

    Args:
        returns_df: DataFrame with columns as assets, values as returns

    Returns:
        Mean correlation coefficient
    """
    if returns_df.empty or returns_df.shape[1] < 2:
        return 0.0

    corr_matrix = returns_df.corr()

    upper_triangle = np.triu(corr_matrix.values, k=1)
    correlations = upper_triangle[upper_triangle != 0]

    if len(correlations) == 0:
        return 0.0

    return float(np.mean(correlations))


def calculate_max_min_correlation(returns_df: pd.DataFrame) -> Tuple[float, float]:
    """Calculate maximum and minimum pairwise correlation

    Args:
        returns_df: DataFrame with columns as assets, values as returns

    Returns:
        Tuple of (max_correlation, min_correlation)
    """
    if returns_df.empty or returns_df.shape[1] < 2:
        return 0.0, 0.0

    corr_matrix = returns_df.corr()

    upper_triangle = np.triu(corr_matrix.values, k=1)
    correlations = upper_triangle[upper_triangle != 0]

    if len(correlations) == 0:
        return 0.0, 0.0

    return float(np.max(correlations)), float(np.min(correlations))


def calculate_upside_capture(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Calculate Upside Capture Ratio

    Measures portfolio's average return when benchmark is positive
    relative to benchmark's average positive return.
    Value > 100 indicates outperformance in up markets.

    Args:
        portfolio_returns: Daily returns of portfolio
        benchmark_returns: Daily returns of benchmark

    Returns:
        Upside capture ratio as percentage (>100 is good)
    """
    if portfolio_returns.empty or benchmark_returns.empty:
        return 0.0

    aligned_portfolio, aligned_benchmark = portfolio_returns.align(benchmark_returns, join='inner')

    if len(aligned_portfolio) < 2:
        return 0.0

    up_market = aligned_benchmark > 0
    portfolio_up_returns = aligned_portfolio[up_market]
    benchmark_up_returns = aligned_benchmark[up_market]

    if len(benchmark_up_returns) == 0 or benchmark_up_returns.mean() == 0:
        return 0.0

    upside_capture = (portfolio_up_returns.mean() / benchmark_up_returns.mean()) * 100
    return float(upside_capture)


def calculate_downside_capture(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Calculate Downside Capture Ratio

    Measures portfolio's average return when benchmark is negative
    relative to benchmark's average negative return.
    Value < 100 indicates outperformance in down markets (less loss).

    Args:
        portfolio_returns: Daily returns of portfolio
        benchmark_returns: Daily returns of benchmark

    Returns:
        Downside capture ratio as percentage (<100 is good)
    """
    if portfolio_returns.empty or benchmark_returns.empty:
        return 0.0

    aligned_portfolio, aligned_benchmark = portfolio_returns.align(benchmark_returns, join='inner')

    if len(aligned_portfolio) < 2:
        return 0.0

    down_market = aligned_benchmark < 0
    portfolio_down_returns = aligned_portfolio[down_market]
    benchmark_down_returns = aligned_benchmark[down_market]

    if len(benchmark_down_returns) == 0 or benchmark_down_returns.mean() == 0:
        return 0.0

    downside_capture = (portfolio_down_returns.mean() / benchmark_down_returns.mean()) * 100
    return float(downside_capture)
