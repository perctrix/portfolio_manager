import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from scipy.optimize import minimize


def calculate_expected_returns(returns_df: pd.DataFrame, annualize: bool = True) -> pd.Series:
    """Calculate expected returns for each asset using historical mean.

    Args:
        returns_df: DataFrame with columns as assets, rows as dates, values as daily returns
        annualize: If True, annualize the returns (multiply by 252)

    Returns:
        Series of expected returns per asset
    """
    if returns_df.empty:
        return pd.Series(dtype=float)

    mean_returns = returns_df.mean()

    if annualize:
        mean_returns = mean_returns * 252

    return mean_returns


def calculate_covariance_matrix(returns_df: pd.DataFrame, annualize: bool = True) -> pd.DataFrame:
    """Calculate covariance matrix from returns.

    Args:
        returns_df: DataFrame with columns as assets, rows as dates, values as daily returns
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


def _portfolio_variance(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
    """Calculate portfolio variance: w'Sigma*w"""
    return float(np.dot(weights.T, np.dot(cov_matrix, weights)))


def _portfolio_volatility(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
    """Calculate portfolio volatility (standard deviation)"""
    return float(np.sqrt(_portfolio_variance(weights, cov_matrix)))


def _portfolio_return(weights: np.ndarray, expected_returns: np.ndarray) -> float:
    """Calculate portfolio expected return: w'mu"""
    return float(np.dot(weights, expected_returns))


def _portfolio_sharpe(
    weights: np.ndarray,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float
) -> float:
    """Calculate portfolio Sharpe ratio"""
    port_return = _portfolio_return(weights, expected_returns)
    port_vol = _portfolio_volatility(weights, cov_matrix)

    if port_vol == 0:
        return 0.0

    return (port_return - risk_free_rate) / port_vol


def _neg_sharpe(
    weights: np.ndarray,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float
) -> float:
    """Negative Sharpe ratio for minimization"""
    return -_portfolio_sharpe(weights, expected_returns, cov_matrix, risk_free_rate)


def _regularize_covariance(cov_matrix: np.ndarray, epsilon: float = 1e-8) -> np.ndarray:
    """Add small regularization to covariance matrix to ensure positive definiteness"""
    n = cov_matrix.shape[0]
    return cov_matrix + epsilon * np.eye(n)


def calculate_gmv_portfolio(
    cov_matrix: pd.DataFrame,
    allow_short_selling: bool = False
) -> Dict[str, Any]:
    """Calculate Global Minimum Variance portfolio.

    Analytical solution (if short selling allowed):
        w_GMV = (Sigma^-1 * 1) / (1^T * Sigma^-1 * 1)

    Numerical solution (if no short selling):
        Uses scipy.optimize.minimize with bounds

    Args:
        cov_matrix: Annualized covariance matrix
        allow_short_selling: Whether negative weights are allowed

    Returns:
        Dictionary with 'weights', 'volatility', 'symbols'
    """
    if cov_matrix.empty:
        return {'weights': {}, 'volatility': 0.0}

    symbols = list(cov_matrix.columns)
    n = len(symbols)
    cov_np = cov_matrix.values

    cov_reg = _regularize_covariance(cov_np)

    if allow_short_selling:
        try:
            cov_inv = np.linalg.inv(cov_reg)
            ones = np.ones(n)
            weights = np.dot(cov_inv, ones) / np.dot(ones.T, np.dot(cov_inv, ones))
            volatility = _portfolio_volatility(weights, cov_np)

            return {
                'weights': {symbols[i]: float(weights[i]) for i in range(n)},
                'volatility': volatility,
                'symbols': symbols
            }
        except np.linalg.LinAlgError:
            pass

    initial_weights = np.ones(n) / n

    constraints = [
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
    ]

    if allow_short_selling:
        bounds = [(None, None) for _ in range(n)]
    else:
        bounds = [(0.0, 1.0) for _ in range(n)]

    result = minimize(
        fun=lambda w: _portfolio_variance(w, cov_np),
        x0=initial_weights,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'ftol': 1e-10, 'maxiter': 1000}
    )

    if result.success:
        weights = result.x
        volatility = _portfolio_volatility(weights, cov_np)
    else:
        weights = initial_weights
        volatility = _portfolio_volatility(weights, cov_np)

    return {
        'weights': {symbols[i]: float(weights[i]) for i in range(n)},
        'volatility': volatility,
        'symbols': symbols
    }


def calculate_tangent_portfolio(
    expected_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    risk_free_rate: float = 0.0,
    allow_short_selling: bool = False
) -> Optional[Dict[str, Any]]:
    """Calculate Maximum Sharpe Ratio (Tangent) portfolio.

    Analytical solution (if short selling allowed):
        w_tan = Sigma^-1 * (mu - rf) / (1^T * Sigma^-1 * (mu - rf))

    Numerical solution (if no short selling):
        Maximize: (w'mu - rf) / sqrt(w'Sigma*w)

    Args:
        expected_returns: Expected returns per asset (annualized)
        cov_matrix: Annualized covariance matrix
        risk_free_rate: Annual risk-free rate
        allow_short_selling: Whether negative weights are allowed

    Returns:
        Dictionary with 'weights', 'expected_return', 'volatility', 'sharpe_ratio'
        or None if optimization fails
    """
    if expected_returns.empty or cov_matrix.empty:
        return None

    symbols = list(cov_matrix.columns)
    expected_returns = expected_returns.reindex(symbols)

    if expected_returns.isna().any():
        return None

    n = len(symbols)
    mu = expected_returns.values
    cov_np = cov_matrix.values
    cov_reg = _regularize_covariance(cov_np)

    excess_returns = mu - risk_free_rate

    if np.all(excess_returns <= 0):
        return None

    if allow_short_selling:
        try:
            cov_inv = np.linalg.inv(cov_reg)
            numerator = np.dot(cov_inv, excess_returns)
            denominator = np.dot(np.ones(n).T, numerator)

            if abs(denominator) < 1e-10:
                return None

            weights = numerator / denominator

            port_return = _portfolio_return(weights, mu)
            port_vol = _portfolio_volatility(weights, cov_np)
            sharpe = _portfolio_sharpe(weights, mu, cov_np, risk_free_rate)

            return {
                'weights': {symbols[i]: float(weights[i]) for i in range(n)},
                'expected_return': port_return,
                'volatility': port_vol,
                'sharpe_ratio': sharpe,
                'symbols': symbols
            }
        except np.linalg.LinAlgError:
            pass

    initial_weights = np.ones(n) / n

    constraints = [
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
    ]

    if allow_short_selling:
        bounds = [(None, None) for _ in range(n)]
    else:
        bounds = [(0.0, 1.0) for _ in range(n)]

    result = minimize(
        fun=lambda w: _neg_sharpe(w, mu, cov_np, risk_free_rate),
        x0=initial_weights,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'ftol': 1e-10, 'maxiter': 1000}
    )

    if result.success:
        weights = result.x
        port_return = _portfolio_return(weights, mu)
        port_vol = _portfolio_volatility(weights, cov_np)
        sharpe = _portfolio_sharpe(weights, mu, cov_np, risk_free_rate)

        if sharpe <= 0:
            return None

        return {
            'weights': {symbols[i]: float(weights[i]) for i in range(n)},
            'expected_return': port_return,
            'volatility': port_vol,
            'sharpe_ratio': sharpe,
            'symbols': symbols
        }

    return None


def calculate_efficient_portfolio_for_return(
    expected_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    target_return: float,
    allow_short_selling: bool = False
) -> Optional[Dict[str, Any]]:
    """Calculate minimum variance portfolio for a target return.

    Minimize: w'Sigma*w
    Subject to: w'mu = target_return, sum(w) = 1, w >= 0 (if no short selling)

    Args:
        expected_returns: Expected returns per asset (annualized)
        cov_matrix: Annualized covariance matrix
        target_return: Target expected return
        allow_short_selling: Whether negative weights are allowed

    Returns:
        Dictionary with 'weights', 'expected_return', 'volatility'
        or None if infeasible
    """
    if expected_returns.empty or cov_matrix.empty:
        return None

    symbols = list(cov_matrix.columns)
    expected_returns = expected_returns.reindex(symbols)

    if expected_returns.isna().any():
        return None

    n = len(symbols)
    mu = expected_returns.values
    cov_np = cov_matrix.values

    if not allow_short_selling:
        if target_return > mu.max() or target_return < mu.min():
            return None

    initial_weights = np.ones(n) / n

    constraints = [
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},
        {'type': 'eq', 'fun': lambda w: np.dot(w, mu) - target_return}
    ]

    if allow_short_selling:
        bounds = [(None, None) for _ in range(n)]
    else:
        bounds = [(0.0, 1.0) for _ in range(n)]

    result = minimize(
        fun=lambda w: _portfolio_variance(w, cov_np),
        x0=initial_weights,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'ftol': 1e-10, 'maxiter': 1000}
    )

    if result.success:
        weights = result.x
        port_return = _portfolio_return(weights, mu)
        port_vol = _portfolio_volatility(weights, cov_np)

        return {
            'weights': {symbols[i]: float(weights[i]) for i in range(n)},
            'expected_return': port_return,
            'volatility': port_vol,
            'symbols': symbols
        }

    return None


def generate_efficient_frontier(
    expected_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    num_points: int = 50,
    risk_free_rate: float = 0.0,
    allow_short_selling: bool = False
) -> List[Dict[str, Any]]:
    """Generate points along the efficient frontier.

    Args:
        expected_returns: Expected returns per asset (annualized)
        cov_matrix: Annualized covariance matrix
        num_points: Number of frontier points to generate
        risk_free_rate: Annual risk-free rate
        allow_short_selling: Whether negative weights are allowed

    Returns:
        List of dictionaries with 'expected_return', 'volatility', 'sharpe_ratio', 'weights'
    """
    if expected_returns.empty or cov_matrix.empty:
        return []

    symbols = list(cov_matrix.columns)
    expected_returns = expected_returns.reindex(symbols)

    if expected_returns.isna().any():
        return []

    mu = expected_returns.values
    cov_np = cov_matrix.values

    gmv_result = calculate_gmv_portfolio(cov_matrix, allow_short_selling)
    gmv_weights = np.array([gmv_result['weights'].get(s, 0) for s in symbols])
    gmv_return = _portfolio_return(gmv_weights, mu)

    if allow_short_selling:
        max_return = max(mu) * 1.5
    else:
        max_return = max(mu)

    target_returns = np.linspace(gmv_return, max_return, num_points)

    frontier_points = []

    for target in target_returns:
        portfolio = calculate_efficient_portfolio_for_return(
            expected_returns,
            cov_matrix,
            target,
            allow_short_selling
        )

        if portfolio is not None:
            weights_array = np.array([portfolio['weights'].get(s, 0) for s in symbols])
            sharpe = _portfolio_sharpe(weights_array, mu, cov_np, risk_free_rate)

            frontier_points.append({
                'expected_return': portfolio['expected_return'],
                'volatility': portfolio['volatility'],
                'sharpe_ratio': sharpe,
                'weights': portfolio['weights']
            })

    return frontier_points


def calculate_current_portfolio_position(
    weights: Dict[str, float],
    expected_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    risk_free_rate: float = 0.0
) -> Dict[str, Any]:
    """Calculate current portfolio's return/risk position.

    Args:
        weights: Current portfolio weights {symbol: weight}
        expected_returns: Expected returns per asset (annualized)
        cov_matrix: Annualized covariance matrix
        risk_free_rate: Annual risk-free rate

    Returns:
        Dictionary with 'expected_return', 'volatility', 'sharpe_ratio', 'weights'
    """
    if not weights or expected_returns.empty or cov_matrix.empty:
        return {
            'expected_return': 0.0,
            'volatility': 0.0,
            'sharpe_ratio': 0.0,
            'weights': weights
        }

    symbols = list(cov_matrix.columns)
    weights_normalized = {s: weights.get(s, 0) for s in symbols}

    total_weight = sum(weights_normalized.values())
    if total_weight > 0:
        weights_normalized = {s: w / total_weight for s, w in weights_normalized.items()}

    weights_array = np.array([weights_normalized.get(s, 0) for s in symbols])
    mu = expected_returns.reindex(symbols).values
    cov_np = cov_matrix.values

    port_return = _portfolio_return(weights_array, mu)
    port_vol = _portfolio_volatility(weights_array, cov_np)
    sharpe = _portfolio_sharpe(weights_array, mu, cov_np, risk_free_rate)

    return {
        'expected_return': port_return,
        'volatility': port_vol,
        'sharpe_ratio': sharpe,
        'weights': weights_normalized
    }


def calculate_asset_statistics(
    expected_returns: pd.Series,
    cov_matrix: pd.DataFrame
) -> Dict[str, Dict[str, float]]:
    """Calculate individual asset statistics.

    Args:
        expected_returns: Expected returns per asset
        cov_matrix: Covariance matrix

    Returns:
        Dictionary of {symbol: {'expected_return': ..., 'volatility': ...}}
    """
    if expected_returns.empty or cov_matrix.empty:
        return {}

    result = {}
    for symbol in expected_returns.index:
        if symbol in cov_matrix.columns:
            volatility = float(np.sqrt(cov_matrix.loc[symbol, symbol]))
            result[symbol] = {
                'expected_return': float(expected_returns[symbol]),
                'volatility': volatility
            }

    return result


def calculate_efficient_frontier_analysis(
    returns_df: pd.DataFrame,
    current_weights: Dict[str, float],
    risk_free_rate: float = 0.0,
    allow_short_selling: bool = False,
    num_frontier_points: int = 50
) -> Optional[Dict[str, Any]]:
    """Main entry point for efficient frontier analysis.

    Args:
        returns_df: Daily returns DataFrame (columns=assets, rows=dates)
        current_weights: Current portfolio weights
        risk_free_rate: Annual risk-free rate
        allow_short_selling: Whether to allow short positions
        num_frontier_points: Number of points on the frontier

    Returns:
        Dictionary with complete efficient frontier analysis or None if insufficient data
    """
    if returns_df.empty or len(returns_df.columns) < 2:
        return None

    if len(returns_df) < 30:
        return None

    common_symbols = [s for s in current_weights.keys() if s in returns_df.columns]
    if len(common_symbols) < 2:
        return None

    returns_df = returns_df[common_symbols]
    current_weights = {s: current_weights[s] for s in common_symbols}

    expected_returns = calculate_expected_returns(returns_df, annualize=True)
    cov_matrix = calculate_covariance_matrix(returns_df, annualize=True)

    frontier_points = generate_efficient_frontier(
        expected_returns,
        cov_matrix,
        num_frontier_points,
        risk_free_rate,
        allow_short_selling
    )

    gmv_result = calculate_gmv_portfolio(cov_matrix, allow_short_selling)
    gmv_weights_array = np.array([gmv_result['weights'].get(s, 0) for s in common_symbols])
    gmv_return = _portfolio_return(gmv_weights_array, expected_returns.values)
    gmv_sharpe = _portfolio_sharpe(
        gmv_weights_array,
        expected_returns.values,
        cov_matrix.values,
        risk_free_rate
    )

    gmv_portfolio = {
        'expected_return': gmv_return,
        'volatility': gmv_result['volatility'],
        'sharpe_ratio': gmv_sharpe,
        'weights': gmv_result['weights']
    }

    tangent_portfolio = calculate_tangent_portfolio(
        expected_returns,
        cov_matrix,
        risk_free_rate,
        allow_short_selling
    )

    current_portfolio = calculate_current_portfolio_position(
        current_weights,
        expected_returns,
        cov_matrix,
        risk_free_rate
    )

    asset_stats = calculate_asset_statistics(expected_returns, cov_matrix)

    return {
        'frontier_points': frontier_points,
        'gmv_portfolio': gmv_portfolio,
        'tangent_portfolio': tangent_portfolio,
        'current_portfolio': current_portfolio,
        'asset_stats': asset_stats,
        'allow_short_selling': allow_short_selling
    }
