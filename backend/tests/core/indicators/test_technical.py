"""Tests for technical module"""
import pytest
import pandas as pd
import numpy as np
from app.core.indicators import technical as technical_module


class TestMovingAverages:
    """Test suite for moving average functions"""

    def test_sma_basic(self):
        """Test basic SMA calculation"""
        close = np.array([100, 102, 104, 103, 105, 107, 106, 108, 110, 109], dtype=np.float64)
        result = technical_module.calculate_sma(close, period=5)

        assert isinstance(result, np.ndarray)
        assert len(result) == len(close)

    def test_ema_basic(self):
        """Test basic EMA calculation"""
        close = np.array([100, 102, 104, 103, 105, 107, 106, 108, 110, 109], dtype=np.float64)
        result = technical_module.calculate_ema(close, period=5)

        assert isinstance(result, np.ndarray)
        assert len(result) == len(close)

    def test_wma_basic(self):
        """Test basic WMA calculation"""
        close = np.array([100, 102, 104, 103, 105, 107, 106, 108, 110, 109], dtype=np.float64)
        result = technical_module.calculate_wma(close, period=5)

        assert isinstance(result, np.ndarray)
        assert len(result) == len(close)

    @pytest.mark.parametrize("period", [5, 10, 20, 50])
    def test_sma_periods(self, period):
        """Test SMA with various periods"""
        close = np.random.randn(100).cumsum() + 100
        result = technical_module.calculate_sma(close, period=period)

        assert len(result) == len(close)


class TestMACD:
    """Test suite for MACD indicator"""

    def test_macd_basic(self):
        """Test basic MACD calculation"""
        close = np.random.randn(100).cumsum() + 100
        macd, signal, hist = technical_module.calculate_macd(close)

        assert isinstance(macd, np.ndarray)
        assert isinstance(signal, np.ndarray)
        assert isinstance(hist, np.ndarray)
        assert len(macd) == len(close)

    def test_macd_custom_periods(self):
        """Test MACD with custom periods"""
        close = np.random.randn(100).cumsum() + 100
        macd, signal, hist = technical_module.calculate_macd(
            close, fastperiod=8, slowperiod=21, signalperiod=5
        )

        assert len(macd) == len(close)


class TestBollingerBands:
    """Test suite for Bollinger Bands"""

    def test_bbands_basic(self):
        """Test basic Bollinger Bands calculation"""
        close = np.random.randn(100).cumsum() + 100
        upper, middle, lower = technical_module.calculate_bollinger_bands(close)

        assert isinstance(upper, np.ndarray)
        assert isinstance(middle, np.ndarray)
        assert isinstance(lower, np.ndarray)
        assert len(upper) == len(close)

    def test_bbands_ordering(self):
        """Test that upper > middle > lower"""
        close = np.random.randn(100).cumsum() + 100
        upper, middle, lower = technical_module.calculate_bollinger_bands(close)

        # Check valid indices (non-NaN)
        valid_idx = ~np.isnan(upper) & ~np.isnan(middle) & ~np.isnan(lower)
        assert np.all(upper[valid_idx] >= middle[valid_idx])
        assert np.all(middle[valid_idx] >= lower[valid_idx])


class TestDonchianChannel:
    """Test suite for Donchian Channel"""

    def test_donchian_basic(self):
        """Test basic Donchian Channel calculation"""
        high = np.random.randn(100).cumsum() + 105
        low = np.random.randn(100).cumsum() + 95
        upper, middle, lower = technical_module.calculate_donchian_channel(high, low)

        assert isinstance(upper, np.ndarray)
        assert isinstance(middle, np.ndarray)
        assert isinstance(lower, np.ndarray)

    @pytest.mark.parametrize("period", [10, 20, 30])
    def test_donchian_periods(self, period):
        """Test Donchian Channel with various periods"""
        high = np.random.randn(100).cumsum() + 105
        low = np.random.randn(100).cumsum() + 95
        upper, middle, lower = technical_module.calculate_donchian_channel(high, low, period=period)

        assert len(upper) == len(high)


class TestATR:
    """Test suite for Average True Range"""

    def test_atr_basic(self):
        """Test basic ATR calculation"""
        high = np.random.randn(100).cumsum() + 105
        low = np.random.randn(100).cumsum() + 95
        close = (high + low) / 2 + np.random.randn(100) * 0.5
        result = technical_module.calculate_atr(high, low, close)

        assert isinstance(result, np.ndarray)
        assert len(result) == len(close)
        # ATR should be non-negative
        valid_idx = ~np.isnan(result)
        assert np.all(result[valid_idx] >= 0)


class TestMomentumIndicators:
    """Test suite for momentum indicators"""

    def test_roc_basic(self):
        """Test basic ROC calculation"""
        close = np.random.randn(100).cumsum() + 100
        result = technical_module.calculate_roc(close)

        assert isinstance(result, np.ndarray)
        assert len(result) == len(close)

    def test_momentum_basic(self):
        """Test basic Momentum calculation"""
        close = np.random.randn(100).cumsum() + 100
        result = technical_module.calculate_momentum(close)

        assert isinstance(result, np.ndarray)
        assert len(result) == len(close)


class TestOscillators:
    """Test suite for oscillator indicators"""

    def test_rsi_basic(self):
        """Test basic RSI calculation"""
        close = np.random.randn(100).cumsum() + 100
        result = technical_module.calculate_rsi(close)

        assert isinstance(result, np.ndarray)
        assert len(result) == len(close)
        # RSI should be between 0 and 100
        valid_idx = ~np.isnan(result)
        assert np.all((result[valid_idx] >= 0) & (result[valid_idx] <= 100))

    def test_stochastic_basic(self):
        """Test basic Stochastic calculation"""
        high = np.random.randn(100).cumsum() + 105
        low = np.random.randn(100).cumsum() + 95
        close = (high + low) / 2 + np.random.randn(100) * 0.5
        slowk, slowd = technical_module.calculate_stochastic(high, low, close)

        assert isinstance(slowk, np.ndarray)
        assert isinstance(slowd, np.ndarray)

    def test_cci_basic(self):
        """Test basic CCI calculation"""
        high = np.random.randn(100).cumsum() + 105
        low = np.random.randn(100).cumsum() + 95
        close = (high + low) / 2 + np.random.randn(100) * 0.5
        result = technical_module.calculate_cci(high, low, close)

        assert isinstance(result, np.ndarray)
        assert len(result) == len(close)

    def test_williams_r_basic(self):
        """Test basic Williams %R calculation"""
        high = np.random.randn(100).cumsum() + 105
        low = np.random.randn(100).cumsum() + 95
        close = (high + low) / 2 + np.random.randn(100) * 0.5
        result = technical_module.calculate_williams_r(high, low, close)

        assert isinstance(result, np.ndarray)
        assert len(result) == len(close)


class Test52WeekHighLow:
    """Test suite for 52-week high/low functions"""

    def test_52week_high_basic(self, sample_prices):
        """Test basic 52-week high calculation"""
        result = technical_module.calculate_52week_high(sample_prices)

        assert isinstance(result, float)
        assert result > 0

    def test_52week_low_basic(self, sample_prices):
        """Test basic 52-week low calculation"""
        result = technical_module.calculate_52week_low(sample_prices)

        assert isinstance(result, float)
        assert result > 0

    def test_52week_ordering(self, sample_prices):
        """Test that 52w high >= 52w low"""
        high = technical_module.calculate_52week_high(sample_prices)
        low = technical_module.calculate_52week_low(sample_prices)

        assert high >= low

    def test_distance_from_52week_high(self, sample_prices):
        """Test distance from 52-week high"""
        result = technical_module.calculate_distance_from_52week_high(sample_prices)

        assert isinstance(result, float)
        assert result <= 0.0  # Distance is non-positive


class TestNDayHighLow:
    """Test suite for N-day high/low functions"""

    def test_n_day_high_basic(self, sample_prices):
        """Test basic N-day high calculation"""
        result = technical_module.calculate_n_day_high(sample_prices, window=20)

        assert isinstance(result, float)
        assert result > 0

    def test_n_day_low_basic(self, sample_prices):
        """Test basic N-day low calculation"""
        result = technical_module.calculate_n_day_low(sample_prices, window=20)

        assert isinstance(result, float)
        assert result > 0

    @pytest.mark.parametrize("window", [5, 10, 20, 50, 100])
    def test_n_day_high_windows(self, sample_prices, window):
        """Test N-day high with various windows"""
        result = technical_module.calculate_n_day_high(sample_prices, window=window)
        assert isinstance(result, float)

    def test_n_day_ordering(self, sample_prices):
        """Test that N-day high >= N-day low"""
        window = 20
        high = technical_module.calculate_n_day_high(sample_prices, window=window)
        low = technical_module.calculate_n_day_low(sample_prices, window=window)

        assert high >= low


class TestPositionInRange:
    """Test suite for position_in_range"""

    def test_position_in_range_basic(self, sample_prices):
        """Test basic position in range calculation"""
        result = technical_module.calculate_position_in_range(sample_prices, window=20)

        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_position_at_high(self):
        """Test position when price is at high"""
        prices = pd.Series([100, 90, 95, 110])  # Last price is highest
        result = technical_module.calculate_position_in_range(prices, window=4)

        assert np.isclose(result, 1.0)

    def test_position_at_low(self):
        """Test position when price is at low"""
        prices = pd.Series([100, 110, 105, 90])  # Last price is lowest
        result = technical_module.calculate_position_in_range(prices, window=4)

        assert np.isclose(result, 0.0)


class TestConnorsRSI:
    """Test suite for Connors RSI"""

    def test_connors_rsi_basic(self, sample_ohlcv_data):
        """Test basic Connors RSI calculation"""
        result = technical_module.calculate_connors_rsi(sample_ohlcv_data)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv_data)

    @pytest.mark.parametrize("rsi_period,streak_period,rank_period", [
        (3, 2, 100),
        (5, 3, 50),
        (7, 4, 200),
    ])
    def test_connors_rsi_params(self, sample_ohlcv_data, rsi_period, streak_period, rank_period):
        """Test Connors RSI with various parameters"""
        result = technical_module.calculate_connors_rsi(
            sample_ohlcv_data,
            rsi_period=rsi_period,
            streak_period=streak_period,
            rank_period=rank_period
        )

        assert isinstance(result, pd.Series)


class TestKalmanFilter:
    """Test suite for Kalman Filter"""

    def test_kalman_basic(self, sample_ohlcv_data):
        """Test basic Kalman filter"""
        filtered, trends = technical_module.apply_kalman_filter(sample_ohlcv_data)

        assert isinstance(filtered, pd.Series)
        assert isinstance(trends, pd.Series)
        assert len(filtered) == len(sample_ohlcv_data)
        assert len(trends) == len(sample_ohlcv_data)

    @pytest.mark.parametrize("measurement_noise,process_noise", [
        (0.1, 0.01),
        (0.5, 0.05),
        (1.0, 0.1),
    ])
    def test_kalman_params(self, sample_ohlcv_data, measurement_noise, process_noise):
        """Test Kalman filter with various parameters"""
        filtered, trends = technical_module.apply_kalman_filter(
            sample_ohlcv_data,
            measurement_noise=measurement_noise,
            process_noise=process_noise
        )

        assert len(filtered) == len(sample_ohlcv_data)


class TestFFTFilter:
    """Test suite for FFT Filter"""

    def test_fft_basic(self, sample_ohlcv_data):
        """Test basic FFT filter"""
        result = technical_module.apply_fft_filter_rolling(
            sample_ohlcv_data, cutoff_period=21
        )

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_ohlcv_data)

    @pytest.mark.parametrize("cutoff_period", [10, 21, 63])
    def test_fft_cutoff_periods(self, sample_ohlcv_data, cutoff_period):
        """Test FFT filter with various cutoff periods"""
        result = technical_module.apply_fft_filter_rolling(
            sample_ohlcv_data, cutoff_period=cutoff_period
        )

        assert len(result) == len(sample_ohlcv_data)


class TestTechnicalIndicatorsBatch:
    """Test suite for calculate_technical_indicators_batch"""

    def test_batch_basic(self, sample_ohlcv_data):
        """Test basic batch calculation"""
        result = technical_module.calculate_technical_indicators_batch(sample_ohlcv_data)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_ohlcv_data)

    def test_batch_columns(self, sample_ohlcv_data):
        """Test that batch adds expected columns"""
        result = technical_module.calculate_technical_indicators_batch(sample_ohlcv_data)

        expected_columns = ['MA5', 'MA20', 'RSI', 'MACD', 'Upper', 'Lower']

        for col in expected_columns:
            assert col in result.columns

    def test_batch_short_data(self):
        """Test batch with short data (< 20 rows)"""
        dates = pd.date_range('2020-01-01', periods=15, freq='D')
        data = pd.DataFrame({
            'Close': np.random.randn(15).cumsum() + 100,
            'High': np.random.randn(15).cumsum() + 105,
            'Low': np.random.randn(15).cumsum() + 95,
            'Volume': np.random.randint(1000000, 10000000, 15)
        }, index=dates)

        result = technical_module.calculate_technical_indicators_batch(data)

        # Should return original data without technical indicators
        assert len(result) == len(data)


@pytest.mark.parametrize("func_name,expected_type", [
    ("calculate_52week_high", float),
    ("calculate_52week_low", float),
    ("calculate_distance_from_52week_high", float),
    ("calculate_position_in_range", float),
])
def test_technical_scalar_functions(func_name, expected_type, sample_prices):
    """Parametrized test for scalar technical functions"""
    func = getattr(technical_module, func_name)

    if 'position_in_range' in func_name:
        result = func(sample_prices, window=20)
    else:
        result = func(sample_prices)

    assert isinstance(result, expected_type)
