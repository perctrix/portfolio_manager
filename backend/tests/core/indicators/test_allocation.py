"""Tests for allocation module"""
import pytest
import pandas as pd
import numpy as np
from app.core.indicators import allocation as allocation_module


class TestCalculateWeights:
    """Test suite for calculate_weights"""

    def test_weights_basic(self, sample_holdings, sample_prices_dict):
        """Test basic weight calculation"""
        result = allocation_module.calculate_weights(sample_holdings, sample_prices_dict)

        assert isinstance(result, dict)
        assert len(result) == len(sample_holdings)
        # Weights should sum to 1
        assert np.isclose(sum(result.values()), 1.0)

    def test_weights_empty(self):
        """Test with empty holdings or prices"""
        result = allocation_module.calculate_weights({}, {})
        assert result == {}

    def test_weights_formula(self):
        """Test weight calculation formula"""
        holdings = {'AAPL': 100, 'GOOGL': 50}
        prices = {'AAPL': 150.0, 'GOOGL': 200.0}

        result = allocation_module.calculate_weights(holdings, prices)

        total_value = 100 * 150 + 50 * 200
        assert np.isclose(result['AAPL'], (100 * 150) / total_value)
        assert np.isclose(result['GOOGL'], (50 * 200) / total_value)

    def test_weights_zero_quantity(self):
        """Test with zero quantity holdings"""
        holdings = {'AAPL': 100, 'GOOGL': 0, 'MSFT': 50}
        prices = {'AAPL': 150.0, 'GOOGL': 200.0, 'MSFT': 300.0}

        result = allocation_module.calculate_weights(holdings, prices)

        # GOOGL should not be in result
        assert 'GOOGL' not in result
        assert len(result) == 2


class TestWeightHistory:
    """Test suite for calculate_weight_history"""

    def test_weight_history_basic(self, sample_price_history):
        """Test basic weight history calculation"""
        dates = sample_price_history.index
        holdings = pd.DataFrame({
            'AAPL': [100] * len(dates),
            'GOOGL': [50] * len(dates),
            'MSFT': [75] * len(dates),
            'AMZN': [25] * len(dates)
        }, index=dates)

        result = allocation_module.calculate_weight_history(holdings, sample_price_history)

        assert isinstance(result, pd.DataFrame)
        assert result.shape == holdings.shape
        # Each row should sum to 1
        assert np.allclose(result.sum(axis=1), 1.0)

    def test_weight_history_empty(self, empty_dataframe):
        """Test with empty dataframes"""
        result = allocation_module.calculate_weight_history(empty_dataframe, empty_dataframe)
        assert result.empty


class TestTopNConcentration:
    """Test suite for calculate_top_n_concentration"""

    def test_top_n_basic(self, sample_weights):
        """Test basic top N concentration"""
        result = allocation_module.calculate_top_n_concentration(sample_weights, n=2)

        assert isinstance(result, float)
        assert 0 <= result <= 1.0

    def test_top_n_formula(self):
        """Test top N concentration formula"""
        weights = {'A': 0.4, 'B': 0.3, 'C': 0.2, 'D': 0.1}

        result = allocation_module.calculate_top_n_concentration(weights, n=2)
        expected = 0.4 + 0.3  # Top 2 weights
        assert np.isclose(result, expected)

    def test_top_n_empty(self):
        """Test with empty weights"""
        result = allocation_module.calculate_top_n_concentration({}, n=5)
        assert result == 0.0

    def test_top_n_exceeds_size(self):
        """Test when n exceeds number of holdings"""
        weights = {'A': 0.5, 'B': 0.5}

        result = allocation_module.calculate_top_n_concentration(weights, n=5)
        assert np.isclose(result, 1.0)


class TestHHI:
    """Test suite for calculate_hhi"""

    def test_hhi_basic(self, sample_weights):
        """Test basic HHI calculation"""
        result = allocation_module.calculate_hhi(sample_weights)

        assert isinstance(result, float)
        assert result > 0

    def test_hhi_formula(self):
        """Test HHI formula: sum of squared weights"""
        weights = {'A': 0.5, 'B': 0.3, 'C': 0.2}

        result = allocation_module.calculate_hhi(weights)
        expected = 0.5**2 + 0.3**2 + 0.2**2
        assert np.isclose(result, expected)

    def test_hhi_empty(self):
        """Test with empty weights"""
        result = allocation_module.calculate_hhi({})
        assert result == 0.0

    def test_hhi_equal_weights(self):
        """Test HHI with equal weights"""
        n = 4
        weights = {f'Asset{i}': 1.0/n for i in range(n)}

        result = allocation_module.calculate_hhi(weights)
        expected = n * (1.0/n)**2  # = 1/n
        assert np.isclose(result, expected)


class TestSectorAllocation:
    """Test suite for calculate_sector_allocation"""

    def test_sector_allocation_basic(self, sample_holdings, sample_prices_dict, sector_map):
        """Test basic sector allocation"""
        result = allocation_module.calculate_sector_allocation(
            sample_holdings, sample_prices_dict, sector_map
        )

        assert isinstance(result, dict)
        assert 'Technology' in result or 'Consumer' in result

    def test_sector_allocation_empty(self):
        """Test with empty inputs"""
        result = allocation_module.calculate_sector_allocation({}, {}, {})
        assert result == {}

    def test_sector_allocation_sum(self, sample_holdings, sample_prices_dict, sector_map):
        """Test that sector allocations sum to 1"""
        result = allocation_module.calculate_sector_allocation(
            sample_holdings, sample_prices_dict, sector_map
        )

        if result:
            assert np.isclose(sum(result.values()), 1.0)


class TestIndustryAllocation:
    """Test suite for calculate_industry_allocation"""

    def test_industry_allocation_basic(self, sample_holdings, sample_prices_dict, industry_map):
        """Test basic industry allocation"""
        result = allocation_module.calculate_industry_allocation(
            sample_holdings, sample_prices_dict, industry_map
        )

        assert isinstance(result, dict)

    def test_industry_allocation_empty(self):
        """Test with empty inputs"""
        result = allocation_module.calculate_industry_allocation({}, {}, {})
        assert result == {}


class TestMaxWeight:
    """Test suite for calculate_max_weight"""

    def test_max_weight_basic(self, sample_weights):
        """Test basic max weight calculation"""
        result = allocation_module.calculate_max_weight(sample_weights)

        assert isinstance(result, float)
        assert result > 0

    def test_max_weight_formula(self):
        """Test max weight is maximum of all weights"""
        weights = {'A': 0.4, 'B': 0.3, 'C': 0.3}

        result = allocation_module.calculate_max_weight(weights)
        assert np.isclose(result, 0.4)

    def test_max_weight_empty(self):
        """Test with empty weights"""
        result = allocation_module.calculate_max_weight({})
        assert result == 0.0


class TestWeightDeviationFromEqual:
    """Test suite for calculate_weight_deviation_from_equal"""

    def test_deviation_basic(self, sample_weights):
        """Test basic deviation calculation"""
        result = allocation_module.calculate_weight_deviation_from_equal(sample_weights)

        assert isinstance(result, float)
        assert result >= 0

    def test_deviation_equal_weights(self):
        """Test with equal weights (deviation should be 0)"""
        n = 4
        weights = {f'Asset{i}': 1.0/n for i in range(n)}

        result = allocation_module.calculate_weight_deviation_from_equal(weights)
        assert np.isclose(result, 0.0, atol=1e-10)

    def test_deviation_empty(self):
        """Test with empty weights"""
        result = allocation_module.calculate_weight_deviation_from_equal({})
        assert result == 0.0


class TestLongShortExposure:
    """Test suite for calculate_long_short_exposure"""

    def test_long_short_basic(self):
        """Test basic long/short exposure"""
        holdings = {'AAPL': 100, 'GOOGL': -50, 'MSFT': 75}
        prices = {'AAPL': 150.0, 'GOOGL': 200.0, 'MSFT': 300.0}

        result = allocation_module.calculate_long_short_exposure(holdings, prices)

        assert isinstance(result, dict)
        assert 'long_exposure' in result
        assert 'short_exposure' in result
        assert 'net_exposure' in result

    def test_long_short_all_long(self, sample_holdings, sample_prices_dict):
        """Test with all long positions"""
        result = allocation_module.calculate_long_short_exposure(
            sample_holdings, sample_prices_dict
        )

        assert result['long_exposure'] == 1.0
        assert result['short_exposure'] == 0.0
        assert result['net_exposure'] == 1.0

    def test_long_short_empty(self):
        """Test with empty inputs"""
        result = allocation_module.calculate_long_short_exposure({}, {})

        assert result['long_exposure'] == 0.0
        assert result['short_exposure'] == 0.0
        assert result['net_exposure'] == 0.0


class TestPortfolioVolatility:
    """Test suite for calculate_portfolio_volatility"""

    def test_portfolio_volatility_basic(self, sample_weights, sample_price_history):
        """Test basic portfolio volatility"""
        result = allocation_module.calculate_portfolio_volatility(
            sample_weights, sample_price_history
        )

        assert isinstance(result, float)
        assert result >= 0

    def test_portfolio_volatility_empty(self, empty_dataframe):
        """Test with empty inputs"""
        result = allocation_module.calculate_portfolio_volatility({}, empty_dataframe)
        assert result == 0.0


class TestMCTR:
    """Test suite for calculate_mctr (Marginal Contribution to Risk)"""

    def test_mctr_basic(self, sample_weights, sample_price_history):
        """Test basic MCTR calculation"""
        result = allocation_module.calculate_mctr(sample_weights, sample_price_history)

        assert isinstance(result, dict)
        assert len(result) <= len(sample_weights)

    def test_mctr_empty(self, empty_dataframe):
        """Test with empty inputs"""
        result = allocation_module.calculate_mctr({}, empty_dataframe)
        assert result == {}


class TestRiskContribution:
    """Test suite for risk contribution functions"""

    def test_risk_contribution_by_asset_basic(self, sample_weights, sample_price_history):
        """Test basic risk contribution by asset"""
        result = allocation_module.calculate_risk_contribution_by_asset(
            sample_weights, sample_price_history
        )

        assert isinstance(result, dict)

        for symbol, risk_data in result.items():
            assert 'mctr' in risk_data
            assert 'risk_contribution' in risk_data
            assert 'pct_risk_contribution' in risk_data

    def test_risk_contribution_by_sector_basic(
            self, sample_weights, sample_price_history, sector_map
    ):
        """Test basic risk contribution by sector"""
        result = allocation_module.calculate_risk_contribution_by_sector(
            sample_weights, sample_price_history, sector_map
        )

        assert isinstance(result, dict)

    def test_risk_contribution_empty(self, empty_dataframe):
        """Test with empty inputs"""
        result = allocation_module.calculate_risk_contribution_by_asset({}, empty_dataframe)
        assert result == {}


@pytest.mark.parametrize("func_name", [
    "calculate_hhi",
    "calculate_top_n_concentration",
    "calculate_max_weight",
    "calculate_weight_deviation_from_equal",
])
def test_allocation_functions_return_float(func_name, sample_weights):
    """Parametrized test that allocation functions return float"""
    func = getattr(allocation_module, func_name)

    if 'top_n' in func_name:
        result = func(sample_weights, 5)
    else:
        result = func(sample_weights)

    assert isinstance(result, float)
