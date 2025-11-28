"""Tests for aggregator module"""
import pytest
import pandas as pd
import numpy as np
from app.core.indicators import aggregator as agg_module
from app.core.indicators import calculate_basic_metrics


class TestBasicPortfolioIndicators:
    """Test suite for calculate_basic_portfolio_indicators"""

    def test_basic_indicators(self, sample_nav):
        """Test basic portfolio indicators"""
        result = agg_module.calculate_basic_portfolio_indicators(sample_nav)

        assert isinstance(result, dict)
        assert 'total_return' in result
        assert 'cagr' in result
        assert 'volatility' in result
        assert 'sharpe' in result
        assert 'max_drawdown' in result

    def test_basic_indicators_empty(self, empty_series):
        """Test with empty NAV"""
        result = agg_module.calculate_basic_portfolio_indicators(empty_series)

        assert isinstance(result, dict)
        assert result['total_return'] == 0.0
        assert result['cagr'] == 0.0

    def test_basic_indicators_values(self, sample_nav):
        """Test that values are floats and reasonable"""
        result = agg_module.calculate_basic_portfolio_indicators(sample_nav)

        for key, value in result.items():
            assert isinstance(value, (int, float))
            assert not np.isnan(value) and not np.isinf(value)


class TestAllPortfolioIndicators:
    """Test suite for calculate_all_portfolio_indicators"""

    def test_all_indicators_basic(self, sample_nav):
        """Test basic all indicators"""
        result = agg_module.calculate_all_portfolio_indicators(sample_nav)

        assert isinstance(result, dict)
        assert 'returns' in result
        assert 'risk' in result
        assert 'drawdown' in result
        assert 'risk_adjusted_ratios' in result
        assert 'tail_risk' in result

    def test_all_indicators_empty(self, empty_series):
        """Test with empty NAV"""
        result = agg_module.calculate_all_portfolio_indicators(empty_series)
        assert result == {}

    def test_all_indicators_with_transactions(
            self, sample_nav, sample_transactions
    ):
        """Test with transaction data"""
        result = agg_module.calculate_all_portfolio_indicators(
            sample_nav, transactions=sample_transactions
        )

        assert 'trading' in result
        assert result['trading'] is not None

    def test_all_indicators_with_holdings(
            self, sample_nav, sample_holdings, sample_prices_dict, sample_weights
    ):
        """Test with holdings and prices"""
        result = agg_module.calculate_all_portfolio_indicators(
            sample_nav,
            holdings=sample_holdings,
            prices=sample_prices_dict,
            weights=sample_weights
        )

        assert 'allocation' in result

    def test_all_indicators_with_price_history(
            self, sample_nav, sample_weights, sample_price_history
    ):
        """Test with price history"""
        result = agg_module.calculate_all_portfolio_indicators(
            sample_nav,
            weights=sample_weights,
            price_history=sample_price_history
        )

        assert 'risk_decomposition' in result or 'correlation' in result

    def test_all_indicators_returns_section(self, sample_nav):
        """Test returns section"""
        result = agg_module.calculate_all_portfolio_indicators(sample_nav)

        returns_section = result['returns']
        assert 'total_return' in returns_section
        assert 'cagr' in returns_section
        assert 'annualized_return' in returns_section
        assert 'ytd_return' in returns_section
        assert 'mtd_return' in returns_section

    def test_all_indicators_risk_section(self, sample_nav):
        """Test risk section"""
        result = agg_module.calculate_all_portfolio_indicators(sample_nav)

        risk_section = result['risk']
        assert 'daily_volatility' in risk_section
        assert 'annualized_volatility' in risk_section
        assert 'upside_volatility' in risk_section
        assert 'downside_volatility' in risk_section

    def test_all_indicators_drawdown_section(self, sample_nav):
        """Test drawdown section"""
        result = agg_module.calculate_all_portfolio_indicators(sample_nav)

        drawdown_section = result['drawdown']
        assert 'max_drawdown' in drawdown_section
        assert 'avg_drawdown' in drawdown_section
        assert 'ulcer_index' in drawdown_section

    def test_all_indicators_ratios_section(self, sample_nav):
        """Test risk-adjusted ratios section"""
        result = agg_module.calculate_all_portfolio_indicators(sample_nav)

        ratios_section = result['risk_adjusted_ratios']
        assert 'sharpe' in ratios_section
        assert 'sortino' in ratios_section
        assert 'calmar' in ratios_section
        assert 'omega' in ratios_section

    def test_all_indicators_tail_risk_section(self, sample_nav):
        """Test tail risk section"""
        result = agg_module.calculate_all_portfolio_indicators(sample_nav)

        tail_section = result['tail_risk']
        assert 'var_95' in tail_section
        assert 'cvar_95' in tail_section
        assert 'skewness' in tail_section
        assert 'kurtosis' in tail_section
        assert 'tail_ratio' in tail_section

    def test_all_indicators_with_sector_map(
            self, sample_nav, sample_holdings, sample_prices_dict,
            sample_weights, sample_price_history, sector_map
    ):
        """Test with sector mapping"""
        result = agg_module.calculate_all_portfolio_indicators(
            sample_nav,
            holdings=sample_holdings,
            prices=sample_prices_dict,
            weights=sample_weights,
            price_history=sample_price_history,
            sector_map=sector_map
        )

        if 'allocation' in result:
            assert 'sector_allocation' in result['allocation']

    def test_all_indicators_with_industry_map(
            self, sample_nav, sample_holdings, sample_prices_dict,
            sample_weights, industry_map
    ):
        """Test with industry mapping"""
        result = agg_module.calculate_all_portfolio_indicators(
            sample_nav,
            holdings=sample_holdings,
            prices=sample_prices_dict,
            weights=sample_weights,
            industry_map=industry_map
        )

        if 'allocation' in result:
            assert 'industry_allocation' in result['allocation']


class TestSanitizeForJSON:
    """Test suite for sanitize_for_json"""

    def test_sanitize_nan(self):
        """Test sanitizing NaN values"""
        data = {'a': float('nan'), 'b': 1.0}
        result = agg_module.sanitize_for_json(data)

        assert result['a'] is None
        assert result['b'] == 1.0

    def test_sanitize_inf(self):
        """Test sanitizing Inf values"""
        data = {'a': float('inf'), 'b': float('-inf'), 'c': 1.0}
        result = agg_module.sanitize_for_json(data)

        assert result['a'] is None
        assert result['b'] is None
        assert result['c'] == 1.0

    def test_sanitize_nested_dict(self):
        """Test sanitizing nested dictionaries"""
        data = {
            'outer': {
                'inner': float('nan'),
                'value': 1.0
            }
        }
        result = agg_module.sanitize_for_json(data)

        assert result['outer']['inner'] is None
        assert result['outer']['value'] == 1.0

    def test_sanitize_list(self):
        """Test sanitizing lists"""
        data = [1.0, float('nan'), float('inf'), 2.0]
        result = agg_module.sanitize_for_json(data)

        assert result[0] == 1.0
        assert result[1] is None
        assert result[2] is None
        assert result[3] == 2.0

    def test_sanitize_numpy_types(self):
        """Test sanitizing numpy types"""
        data = {
            'int': np.int64(10),
            'float': np.float64(1.5),
            'nan': np.float64(np.nan)
        }
        result = agg_module.sanitize_for_json(data)

        assert result['int'] == 10
        assert isinstance(result['int'], int)
        assert result['float'] == 1.5
        assert isinstance(result['float'], float)
        assert result['nan'] is None


class TestBenchmarkComparison:
    """Test suite for calculate_benchmark_comparison"""

    def test_benchmark_comparison_basic(self, sample_returns, benchmark_returns):
        """Test basic benchmark comparison"""
        benchmark_dict = {
            'SPY': benchmark_returns,
            'QQQ': benchmark_returns
        }

        result = agg_module.calculate_benchmark_comparison(
            sample_returns, benchmark_dict
        )

        assert isinstance(result, dict)
        assert 'SPY' in result
        assert 'QQQ' in result

    def test_benchmark_comparison_empty(self, sample_returns):
        """Test with empty benchmark dict"""
        result = agg_module.calculate_benchmark_comparison(sample_returns, {})
        assert result == {}

    def test_benchmark_comparison_metrics(self, sample_returns, benchmark_returns):
        """Test that benchmark comparison includes expected metrics"""
        benchmark_dict = {'SPY': benchmark_returns}

        result = agg_module.calculate_benchmark_comparison(
            sample_returns, benchmark_dict
        )

        spy_metrics = result['SPY']
        assert 'beta' in spy_metrics
        assert 'alpha' in spy_metrics
        assert 'correlation' in spy_metrics


@pytest.mark.integration
class TestFullIndicatorCalculation:
    """Integration tests for full indicator calculation"""

    def test_full_calculation_complete(
            self, sample_nav, sample_transactions, sample_holdings,
            sample_prices_dict, sample_weights, sample_price_history,
            sector_map, industry_map
    ):
        """Test complete indicator calculation with all inputs"""
        result = agg_module.calculate_all_portfolio_indicators(
            nav=sample_nav,
            transactions=sample_transactions,
            holdings=sample_holdings,
            prices=sample_prices_dict,
            price_history=sample_price_history,
            weights=sample_weights,
            sector_map=sector_map,
            industry_map=industry_map
        )

        # Should have all major sections
        assert 'returns' in result
        assert 'risk' in result
        assert 'drawdown' in result
        assert 'risk_adjusted_ratios' in result
        assert 'tail_risk' in result

        # Check data integrity (no NaN/Inf after sanitization)
        def check_no_nan_inf(obj):
            if isinstance(obj, dict):
                for v in obj.values():
                    check_no_nan_inf(v)
            elif isinstance(obj, list):
                for item in obj:
                    check_no_nan_inf(item)
            elif isinstance(obj, float):
                assert not np.isnan(obj)
                assert not np.isinf(obj)

        check_no_nan_inf(result)

    def test_backward_compatibility(self, sample_nav):
        """Test backward compatibility functions"""
        # Test calculate_basic_metrics alias
        result = calculate_basic_metrics(sample_nav)

        assert isinstance(result, dict)
        assert 'total_return' in result


def test_all_values_json_serializable(sample_nav):
    """Test that all output values are JSON serializable"""
    import json

    result = agg_module.calculate_all_portfolio_indicators(sample_nav)

    # Should not raise exception
    json_str = json.dumps(result)
    assert isinstance(json_str, str)
