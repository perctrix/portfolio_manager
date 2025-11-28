"""Tests for correlation_beta module"""
import pytest
import pandas as pd
import numpy as np
from app.core.indicators import correlation_beta as corr_module


class TestCorrelationToPortfolio:
    """Test suite for calculate_correlation_to_portfolio"""

    def test_correlation_basic(self, correlated_returns):
        """Test basic correlation calculation"""
        portfolio_returns, benchmark_returns = correlated_returns
        result = corr_module.calculate_correlation_to_portfolio(
            portfolio_returns, benchmark_returns
        )

        assert isinstance(result, float)
        assert -1.0 <= result <= 1.0

    def test_correlation_perfect_positive(self):
        """Test perfect positive correlation"""
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        returns = pd.Series(np.random.randn(100) * 0.01, index=dates)

        result = corr_module.calculate_correlation_to_portfolio(returns, returns)
        assert np.isclose(result, 1.0)

    def test_correlation_perfect_negative(self):
        """Test perfect negative correlation"""
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        returns = pd.Series(np.random.randn(100) * 0.01, index=dates)
        neg_returns = -returns

        result = corr_module.calculate_correlation_to_portfolio(returns, neg_returns)
        assert np.isclose(result, -1.0)

    def test_correlation_empty(self, empty_series):
        """Test with empty series"""
        result = corr_module.calculate_correlation_to_portfolio(empty_series, empty_series)
        assert result == 0.0


class TestCorrelationMatrix:
    """Test suite for calculate_correlation_matrix"""

    def test_corr_matrix_basic(self, multi_asset_returns):
        """Test basic correlation matrix calculation"""
        result = corr_module.calculate_correlation_matrix(multi_asset_returns)

        assert isinstance(result, pd.DataFrame)
        assert result.shape[0] == result.shape[1]  # Square matrix
        # Diagonal should be 1
        assert np.allclose(np.diag(result.values), 1.0)

    def test_corr_matrix_empty(self, empty_dataframe):
        """Test with empty dataframe"""
        result = corr_module.calculate_correlation_matrix(empty_dataframe)
        assert result.empty

    def test_corr_matrix_symmetric(self, multi_asset_returns):
        """Test that correlation matrix is symmetric"""
        result = corr_module.calculate_correlation_matrix(multi_asset_returns)

        assert np.allclose(result.values, result.values.T)


class TestCovarianceMatrix:
    """Test suite for calculate_covariance_matrix"""

    def test_cov_matrix_basic(self, multi_asset_returns):
        """Test basic covariance matrix calculation"""
        result = corr_module.calculate_covariance_matrix(multi_asset_returns)

        assert isinstance(result, pd.DataFrame)
        assert result.shape[0] == result.shape[1]  # Square matrix

    def test_cov_matrix_annualized(self, multi_asset_returns):
        """Test annualized vs non-annualized covariance"""
        cov_ann = corr_module.calculate_covariance_matrix(multi_asset_returns, annualize=True)
        cov_daily = corr_module.calculate_covariance_matrix(multi_asset_returns, annualize=False)

        # Annualized should be ~252x daily
        ratio = cov_ann.values / cov_daily.values
        assert np.allclose(ratio, 252.0, rtol=0.01)

    def test_cov_matrix_empty(self, empty_dataframe):
        """Test with empty dataframe"""
        result = corr_module.calculate_covariance_matrix(empty_dataframe)
        assert result.empty


class TestBeta:
    """Test suite for calculate_beta"""

    def test_beta_basic(self, correlated_returns):
        """Test basic beta calculation"""
        portfolio_returns, benchmark_returns = correlated_returns
        result = corr_module.calculate_beta(portfolio_returns, benchmark_returns)

        assert isinstance(result, float)

    def test_beta_formula(self):
        """Test beta formula: Cov(p,b) / Var(b)"""
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        benchmark = pd.Series(np.random.randn(100) * 0.01, index=dates)
        portfolio = benchmark * 1.5 + np.random.randn(100) * 0.005

        result = corr_module.calculate_beta(portfolio, benchmark)

        # Beta should be close to 1.5
        assert 1.0 < result < 2.0

    def test_beta_same_asset(self, sample_returns):
        """Test beta of asset with itself (should be 1)"""
        result = corr_module.calculate_beta(sample_returns, sample_returns)
        assert np.isclose(result, 1.0)

    def test_beta_empty(self, empty_series):
        """Test with empty series"""
        result = corr_module.calculate_beta(empty_series, empty_series)
        assert result == 0.0


class TestAlpha:
    """Test suite for calculate_alpha"""

    def test_alpha_basic(self, correlated_returns):
        """Test basic alpha calculation"""
        portfolio_returns, benchmark_returns = correlated_returns
        result = corr_module.calculate_alpha(portfolio_returns, benchmark_returns)

        assert isinstance(result, float)

    def test_alpha_same_returns(self, sample_returns):
        """Test alpha when portfolio equals benchmark (should be ~0)"""
        result = corr_module.calculate_alpha(sample_returns, sample_returns, risk_free_rate=0.0)
        assert np.isclose(result, 0.0, atol=0.01)

    def test_alpha_empty(self, empty_series):
        """Test with empty series"""
        result = corr_module.calculate_alpha(empty_series, empty_series)
        assert result == 0.0


class TestRSquared:
    """Test suite for calculate_r_squared"""

    def test_r_squared_basic(self, correlated_returns):
        """Test basic R² calculation"""
        portfolio_returns, benchmark_returns = correlated_returns
        result = corr_module.calculate_r_squared(portfolio_returns, benchmark_returns)

        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_r_squared_perfect_fit(self, sample_returns):
        """Test R² with perfect fit (should be 1)"""
        result = corr_module.calculate_r_squared(sample_returns, sample_returns)
        assert np.isclose(result, 1.0)

    def test_r_squared_empty(self, empty_series):
        """Test with empty series"""
        result = corr_module.calculate_r_squared(empty_series, empty_series)
        assert result == 0.0


class TestTrackingError:
    """Test suite for calculate_tracking_error"""

    def test_tracking_error_basic(self, correlated_returns):
        """Test basic tracking error calculation"""
        portfolio_returns, benchmark_returns = correlated_returns
        result = corr_module.calculate_tracking_error(portfolio_returns, benchmark_returns)

        assert isinstance(result, float)
        assert result >= 0

    def test_tracking_error_same_returns(self, sample_returns):
        """Test tracking error when portfolio equals benchmark (should be 0)"""
        result = corr_module.calculate_tracking_error(sample_returns, sample_returns)
        assert np.isclose(result, 0.0, atol=1e-10)

    def test_tracking_error_annualized(self, correlated_returns):
        """Test annualized vs non-annualized tracking error"""
        portfolio_returns, benchmark_returns = correlated_returns

        te_ann = corr_module.calculate_tracking_error(
            portfolio_returns, benchmark_returns, annualize=True
        )
        te_daily = corr_module.calculate_tracking_error(
            portfolio_returns, benchmark_returns, annualize=False
        )

        # Annualized should be ~sqrt(252) * daily
        assert np.isclose(te_ann / te_daily, np.sqrt(252), rtol=0.1)

    def test_tracking_error_empty(self, empty_series):
        """Test with empty series"""
        result = corr_module.calculate_tracking_error(empty_series, empty_series)
        assert result == 0.0


class TestInformationRatio:
    """Test suite for calculate_information_ratio"""

    def test_ir_basic(self, correlated_returns):
        """Test basic information ratio calculation"""
        portfolio_returns, benchmark_returns = correlated_returns
        result = corr_module.calculate_information_ratio(portfolio_returns, benchmark_returns)

        assert isinstance(result, float)

    def test_ir_same_returns(self, sample_returns):
        """Test IR when portfolio equals benchmark"""
        result = corr_module.calculate_information_ratio(sample_returns, sample_returns)
        # Zero excess return / zero tracking error = undefined, but function returns 0
        assert result == 0.0

    def test_ir_empty(self, empty_series):
        """Test with empty series"""
        result = corr_module.calculate_information_ratio(empty_series, empty_series)
        assert result == 0.0


class TestAllBenchmarkMetrics:
    """Test suite for calculate_all_benchmark_metrics"""

    def test_all_metrics_basic(self, correlated_returns):
        """Test basic all benchmark metrics"""
        portfolio_returns, benchmark_returns = correlated_returns
        result = corr_module.calculate_all_benchmark_metrics(
            portfolio_returns, benchmark_returns
        )

        assert isinstance(result, dict)
        assert 'beta' in result
        assert 'alpha' in result
        assert 'r_squared' in result
        assert 'correlation' in result
        assert 'tracking_error' in result
        assert 'information_ratio' in result

    def test_all_metrics_empty(self, empty_series):
        """Test with empty series"""
        result = corr_module.calculate_all_benchmark_metrics(empty_series, empty_series)

        assert isinstance(result, dict)
        assert result['beta'] == 0.0
        assert result['alpha'] == 0.0


class TestMultiBenchmarkMetrics:
    """Test suite for calculate_multi_benchmark_metrics"""

    def test_multi_benchmark_basic(self, sample_returns, correlated_returns):
        """Test basic multi-benchmark metrics"""
        _, benchmark1 = correlated_returns

        benchmark_dict = {
            'SPY': benchmark1,
            'QQQ': sample_returns
        }

        result = corr_module.calculate_multi_benchmark_metrics(
            sample_returns, benchmark_dict
        )

        assert isinstance(result, dict)
        assert 'SPY' in result
        assert 'QQQ' in result
        assert 'beta' in result['SPY']

    def test_multi_benchmark_empty(self, sample_returns):
        """Test with empty benchmark dict"""
        result = corr_module.calculate_multi_benchmark_metrics(sample_returns, {})
        assert result == {}


class TestMeanPairwiseCorrelation:
    """Test suite for calculate_mean_pairwise_correlation"""

    def test_mean_corr_basic(self, multi_asset_returns):
        """Test basic mean pairwise correlation"""
        result = corr_module.calculate_mean_pairwise_correlation(multi_asset_returns)

        assert isinstance(result, float)
        assert -1.0 <= result <= 1.0

    def test_mean_corr_empty(self, empty_dataframe):
        """Test with empty dataframe"""
        result = corr_module.calculate_mean_pairwise_correlation(empty_dataframe)
        assert result == 0.0

    def test_mean_corr_single_asset(self, sample_returns):
        """Test with single asset (no pairs)"""
        df = pd.DataFrame({'A': sample_returns})
        result = corr_module.calculate_mean_pairwise_correlation(df)
        assert result == 0.0


class TestMaxMinCorrelation:
    """Test suite for calculate_max_min_correlation"""

    def test_max_min_corr_basic(self, multi_asset_returns):
        """Test basic max/min correlation"""
        max_corr, min_corr = corr_module.calculate_max_min_correlation(multi_asset_returns)

        assert isinstance(max_corr, float)
        assert isinstance(min_corr, float)
        assert -1.0 <= min_corr <= max_corr <= 1.0

    def test_max_min_corr_empty(self, empty_dataframe):
        """Test with empty dataframe"""
        max_corr, min_corr = corr_module.calculate_max_min_correlation(empty_dataframe)
        assert max_corr == 0.0
        assert min_corr == 0.0


class TestCaptureRatios:
    """Test suite for upside/downside capture ratios"""

    def test_upside_capture_basic(self, correlated_returns):
        """Test basic upside capture"""
        portfolio_returns, benchmark_returns = correlated_returns
        result = corr_module.calculate_upside_capture(portfolio_returns, benchmark_returns)

        assert isinstance(result, float)
        assert result >= 0

    def test_downside_capture_basic(self, correlated_returns):
        """Test basic downside capture"""
        portfolio_returns, benchmark_returns = correlated_returns
        result = corr_module.calculate_downside_capture(portfolio_returns, benchmark_returns)

        assert isinstance(result, float)
        assert result >= 0

    def test_upside_capture_same_returns(self, sample_returns):
        """Test upside capture when portfolio equals benchmark (should be 100)"""
        result = corr_module.calculate_upside_capture(sample_returns, sample_returns)
        assert np.isclose(result, 100.0)

    def test_downside_capture_same_returns(self, sample_returns):
        """Test downside capture when portfolio equals benchmark (should be 100)"""
        result = corr_module.calculate_downside_capture(sample_returns, sample_returns)
        assert np.isclose(result, 100.0)

    def test_upside_capture_empty(self, empty_series):
        """Test with empty series"""
        result = corr_module.calculate_upside_capture(empty_series, empty_series)
        assert result == 0.0

    def test_downside_capture_empty(self, empty_series):
        """Test with empty series"""
        result = corr_module.calculate_downside_capture(empty_series, empty_series)
        assert result == 0.0


@pytest.mark.parametrize("func_name,expected_range", [
    ("calculate_beta", (-float('inf'), float('inf'))),
    ("calculate_r_squared", (0.0, 1.0)),
    ("calculate_tracking_error", (0.0, float('inf'))),
    ("calculate_correlation_to_portfolio", (-1.0, 1.0)),
])
def test_correlation_functions_range(func_name, expected_range, correlated_returns):
    """Parametrized test for correlation function output ranges"""
    portfolio_returns, benchmark_returns = correlated_returns
    func = getattr(corr_module, func_name)

    result = func(portfolio_returns, benchmark_returns)

    assert expected_range[0] <= result <= expected_range[1]
