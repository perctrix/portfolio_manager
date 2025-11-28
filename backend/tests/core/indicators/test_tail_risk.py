"""Tests for tail_risk module"""
import pytest
import pandas as pd
import numpy as np
from app.core.indicators import tail_risk as tail_risk_module


class TestVaR:
    """Test suite for calculate_var"""

    def test_var_basic(self, sample_returns):
        """Test basic VaR calculation"""
        result = tail_risk_module.calculate_var(sample_returns, confidence_level=0.95)

        assert isinstance(result, float)
        assert result <= 0.0  # VaR should be negative (potential loss)

    def test_var_formula(self):
        """Test VaR as percentile"""
        returns = pd.Series([-0.05, -0.02, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08])
        confidence = 0.95

        result = tail_risk_module.calculate_var(returns, confidence_level=confidence)

        percentile = (1 - confidence) * 100
        expected = np.percentile(returns, percentile)
        assert np.isclose(result, expected)

    def test_var_empty(self, empty_series):
        """Test with empty series"""
        result = tail_risk_module.calculate_var(empty_series)
        assert result == 0.0

    @pytest.mark.parametrize("confidence", [0.90, 0.95, 0.99])
    def test_var_confidence_levels(self, sample_returns, confidence):
        """Test with different confidence levels"""
        result = tail_risk_module.calculate_var(sample_returns, confidence_level=confidence)
        assert isinstance(result, float)

    def test_var_ordering(self, sample_returns):
        """Test that higher confidence gives more extreme VaR"""
        var_90 = tail_risk_module.calculate_var(sample_returns, 0.90)
        var_95 = tail_risk_module.calculate_var(sample_returns, 0.95)
        var_99 = tail_risk_module.calculate_var(sample_returns, 0.99)

        # Higher confidence = more extreme (more negative) VaR
        assert var_99 <= var_95 <= var_90


class TestCVaR:
    """Test suite for calculate_cvar"""

    def test_cvar_basic(self, sample_returns):
        """Test basic CVaR calculation"""
        result = tail_risk_module.calculate_cvar(sample_returns, confidence_level=0.95)

        assert isinstance(result, float)
        assert result <= 0.0  # CVaR should be negative

    def test_cvar_formula(self):
        """Test CVaR as mean of returns beyond VaR"""
        returns = pd.Series([-0.05, -0.04, -0.03, -0.02, -0.01, 0.01, 0.02, 0.03, 0.04, 0.05])
        confidence = 0.90

        result = tail_risk_module.calculate_cvar(returns, confidence_level=confidence)

        var = tail_risk_module.calculate_var(returns, confidence)
        expected = returns[returns <= var].mean()
        assert np.isclose(result, expected)

    def test_cvar_empty(self, empty_series):
        """Test with empty series"""
        result = tail_risk_module.calculate_cvar(empty_series)
        assert result == 0.0

    def test_cvar_worse_than_var(self, sample_returns):
        """Test that CVaR <= VaR (CVaR is conditional expected loss)"""
        var = tail_risk_module.calculate_var(sample_returns, 0.95)
        cvar = tail_risk_module.calculate_cvar(sample_returns, 0.95)

        # CVaR should be more negative (worse) than VaR
        assert cvar <= var


class TestSkewness:
    """Test suite for calculate_skewness"""

    def test_skewness_basic(self, sample_returns):
        """Test basic skewness calculation"""
        result = tail_risk_module.calculate_skewness(sample_returns)

        assert isinstance(result, float)

    def test_skewness_symmetric(self):
        """Test skewness of symmetric distribution"""
        # Normal distribution should have skew close to 0
        np.random.seed(42)
        returns = pd.Series(np.random.randn(1000))

        result = tail_risk_module.calculate_skewness(returns)
        assert abs(result) < 0.5  # Should be close to 0

    def test_skewness_empty(self, empty_series):
        """Test with empty series"""
        result = tail_risk_module.calculate_skewness(empty_series)
        assert result == 0.0

    def test_skewness_positive(self):
        """Test positive skewness"""
        # Right-skewed distribution
        returns = pd.Series([0.01] * 90 + [0.10] * 10)

        result = tail_risk_module.calculate_skewness(returns)
        assert result > 0

    def test_skewness_negative(self):
        """Test negative skewness"""
        # Left-skewed distribution
        returns = pd.Series([0.01] * 90 + [-0.10] * 10)

        result = tail_risk_module.calculate_skewness(returns)
        assert result < 0


class TestKurtosis:
    """Test suite for calculate_kurtosis"""

    def test_kurtosis_basic(self, sample_returns):
        """Test basic kurtosis calculation"""
        result = tail_risk_module.calculate_kurtosis(sample_returns, excess=True)

        assert isinstance(result, float)

    def test_kurtosis_normal(self):
        """Test kurtosis of normal distribution"""
        np.random.seed(42)
        returns = pd.Series(np.random.randn(1000))

        # Excess kurtosis should be close to 0 for normal distribution
        result = tail_risk_module.calculate_kurtosis(returns, excess=True)
        assert abs(result) < 1.0

    def test_kurtosis_empty(self, empty_series):
        """Test with empty series"""
        result = tail_risk_module.calculate_kurtosis(empty_series)
        assert result == 0.0

    def test_kurtosis_excess_vs_normal(self):
        """Test difference between excess and normal kurtosis"""
        returns = pd.Series(np.random.randn(100))

        excess_kurt = tail_risk_module.calculate_kurtosis(returns, excess=True)
        normal_kurt = tail_risk_module.calculate_kurtosis(returns, excess=False)

        # Difference should be 3
        assert np.isclose(normal_kurt - excess_kurt, 3.0)

    def test_kurtosis_fat_tails(self):
        """Test kurtosis with fat-tailed distribution"""
        # Mix of normal and extreme values (fat tails)
        np.random.seed(42)
        normal_part = np.random.randn(90) * 0.01
        extreme_part = np.random.randn(10) * 0.10
        returns = pd.Series(np.concatenate([normal_part, extreme_part]))

        result = tail_risk_module.calculate_kurtosis(returns, excess=True)
        # Should have positive excess kurtosis (fat tails)
        assert result > 0


class TestTailRatio:
    """Test suite for calculate_tail_ratio"""

    def test_tail_ratio_basic(self, sample_returns):
        """Test basic tail ratio calculation"""
        result = tail_risk_module.calculate_tail_ratio(sample_returns)

        assert isinstance(result, float)
        assert result >= 0

    def test_tail_ratio_formula(self):
        """Test tail ratio formula: 95th percentile / abs(5th percentile)"""
        returns = pd.Series(range(-100, 101))

        result = tail_risk_module.calculate_tail_ratio(returns, percentile=95.0)

        upper = np.percentile(returns, 95)
        lower = np.percentile(returns, 5)
        expected = upper / abs(lower)
        assert np.isclose(result, expected)

    def test_tail_ratio_empty(self, empty_series):
        """Test with empty series"""
        result = tail_risk_module.calculate_tail_ratio(empty_series)
        assert result == 0.0

    def test_tail_ratio_symmetric(self):
        """Test tail ratio of symmetric distribution"""
        # Symmetric around 0
        returns = pd.Series(list(range(-50, 51)))

        result = tail_risk_module.calculate_tail_ratio(returns)
        # Should be close to 1 for symmetric distribution
        assert np.isclose(result, 1.0, rtol=0.1)

    def test_tail_ratio_positive_skew(self):
        """Test tail ratio with positive skew"""
        # Positive tail is stronger
        returns = pd.Series([-0.01] * 90 + [0.10] * 10)

        result = tail_risk_module.calculate_tail_ratio(returns)
        # Should be > 1 for positive skew
        assert result > 1.0

    @pytest.mark.parametrize("percentile", [90.0, 95.0, 99.0])
    def test_tail_ratio_percentiles(self, sample_returns, percentile):
        """Test with different percentiles"""
        result = tail_risk_module.calculate_tail_ratio(sample_returns, percentile=percentile)
        assert isinstance(result, float)
        assert result >= 0


@pytest.mark.parametrize("func_name,expected_type", [
    ("calculate_var", float),
    ("calculate_cvar", float),
    ("calculate_skewness", float),
    ("calculate_kurtosis", float),
    ("calculate_tail_ratio", float),
])
def test_tail_risk_functions_type(func_name, expected_type, sample_returns):
    """Parametrized test for tail risk function output types"""
    func = getattr(tail_risk_module, func_name)

    if 'kurtosis' in func_name:
        result = func(sample_returns, excess=True)
    elif 'var' in func_name or 'cvar' in func_name:
        result = func(sample_returns, confidence_level=0.95)
    else:
        result = func(sample_returns)

    assert isinstance(result, expected_type)


def test_var_cvar_relationship(sample_returns):
    """Test relationship between VaR and CVaR"""
    var = tail_risk_module.calculate_var(sample_returns, 0.95)
    cvar = tail_risk_module.calculate_cvar(sample_returns, 0.95)

    # CVaR should be <= VaR (more extreme)
    assert cvar <= var

    # Both should be negative (losses)
    assert var <= 0.0
    assert cvar <= 0.0
