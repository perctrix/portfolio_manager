from .utils import rolling_normalize

from .returns import (
    calculate_simple_returns,
    calculate_log_returns,
    calculate_cumulative_returns,
    calculate_annualized_return,
    calculate_cagr,
    calculate_monthly_returns,
    calculate_yearly_returns,
    calculate_ytd_return,
    calculate_mtd_return,
    calculate_rolling_return,
    calculate_realized_pnl,
    calculate_unrealized_pnl,
    calculate_total_pnl,
    calculate_trade_pnl,
    calculate_twr,
    calculate_irr
)

from .risk import (
    calculate_daily_volatility,
    calculate_annualized_volatility,
    calculate_rolling_volatility,
    calculate_upside_volatility,
    calculate_downside_volatility,
    calculate_semivariance
)

from .drawdown import (
    calculate_drawdown_series,
    calculate_max_drawdown,
    calculate_drawdown_duration,
    calculate_avg_drawdown,
    calculate_recovery_time,
    calculate_max_daily_loss,
    calculate_max_daily_gain,
    calculate_consecutive_loss_days,
    calculate_consecutive_gain_days,
    calculate_ulcer_index
)

from .ratios import (
    calculate_sharpe_ratio,
    calculate_rolling_sharpe,
    calculate_sortino_ratio,
    calculate_calmar_ratio,
    calculate_treynor_ratio,
    calculate_omega_ratio,
    calculate_m2_measure,
    calculate_gain_to_pain_ratio,
    calculate_ulcer_performance_index
)

from .allocation import (
    calculate_weights,
    calculate_weight_history,
    calculate_top_n_concentration,
    calculate_hhi,
    calculate_sector_allocation,
    calculate_industry_allocation,
    calculate_max_weight,
    calculate_weight_deviation_from_equal,
    calculate_long_short_exposure,
    calculate_portfolio_volatility,
    calculate_mctr,
    calculate_risk_contribution_by_asset,
    calculate_risk_contribution_by_sector
)

from .trading import (
    calculate_trade_count,
    calculate_turnover_rate,
    calculate_turnover_rate_by_asset,
    calculate_avg_holding_period,
    calculate_win_rate,
    calculate_profit_loss_ratio,
    calculate_max_trade_profit,
    calculate_max_trade_loss,
    calculate_consecutive_winning_trades,
    calculate_consecutive_losing_trades,
    calculate_all_trading_metrics,
    calculate_profit_factor,
    calculate_recovery_factor,
    calculate_kelly_criterion
)

from .technical import (
    calculate_sma,
    calculate_ema,
    calculate_wma,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_donchian_channel,
    calculate_atr,
    calculate_roc,
    calculate_momentum,
    calculate_stochastic,
    calculate_rsi,
    calculate_cci,
    calculate_williams_r,
    calculate_52week_high,
    calculate_52week_low,
    calculate_distance_from_52week_high,
    calculate_n_day_high,
    calculate_n_day_low,
    calculate_position_in_range,
    calculate_connors_rsi,
    apply_kalman_filter,
    apply_fft_filter_rolling,
    calculate_technical_indicators_batch
)

from .tail_risk import (
    calculate_var,
    calculate_cvar,
    calculate_skewness,
    calculate_kurtosis,
    calculate_tail_ratio
)

from .correlation_beta import (
    calculate_correlation_to_portfolio,
    calculate_correlation_matrix,
    calculate_covariance_matrix,
    calculate_beta,
    calculate_alpha,
    calculate_r_squared,
    calculate_tracking_error,
    calculate_information_ratio,
    calculate_all_benchmark_metrics,
    calculate_multi_benchmark_metrics,
    calculate_mean_pairwise_correlation,
    calculate_max_min_correlation,
    calculate_upside_capture,
    calculate_downside_capture
)

from .aggregator import (
    calculate_all_portfolio_indicators,
    calculate_basic_portfolio_indicators
)

def calculate_basic_metrics(nav_series):
    """Backward compatibility alias for calculate_basic_portfolio_indicators"""
    return calculate_basic_portfolio_indicators(nav_series)

def calculate_risk_metrics(returns_series, risk_free_rate: float = 0.0):
    """Backward compatibility: Calculate advanced risk metrics"""
    from .ratios import calculate_sortino_ratio, calculate_calmar_ratio
    from .tail_risk import calculate_var, calculate_cvar, calculate_skewness, calculate_kurtosis
    from .returns import calculate_annualized_return
    from .drawdown import calculate_max_drawdown

    if returns_series.empty:
        return {}

    nav = (1 + returns_series).cumprod()

    return {
        "sortino": calculate_sortino_ratio(returns_series, risk_free_rate=risk_free_rate),
        "calmar": calculate_calmar_ratio(nav, returns_series),
        "var_95": calculate_var(returns_series, 0.95),
        "cvar_95": calculate_cvar(returns_series, 0.95),
        "skewness": calculate_skewness(returns_series),
        "kurtosis": calculate_kurtosis(returns_series, excess=True)
    }

def calculate_allocation_metrics(weights):
    """Backward compatibility: Calculate allocation metrics"""
    from .allocation import calculate_hhi, calculate_top_n_concentration

    if not weights:
        return {}

    return {
        "hhi": calculate_hhi(weights),
        "top_5_concentration": calculate_top_n_concentration(weights, 5)
    }

def calculate_risk_contribution(weights, price_history):
    """Backward compatibility: Calculate risk contribution"""
    from .allocation import calculate_portfolio_volatility, calculate_risk_contribution_by_asset

    if not weights or price_history.empty:
        return {}

    portfolio_volatility = calculate_portfolio_volatility(weights, price_history)
    risk_decomp = calculate_risk_contribution_by_asset(weights, price_history)

    return {
        "portfolio_volatility": portfolio_volatility,
        "risk_decomposition": risk_decomp
    }

__all__ = [
    'rolling_normalize',
    'calculate_simple_returns',
    'calculate_log_returns',
    'calculate_cumulative_returns',
    'calculate_annualized_return',
    'calculate_cagr',
    'calculate_monthly_returns',
    'calculate_yearly_returns',
    'calculate_ytd_return',
    'calculate_mtd_return',
    'calculate_rolling_return',
    'calculate_realized_pnl',
    'calculate_unrealized_pnl',
    'calculate_total_pnl',
    'calculate_trade_pnl',
    'calculate_twr',
    'calculate_irr',
    'calculate_daily_volatility',
    'calculate_annualized_volatility',
    'calculate_rolling_volatility',
    'calculate_upside_volatility',
    'calculate_downside_volatility',
    'calculate_semivariance',
    'calculate_drawdown_series',
    'calculate_max_drawdown',
    'calculate_drawdown_duration',
    'calculate_avg_drawdown',
    'calculate_recovery_time',
    'calculate_max_daily_loss',
    'calculate_max_daily_gain',
    'calculate_consecutive_loss_days',
    'calculate_consecutive_gain_days',
    'calculate_ulcer_index',
    'calculate_sharpe_ratio',
    'calculate_rolling_sharpe',
    'calculate_sortino_ratio',
    'calculate_calmar_ratio',
    'calculate_treynor_ratio',
    'calculate_omega_ratio',
    'calculate_m2_measure',
    'calculate_gain_to_pain_ratio',
    'calculate_ulcer_performance_index',
    'calculate_weights',
    'calculate_weight_history',
    'calculate_top_n_concentration',
    'calculate_hhi',
    'calculate_sector_allocation',
    'calculate_industry_allocation',
    'calculate_max_weight',
    'calculate_weight_deviation_from_equal',
    'calculate_long_short_exposure',
    'calculate_portfolio_volatility',
    'calculate_mctr',
    'calculate_risk_contribution_by_asset',
    'calculate_risk_contribution_by_sector',
    'calculate_trade_count',
    'calculate_turnover_rate',
    'calculate_turnover_rate_by_asset',
    'calculate_avg_holding_period',
    'calculate_win_rate',
    'calculate_profit_loss_ratio',
    'calculate_max_trade_profit',
    'calculate_max_trade_loss',
    'calculate_consecutive_winning_trades',
    'calculate_consecutive_losing_trades',
    'calculate_all_trading_metrics',
    'calculate_profit_factor',
    'calculate_recovery_factor',
    'calculate_kelly_criterion',
    'calculate_sma',
    'calculate_ema',
    'calculate_wma',
    'calculate_macd',
    'calculate_bollinger_bands',
    'calculate_donchian_channel',
    'calculate_atr',
    'calculate_roc',
    'calculate_momentum',
    'calculate_stochastic',
    'calculate_rsi',
    'calculate_cci',
    'calculate_williams_r',
    'calculate_52week_high',
    'calculate_52week_low',
    'calculate_distance_from_52week_high',
    'calculate_n_day_high',
    'calculate_n_day_low',
    'calculate_position_in_range',
    'calculate_connors_rsi',
    'apply_kalman_filter',
    'apply_fft_filter_rolling',
    'calculate_technical_indicators_batch',
    'calculate_var',
    'calculate_cvar',
    'calculate_skewness',
    'calculate_kurtosis',
    'calculate_tail_ratio',
    'calculate_correlation_to_portfolio',
    'calculate_correlation_matrix',
    'calculate_covariance_matrix',
    'calculate_beta',
    'calculate_alpha',
    'calculate_r_squared',
    'calculate_tracking_error',
    'calculate_information_ratio',
    'calculate_all_benchmark_metrics',
    'calculate_multi_benchmark_metrics',
    'calculate_mean_pairwise_correlation',
    'calculate_max_min_correlation',
    'calculate_upside_capture',
    'calculate_downside_capture',
    'calculate_all_portfolio_indicators',
    'calculate_basic_portfolio_indicators',
    'calculate_basic_metrics',
    'calculate_risk_metrics',
    'calculate_allocation_metrics',
    'calculate_risk_contribution'
]
