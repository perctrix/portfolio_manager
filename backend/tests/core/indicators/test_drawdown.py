"""Tests for drawdown module"""
import pytest
import pandas as pd
import numpy as np
from app.core.indicators import drawdown as drawdown_module


class TestDrawdownSeries:
    """Test suite for calculate_drawdown_series"""

    def test_drawdown_series_basic(self, sample_nav):
        """Test basic drawdown series calculation"""
        result = drawdown_module.calculate_drawdown_series(sample_nav)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_nav)
        assert (result <= 0).all()  # Drawdowns are non-positive

    def test_drawdown_series_formula(self):
        """Test drawdown formula: (NAV - peak) / peak"""
        nav = pd.Series([100, 110, 105, 115, 120],
                        index=pd.date_range('2020-01-01', periods=5))

        result = drawdown_module.calculate_drawdown_series(nav)

        assert result.iloc[0] == 0.0  # First value is at peak
        assert result.iloc[1] == 0.0  # New peak
        assert np.isclose(result.iloc[2], (105 - 110) / 110)
        assert result.iloc[3] == 0.0  # New peak
        assert result.iloc[4] == 0.0  # New peak

    def test_drawdown_series_empty(self, empty_series):
        """Test with empty series"""
        result = drawdown_module.calculate_drawdown_series(empty_series)
        assert result.empty

    def test_drawdown_series_increasing(self):
        """Test with always increasing NAV"""
        nav = pd.Series([100, 110, 120, 130],
                        index=pd.date_range('2020-01-01', periods=4))

        result = drawdown_module.calculate_drawdown_series(nav)

        # Should be all zeros
        assert (result == 0.0).all()

    def test_drawdown_series_decreasing(self):
        """Test with always decreasing NAV"""
        nav = pd.Series([100, 90, 80, 70],
                        index=pd.date_range('2020-01-01', periods=4))

        result = drawdown_module.calculate_drawdown_series(nav)

        # Should be increasingly negative
        assert (result <= 0).all()
        assert result.iloc[0] == 0.0
        assert result.iloc[1] < result.iloc[0]


class TestMaxDrawdown:
    """Test suite for calculate_max_drawdown"""

    def test_max_drawdown_basic(self, sample_nav):
        """Test basic max drawdown calculation"""
        result = drawdown_module.calculate_max_drawdown(sample_nav)

        assert isinstance(result, float)
        assert result <= 0.0  # Max drawdown is non-positive

    def test_max_drawdown_formula(self):
        """Test max drawdown is minimum of drawdown series"""
        nav = pd.Series([100, 110, 80, 90],
                        index=pd.date_range('2020-01-01', periods=4))

        result = drawdown_module.calculate_max_drawdown(nav)

        # Max drawdown should be at index 2: (80 - 110) / 110
        expected = (80 - 110) / 110
        assert np.isclose(result, expected)

    def test_max_drawdown_empty(self, empty_series):
        """Test with empty series"""
        result = drawdown_module.calculate_max_drawdown(empty_series)
        assert result == 0.0

    def test_max_drawdown_increasing(self):
        """Test with always increasing NAV"""
        nav = pd.Series([100, 110, 120, 130],
                        index=pd.date_range('2020-01-01', periods=4))

        result = drawdown_module.calculate_max_drawdown(nav)
        assert result == 0.0

    def test_max_drawdown_crash_recovery(self):
        """Test max drawdown with crash and recovery"""
        nav = pd.Series([100, 120, 60, 100],
                        index=pd.date_range('2020-01-01', periods=4))

        result = drawdown_module.calculate_max_drawdown(nav)

        # Max drawdown at index 2: (60 - 120) / 120 = -0.5
        expected = (60 - 120) / 120
        assert np.isclose(result, expected)


class TestDrawdownDuration:
    """Test suite for calculate_drawdown_duration"""

    def test_drawdown_duration_basic(self, sample_nav):
        """Test basic drawdown duration calculation"""
        result = drawdown_module.calculate_drawdown_duration(sample_nav)

        assert isinstance(result, dict)
        assert 'max_drawdown_duration' in result
        assert 'longest_drawdown_period' in result
        assert 'avg_drawdown_duration' in result

    def test_drawdown_duration_empty(self, empty_series):
        """Test with empty series"""
        result = drawdown_module.calculate_drawdown_duration(empty_series)
        assert result == {}

    def test_drawdown_duration_no_drawdown(self):
        """Test with no drawdowns"""
        nav = pd.Series([100, 110, 120, 130],
                        index=pd.date_range('2020-01-01', periods=4))

        result = drawdown_module.calculate_drawdown_duration(nav)

        assert result['max_drawdown_duration'] == 0.0
        assert result['longest_drawdown_period'] == 0.0
        assert result['avg_drawdown_duration'] == 0.0


class TestAvgDrawdown:
    """Test suite for calculate_avg_drawdown"""

    def test_avg_drawdown_basic(self, sample_nav):
        """Test basic average drawdown calculation"""
        result = drawdown_module.calculate_avg_drawdown(sample_nav)

        assert isinstance(result, float)
        assert result <= 0.0  # Average drawdown is non-positive

    def test_avg_drawdown_empty(self, empty_series):
        """Test with empty series"""
        result = drawdown_module.calculate_avg_drawdown(empty_series)
        assert result == 0.0

    def test_avg_drawdown_no_drawdown(self):
        """Test with no drawdowns"""
        nav = pd.Series([100, 110, 120, 130],
                        index=pd.date_range('2020-01-01', periods=4))

        result = drawdown_module.calculate_avg_drawdown(nav)
        assert result == 0.0


class TestRecoveryTime:
    """Test suite for calculate_recovery_time"""

    def test_recovery_time_basic(self, sample_nav):
        """Test basic recovery time calculation"""
        result = drawdown_module.calculate_recovery_time(sample_nav)

        assert isinstance(result, dict)

    def test_recovery_time_empty(self, empty_series):
        """Test with empty series"""
        result = drawdown_module.calculate_recovery_time(empty_series)
        assert result == {}

    def test_recovery_time_single_value(self, single_value_series):
        """Test with single value"""
        result = drawdown_module.calculate_recovery_time(single_value_series)
        assert result == {}

    def test_recovery_time_full_recovery(self):
        """Test with full recovery"""
        nav = pd.Series([100, 120, 60, 100, 120],
                        index=pd.date_range('2020-01-01', periods=5))

        result = drawdown_module.calculate_recovery_time(nav)

        assert 'recovery_days' in result
        assert 'recovered' in result
        assert result['recovered'] == True

    def test_recovery_time_no_recovery(self):
        """Test with no recovery"""
        nav = pd.Series([100, 120, 60, 70, 80],
                        index=pd.date_range('2020-01-01', periods=5))

        result = drawdown_module.calculate_recovery_time(nav)

        assert 'recovery_days' in result
        assert 'recovered' in result
        assert result['recovered'] == False
        assert np.isinf(result['recovery_days'])


class TestMaxDailyLoss:
    """Test suite for calculate_max_daily_loss"""

    def test_max_daily_loss_basic(self, sample_returns):
        """Test basic max daily loss calculation"""
        result = drawdown_module.calculate_max_daily_loss(sample_returns)

        assert isinstance(result, float)
        assert result <= 0.0  # Max loss is non-positive

    def test_max_daily_loss_formula(self):
        """Test max daily loss is minimum return"""
        returns = pd.Series([0.01, 0.02, -0.05, 0.01, -0.03])

        result = drawdown_module.calculate_max_daily_loss(returns)
        expected = -0.05
        assert np.isclose(result, expected)

    def test_max_daily_loss_empty(self, empty_series):
        """Test with empty series"""
        result = drawdown_module.calculate_max_daily_loss(empty_series)
        assert result == 0.0


class TestMaxDailyGain:
    """Test suite for calculate_max_daily_gain"""

    def test_max_daily_gain_basic(self, sample_returns):
        """Test basic max daily gain calculation"""
        result = drawdown_module.calculate_max_daily_gain(sample_returns)

        assert isinstance(result, float)
        assert result >= 0.0  # Max gain is non-negative (or zero)

    def test_max_daily_gain_formula(self):
        """Test max daily gain is maximum return"""
        returns = pd.Series([0.01, 0.05, -0.02, 0.01, -0.03])

        result = drawdown_module.calculate_max_daily_gain(returns)
        expected = 0.05
        assert np.isclose(result, expected)

    def test_max_daily_gain_empty(self, empty_series):
        """Test with empty series"""
        result = drawdown_module.calculate_max_daily_gain(empty_series)
        assert result == 0.0


class TestConsecutiveLossDays:
    """Test suite for calculate_consecutive_loss_days"""

    def test_consecutive_loss_days_basic(self, sample_returns):
        """Test basic consecutive loss days calculation"""
        result = drawdown_module.calculate_consecutive_loss_days(sample_returns)

        assert isinstance(result, int)
        assert result >= 0

    def test_consecutive_loss_days_formula(self):
        """Test consecutive loss days counting"""
        returns = pd.Series([0.01, -0.01, -0.02, -0.01, 0.01, -0.01])

        result = drawdown_module.calculate_consecutive_loss_days(returns)
        expected = 3  # Three consecutive losses at indices 1, 2, 3
        assert result == expected

    def test_consecutive_loss_days_empty(self, empty_series):
        """Test with empty series"""
        result = drawdown_module.calculate_consecutive_loss_days(empty_series)
        assert result == 0

    def test_consecutive_loss_days_only_gains(self, positive_returns):
        """Test with only positive returns"""
        result = drawdown_module.calculate_consecutive_loss_days(positive_returns)
        assert result == 0


class TestConsecutiveGainDays:
    """Test suite for calculate_consecutive_gain_days"""

    def test_consecutive_gain_days_basic(self, sample_returns):
        """Test basic consecutive gain days calculation"""
        result = drawdown_module.calculate_consecutive_gain_days(sample_returns)

        assert isinstance(result, int)
        assert result >= 0

    def test_consecutive_gain_days_formula(self):
        """Test consecutive gain days counting"""
        returns = pd.Series([-0.01, 0.01, 0.02, 0.01, -0.01, 0.01])

        result = drawdown_module.calculate_consecutive_gain_days(returns)
        expected = 3  # Three consecutive gains at indices 1, 2, 3
        assert result == expected

    def test_consecutive_gain_days_empty(self, empty_series):
        """Test with empty series"""
        result = drawdown_module.calculate_consecutive_gain_days(empty_series)
        assert result == 0

    def test_consecutive_gain_days_only_losses(self, negative_returns):
        """Test with only negative returns"""
        result = drawdown_module.calculate_consecutive_gain_days(negative_returns)
        assert result == 0


class TestUlcerIndex:
    """Test suite for calculate_ulcer_index"""

    def test_ulcer_index_basic(self, sample_nav):
        """Test basic Ulcer Index calculation"""
        result = drawdown_module.calculate_ulcer_index(sample_nav)

        assert isinstance(result, float)
        assert result >= 0.0  # Ulcer Index is non-negative

    def test_ulcer_index_empty(self, empty_series):
        """Test with empty series"""
        result = drawdown_module.calculate_ulcer_index(empty_series)
        assert result == 0.0

    def test_ulcer_index_short_series(self):
        """Test with series shorter than window"""
        nav = pd.Series([100, 105, 103],
                        index=pd.date_range('2020-01-01', periods=3))

        result = drawdown_module.calculate_ulcer_index(nav, window=14)
        assert result == 0.0

    def test_ulcer_index_no_drawdown(self):
        """Test with no drawdowns"""
        nav = pd.Series([100 * 1.01 ** i for i in range(50)],
                        index=pd.date_range('2020-01-01', periods=50))

        result = drawdown_module.calculate_ulcer_index(nav, window=14)
        assert result == 0.0 or np.isclose(result, 0.0, atol=1e-6)

    @pytest.mark.parametrize("window", [7, 14, 21, 30])
    def test_ulcer_index_windows(self, sample_nav, window):
        """Test with various window sizes"""
        if len(sample_nav) >= window:
            result = drawdown_module.calculate_ulcer_index(sample_nav, window=window)
            assert isinstance(result, float)
            assert result >= 0.0


@pytest.mark.parametrize("func_name,expected_type", [
    ("calculate_max_drawdown", float),
    ("calculate_avg_drawdown", float),
    ("calculate_max_daily_loss", float),
    ("calculate_max_daily_gain", float),
    ("calculate_consecutive_loss_days", int),
    ("calculate_consecutive_gain_days", int),
])
def test_drawdown_functions_type(func_name, expected_type, sample_nav, sample_returns):
    """Parametrized test for drawdown function output types"""
    func = getattr(drawdown_module, func_name)

    if 'daily' in func_name or 'consecutive' in func_name:
        result = func(sample_returns)
    else:
        result = func(sample_nav)

    assert isinstance(result, expected_type)
