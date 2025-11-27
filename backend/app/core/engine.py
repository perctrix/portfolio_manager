import pandas as pd
import numpy as np
from datetime import datetime
from typing import Any, Dict, Optional
from app.models.portfolio import Portfolio, PortfolioType
from app.core import prices
from app.core import indicators

class PortfolioEngine:
    def __init__(self, portfolio: Portfolio, data: list[dict]):
        self.portfolio: Portfolio = portfolio
        self.failed_tickers: list[str] = []
        self.suggested_initial_deposit: float = 0.0
        self.cash_history: pd.Series = pd.Series()

        # Request-scoped caches
        self._price_cache: Dict[str, pd.DataFrame] = {}
        self._nav_cache: Optional[pd.Series] = None
        self._base_data_cache: Optional[Dict[str, Any]] = None

        if self.portfolio.type == PortfolioType.TRANSACTION:
            if data:
                self.transactions: pd.DataFrame = pd.DataFrame(data)
                self.transactions['datetime'] = pd.to_datetime(self.transactions['datetime'])
                self.transactions = self.transactions.sort_values('datetime')
            else:
                self.transactions: pd.DataFrame = pd.DataFrame(columns=["datetime", "symbol", "side", "quantity", "price", "fee", "currency", "account", "note"])
        else:
            if data:
                self.positions: pd.DataFrame = pd.DataFrame(data)
            else:
                self.positions: pd.DataFrame = pd.DataFrame(columns=["as_of", "symbol", "quantity", "cost_basis", "currency", "note"])

    def _get_price_history(self, symbol: str) -> pd.DataFrame:
        """Get price history with request-scoped cache.

        Args:
            symbol: Stock ticker symbol

        Returns:
            DataFrame with price history (columns: Open, High, Low, Close, Volume)
        """
        if symbol not in self._price_cache:
            self._price_cache[symbol] = prices.get_price_history(symbol)
        return self._price_cache[symbol]

    def set_price_cache(self, cache: Dict[str, pd.DataFrame]) -> None:
        """Set pre-loaded price cache from endpoint.

        Args:
            cache: Dictionary mapping symbol -> price DataFrame
        """
        self._price_cache = cache

    def _prepare_base_data(self) -> Dict[str, Any]:
        """Prepare all base data for indicator calculations (cached).

        Returns:
            Dictionary containing:
            - nav: pd.Series - NAV history
            - returns: pd.Series - Daily returns
            - current_holdings: Dict[str, float] - {symbol: quantity}
            - current_prices: Dict[str, float] - {symbol: current_price}
            - weights: Dict[str, float] - {symbol: portfolio_weight}
            - price_history: pd.DataFrame - Price history for all holdings
        """
        if self._base_data_cache is not None:
            return self._base_data_cache

        nav = self.calculate_nav_history()

        if nav.empty:
            self._base_data_cache = {
                'nav': nav,
                'returns': pd.Series(),
                'current_holdings': {},
                'current_prices': {},
                'weights': {},
                'price_history': pd.DataFrame()
            }
            return self._base_data_cache

        returns = nav.pct_change(fill_method=None).dropna()
        current_holdings = self._get_current_holdings()
        current_prices = self._get_current_prices(current_holdings)
        weights = self._calculate_weights(current_holdings, current_prices)
        price_history = self._build_price_history_df(current_holdings)

        self._base_data_cache = {
            'nav': nav,
            'returns': returns,
            'current_holdings': current_holdings,
            'current_prices': current_prices,
            'weights': weights,
            'price_history': price_history
        }
        return self._base_data_cache

    def _calculate_suggested_deposit(self, txns: pd.DataFrame) -> float:
        """Calculate suggested initial deposit amount based on transaction history"""
        temp_cash = 0.0
        min_cash = 0.0

        for _, txn in txns.iterrows():
            side = txn['side'].upper()
            qty = float(txn['quantity'])
            price = float(txn['price'])
            fee = float(txn['fee']) if not pd.isna(txn['fee']) else 0.0

            if side == 'BUY':
                temp_cash -= (qty * price + fee)
            elif side == 'SELL':
                temp_cash += (qty * price - fee)
            elif side == 'DEPOSIT':
                temp_cash += qty
            elif side == 'WITHDRAW':
                temp_cash -= qty

            min_cash = min(min_cash, temp_cash)

        suggested = abs(min_cash) if min_cash < 0 else 0.0
        return round(suggested, -2) if suggested > 100 else round(suggested, 2)

    def calculate_nav_history(self) -> pd.Series:
        """Calculate NAV history with caching."""
        if self._nav_cache is not None:
            return self._nav_cache

        result = self._calculate_nav_history_impl()
        self._nav_cache = result
        return result

    def _calculate_nav_history_impl(self) -> pd.Series:
        """Internal implementation of NAV history calculation."""
        if self.portfolio.type == PortfolioType.SNAPSHOT:
            positions = self.positions
            if positions.empty:
                return pd.Series()
                
            # Get all symbols
            symbols = positions['symbol'].unique()
            price_data = {}

            # Load prices
            for sym in symbols:
                df = self._get_price_history(sym)
                if not df.empty:
                    price_data[sym] = df['Close']
                else:
                    self.failed_tickers.append(sym)
            
            if not price_data:
                return pd.Series()
                
            # Align dates (inner join to find common history)
            price_df = pd.DataFrame(price_data).dropna()
            
            if price_df.empty:
                return pd.Series()
                
            # Calculate NAV
            nav = pd.Series(0.0, index=price_df.index)
            
            for _, row in positions.iterrows():
                sym = row['symbol']
                qty = row['quantity']
                if sym in price_df.columns:
                    nav += price_df[sym] * qty
                    
            return nav
            
        elif self.portfolio.type == PortfolioType.TRANSACTION:
            txns = self.transactions
            if txns.empty:
                return pd.Series()

            # Check if there is an initial DEPOSIT
            txns_sorted = txns.sort_values('datetime')
            deposit_txns = txns_sorted[txns_sorted['side'].str.upper() == 'DEPOSIT']
            has_initial_deposit = False
            initial_cash = 0.0
            initial_deposit_indices = set()

            if not deposit_txns.empty:
                # Find first BUY/SELL transaction
                trade_txns = txns_sorted[txns_sorted['side'].str.upper().isin(['BUY', 'SELL'])]

                if not trade_txns.empty:
                    first_trade_time = trade_txns.iloc[0]['datetime']
                    # Check if any DEPOSIT exists before or at the same time as first trade
                    # Use floor to minute to handle precision issues
                    first_trade_time_floored = first_trade_time.floor('min')
                    early_deposits = deposit_txns[deposit_txns['datetime'].dt.floor('min') <= first_trade_time_floored]

                    if not early_deposits.empty:
                        has_initial_deposit = True
                        initial_cash = early_deposits['quantity'].sum()
                        initial_deposit_indices = set(early_deposits.index)
                else:
                    # Only DEPOSIT transactions exist, no trades yet
                    has_initial_deposit = True
                    initial_cash = deposit_txns['quantity'].sum()
                    initial_deposit_indices = set(deposit_txns.index)

            if not has_initial_deposit:
                suggested_amount = self._calculate_suggested_deposit(txns_sorted)
                self.suggested_initial_deposit = suggested_amount
                initial_cash = suggested_amount

            # Identify all symbols and date range
            symbols = txns['symbol'].unique()
            start_date = txns['datetime'].min().date()
            end_date = datetime.now().date() # Or max price date

            # Fetch prices
            price_data = {}
            for sym in symbols:
                if sym == 'CASH': continue
                df = self._get_price_history(sym)
                if not df.empty:
                    price_data[sym] = df['Close']
                else:
                    self.failed_tickers.append(sym)
            
            if not price_data:
                return pd.Series()

            # Create master price DataFrame
            price_df = pd.DataFrame(price_data)
            # Filter to start date
            price_df = price_df[price_df.index.date >= start_date]
            # Forward fill missing prices (holdings don't disappear if price is missing)
            price_df = price_df.ffill()

            # Create complete date range including all transaction dates
            txn_dates = txns['datetime'].dt.normalize().unique()
            all_dates = pd.DatetimeIndex(sorted(set(price_df.index.normalize()).union(set(txn_dates))))
            all_dates = all_dates[all_dates.date >= start_date]

            # Reindex price_df to include all dates, forward fill prices for non-trading days
            price_df = price_df.reindex(all_dates, method='ffill')

            # Initialize state
            current_holdings = {sym: 0.0 for sym in symbols}
            current_cash = initial_cash

            nav_history = {}
            cash_history = {}

            # Iterate through each day (including transaction-only days)
            # We need to process transactions that happened on or before this day
            # Optimization: Group txns by date
            txns['date'] = txns['datetime'].dt.date
            txns_by_date = txns.groupby('date')

            for date in price_df.index:
                d = date.date()
                
                # Process transactions for this day
                if d in txns_by_date.groups:
                    day_txns = txns_by_date.get_group(d)
                    for idx, txn in day_txns.iterrows():
                        sym = txn['symbol']
                        qty = float(txn['quantity'])
                        price = float(txn['price'])
                        fee = float(txn['fee']) if not pd.isna(txn['fee']) else 0.0
                        side = txn['side'].upper()

                        if side == 'BUY':
                            current_holdings[sym] = current_holdings.get(sym, 0.0) + qty
                            current_cash -= (qty * price + fee)
                        elif side == 'SELL':
                            current_holdings[sym] = current_holdings.get(sym, 0.0) - qty
                            current_cash += (qty * price - fee)
                        elif side == 'DEPOSIT':
                            # Skip DEPOSIT if it was already counted in initial_cash
                            if idx not in initial_deposit_indices:
                                current_cash += qty
                        elif side == 'WITHDRAW':
                            current_cash -= qty

                # Calculate NAV for this day
                daily_value = current_cash
                for sym, qty in current_holdings.items():
                    if qty != 0 and sym in price_df.columns:
                        # Use today's price, or prev if missing
                        if not pd.isna(price_df.at[date, sym]):
                            daily_value += qty * price_df.at[date, sym]

                nav_history[date] = daily_value
                cash_history[date] = current_cash

            self.cash_history = pd.Series(cash_history)
            return pd.Series(nav_history)
            
        return pd.Series()

    def get_indicators(self) -> Dict[str, Any]:
        """Get basic indicators using cached base data.

        Returns:
            Dictionary with basic indicators including:
            - total_return, cagr, volatility, sharpe, max_drawdown
            - sortino, calmar, var_95, cvar_95
            - allocation metrics (hhi, concentration)
            - risk_decomposition (if multiple holdings)
        """
        data = self._prepare_base_data()

        if data['nav'].empty:
            return {}

        basic = indicators.calculate_basic_metrics(data['nav'])

        if not data['returns'].empty:
            advanced_risk = indicators.calculate_risk_metrics(data['returns'])
            basic.update(advanced_risk)

        allocation = indicators.calculate_allocation_metrics(data['weights'])
        basic.update(allocation)

        if not data['price_history'].empty and len(data['weights']) > 1:
            risk_decomp = indicators.calculate_risk_contribution(
                data['weights'], data['price_history']
            )
            basic["risk_decomposition"] = risk_decomp

        return basic

    def _get_current_holdings(self) -> Dict[str, float]:
        """Get current holdings as {symbol: quantity}"""
        current_holdings = {}

        if self.portfolio.type == PortfolioType.SNAPSHOT:
            positions = self.positions
            for _, row in positions.iterrows():
                current_holdings[row['symbol']] = float(row['quantity'])
        elif self.portfolio.type == PortfolioType.TRANSACTION:
            txns = self.transactions
            for _, txn in txns.iterrows():
                sym = txn['symbol']
                qty = float(txn['quantity'])
                side = txn['side'].upper()
                if side == 'BUY':
                    current_holdings[sym] = current_holdings.get(sym, 0.0) + qty
                elif side == 'SELL':
                    current_holdings[sym] = current_holdings.get(sym, 0.0) - qty

        return {k: v for k, v in current_holdings.items() if v != 0}

    def _get_current_prices(self, holdings: Dict[str, float]) -> Dict[str, float]:
        """Get current prices for holdings using cache."""
        current_prices: Dict[str, float] = {}
        for sym in holdings.keys():
            df = self._get_price_history(sym)
            if not df.empty:
                current_prices[sym] = float(df['Close'].iloc[-1])
        return current_prices

    def _calculate_weights(self, holdings: Dict[str, float], prices: Dict[str, float]) -> Dict[str, float]:
        """Calculate portfolio weights"""
        return indicators.calculate_weights(holdings, prices)

    def _build_price_history_df(self, holdings: Dict[str, float]) -> pd.DataFrame:
        """Build price history DataFrame for holdings using cache."""
        price_data: Dict[str, pd.Series] = {}
        for sym in holdings.keys():
            df = self._get_price_history(sym)
            if not df.empty:
                price_data[sym] = df['Close']

        if not price_data:
            return pd.DataFrame()

        return pd.DataFrame(price_data)

    def get_basic_indicators(self) -> Dict[str, float]:
        """Get 5 basic indicators: total_return, cagr, volatility, sharpe, max_drawdown"""
        nav = self.calculate_nav_history()
        return indicators.calculate_basic_portfolio_indicators(nav)

    def get_all_indicators(self) -> Dict[str, Any]:
        """Get all portfolio indicators using cached base data (approximately 79 indicators).

        Returns:
            Dictionary with indicators organized by category:
            - returns: total_return, cagr, ytd, mtd, pnl, etc.
            - risk: volatility, var, cvar, etc.
            - drawdown: max_drawdown, recovery time, etc.
            - risk_adjusted_ratios: sharpe, sortino, calmar, etc.
            - allocation: weights, concentration, etc.
            - trading: turnover, win_rate, profit_loss_ratio, etc. (transaction mode only)
        """
        data = self._prepare_base_data()

        transactions = (
            self.transactions
            if self.portfolio.type == PortfolioType.TRANSACTION
            else None
        )

        return indicators.calculate_all_portfolio_indicators(
            nav=data['nav'],
            transactions=transactions,
            holdings=data['current_holdings'],
            prices=data['current_prices'],
            price_history=data['price_history'],
            weights=data['weights']
        )
