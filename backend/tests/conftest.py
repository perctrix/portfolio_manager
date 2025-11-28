"""Shared pytest fixtures for all tests"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_prices():
    """Generate sample price series for testing"""
    dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')
    np.random.seed(42)
    prices = 100 * (1 + np.random.randn(len(dates)).cumsum() * 0.01)
    prices = pd.Series(prices, index=dates)
    return prices


@pytest.fixture
def sample_nav():
    """Generate sample NAV series with known characteristics"""
    dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')
    np.random.seed(42)
    returns = np.random.randn(len(dates)) * 0.01
    nav = 100 * (1 + pd.Series(returns, index=dates)).cumprod()
    return nav


@pytest.fixture
def sample_returns():
    """Generate sample returns series"""
    dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')
    np.random.seed(42)
    returns = pd.Series(np.random.randn(len(dates)) * 0.01, index=dates)
    return returns


@pytest.fixture
def positive_returns():
    """Generate returns series with only positive values"""
    dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')
    np.random.seed(42)
    returns = pd.Series(np.abs(np.random.randn(len(dates))) * 0.01, index=dates)
    return returns


@pytest.fixture
def negative_returns():
    """Generate returns series with only negative values"""
    dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')
    np.random.seed(42)
    returns = pd.Series(-np.abs(np.random.randn(len(dates))) * 0.01, index=dates)
    return returns


@pytest.fixture
def empty_series():
    """Empty pandas Series"""
    return pd.Series(dtype=float)


@pytest.fixture
def empty_dataframe():
    """Empty pandas DataFrame"""
    return pd.DataFrame()


@pytest.fixture
def sample_transactions():
    """Generate sample transaction DataFrame"""
    data = [
        {'datetime': pd.Timestamp('2020-01-01'), 'symbol': 'AAPL', 'side': 'BUY', 'quantity': 100, 'price': 100.0, 'fee': 1.0},
        {'datetime': pd.Timestamp('2020-02-01'), 'symbol': 'GOOGL', 'side': 'BUY', 'quantity': 50, 'price': 200.0, 'fee': 1.0},
        {'datetime': pd.Timestamp('2020-03-01'), 'symbol': 'AAPL', 'side': 'SELL', 'quantity': 50, 'price': 110.0, 'fee': 0.5},
        {'datetime': pd.Timestamp('2020-04-01'), 'symbol': 'GOOGL', 'side': 'SELL', 'quantity': 25, 'price': 210.0, 'fee': 0.5},
        {'datetime': pd.Timestamp('2020-05-01'), 'symbol': 'AAPL', 'side': 'BUY', 'quantity': 50, 'price': 105.0, 'fee': 0.5},
        {'datetime': pd.Timestamp('2020-06-01'), 'symbol': 'AAPL', 'side': 'SELL', 'quantity': 100, 'price': 120.0, 'fee': 1.0},
    ]
    return pd.DataFrame(data)


@pytest.fixture
def sample_holdings():
    """Generate sample holdings dictionary"""
    return {
        'AAPL': 100,
        'GOOGL': 50,
        'MSFT': 75,
        'AMZN': 25
    }


@pytest.fixture
def sample_prices_dict():
    """Generate sample prices dictionary"""
    return {
        'AAPL': 150.0,
        'GOOGL': 2800.0,
        'MSFT': 300.0,
        'AMZN': 3300.0
    }


@pytest.fixture
def sample_weights():
    """Generate sample portfolio weights"""
    return {
        'AAPL': 0.25,
        'GOOGL': 0.35,
        'MSFT': 0.25,
        'AMZN': 0.15
    }


@pytest.fixture
def sample_price_history():
    """Generate sample price history DataFrame"""
    dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')
    np.random.seed(42)

    data = {}
    for symbol in ['AAPL', 'GOOGL', 'MSFT', 'AMZN']:
        base = 100 if symbol == 'AAPL' else (200 if symbol == 'GOOGL' else (150 if symbol == 'MSFT' else 250))
        returns = np.random.randn(len(dates)) * 0.015
        prices = base * (1 + pd.Series(returns).cumsum() * 0.01)
        data[symbol] = prices.values

    return pd.DataFrame(data, index=dates)


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV DataFrame for technical indicators"""
    dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')
    np.random.seed(42)

    close = 100 * (1 + np.random.randn(len(dates)).cumsum() * 0.01)
    high = close * (1 + np.abs(np.random.randn(len(dates))) * 0.01)
    low = close * (1 - np.abs(np.random.randn(len(dates))) * 0.01)
    open_prices = close * (1 + np.random.randn(len(dates)) * 0.005)
    volume = np.random.randint(1000000, 10000000, size=len(dates))

    return pd.DataFrame({
        'Open': open_prices,
        'High': high,
        'Low': low,
        'Close': close,
        'Volume': volume
    }, index=dates)


@pytest.fixture
def sector_map():
    """Generate sample sector mapping"""
    return {
        'AAPL': 'Technology',
        'GOOGL': 'Technology',
        'MSFT': 'Technology',
        'AMZN': 'Consumer'
    }


@pytest.fixture
def industry_map():
    """Generate sample industry mapping"""
    return {
        'AAPL': 'Hardware',
        'GOOGL': 'Internet',
        'MSFT': 'Software',
        'AMZN': 'E-commerce'
    }


@pytest.fixture
def benchmark_returns():
    """Generate sample benchmark returns"""
    dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')
    np.random.seed(123)
    returns = pd.Series(np.random.randn(len(dates)) * 0.008, index=dates)
    return returns


@pytest.fixture
def cashflows():
    """Generate sample cashflow DataFrame"""
    data = [
        {'date': pd.Timestamp('2020-01-01'), 'amount': -10000},
        {'date': pd.Timestamp('2020-04-01'), 'amount': -5000},
        {'date': pd.Timestamp('2020-08-01'), 'amount': 3000},
        {'date': pd.Timestamp('2020-12-31'), 'amount': 15000}
    ]
    return pd.DataFrame(data)


@pytest.fixture
def constant_series():
    """Generate series with constant values"""
    dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')
    return pd.Series(100.0, index=dates)


@pytest.fixture
def single_value_series():
    """Generate series with single value"""
    return pd.Series([100.0], index=[pd.Timestamp('2020-01-01')])


@pytest.fixture
def zero_returns():
    """Generate returns series with all zeros"""
    dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')
    return pd.Series(0.0, index=dates)


@pytest.fixture
def correlated_returns():
    """Generate two correlated return series"""
    dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')
    np.random.seed(42)
    base_returns = np.random.randn(len(dates)) * 0.01

    portfolio_returns = pd.Series(base_returns + np.random.randn(len(dates)) * 0.003, index=dates)
    benchmark_returns = pd.Series(base_returns + np.random.randn(len(dates)) * 0.002, index=dates)

    return portfolio_returns, benchmark_returns


@pytest.fixture
def multi_asset_returns():
    """Generate returns DataFrame with multiple assets"""
    dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')
    np.random.seed(42)

    returns_data = {}
    for symbol in ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']:
        returns_data[symbol] = np.random.randn(len(dates)) * 0.015

    return pd.DataFrame(returns_data, index=dates)
