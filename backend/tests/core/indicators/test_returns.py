"""Tests for returns module"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.core.indicators import returns as returns_module


class TestSimpleReturns:
    """Test suite for calculate_simple_returns"""

    def test_simple_returns_basic(self, sample_prices):
        """Test basic simple returns calculation"""
        result = returns_module.calculate_simple_returns(sample_prices)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_prices)
        assert pd.isna(result.iloc[0])  # First return is NaN

    def test_simple_returns_formula(self):
        """Test that formula is correct: r_t = P_t / P_{t-1} - 1"""
        prices = pd.Series([100, 110, 105, 115], index=pd.date_range('2020-01-01', periods=4))
        returns = returns_module.calculate_simple_returns(prices)

        assert np.isclose(returns.iloc[1], 0.10)  # (110-100)/100
        assert np.isclose(returns.iloc[2], -0.0454545, atol=1e-5)  # (105-110)/110
        assert np.isclose(returns.iloc[3], 0.0952381, atol=1e-5)  # (115-105)/105

    def test_simple_returns_empty(self, empty_series):
        """Test with empty series"""
        result = returns_module.calculate_simple_returns(empty_series)
        assert result.empty


class TestLogReturns:
    """Test suite for calculate_log_returns"""

    def test_log_returns_basic(self, sample_prices):
        """Test basic log returns calculation"""
        result = returns_module.calculate_log_returns(sample_prices)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_prices)
        assert pd.isna(result.iloc[0])

    def test_log_returns_formula(self):
        """Test that formula is correct: ln(P_t / P_{t-1})"""
        prices = pd.Series([100, 110, 105], index=pd.date_range('2020-01-01', periods=3))
        returns = returns_module.calculate_log_returns(prices)

        assert np.isclose(returns.iloc[1], np.log(1.1))
        assert np.isclose(returns.iloc[2], np.log(105/110))

    def test_log_returns_empty(self, empty_series):
        """Test with empty series"""
        result = returns_module.calculate_log_returns(empty_series)
        assert result.empty


class TestCumulativeReturns:
    """Test suite for calculate_cumulative_returns"""

    def test_cumulative_returns_basic(self, sample_returns):
        """Test basic cumulative returns"""
        result = returns_module.calculate_cumulative_returns(sample_returns)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_returns)

    def test_cumulative_returns_formula(self):
        """Test cumulative returns formula"""
        returns = pd.Series([0.1, 0.05, -0.03], index=pd.date_range('2020-01-01', periods=3))
        cum_returns = returns_module.calculate_cumulative_returns(returns)

        expected_0 = 1.1 - 1  # 0.1
        expected_1 = 1.1 * 1.05 - 1  # 0.155
        expected_2 = 1.1 * 1.05 * 0.97 - 1  # 0.12035

        assert np.isclose(cum_returns.iloc[0], expected_0)
        assert np.isclose(cum_returns.iloc[1], expected_1)
        assert np.isclose(cum_returns.iloc[2], expected_2)

    def test_cumulative_returns_empty(self, empty_series):
        """Test with empty series"""
        result = returns_module.calculate_cumulative_returns(empty_series)
        assert result.empty


class TestAnnualizedReturn:
    """Test suite for calculate_annualized_return"""

    def test_annualized_return_basic(self, sample_returns):
        """Test basic annualized return"""
        result = returns_module.calculate_annualized_return(sample_returns)

        assert isinstance(result, float)

    def test_annualized_return_formula(self):
        """Test annualized return formula"""
        returns = pd.Series([0.001] * 252)  # 0.1% daily for a year
        result = returns_module.calculate_annualized_return(returns)

        expected = 0.001 * 252
        assert np.isclose(result, expected)

    def test_annualized_return_empty(self, empty_series):
        """Test with empty series"""
        result = returns_module.calculate_annualized_return(empty_series)
        assert result == 0.0

    def test_annualized_return_custom_periods(self):
        """Test with custom periods per year"""
        returns = pd.Series([0.001] * 100)
        result = returns_module.calculate_annualized_return(returns, periods_per_year=12)

        expected = 0.001 * 12
        assert np.isclose(result, expected)


class TestCAGR:
    """Test suite for calculate_cagr"""

    def test_cagr_basic(self, sample_nav):
        """Test basic CAGR calculation"""
        result = returns_module.calculate_cagr(sample_nav)

        assert isinstance(result, float)

    def test_cagr_formula(self):
        """Test CAGR formula: (final/initial)^(1/years) - 1"""
        dates = pd.date_range('2020-01-01', '2021-01-01', freq='D')
        nav = pd.Series([100.0, 110.0], index=[dates[0], dates[-1]])

        result = returns_module.calculate_cagr(nav)
        expected = (110.0 / 100.0) - 1  # Exactly 1 year
        assert np.isclose(result, expected, rtol=0.01)

    def test_cagr_empty(self, empty_series):
        """Test with empty series"""
        result = returns_module.calculate_cagr(empty_series)
        assert result == 0.0

    def test_cagr_single_value(self, single_value_series):
        """Test with single value"""
        result = returns_module.calculate_cagr(single_value_series)
        assert result == 0.0

    def test_cagr_positive_growth(self):
        """Test with positive growth"""
        dates = pd.date_range('2020-01-01', periods=730, freq='D')  # 2 years
        nav = pd.Series([100.0, 121.0], index=[dates[0], dates[-1]])

        result = returns_module.calculate_cagr(nav)
        # Should be approximately 10% CAGR (1.1^2 = 1.21)
        assert np.isclose(result, 0.10, rtol=0.01)


class TestMonthlyYearlyReturns:
    """Test suite for monthly and yearly returns"""

    def test_monthly_returns_basic(self, sample_returns):
        """Test monthly returns aggregation"""
        result = returns_module.calculate_monthly_returns(sample_returns)

        assert isinstance(result, pd.Series)
        assert len(result) <= 12  # Max 12 months in sample data

    def test_monthly_returns_empty(self, empty_series):
        """Test with empty series"""
        result = returns_module.calculate_monthly_returns(empty_series)
        assert result.empty

    def test_yearly_returns_basic(self, sample_returns):
        """Test yearly returns aggregation"""
        result = returns_module.calculate_yearly_returns(sample_returns)

        assert isinstance(result, pd.Series)

    def test_yearly_returns_empty(self, empty_series):
        """Test with empty series"""
        result = returns_module.calculate_yearly_returns(empty_series)
        assert result.empty


class TestYTDMTDReturns:
    """Test suite for YTD and MTD returns"""

    def test_ytd_return_basic(self, sample_nav):
        """Test YTD return calculation"""
        result = returns_module.calculate_ytd_return(sample_nav)

        assert isinstance(result, float)

    def test_ytd_return_empty(self, empty_series):
        """Test with empty series"""
        result = returns_module.calculate_ytd_return(empty_series)
        assert result == 0.0

    def test_ytd_return_single_value(self, single_value_series):
        """Test with single value"""
        result = returns_module.calculate_ytd_return(single_value_series)
        assert result == 0.0

    def test_mtd_return_basic(self, sample_nav):
        """Test MTD return calculation"""
        result = returns_module.calculate_mtd_return(sample_nav)

        assert isinstance(result, float)

    def test_mtd_return_empty(self, empty_series):
        """Test with empty series"""
        result = returns_module.calculate_mtd_return(empty_series)
        assert result == 0.0


class TestRollingReturn:
    """Test suite for calculate_rolling_return"""

    def test_rolling_return_basic(self, sample_returns):
        """Test basic rolling return"""
        result = returns_module.calculate_rolling_return(sample_returns, window=21)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_returns)

    def test_rolling_return_window(self, sample_returns):
        """Test different window sizes"""
        for window in [5, 10, 20, 50]:
            result = returns_module.calculate_rolling_return(sample_returns, window=window)
            assert len(result) == len(sample_returns)


class TestPnLCalculations:
    """Test suite for P&L calculations"""

    def test_realized_pnl_basic(self, sample_transactions):
        """Test basic realized P&L calculation"""
        result = returns_module.calculate_realized_pnl(sample_transactions)

        assert isinstance(result, float)

    def test_realized_pnl_empty(self, empty_dataframe):
        """Test with empty transactions"""
        result = returns_module.calculate_realized_pnl(empty_dataframe)
        assert result == 0.0

    def test_realized_pnl_none(self):
        """Test with None transactions"""
        result = returns_module.calculate_realized_pnl(None)
        assert result == 0.0

    def test_realized_pnl_fifo(self):
        """Test FIFO (First In First Out) accounting"""
        txns = pd.DataFrame([
            {'datetime': pd.Timestamp('2020-01-01'), 'symbol': 'AAPL', 'side': 'BUY',
             'quantity': 100, 'price': 100.0, 'fee': 1.0},
            {'datetime': pd.Timestamp('2020-02-01'), 'symbol': 'AAPL', 'side': 'BUY',
             'quantity': 100, 'price': 110.0, 'fee': 1.0},
            {'datetime': pd.Timestamp('2020-03-01'), 'symbol': 'AAPL', 'side': 'SELL',
             'quantity': 150, 'price': 120.0, 'fee': 1.5},
        ])

        result = returns_module.calculate_realized_pnl(txns)

        # First 100 shares: profit = 100 * (120 - 100) = 2000
        # Next 50 shares: profit = 50 * (120 - 110) = 500
        # Total before fees: 2500
        # Fees: 1.0 + 1.0 + 1.5 = 3.5
        expected = 2000 + 500 - 3.5
        assert np.isclose(result, expected, rtol=0.01)

    def test_unrealized_pnl_basic(self, sample_holdings, sample_prices_dict):
        """Test basic unrealized P&L"""
        result = returns_module.calculate_unrealized_pnl(sample_holdings, sample_prices_dict)

        assert isinstance(result, float)

    def test_unrealized_pnl_empty(self):
        """Test with empty holdings or prices"""
        result = returns_module.calculate_unrealized_pnl({}, {})
        assert result == 0.0

    def test_unrealized_pnl_calculation(self):
        """Test unrealized P&L calculation"""
        holdings = {'AAPL': 100, 'GOOGL': 50}
        prices = {'AAPL': 150.0, 'GOOGL': 2800.0}

        result = returns_module.calculate_unrealized_pnl(holdings, prices)
        expected = 100 * 150.0 + 50 * 2800.0
        assert np.isclose(result, expected)

    def test_total_pnl(self):
        """Test total P&L calculation"""
        realized = 1000.0
        unrealized = 5000.0

        result = returns_module.calculate_total_pnl(realized, unrealized)
        assert result == 6000.0


class TestTradePnL:
    """Test suite for calculate_trade_pnl"""

    def test_trade_pnl_basic(self, sample_transactions):
        """Test basic trade P&L calculation"""
        result = returns_module.calculate_trade_pnl(sample_transactions)

        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert 'pnl' in result.columns
        assert 'return_pct' in result.columns

    def test_trade_pnl_empty(self, empty_dataframe):
        """Test with empty transactions"""
        result = returns_module.calculate_trade_pnl(empty_dataframe)
        assert result.empty

    def test_trade_pnl_columns(self, sample_transactions):
        """Test that output has correct columns"""
        result = returns_module.calculate_trade_pnl(sample_transactions)

        expected_columns = ['symbol', 'buy_date', 'sell_date', 'quantity',
                            'buy_price', 'sell_price', 'pnl', 'return_pct']

        for col in expected_columns:
            assert col in result.columns


class TestTWR:
    """Test suite for Time-Weighted Return"""

    def test_twr_basic(self, sample_nav):
        """Test basic TWR calculation"""
        result = returns_module.calculate_twr(sample_nav)

        assert isinstance(result, float)

    def test_twr_no_cashflows(self, sample_nav):
        """Test TWR without cashflows (should equal CAGR)"""
        twr = returns_module.calculate_twr(sample_nav, cashflows=None)
        cagr = returns_module.calculate_cagr(sample_nav)

        assert np.isclose(twr, cagr, rtol=0.01)

    def test_twr_empty(self, empty_series):
        """Test with empty NAV"""
        result = returns_module.calculate_twr(empty_series)
        assert result == 0.0

    def test_twr_with_cashflows(self, sample_nav, cashflows):
        """Test TWR with cashflows"""
        result = returns_module.calculate_twr(sample_nav, cashflows=cashflows)

        assert isinstance(result, float)


class TestIRR:
    """Test suite for Internal Rate of Return"""

    def test_irr_basic(self, cashflows):
        """Test basic IRR calculation"""
        result = returns_module.calculate_irr(cashflows)

        assert isinstance(result, float)

    def test_irr_empty(self, empty_dataframe):
        """Test with empty cashflows"""
        result = returns_module.calculate_irr(empty_dataframe)
        assert result == 0.0

    def test_irr_none(self):
        """Test with None cashflows"""
        result = returns_module.calculate_irr(None)
        assert result == 0.0


@pytest.mark.parametrize("func_name,expected_type", [
    ("calculate_simple_returns", pd.Series),
    ("calculate_log_returns", pd.Series),
    ("calculate_cumulative_returns", pd.Series),
])
def test_return_functions_type(func_name, expected_type, sample_prices):
    """Parametrized test for return function output types"""
    func = getattr(returns_module, func_name)
    result = func(sample_prices)
    assert isinstance(result, expected_type)
