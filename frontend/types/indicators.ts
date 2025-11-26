export interface ReturnsMetrics {
  simple_returns_mean: number;
  total_return: number;
  cagr: number;
  annualized_return: number;
  ytd_return: number;
  mtd_return: number;
  realized_pnl: number;
  unrealized_pnl: number;
  total_pnl: number;
  twr: number;
  irr: number;
  monthly_returns: { [key: string]: number };
}

export interface RiskMetrics {
  daily_volatility: number;
  annualized_volatility: number;
  upside_volatility: number;
  downside_volatility: number;
  semivariance: number;
  rolling_volatility_30d: number;
}

export interface DrawdownMetrics {
  max_drawdown: number;
  avg_drawdown: number;
  max_daily_loss: number;
  max_daily_gain: number;
  consecutive_loss_days: number;
  consecutive_gain_days: number;
  max_drawdown_duration?: number;
  longest_drawdown_period?: number;
  avg_drawdown_duration?: number;
  recovery_days?: number;
  recovered?: boolean;
  ulcer_index?: number;
}

export interface RiskAdjustedRatios {
  sharpe: number;
  sortino: number;
  calmar: number;
  rolling_sharpe_30d: number;
  treynor?: number;
  omega?: number;
  m2_measure?: number;
  gain_to_pain?: number;
  ulcer_performance_index?: number;
}

export interface TailRiskMetrics {
  var_95: number;
  cvar_95: number;
  skewness: number;
  kurtosis: number;
  tail_ratio?: number;
}

export interface AllocationMetrics {
  weights: { [symbol: string]: number };
  hhi: number;
  top_5_concentration: number;
  max_weight: number;
  weight_deviation_from_equal: number;
  long_short_exposure?: {
    long_exposure: number;
    short_exposure: number;
    net_exposure: number;
  };
  sector_allocation?: { [sector: string]: number };
}

export interface RiskDecompositionMetrics {
  portfolio_volatility: number;
  mctr: { [symbol: string]: number };
  by_asset: {
    [symbol: string]: {
      mctr: number;
      risk_contribution: number;
      pct_risk_contribution: number;
    };
  };
  by_sector?: { [sector: string]: number };
}

export interface TradingMetrics {
  trade_count: number;
  turnover_rate: number;
  avg_holding_period: number;
  win_rate: number;
  profit_loss_ratio: number;
  max_trade_profit: number;
  max_trade_loss: number;
  consecutive_winning_trades: number;
  consecutive_losing_trades: number;
  profit_factor?: number;
  recovery_factor?: number;
  kelly_criterion?: number;
}

export interface AllIndicators {
  returns: ReturnsMetrics;
  risk: RiskMetrics;
  drawdown: DrawdownMetrics;
  risk_adjusted_ratios: RiskAdjustedRatios;
  tail_risk: TailRiskMetrics;
  allocation?: AllocationMetrics;
  risk_decomposition?: RiskDecompositionMetrics;
  trading?: TradingMetrics;
}

export interface BasicIndicators {
  total_return: number;
  cagr: number;
  volatility: number;
  sharpe: number;
  max_drawdown: number;
}

export interface IndicatorItem {
  label: string;
  value: string | number;
  format?: 'percentage' | 'number' | 'currency' | 'days';
  trend?: 'up' | 'down' | 'neutral';
  description?: string;
}
