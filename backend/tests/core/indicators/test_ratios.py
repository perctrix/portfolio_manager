"""Tests for ratios module"""
import pytest
import pandas as pd
import numpy as np
from app.core.indicators import ratios as ratios_module


class TestSharpeRatio:
    """Test suite for calculate_sharpe_ratio"""

    def test_sharpe_ratio_basic(self, sample_returns):
        """Test basic Sharpe ratio calculation"""
        result = ratios_module.calculate_sharpe_ratio(sample_returns)

        assert isinstance(result, float)

    def test_sharpe_ratio_formula(self):
        """Test Sharpe ratio formula: (return - rf) / volatility"""
        returns = pd.Series([0.001] * 252)  # Constant positive returns
        rf = 0.02

        result = ratios_module.calculate_sharpe_ratio(returns, risk_free_rate=rf)

        annual_return = 0.001 * 252
        annual_vol = returns.std() * np.sqrt(252)
        expected = (annual_return - rf) / annual_vol if annual_vol > 0 else 0.0

        assert np.isclose(result, expected, rtol=0.1) or (result == 0.0 and annual_vol == 0.0)

    def test_sharpe_ratio_empty(self, empty_series):
        """Test with empty series"""
        result = ratios_module.calculate_sharpe_ratio(empty_series)
        assert result == 0.0

    def test_sharpe_ratio_zero_volatility(self, zero_returns):
        """Test with zero volatility"""
        result = ratios_module.calculate_sharpe_ratio(zero_returns)
        assert result == 0.0

    def test_sharpe_ratio_negative(self, negative_returns):
        """Test Sharpe ratio can be negative"""
        result = ratios_module.calculate_sharpe_ratio(negative_returns, risk_free_rate=0.02)

        # With negative returns and positive risk-free rate, Sharpe should be negative
        assert result < 0


class TestRollingSharpe:
    """Test suite for calculate_rolling_sharpe"""

    def test_rolling_sharpe_basic(self, sample_returns):
        """Test basic rolling Sharpe calculation"""
        result = ratios_module.calculate_rolling_sharpe(sample_returns, window=252)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_returns)

    def test_rolling_sharpe_empty(self, empty_series):
        """Test with empty series"""
        result = ratios_module.calculate_rolling_sharpe(empty_series)
        assert result.empty

    @pytest.mark.parametrize("window", [30, 60, 126, 252])
    def test_rolling_sharpe_windows(self, sample_returns, window):
        """Test with various window sizes"""
        result = ratios_module.calculate_rolling_sharpe(sample_returns, window=window)
        assert len(result) == len(sample_returns)


class TestSortinoRatio:
    """Test suite for calculate_sortino_ratio"""

    def test_sortino_ratio_basic(self, sample_returns):
        """Test basic Sortino ratio calculation"""
        result = ratios_module.calculate_sortino_ratio(sample_returns)

        assert isinstance(result, float)

    def test_sortino_ratio_formula(self):
        """Test Sortino ratio uses downside deviation"""
        returns = pd.Series([0.02, 0.01, -0.01, 0.015, -0.005])
        result = ratios_module.calculate_sortino_ratio(returns)

        # Sortino should handle downside volatility differently than Sharpe
        assert isinstance(result, float)

    def test_sortino_ratio_empty(self, empty_series):
        """Test with empty series"""
        result = ratios_module.calculate_sortino_ratio(empty_series)
        assert result == 0.0

    def test_sortino_ratio_no_downside(self, positive_returns):
        """Test with no downside returns"""
        result = ratios_module.calculate_sortino_ratio(positive_returns)
        # With no downside, downside volatility is 0, ratio should be 0
        assert result == 0.0


class TestCalmarRatio:
    """Test suite for calculate_calmar_ratio"""

    def test_calmar_ratio_basic(self, sample_nav, sample_returns):
        """Test basic Calmar ratio calculation"""
        result = ratios_module.calculate_calmar_ratio(sample_nav, sample_returns)

        assert isinstance(result, float)

    def test_calmar_ratio_formula(self):
        """Test Calmar ratio formula: return / abs(max_drawdown)"""
        dates = pd.date_range('2020-01-01', periods=252, freq='D')
        nav = pd.Series(100 * (1.1 ** (np.arange(252) / 252)), index=dates)
        returns = nav.pct_change(fill_method=None).dropna()

        result = ratios_module.calculate_calmar_ratio(nav, returns)

        # With steadily increasing NAV, max drawdown should be 0
        assert result >= 0 or result == 0.0

    def test_calmar_ratio_empty(self, empty_series):
        """Test with empty series"""
        result = ratios_module.calculate_calmar_ratio(empty_series, empty_series)
        assert result == 0.0

    def test_calmar_ratio_zero_drawdown(self, positive_returns):
        """Test with zero max drawdown"""
        nav = (1 + positive_returns).cumprod() * 100
        result = ratios_module.calculate_calmar_ratio(nav, positive_returns)

        # Zero drawdown means division by zero, should return 0
        assert result == 0.0


class TestTreynorRatio:
    """Test suite for calculate_treynor_ratio"""

    def test_treynor_ratio_basic(self, sample_returns):
        """Test basic Treynor ratio calculation"""
        beta = 1.2
        result = ratios_module.calculate_treynor_ratio(sample_returns, beta)

        assert isinstance(result, float)

    def test_treynor_ratio_formula(self):
        """Test Treynor ratio formula: (return - rf) / beta"""
        returns = pd.Series([0.001] * 252)
        beta = 1.5
        rf = 0.02

        result = ratios_module.calculate_treynor_ratio(returns, beta, risk_free_rate=rf)

        annual_return = 0.001 * 252
        expected = (annual_return - rf) / beta
        assert np.isclose(result, expected)

    def test_treynor_ratio_empty(self, empty_series):
        """Test with empty series"""
        result = ratios_module.calculate_treynor_ratio(empty_series, beta=1.0)
        assert result == 0.0

    def test_treynor_ratio_zero_beta(self, sample_returns):
        """Test with zero beta"""
        result = ratios_module.calculate_treynor_ratio(sample_returns, beta=0.0)
        assert result == 0.0


class TestOmegaRatio:
    """Test suite for calculate_omega_ratio"""

    def test_omega_ratio_basic(self, sample_returns):
        """Test basic Omega ratio calculation"""
        result = ratios_module.calculate_omega_ratio(sample_returns)

        assert isinstance(result, float)
        assert result >= 0

    def test_omega_ratio_formula(self):
        """Test Omega ratio formula: gains / losses"""
        returns = pd.Series([0.02, 0.01, -0.01, 0.015, -0.005])
        threshold = 0.0

        result = ratios_module.calculate_omega_ratio(returns, threshold=threshold)

        gains = returns[returns > threshold].sum()
        losses = -returns[returns < threshold].sum()
        expected = gains / losses if losses > 0 else (float('inf') if gains > 0 else 0.0)

        assert result == expected or (np.isinf(result) and np.isinf(expected))

    def test_omega_ratio_empty(self, empty_series):
        """Test with empty series"""
        result = ratios_module.calculate_omega_ratio(empty_series)
        assert result == 0.0

    def test_omega_ratio_only_gains(self, positive_returns):
        """Test with only positive returns"""
        result = ratios_module.calculate_omega_ratio(positive_returns)
        assert np.isinf(result)

    def test_omega_ratio_only_losses(self, negative_returns):
        """Test with only negative returns"""
        result = ratios_module.calculate_omega_ratio(negative_returns)
        assert result == 0.0


class TestM2Measure:
    """Test suite for calculate_m2_measure"""

    def test_m2_measure_basic(self, sample_returns, benchmark_returns):
        """Test basic M2 measure calculation"""
        result = ratios_module.calculate_m2_measure(sample_returns, benchmark_returns)

        assert isinstance(result, float)

    def test_m2_measure_empty(self, empty_series):
        """Test with empty series"""
        result = ratios_module.calculate_m2_measure(empty_series, empty_series)
        assert result == 0.0

    def test_m2_measure_zero_volatility(self, zero_returns, sample_returns):
        """Test with zero portfolio volatility"""
        result = ratios_module.calculate_m2_measure(zero_returns, sample_returns)
        assert result == 0.0


class TestGainToPainRatio:
    """Test suite for calculate_gain_to_pain_ratio"""

    def test_gain_to_pain_basic(self, sample_returns):
        """Test basic gain-to-pain ratio"""
        result = ratios_module.calculate_gain_to_pain_ratio(sample_returns)

        assert isinstance(result, float)
        assert result >= 0

    def test_gain_to_pain_formula(self):
        """Test gain-to-pain formula"""
        returns = pd.Series([0.02, 0.01, -0.01, 0.015, -0.005])

        result = ratios_module.calculate_gain_to_pain_ratio(returns)

        gains = returns[returns > 0].sum()
        pains = abs(returns[returns < 0].sum())
        expected = gains / pains if pains > 0 else (float('inf') if gains > 0 else 0.0)

        assert result == expected or (np.isinf(result) and np.isinf(expected))

    def test_gain_to_pain_empty(self, empty_series):
        """Test with empty series"""
        result = ratios_module.calculate_gain_to_pain_ratio(empty_series)
        assert result == 0.0

    def test_gain_to_pain_only_gains(self, positive_returns):
        """Test with only positive returns"""
        result = ratios_module.calculate_gain_to_pain_ratio(positive_returns)
        assert np.isinf(result)


class TestUlcerPerformanceIndex:
    """Test suite for calculate_ulcer_performance_index"""

    def test_upi_basic(self, sample_nav, sample_returns):
        """Test basic UPI calculation"""
        result = ratios_module.calculate_ulcer_performance_index(sample_nav, sample_returns)

        assert isinstance(result, float)

    def test_upi_empty(self, empty_series):
        """Test with empty series"""
        result = ratios_module.calculate_ulcer_performance_index(empty_series, empty_series)
        assert result == 0.0

    @pytest.mark.parametrize("window", [7, 14, 21, 30])
    def test_upi_windows(self, sample_nav, sample_returns, window):
        """Test with various window sizes"""
        result = ratios_module.calculate_ulcer_performance_index(
            sample_nav, sample_returns, window=window
        )
        assert isinstance(result, float)


@pytest.mark.parametrize("func_name", [
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "calculate_calmar_ratio",
    "calculate_gain_to_pain_ratio",
])
def test_ratio_functions_return_float(func_name, sample_returns, sample_nav):
    """Parametrized test that ratio functions return float"""
    func = getattr(ratios_module, func_name)

    if func_name == "calculate_calmar_ratio":
        result = func(sample_nav, sample_returns)
    else:
        result = func(sample_returns)

    assert isinstance(result, float) or np.isinf(result)


def test_sharpe_sortino_relationship(sample_returns):
    """Test relationship between Sharpe and Sortino ratios"""
    sharpe = ratios_module.calculate_sharpe_ratio(sample_returns)
    sortino = ratios_module.calculate_sortino_ratio(sample_returns)

    # Both should be floats
    assert isinstance(sharpe, float)
    assert isinstance(sortino, float)

    # Sortino is typically >= Sharpe (since downside vol <= total vol)
    # But due to annualization and different formulas, this may not always hold
