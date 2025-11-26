import pandas as pd
import numpy as np
from typing import Dict, Optional, Any

from . import returns as returns_module
from . import risk as risk_module
from . import drawdown as drawdown_module
from . import ratios as ratios_module
from . import allocation as allocation_module
from . import trading as trading_module
from . import tail_risk as tail_risk_module
from . import correlation_beta

def calculate_basic_portfolio_indicators(nav: pd.Series) -> Dict[str, float]:
    """Calculate 5 basic portfolio indicators

    Returns:
        {
            'total_return': float,
            'cagr': float,
            'volatility': float,
            'sharpe': float,
            'max_drawdown': float
        }
    """
    if nav.empty:
        return {
            'total_return': 0.0,
            'cagr': 0.0,
            'volatility': 0.0,
            'sharpe': 0.0,
            'max_drawdown': 0.0
        }

    returns = nav.pct_change().dropna()

    total_return = (nav.iloc[-1] / nav.iloc[0]) - 1
    cagr = returns_module.calculate_cagr(nav)
    volatility = risk_module.calculate_annualized_volatility(returns)
    sharpe = ratios_module.calculate_sharpe_ratio(returns)
    max_drawdown = drawdown_module.calculate_max_drawdown(nav)

    return {
        'total_return': float(total_return),
        'cagr': float(cagr),
        'volatility': float(volatility),
        'sharpe': float(sharpe),
        'max_drawdown': float(max_drawdown)
    }

def calculate_all_portfolio_indicators(
    nav: pd.Series,
    transactions: Optional[pd.DataFrame] = None,
    holdings: Optional[Dict[str, float]] = None,
    prices: Optional[Dict[str, float]] = None,
    price_history: Optional[pd.DataFrame] = None,
    weights: Optional[Dict[str, float]] = None,
    sector_map: Optional[Dict[str, str]] = None,
    industry_map: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Calculate all portfolio indicators (approximately 87 indicators)

    Args:
        nav: NAV time series
        transactions: Transaction history (for TRANSACTION mode)
        holdings: Current holdings {symbol: quantity}
        prices: Current prices {symbol: price}
        price_history: Price history DataFrame with symbols as columns
        weights: Portfolio weights {symbol: weight}
        sector_map: Sector mapping {symbol: sector}
        industry_map: Industry mapping {symbol: industry}

    Returns:
        Dict with all indicators organized by category
    """
    result = {}

    if nav.empty:
        return result

    returns = nav.pct_change().dropna()

    result['returns'] = {}
    result['returns']['simple_returns_mean'] = float(returns.mean())
    result['returns']['total_return'] = float((nav.iloc[-1] / nav.iloc[0]) - 1)
    result['returns']['cagr'] = returns_module.calculate_cagr(nav)
    result['returns']['annualized_return'] = returns_module.calculate_annualized_return(returns)
    result['returns']['ytd_return'] = returns_module.calculate_ytd_return(nav)
    result['returns']['mtd_return'] = returns_module.calculate_mtd_return(nav)

    if transactions is not None and not transactions.empty:
        result['returns']['realized_pnl'] = returns_module.calculate_realized_pnl(transactions)
        result['returns']['twr'] = returns_module.calculate_twr(nav)
        result['returns']['irr'] = returns_module.calculate_irr(transactions)
    else:
        result['returns']['realized_pnl'] = 0.0
        result['returns']['twr'] = returns_module.calculate_cagr(nav)
        result['returns']['irr'] = 0.0

    if holdings is not None and prices is not None:
        result['returns']['unrealized_pnl'] = returns_module.calculate_unrealized_pnl(holdings, prices)
    else:
        result['returns']['unrealized_pnl'] = 0.0

    result['returns']['total_pnl'] = returns_module.calculate_total_pnl(
        result['returns']['realized_pnl'],
        result['returns']['unrealized_pnl']
    )

    monthly_returns = returns_module.calculate_monthly_returns(returns)
    result['returns']['monthly_returns'] = monthly_returns.to_dict() if not monthly_returns.empty else {}

    result['risk'] = {}
    result['risk']['daily_volatility'] = risk_module.calculate_daily_volatility(returns)
    result['risk']['annualized_volatility'] = risk_module.calculate_annualized_volatility(returns)
    result['risk']['upside_volatility'] = risk_module.calculate_upside_volatility(returns)
    result['risk']['downside_volatility'] = risk_module.calculate_downside_volatility(returns)
    result['risk']['semivariance'] = risk_module.calculate_semivariance(returns)

    rolling_vol_30d = risk_module.calculate_rolling_volatility(returns, window=30)
    result['risk']['rolling_volatility_30d'] = float(rolling_vol_30d.iloc[-1]) if not rolling_vol_30d.empty and len(rolling_vol_30d) > 0 else 0.0

    result['drawdown'] = {}
    result['drawdown']['max_drawdown'] = drawdown_module.calculate_max_drawdown(nav)
    result['drawdown']['avg_drawdown'] = drawdown_module.calculate_avg_drawdown(nav)
    result['drawdown']['max_daily_loss'] = drawdown_module.calculate_max_daily_loss(returns)
    result['drawdown']['max_daily_gain'] = drawdown_module.calculate_max_daily_gain(returns)
    result['drawdown']['consecutive_loss_days'] = drawdown_module.calculate_consecutive_loss_days(returns)
    result['drawdown']['consecutive_gain_days'] = drawdown_module.calculate_consecutive_gain_days(returns)

    dd_duration = drawdown_module.calculate_drawdown_duration(nav)
    result['drawdown'].update(dd_duration)

    recovery_info = drawdown_module.calculate_recovery_time(nav)
    result['drawdown'].update(recovery_info)

    result['drawdown']['ulcer_index'] = drawdown_module.calculate_ulcer_index(nav)

    result['risk_adjusted_ratios'] = {}
    result['risk_adjusted_ratios']['sharpe'] = ratios_module.calculate_sharpe_ratio(returns)
    result['risk_adjusted_ratios']['sortino'] = ratios_module.calculate_sortino_ratio(returns)
    result['risk_adjusted_ratios']['calmar'] = ratios_module.calculate_calmar_ratio(nav, returns)
    result['risk_adjusted_ratios']['omega'] = ratios_module.calculate_omega_ratio(returns)
    result['risk_adjusted_ratios']['gain_to_pain'] = ratios_module.calculate_gain_to_pain_ratio(returns)
    result['risk_adjusted_ratios']['ulcer_performance_index'] = ratios_module.calculate_ulcer_performance_index(nav, returns)

    rolling_sharpe_30d = ratios_module.calculate_rolling_sharpe(returns, window=30)
    result['risk_adjusted_ratios']['rolling_sharpe_30d'] = float(rolling_sharpe_30d.iloc[-1]) if not rolling_sharpe_30d.empty and len(rolling_sharpe_30d) > 0 else 0.0

    result['tail_risk'] = {}
    result['tail_risk']['var_95'] = tail_risk_module.calculate_var(returns, 0.95)
    result['tail_risk']['cvar_95'] = tail_risk_module.calculate_cvar(returns, 0.95)
    result['tail_risk']['skewness'] = tail_risk_module.calculate_skewness(returns)
    result['tail_risk']['kurtosis'] = tail_risk_module.calculate_kurtosis(returns, excess=True)
    result['tail_risk']['tail_ratio'] = tail_risk_module.calculate_tail_ratio(returns)

    if weights is not None and len(weights) > 0:
        result['allocation'] = {}
        result['allocation']['weights'] = weights
        result['allocation']['hhi'] = allocation_module.calculate_hhi(weights)
        result['allocation']['top_5_concentration'] = allocation_module.calculate_top_n_concentration(weights, 5)
        result['allocation']['max_weight'] = allocation_module.calculate_max_weight(weights)
        result['allocation']['weight_deviation_from_equal'] = allocation_module.calculate_weight_deviation_from_equal(weights)

        if holdings is not None and prices is not None:
            long_short = allocation_module.calculate_long_short_exposure(holdings, prices)
            result['allocation']['long_short_exposure'] = long_short

        if sector_map is not None:
            sector_alloc = allocation_module.calculate_sector_allocation(holdings, prices, sector_map)
            result['allocation']['sector_allocation'] = sector_alloc

        if industry_map is not None:
            industry_alloc = allocation_module.calculate_industry_allocation(holdings, prices, industry_map)
            result['allocation']['industry_allocation'] = industry_alloc

    if price_history is not None and not price_history.empty and weights is not None and len(weights) > 1:
        result['risk_decomposition'] = {}
        result['risk_decomposition']['portfolio_volatility'] = allocation_module.calculate_portfolio_volatility(weights, price_history)

        mctr = allocation_module.calculate_mctr(weights, price_history)
        result['risk_decomposition']['mctr'] = mctr

        risk_contrib = allocation_module.calculate_risk_contribution_by_asset(weights, price_history)
        result['risk_decomposition']['by_asset'] = risk_contrib

        if sector_map is not None:
            sector_risk = allocation_module.calculate_risk_contribution_by_sector(weights, price_history, sector_map)
            result['risk_decomposition']['by_sector'] = sector_risk

    if transactions is not None and not transactions.empty:
        result['trading'] = trading_module.calculate_all_trading_metrics(transactions, nav)
        result['trading']['turnover_by_asset'] = trading_module.calculate_turnover_rate_by_asset(transactions, nav)
    else:
        result['trading'] = None

    if price_history is not None and not price_history.empty and len(price_history) > 1:
        result['correlation'] = {}
        returns_df = price_history.pct_change().dropna()
        if not returns_df.empty and returns_df.shape[1] > 1:
            result['correlation']['mean_pairwise'] = correlation_beta.calculate_mean_pairwise_correlation(returns_df)
            max_corr, min_corr = correlation_beta.calculate_max_min_correlation(returns_df)
            result['correlation']['max_pairwise'] = max_corr
            result['correlation']['min_pairwise'] = min_corr

    return result


def calculate_benchmark_comparison(
    portfolio_returns: pd.Series,
    benchmark_returns_dict: Dict[str, pd.Series],
    risk_free_rate: float = 0.0
) -> Dict[str, Dict[str, float]]:
    """Calculate portfolio performance relative to multiple benchmarks

    Args:
        portfolio_returns: Daily returns of portfolio
        benchmark_returns_dict: Dict of {benchmark_symbol: returns_series}
        risk_free_rate: Annual risk-free rate

    Returns:
        Dict of {benchmark_symbol: {metric: value}}
    """
    return correlation_beta.calculate_multi_benchmark_metrics(
        portfolio_returns,
        benchmark_returns_dict,
        risk_free_rate
    )
