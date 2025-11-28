"""Tests for utils module"""
import pytest
import pandas as pd
import numpy as np
from app.core.indicators.utils import rolling_normalize


class TestRollingNormalize:
    """Test suite for rolling_normalize function"""

    def test_rolling_normalize_basic(self, sample_prices):
        """Test basic rolling normalization"""
        result = rolling_normalize(sample_prices, window=21)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_prices)
        assert not result.isna().any()

    def test_rolling_normalize_window_size(self, sample_prices):
        """Test different window sizes"""
        for window in [5, 10, 20, 50]:
            result = rolling_normalize(sample_prices, window=window)
            assert len(result) == len(sample_prices)
            assert not result.isna().any()

    def test_rolling_normalize_empty_series(self, empty_series):
        """Test with empty series"""
        result = rolling_normalize(empty_series, window=21)
        assert result.empty

    def test_rolling_normalize_single_value(self, single_value_series):
        """Test with single value"""
        result = rolling_normalize(single_value_series, window=21)
        assert len(result) == 1
        # With single value, std is 0, so normalized value should be 0 (due to eps)
        assert pd.isna(result.iloc[0])

    def test_rolling_normalize_constant_series(self):
        """Test with constant values (zero variance)"""
        dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
        constant = pd.Series(100.0, index=dates)

        result = rolling_normalize(constant, window=21)

        # All values should be close to 0 (normalized constant is 0)
        assert np.allclose(result, 0, atol=1e-6)

    def test_rolling_normalize_statistical_properties(self, sample_prices):
        """Test statistical properties of normalized data"""
        window = 21
        result = rolling_normalize(sample_prices, window=window)

        # Check that mean is close to 0 and std close to 1 for later windows
        rolling_mean = result.iloc[window:].rolling(window=window).mean()
        rolling_std = result.iloc[window:].rolling(window=window).std()

        # Mean should be close to 0
        assert abs(rolling_mean.mean()) < 0.5

        # Std should be close to 1
        assert abs(rolling_std.mean() - 1.0) < 0.5

    def test_rolling_normalize_no_nan_propagation(self):
        """Test that forward and backward fill handle edge cases"""
        dates = pd.date_range(start='2020-01-01', periods=50, freq='D')
        series = pd.Series(range(50), index=dates, dtype=float)

        result = rolling_normalize(series, window=10)

        # Should have no NaN values
        assert not result.isna().any()

    def test_rolling_normalize_preserves_index(self, sample_prices):
        """Test that index is preserved"""
        result = rolling_normalize(sample_prices, window=21)

        assert result.index.equals(sample_prices.index)

    @pytest.mark.parametrize("window", [2, 5, 10, 21, 50, 100])
    def test_rolling_normalize_various_windows(self, sample_prices, window):
        """Test with various window sizes"""
        result = rolling_normalize(sample_prices, window=window)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_prices)
        assert not result.isna().any()

    def test_rolling_normalize_with_negative_values(self):
        """Test with series containing negative values"""
        dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
        np.random.seed(42)
        series = pd.Series(np.random.randn(100) * 50 - 25, index=dates)

        result = rolling_normalize(series, window=20)

        assert not result.isna().any()
        assert len(result) == len(series)

    def test_rolling_normalize_large_window(self, sample_prices):
        """Test with window larger than series length"""
        window = len(sample_prices) + 100
        result = rolling_normalize(sample_prices, window=window)

        # Should still work with min_periods=1
        assert len(result) == len(sample_prices)
        assert not result.isna().any()
