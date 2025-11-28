"""Tests for trading module"""
import pytest
import pandas as pd
import numpy as np
from app.core.indicators import trading as trading_module


class TestTradeCount:
    """Test suite for calculate_trade_count"""

    def test_trade_count_basic(self, sample_transactions):
        """Test basic trade count"""
        result = trading_module.calculate_trade_count(sample_transactions)

        assert isinstance(result, int)
        assert result >= 0

    def test_trade_count_empty(self, empty_dataframe):
        """Test with empty transactions"""
        result = trading_module.calculate_trade_count(empty_dataframe)
        assert result == 0

    def test_trade_count_none(self):
        """Test with None transactions"""
        result = trading_module.calculate_trade_count(None)
        assert result == 0

    def test_trade_count_formula(self):
        """Test trade count is minimum of buy and sell count"""
        txns = pd.DataFrame([
            {'symbol': 'AAPL', 'side': 'BUY', 'quantity': 100, 'price': 100.0, 'fee': 1.0},
            {'symbol': 'AAPL', 'side': 'BUY', 'quantity': 100, 'price': 110.0, 'fee': 1.0},
            {'symbol': 'AAPL', 'side': 'SELL', 'quantity': 150, 'price': 120.0, 'fee': 1.5},
        ])

        result = trading_module.calculate_trade_count(txns)
        # 2 buys, 1 sell -> min(2, 1) = 1
        assert result == 1


class TestTurnoverRate:
    """Test suite for calculate_turnover_rate"""

    def test_turnover_rate_basic(self, sample_transactions, sample_nav):
        """Test basic turnover rate"""
        result = trading_module.calculate_turnover_rate(sample_transactions, sample_nav)

        assert isinstance(result, float)
        assert result >= 0

    def test_turnover_rate_empty(self, empty_dataframe, sample_nav):
        """Test with empty transactions"""
        result = trading_module.calculate_turnover_rate(empty_dataframe, sample_nav)
        assert result == 0.0

    def test_turnover_rate_none(self, sample_nav):
        """Test with None transactions"""
        result = trading_module.calculate_turnover_rate(None, sample_nav)
        assert result == 0.0


class TestTurnoverRateByAsset:
    """Test suite for calculate_turnover_rate_by_asset"""

    def test_turnover_by_asset_basic(self, sample_transactions, sample_nav):
        """Test basic turnover by asset"""
        result = trading_module.calculate_turnover_rate_by_asset(
            sample_transactions, sample_nav
        )

        assert isinstance(result, dict)

    def test_turnover_by_asset_empty(self, empty_dataframe, sample_nav):
        """Test with empty transactions"""
        result = trading_module.calculate_turnover_rate_by_asset(empty_dataframe, sample_nav)
        assert result == {}


class TestAvgHoldingPeriod:
    """Test suite for calculate_avg_holding_period"""

    def test_avg_holding_period_basic(self, sample_transactions):
        """Test basic average holding period"""
        result = trading_module.calculate_avg_holding_period(sample_transactions)

        assert isinstance(result, float)
        assert result >= 0

    def test_avg_holding_period_empty(self, empty_dataframe):
        """Test with empty transactions"""
        result = trading_module.calculate_avg_holding_period(empty_dataframe)
        assert result == 0.0


class TestWinRate:
    """Test suite for calculate_win_rate"""

    def test_win_rate_basic(self, sample_transactions):
        """Test basic win rate"""
        result = trading_module.calculate_win_rate(sample_transactions)

        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_win_rate_empty(self, empty_dataframe):
        """Test with empty transactions"""
        result = trading_module.calculate_win_rate(empty_dataframe)
        assert result == 0.0

    def test_win_rate_all_wins(self):
        """Test with all winning trades"""
        txns = pd.DataFrame([
            {'datetime': pd.Timestamp('2020-01-01'), 'symbol': 'AAPL', 'side': 'BUY',
             'quantity': 100, 'price': 100.0, 'fee': 1.0},
            {'datetime': pd.Timestamp('2020-02-01'), 'symbol': 'AAPL', 'side': 'SELL',
             'quantity': 100, 'price': 120.0, 'fee': 1.0},
        ])

        result = trading_module.calculate_win_rate(txns)
        assert result == 1.0


class TestProfitLossRatio:
    """Test suite for calculate_profit_loss_ratio"""

    def test_pl_ratio_basic(self, sample_transactions):
        """Test basic profit/loss ratio"""
        result = trading_module.calculate_profit_loss_ratio(sample_transactions)

        assert isinstance(result, float)
        assert result >= 0

    def test_pl_ratio_empty(self, empty_dataframe):
        """Test with empty transactions"""
        result = trading_module.calculate_profit_loss_ratio(empty_dataframe)
        assert result == 0.0


class TestMaxTradeProfitLoss:
    """Test suite for max trade profit/loss"""

    def test_max_trade_profit_basic(self, sample_transactions):
        """Test basic max trade profit"""
        result = trading_module.calculate_max_trade_profit(sample_transactions)

        assert isinstance(result, float)

    def test_max_trade_loss_basic(self, sample_transactions):
        """Test basic max trade loss"""
        result = trading_module.calculate_max_trade_loss(sample_transactions)

        assert isinstance(result, float)

    def test_max_trade_profit_empty(self, empty_dataframe):
        """Test with empty transactions"""
        result = trading_module.calculate_max_trade_profit(empty_dataframe)
        assert result == 0.0

    def test_max_trade_loss_empty(self, empty_dataframe):
        """Test with empty transactions"""
        result = trading_module.calculate_max_trade_loss(empty_dataframe)
        assert result == 0.0


class TestConsecutiveTrades:
    """Test suite for consecutive winning/losing trades"""

    def test_consecutive_winning_basic(self, sample_transactions):
        """Test basic consecutive winning trades"""
        result = trading_module.calculate_consecutive_winning_trades(sample_transactions)

        assert isinstance(result, int)
        assert result >= 0

    def test_consecutive_losing_basic(self, sample_transactions):
        """Test basic consecutive losing trades"""
        result = trading_module.calculate_consecutive_losing_trades(sample_transactions)

        assert isinstance(result, int)
        assert result >= 0

    def test_consecutive_winning_empty(self, empty_dataframe):
        """Test with empty transactions"""
        result = trading_module.calculate_consecutive_winning_trades(empty_dataframe)
        assert result == 0

    def test_consecutive_losing_empty(self, empty_dataframe):
        """Test with empty transactions"""
        result = trading_module.calculate_consecutive_losing_trades(empty_dataframe)
        assert result == 0


class TestProfitFactor:
    """Test suite for calculate_profit_factor"""

    def test_profit_factor_basic(self, sample_transactions):
        """Test basic profit factor"""
        result = trading_module.calculate_profit_factor(sample_transactions)

        assert isinstance(result, float)
        assert result >= 0

    def test_profit_factor_empty(self, empty_dataframe):
        """Test with empty transactions"""
        result = trading_module.calculate_profit_factor(empty_dataframe)
        assert result == 0.0

    def test_profit_factor_only_wins(self):
        """Test with only winning trades"""
        txns = pd.DataFrame([
            {'datetime': pd.Timestamp('2020-01-01'), 'symbol': 'AAPL', 'side': 'BUY',
             'quantity': 100, 'price': 100.0, 'fee': 1.0},
            {'datetime': pd.Timestamp('2020-02-01'), 'symbol': 'AAPL', 'side': 'SELL',
             'quantity': 100, 'price': 120.0, 'fee': 1.0},
        ])

        result = trading_module.calculate_profit_factor(txns)
        assert np.isinf(result)


class TestRecoveryFactor:
    """Test suite for calculate_recovery_factor"""

    def test_recovery_factor_basic(self, sample_nav):
        """Test basic recovery factor"""
        result = trading_module.calculate_recovery_factor(sample_nav)

        assert isinstance(result, float)

    def test_recovery_factor_empty(self, empty_series):
        """Test with empty NAV"""
        result = trading_module.calculate_recovery_factor(empty_series)
        assert result == 0.0


class TestKellyCriterion:
    """Test suite for calculate_kelly_criterion"""

    def test_kelly_basic(self):
        """Test basic Kelly criterion"""
        win_rate = 0.6
        pl_ratio = 2.0

        result = trading_module.calculate_kelly_criterion(win_rate, pl_ratio)

        assert isinstance(result, float)
        assert 0 <= result <= 1.0

    def test_kelly_formula(self):
        """Test Kelly formula: (bp - q) / b"""
        win_rate = 0.6
        loss_rate = 0.4
        pl_ratio = 2.0

        result = trading_module.calculate_kelly_criterion(win_rate, pl_ratio)

        expected = (pl_ratio * win_rate - loss_rate) / pl_ratio
        assert np.isclose(result, max(0.0, expected))

    def test_kelly_invalid_inputs(self):
        """Test with invalid inputs"""
        assert trading_module.calculate_kelly_criterion(0.0, 2.0) == 0.0
        assert trading_module.calculate_kelly_criterion(1.0, 2.0) == 0.0
        assert trading_module.calculate_kelly_criterion(0.6, 0.0) == 0.0
        assert trading_module.calculate_kelly_criterion(0.6, -1.0) == 0.0


class TestAllTradingMetrics:
    """Test suite for calculate_all_trading_metrics"""

    def test_all_metrics_basic(self, sample_transactions, sample_nav):
        """Test basic all trading metrics"""
        result = trading_module.calculate_all_trading_metrics(
            sample_transactions, sample_nav
        )

        assert isinstance(result, dict)
        assert 'trade_count' in result
        assert 'turnover_rate' in result
        assert 'win_rate' in result
        assert 'profit_loss_ratio' in result
        assert 'kelly_criterion' in result

    def test_all_metrics_empty(self, empty_dataframe, sample_nav):
        """Test with empty transactions"""
        result = trading_module.calculate_all_trading_metrics(empty_dataframe, sample_nav)

        assert isinstance(result, dict)
        assert result['trade_count'] == 0
        assert result['win_rate'] == 0.0

    def test_all_metrics_none(self, sample_nav):
        """Test with None transactions"""
        result = trading_module.calculate_all_trading_metrics(None, sample_nav)

        assert isinstance(result, dict)
        assert result['trade_count'] == 0


@pytest.mark.parametrize("func_name", [
    "calculate_trade_count",
    "calculate_consecutive_winning_trades",
    "calculate_consecutive_losing_trades",
])
def test_trading_functions_return_int(func_name, sample_transactions):
    """Parametrized test that counting functions return int"""
    func = getattr(trading_module, func_name)
    result = func(sample_transactions)
    assert isinstance(result, int)
