import pandas as pd
import numpy as np
from typing import Dict

def calculate_weights(holdings: Dict[str, float], prices: Dict[str, float]) -> Dict[str, float]:
    """Calculate portfolio weights from holdings and prices"""
    if not holdings or not prices:
        return {}

    values = {}
    total_value = 0.0

    for symbol, qty in holdings.items():
        if symbol in prices and qty != 0:
            value = qty * prices[symbol]
            values[symbol] = value
            total_value += value

    if total_value == 0:
        return {}

    weights = {symbol: value / total_value for symbol, value in values.items()}
    return weights

def calculate_weight_history(holdings_history: pd.DataFrame, price_history: pd.DataFrame) -> pd.DataFrame:
    """Calculate historical weights time series

    Args:
        holdings_history: DataFrame with columns as symbols, rows as dates, values as quantities
        price_history: DataFrame with columns as symbols, rows as dates, values as prices
    """
    if holdings_history.empty or price_history.empty:
        return pd.DataFrame()

    values = holdings_history * price_history
    total_value = values.sum(axis=1)

    weights = values.div(total_value, axis=0)
    return weights

def calculate_top_n_concentration(weights: Dict[str, float], n: int = 5) -> float:
    """Calculate concentration of top N holdings"""
    if not weights:
        return 0.0

    sorted_weights = sorted(weights.values(), reverse=True)
    top_n_weights = sorted_weights[:n]

    return float(sum(top_n_weights))

def calculate_hhi(weights: Dict[str, float]) -> float:
    """Calculate Herfindahl-Hirschman Index (HHI) = sum(w_i^2)"""
    if not weights:
        return 0.0

    hhi = sum(w ** 2 for w in weights.values())
    return float(hhi)

def calculate_sector_allocation(holdings: Dict[str, float], prices: Dict[str, float], sector_map: Dict[str, str]) -> Dict[str, float]:
    """Calculate allocation by sector

    Args:
        holdings: {symbol: quantity}
        prices: {symbol: price}
        sector_map: {symbol: sector}
    """
    if not holdings or not prices or not sector_map:
        return {}

    weights = calculate_weights(holdings, prices)
    sector_weights = {}

    for symbol, weight in weights.items():
        sector = sector_map.get(symbol, 'Unknown')
        sector_weights[sector] = sector_weights.get(sector, 0.0) + weight

    return sector_weights


def calculate_industry_allocation(holdings: Dict[str, float], prices: Dict[str, float], industry_map: Dict[str, str]) -> Dict[str, float]:
    """Calculate allocation by industry

    Args:
        holdings: {symbol: quantity}
        prices: {symbol: price}
        industry_map: {symbol: industry}
    """
    if not holdings or not prices or not industry_map:
        return {}

    weights = calculate_weights(holdings, prices)
    industry_weights = {}

    for symbol, weight in weights.items():
        industry = industry_map.get(symbol, 'Unknown')
        industry_weights[industry] = industry_weights.get(industry, 0.0) + weight

    return industry_weights

def calculate_max_weight(weights: Dict[str, float]) -> float:
    """Calculate maximum single position weight"""
    if not weights:
        return 0.0

    return float(max(weights.values()))

def calculate_weight_deviation_from_equal(weights: Dict[str, float]) -> float:
    """Calculate sum of absolute deviations from equal weight"""
    if not weights:
        return 0.0

    n = len(weights)
    equal_weight = 1.0 / n

    deviation = sum(abs(w - equal_weight) for w in weights.values())
    return float(deviation)

def calculate_long_short_exposure(holdings: Dict[str, float], prices: Dict[str, float]) -> Dict[str, float]:
    """Calculate long and short exposure

    Args:
        holdings: {symbol: quantity} (can be negative for short positions)
        prices: {symbol: price}
    """
    if not holdings or not prices:
        return {'long_exposure': 0.0, 'short_exposure': 0.0, 'net_exposure': 0.0}

    long_value = 0.0
    short_value = 0.0

    for symbol, qty in holdings.items():
        if symbol in prices:
            value = qty * prices[symbol]
            if value > 0:
                long_value += value
            else:
                short_value += abs(value)

    total_value = long_value + short_value
    return {
        'long_exposure': float(long_value / total_value) if total_value > 0 else 0.0,
        'short_exposure': float(short_value / total_value) if total_value > 0 else 0.0,
        'net_exposure': float((long_value - short_value) / total_value) if total_value > 0 else 0.0
    }

def calculate_portfolio_volatility(weights: Dict[str, float], price_history: pd.DataFrame) -> float:
    """Calculate portfolio volatility from weights and price history"""
    if not weights or price_history.empty:
        return 0.0

    symbols = [s for s in weights.keys() if s in price_history.columns]
    if not symbols:
        return 0.0

    w = np.array([weights[s] for s in symbols])
    w = w / np.sum(w)

    returns = price_history[symbols].pct_change(fill_method=None).dropna()
    if returns.empty:
        return 0.0

    cov_matrix = returns.cov() * 252

    port_var = np.dot(w.T, np.dot(cov_matrix, w))
    port_vol = np.sqrt(port_var)

    return float(port_vol)

def calculate_mctr(weights: Dict[str, float], price_history: pd.DataFrame) -> Dict[str, float]:
    """Calculate Marginal Contribution to Risk (MCTR)

    MCTR_i = (Cov * w)_i / portfolio_volatility
    """
    if not weights or price_history.empty:
        return {}

    symbols = [s for s in weights.keys() if s in price_history.columns]
    if not symbols:
        return {}

    w = np.array([weights[s] for s in symbols])
    w = w / np.sum(w)

    returns = price_history[symbols].pct_change(fill_method=None).dropna()
    if returns.empty:
        return {}

    cov_matrix = returns.cov() * 252

    port_vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))

    if port_vol == 0:
        return {sym: 0.0 for sym in symbols}

    mctr = np.dot(cov_matrix, w) / port_vol

    return {symbols[i]: float(mctr[i]) for i in range(len(symbols))}

def calculate_risk_contribution_by_asset(weights: Dict[str, float], price_history: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """Calculate risk contribution for each asset

    Returns:
        {symbol: {'mctr': ..., 'risk_contribution': ..., 'pct_risk_contribution': ...}}
    """
    if not weights or price_history.empty:
        return {}

    symbols = [s for s in weights.keys() if s in price_history.columns]
    if not symbols:
        return {}

    w = np.array([weights[s] for s in symbols])
    w = w / np.sum(w)

    returns = price_history[symbols].pct_change(fill_method=None).dropna()
    if returns.empty:
        return {}

    cov_matrix = returns.cov() * 252

    port_vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))

    if port_vol == 0:
        return {sym: {'mctr': 0.0, 'risk_contribution': 0.0, 'pct_risk_contribution': 0.0} for sym in symbols}

    mctr = np.dot(cov_matrix, w) / port_vol
    risk_contrib = w * mctr
    pct_risk_contrib = risk_contrib / port_vol

    result = {}
    for i, sym in enumerate(symbols):
        result[sym] = {
            'mctr': float(mctr[i]),
            'risk_contribution': float(risk_contrib[i]),
            'pct_risk_contribution': float(pct_risk_contrib[i])
        }

    return result

def calculate_risk_contribution_by_sector(weights: Dict[str, float], price_history: pd.DataFrame, sector_map: Dict[str, str]) -> Dict[str, float]:
    """Calculate risk contribution aggregated by sector"""
    if not weights or price_history.empty or not sector_map:
        return {}

    asset_risk = calculate_risk_contribution_by_asset(weights, price_history)

    sector_risk = {}
    for symbol, risk_data in asset_risk.items():
        sector = sector_map.get(symbol, 'Unknown')
        sector_risk[sector] = sector_risk.get(sector, 0.0) + risk_data['pct_risk_contribution']

    return sector_risk
