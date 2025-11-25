import pandas as pd
import json
import os
from typing import Dict, List, Optional
from pathlib import Path


class BenchmarkLoader:
    """Load and manage benchmark index data"""

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            current_file = Path(__file__)
            self.data_dir = current_file.parent.parent.parent / "data"
        else:
            self.data_dir = Path(data_dir)

        self.benchmarks_config = self._load_benchmarks_config()

    def _load_benchmarks_config(self) -> Dict:
        """Load benchmarks configuration from JSON file"""
        config_path = self.data_dir / "benchmarks.json"

        if not config_path.exists():
            return {"benchmarks": []}

        with open(config_path, 'r') as f:
            return json.load(f)

    def get_available_benchmarks(self) -> List[Dict]:
        """Get list of available benchmark indices

        Returns:
            List of benchmark dicts with symbol, name, region, category
        """
        return self.benchmarks_config.get("benchmarks", [])

    def load_benchmark_price(self, symbol: str, start_date: Optional[pd.Timestamp] = None,
                            end_date: Optional[pd.Timestamp] = None) -> pd.Series:
        """Load price data for a specific benchmark

        Args:
            symbol: Benchmark symbol (e.g., '^GSPC')
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            pd.Series with date index and close prices
        """
        price_file = self.data_dir / "prices" / f"{symbol}.csv"

        if not price_file.exists():
            return pd.Series(dtype=float)

        try:
            df = pd.read_csv(price_file, index_col=0, parse_dates=True)

            if 'Close' in df.columns:
                prices = df['Close']
            elif 'Adj Close' in df.columns:
                prices = df['Adj Close']
            else:
                return pd.Series(dtype=float)

            if start_date is not None:
                prices = prices[prices.index >= start_date]

            if end_date is not None:
                prices = prices[prices.index <= end_date]

            return prices.dropna()

        except Exception as e:
            print(f"Error loading benchmark {symbol}: {e}")
            return pd.Series(dtype=float)

    def load_all_benchmarks(self, start_date: Optional[pd.Timestamp] = None,
                           end_date: Optional[pd.Timestamp] = None) -> Dict[str, pd.Series]:
        """Load all available benchmark price data

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dict of {symbol: price_series}
        """
        benchmarks = {}

        for benchmark in self.get_available_benchmarks():
            symbol = benchmark['symbol']
            prices = self.load_benchmark_price(symbol, start_date, end_date)

            if not prices.empty:
                benchmarks[symbol] = prices

        return benchmarks

    def load_benchmarks_by_region(self, region: str, start_date: Optional[pd.Timestamp] = None,
                                  end_date: Optional[pd.Timestamp] = None) -> Dict[str, pd.Series]:
        """Load benchmarks filtered by region

        Args:
            region: Region filter (e.g., 'US', 'Europe', 'Asia')
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dict of {symbol: price_series}
        """
        benchmarks = {}

        for benchmark in self.get_available_benchmarks():
            if benchmark.get('region') == region:
                symbol = benchmark['symbol']
                prices = self.load_benchmark_price(symbol, start_date, end_date)

                if not prices.empty:
                    benchmarks[symbol] = prices

        return benchmarks

    def get_benchmark_name(self, symbol: str) -> str:
        """Get display name for a benchmark symbol

        Args:
            symbol: Benchmark symbol

        Returns:
            Human-readable name
        """
        for benchmark in self.get_available_benchmarks():
            if benchmark['symbol'] == symbol:
                return benchmark.get('name', symbol)

        return symbol

    def load_benchmark_returns(self, symbol: str, start_date: Optional[pd.Timestamp] = None,
                               end_date: Optional[pd.Timestamp] = None) -> pd.Series:
        """Load and calculate returns for a benchmark

        Args:
            symbol: Benchmark symbol
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            pd.Series of daily returns
        """
        prices = self.load_benchmark_price(symbol, start_date, end_date)

        if prices.empty:
            return pd.Series(dtype=float)

        returns = prices.pct_change().dropna()
        return returns

    def load_all_benchmark_returns(self, start_date: Optional[pd.Timestamp] = None,
                                   end_date: Optional[pd.Timestamp] = None) -> Dict[str, pd.Series]:
        """Load returns for all benchmarks

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dict of {symbol: returns_series}
        """
        all_returns = {}

        for benchmark in self.get_available_benchmarks():
            symbol = benchmark['symbol']
            returns = self.load_benchmark_returns(symbol, start_date, end_date)

            if not returns.empty:
                all_returns[symbol] = returns

        return all_returns


def get_benchmark_loader() -> BenchmarkLoader:
    """Factory function to get BenchmarkLoader instance"""
    return BenchmarkLoader()
