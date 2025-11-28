"""Tests for risk module"""
import pytest
import pandas as pd
import numpy as np
from app.core.indicators import risk as risk_module


class TestDailyVolatility:
    """Test suite for calculate_daily_volatility"""

    def test_daily_volatility_basic(self, sample_returns):
        """Test basic daily volatility calculation"""
        result = risk_module.calculate_daily_volatility(sample_returns)

        assert isinstance(result, float)
        assert result >= 0

    def test_daily_volatility_formula(self):
        """Test that volatility is standard deviation"""
        returns = pd.Series([0.01, 0.02, -0.01, 0.015, -0.005])
        result = risk_module.calculate_daily_volatility(returns)

        expected = returns.std()
        assert np.isclose(result, expected)

    def test_daily_volatility_empty(self, empty_series):
        """Test with empty series"""
        result = risk_module.calculate_daily_volatility(empty_series)
        assert result == 0.0

    def test_daily_volatility_constant(self, zero_returns):
        """Test with constant returns (zero volatility)"""
        result = risk_module.calculate_daily_volatility(zero_returns)
        assert result == 0.0


class TestAnnualizedVolatility:
    """Test suite for calculate_annualized_volatility"""

    def test_annualized_volatility_basic(self, sample_returns):
        """Test basic annualized volatility"""
        result = risk_module.calculate_annualized_volatility(sample_returns)

        assert isinstance(result, float)
        assert result >= 0

    def test_annualized_volatility_formula(self):
        """Test annualization formula: daily_vol * sqrt(252)"""
        returns = pd.Series([0.01, 0.02, -0.01, 0.015, -0.005])
        result = risk_module.calculate_annualized_volatility(returns, periods_per_year=252)

        daily_vol = returns.std()
        expected = daily_vol * np.sqrt(252)
        assert np.isclose(result, expected)

    def test_annualized_volatility_empty(self, empty_series):
        """Test with empty series"""
        result = risk_module.calculate_annualized_volatility(empty_series)
        assert result == 0.0

    def test_annualized_volatility_custom_periods(self):
        """Test with custom periods per year"""
        returns = pd.Series([0.01] * 100)
        result = risk_module.calculate_annualized_volatility(returns, periods_per_year=12)

        daily_vol = returns.std()
        expected = daily_vol * np.sqrt(12)
        assert np.isclose(result, expected)


class TestRollingVolatility:
    """Test suite for calculate_rolling_volatility"""

    def test_rolling_volatility_basic(self, sample_returns):
        """Test basic rolling volatility"""
        result = risk_module.calculate_rolling_volatility(sample_returns, window=21)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_returns)

    def test_rolling_volatility_annualized(self, sample_returns):
        """Test rolling volatility with annualization"""
        result = risk_module.calculate_rolling_volatility(sample_returns, window=21, annualize=True)

        # Check that values are scaled by sqrt(252)
        result_not_ann = risk_module.calculate_rolling_volatility(sample_returns, window=21, annualize=False)

        # Non-NaN values should differ by factor of sqrt(252)
        valid_idx = ~result.isna() & ~result_not_ann.isna()
        if valid_idx.any():
            ratio = result[valid_idx] / result_not_ann[valid_idx]
            assert np.allclose(ratio, np.sqrt(252), rtol=0.01)

    def test_rolling_volatility_empty(self, empty_series):
        """Test with empty series"""
        result = risk_module.calculate_rolling_volatility(empty_series, window=21)
        assert result.empty

    @pytest.mark.parametrize("window", [5, 10, 20, 50, 100])
    def test_rolling_volatility_windows(self, sample_returns, window):
        """Test with various window sizes"""
        result = risk_module.calculate_rolling_volatility(sample_returns, window=window)

        assert len(result) == len(sample_returns)


class TestUpsideVolatility:
    """Test suite for calculate_upside_volatility"""

    def test_upside_volatility_basic(self, sample_returns):
        """Test basic upside volatility"""
        result = risk_module.calculate_upside_volatility(sample_returns)

        assert isinstance(result, float)
        assert result >= 0

    def test_upside_volatility_only_positive(self, positive_returns):
        """Test upside volatility with only positive returns"""
        result = risk_module.calculate_upside_volatility(positive_returns)

        # Should equal annualized volatility of all returns
        expected_vol = positive_returns.std() * np.sqrt(252)
        assert np.isclose(result, expected_vol, rtol=0.01)

    def test_upside_volatility_only_negative(self, negative_returns):
        """Test upside volatility with only negative returns"""
        result = risk_module.calculate_upside_volatility(negative_returns)

        # No positive returns, should be 0
        assert result == 0.0

    def test_upside_volatility_empty(self, empty_series):
        """Test with empty series"""
        result = risk_module.calculate_upside_volatility(empty_series)
        assert result == 0.0

    def test_upside_volatility_no_annualize(self, sample_returns):
        """Test without annualization"""
        result = risk_module.calculate_upside_volatility(sample_returns, annualize=False)

        upside_returns = sample_returns[sample_returns > 0]
        expected = upside_returns.std() if not upside_returns.empty else 0.0
        assert np.isclose(result, expected, rtol=0.01)


class TestDownsideVolatility:
    """Test suite for calculate_downside_volatility"""

    def test_downside_volatility_basic(self, sample_returns):
        """Test basic downside volatility"""
        result = risk_module.calculate_downside_volatility(sample_returns)

        assert isinstance(result, float)
        assert result >= 0

    def test_downside_volatility_only_negative(self, negative_returns):
        """Test downside volatility with only negative returns"""
        result = risk_module.calculate_downside_volatility(negative_returns)

        # Should equal annualized volatility of all returns
        expected_vol = negative_returns.std() * np.sqrt(252)
        assert np.isclose(result, expected_vol, rtol=0.01)

    def test_downside_volatility_only_positive(self, positive_returns):
        """Test downside volatility with only positive returns"""
        result = risk_module.calculate_downside_volatility(positive_returns)

        # No negative returns, should be 0
        assert result == 0.0

    def test_downside_volatility_empty(self, empty_series):
        """Test with empty series"""
        result = risk_module.calculate_downside_volatility(empty_series)
        assert result == 0.0

    def test_downside_volatility_custom_target(self):
        """Test with custom target return"""
        returns = pd.Series([0.02, 0.01, -0.01, 0.015, -0.005])
        target = 0.01

        result = risk_module.calculate_downside_volatility(returns, target_return=target)

        downside = returns[returns < target]
        expected = downside.std() * np.sqrt(252)
        assert np.isclose(result, expected, rtol=0.01)


class TestSemivariance:
    """Test suite for calculate_semivariance"""

    def test_semivariance_basic(self, sample_returns):
        """Test basic semivariance calculation"""
        result = risk_module.calculate_semivariance(sample_returns)

        assert isinstance(result, float)
        assert result >= 0

    def test_semivariance_formula(self):
        """Test semivariance formula: mean of squared downside deviations"""
        returns = pd.Series([0.02, 0.01, -0.01, 0.015, -0.005])
        target = 0.0

        result = risk_module.calculate_semivariance(returns, target_return=target)

        downside = returns[returns < target]
        expected = (downside ** 2).mean()
        assert np.isclose(result, expected)

    def test_semivariance_empty(self, empty_series):
        """Test with empty series"""
        result = risk_module.calculate_semivariance(empty_series)
        assert result == 0.0

    def test_semivariance_no_downside(self, positive_returns):
        """Test with no downside returns"""
        result = risk_module.calculate_semivariance(positive_returns)
        assert result == 0.0

    def test_semivariance_all_downside(self, negative_returns):
        """Test with all downside returns"""
        result = risk_module.calculate_semivariance(negative_returns)

        expected = (negative_returns ** 2).mean()
        assert np.isclose(result, expected)

    def test_semivariance_custom_target(self):
        """Test with custom target return"""
        returns = pd.Series([0.02, 0.01, -0.01, 0.015, -0.005])
        target = 0.01

        result = risk_module.calculate_semivariance(returns, target_return=target)

        downside = returns[returns < target]
        expected = (downside ** 2).mean()
        assert np.isclose(result, expected)


@pytest.mark.parametrize("func_name,expected_range", [
    ("calculate_daily_volatility", (0, float('inf'))),
    ("calculate_annualized_volatility", (0, float('inf'))),
    ("calculate_upside_volatility", (0, float('inf'))),
    ("calculate_downside_volatility", (0, float('inf'))),
    ("calculate_semivariance", (0, float('inf'))),
])
def test_risk_functions_non_negative(func_name, expected_range, sample_returns):
    """Parametrized test that risk measures are non-negative"""
    func = getattr(risk_module, func_name)
    result = func(sample_returns)

    assert result >= expected_range[0]


def test_volatility_relationship(sample_returns):
    """Test relationship between different volatility measures"""
    daily_vol = risk_module.calculate_daily_volatility(sample_returns)
    annual_vol = risk_module.calculate_annualized_volatility(sample_returns)

    # Annualized should be daily * sqrt(252)
    expected_annual = daily_vol * np.sqrt(252)
    assert np.isclose(annual_vol, expected_annual, rtol=0.01)
