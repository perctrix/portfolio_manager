import pandas as pd
import numpy as np
from datetime import datetime
from typing import Any
from app.models.portfolio import Portfolio, PortfolioType
from app.core import prices, indicators

class PortfolioEngine:
    def __init__(self, portfolio: Portfolio, data: list[dict]):
        self.portfolio = portfolio

        if self.portfolio.type == PortfolioType.TRANSACTION:
            if data:
                self.transactions = pd.DataFrame(data)
                self.transactions['datetime'] = pd.to_datetime(self.transactions['datetime'])
                self.transactions = self.transactions.sort_values('datetime')
            else:
                self.transactions = pd.DataFrame(columns=["datetime", "symbol", "side", "quantity", "price", "fee", "currency", "account", "note"])
        else:
            if data:
                self.positions = pd.DataFrame(data)
            else:
                self.positions = pd.DataFrame(columns=["as_of", "symbol", "quantity", "cost_basis", "currency", "note"])

    def calculate_nav_history(self) -> pd.Series:
        """
        Calculate NAV history.
        """
        if self.portfolio.type == PortfolioType.SNAPSHOT:
            positions = self.positions
            if positions.empty:
                return pd.Series()
                
            # Get all symbols
            symbols = positions['symbol'].unique()
            price_data = {}
            
            # Load prices
            for sym in symbols:
                df = prices.get_price_history(sym)
                if not df.empty:
                    price_data[sym] = df['Close']
            
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

            # Identify all symbols and date range
            symbols = txns['symbol'].unique()
            start_date = txns['datetime'].min().date()
            end_date = datetime.now().date() # Or max price date

            # Fetch prices
            price_data = {}
            for sym in symbols:
                if sym == 'CASH': continue
                df = prices.get_price_history(sym)
                if not df.empty:
                    price_data[sym] = df['Close']
            
            if not price_data:
                return pd.Series()

            # Create master price DataFrame
            price_df = pd.DataFrame(price_data)
            # Filter to start date
            price_df = price_df[price_df.index.date >= start_date]
            # Forward fill missing prices (holdings don't disappear if price is missing)
            price_df = price_df.ffill()
            
            # Initialize state
            current_holdings = {sym: 0.0 for sym in symbols}
            current_cash = 0.0
            
            nav_history = {}
            
            # Iterate through each day in price_df
            # We need to process transactions that happened on or before this day
            # Optimization: Group txns by date
            txns['date'] = txns['datetime'].dt.date
            txns_by_date = txns.groupby('date')
            
            for date in price_df.index:
                d = date.date()
                
                # Process transactions for this day
                if d in txns_by_date.groups:
                    day_txns = txns_by_date.get_group(d)
                    for _, txn in day_txns.iterrows():
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
                            current_cash += qty # Assuming qty is amount
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
                
            return pd.Series(nav_history)
            
        return pd.Series()

    def get_indicators(self) -> dict[str, Any]:
        nav = self.calculate_nav_history()
        basic = indicators.calculate_basic_metrics(nav)
        
        # Advanced Risk Metrics
        if not nav.empty:
            returns = nav.pct_change().dropna()
            advanced_risk = indicators.calculate_risk_metrics(returns)
            basic.update(advanced_risk)
            
        # Allocation Metrics & Risk Decomposition
        # We need current weights.
        # For Snapshot: straightforward.
        # For Transaction: use current_holdings from the last step of calculation.
        # To avoid re-calculating everything, we might need to refactor calculate_nav_history to return holdings too,
        # or just re-calculate current holdings here quickly.
        
        current_holdings = {}
        if self.portfolio.type == PortfolioType.SNAPSHOT:
            positions = self.positions
            for _, row in positions.iterrows():
                current_holdings[row['symbol']] = row['quantity']
        elif self.portfolio.type == PortfolioType.TRANSACTION:
            # Quick replay to get current holdings
            txns = self.transactions
            for _, txn in txns.iterrows():
                sym = txn['symbol']
                qty = float(txn['quantity'])
                side = txn['side'].upper()
                if side == 'BUY':
                    current_holdings[sym] = current_holdings.get(sym, 0.0) + qty
                elif side == 'SELL':
                    current_holdings[sym] = current_holdings.get(sym, 0.0) - qty
        
        # Calculate current value for weights
        # We need current prices
        current_prices = {}
        price_history_df = pd.DataFrame()
        
        for sym, qty in current_holdings.items():
            if qty == 0: continue
            df = prices.get_price_history(sym)
            if not df.empty:
                current_prices[sym] = df['Close'].iloc[-1]
                # Collect history for Risk Decomposition
                if price_history_df.empty:
                    price_history_df = df[['Close']].rename(columns={'Close': sym})
                else:
                    price_history_df = price_history_df.join(df[['Close']].rename(columns={'Close': sym}), how='outer')
        
        total_value = sum(qty * current_prices.get(sym, 0) for sym, qty in current_holdings.items())
        
        weights = {}
        if total_value > 0:
            for sym, qty in current_holdings.items():
                if qty != 0:
                    val = qty * current_prices.get(sym, 0)
                    weights[sym] = val / total_value
                    
        allocation = indicators.calculate_allocation_metrics(weights)
        basic.update(allocation)
        
        # Risk Decomposition
        if not price_history_df.empty and len(weights) > 1:
            risk_decomp = indicators.calculate_risk_contribution(weights, price_history_df)
            basic["risk_decomposition"] = risk_decomp
            
        return basic
