import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional

def calculate_simple_returns(prices: pd.Series) -> pd.Series:
    """Calculate daily simple returns: r_t = P_t / P_{t-1} - 1"""
    return prices.pct_change()

def calculate_log_returns(prices: pd.Series) -> pd.Series:
    """Calculate daily log returns: ln(P_t / P_{t-1})"""
    return np.log(prices / prices.shift(1))

def calculate_cumulative_returns(returns: pd.Series) -> pd.Series:
    """Calculate cumulative returns"""
    return (1 + returns).cumprod() - 1

def calculate_annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Calculate annualized return from daily returns"""
    if returns.empty:
        return 0.0
    mean_return = returns.mean()
    return float(mean_return * periods_per_year)

def calculate_cagr(nav: pd.Series) -> float:
    """Calculate Compound Annual Growth Rate"""
    if nav.empty or len(nav) < 2:
        return 0.0

    days = (nav.index[-1] - nav.index[0]).days
    if days <= 0:
        return 0.0

    total_return = nav.iloc[-1] / nav.iloc[0]
    years = days / 365.0
    cagr = (total_return ** (1.0 / years)) - 1.0

    return float(cagr)

def calculate_monthly_returns(returns: pd.Series) -> pd.Series:
    """Aggregate daily returns to monthly returns"""
    if returns.empty:
        return pd.Series()

    monthly = (1 + returns).resample('M').prod() - 1
    return monthly

def calculate_yearly_returns(returns: pd.Series) -> pd.Series:
    """Aggregate daily returns to yearly returns"""
    if returns.empty:
        return pd.Series()

    yearly = (1 + returns).resample('Y').prod() - 1
    return yearly

def calculate_ytd_return(nav: pd.Series) -> float:
    """Calculate Year-To-Date return"""
    if nav.empty:
        return 0.0

    current_year = nav.index[-1].year
    ytd_nav = nav[nav.index.year == current_year]

    if len(ytd_nav) < 2:
        return 0.0

    return float(ytd_nav.iloc[-1] / ytd_nav.iloc[0] - 1)

def calculate_mtd_return(nav: pd.Series) -> float:
    """Calculate Month-To-Date return"""
    if nav.empty:
        return 0.0

    current_year = nav.index[-1].year
    current_month = nav.index[-1].month
    mtd_nav = nav[(nav.index.year == current_year) & (nav.index.month == current_month)]

    if len(mtd_nav) < 2:
        return 0.0

    return float(mtd_nav.iloc[-1] / mtd_nav.iloc[0] - 1)

def calculate_rolling_return(returns: pd.Series, window: int) -> pd.Series:
    """Calculate N-day rolling returns"""
    return (1 + returns).rolling(window=window).apply(lambda x: x.prod() - 1, raw=True)

def calculate_realized_pnl(transactions: pd.DataFrame) -> float:
    """Calculate realized P&L from completed trades"""
    if transactions is None or transactions.empty:
        return 0.0

    realized = 0.0
    positions = {}

    for _, txn in transactions.iterrows():
        symbol = txn['symbol']
        side = txn['side'].upper()
        qty = float(txn['quantity'])
        price = float(txn['price'])
        fee = float(txn['fee']) if not pd.isna(txn['fee']) else 0.0

        if side == 'BUY':
            if symbol not in positions:
                positions[symbol] = []
            positions[symbol].append({'qty': qty, 'price': price, 'fee': fee})
        elif side == 'SELL':
            if symbol in positions and positions[symbol]:
                remaining_qty = qty
                while remaining_qty > 0 and positions[symbol]:
                    buy_position = positions[symbol][0]
                    sell_qty = min(remaining_qty, buy_position['qty'])

                    pnl = sell_qty * (price - buy_position['price']) - fee * (sell_qty / qty)
                    realized += pnl

                    buy_position['qty'] -= sell_qty
                    remaining_qty -= sell_qty

                    if buy_position['qty'] <= 0:
                        positions[symbol].pop(0)

    return float(realized)

def calculate_unrealized_pnl(holdings: Dict[str, float], prices: Dict[str, float]) -> float:
    """Calculate unrealized P&L from current holdings

    Args:
        holdings: Dict of {symbol: quantity}
        prices: Dict of {symbol: current_price}
    """
    if not holdings or not prices:
        return 0.0

    unrealized = 0.0
    for symbol, qty in holdings.items():
        if symbol in prices and qty != 0:
            unrealized += qty * prices[symbol]

    return float(unrealized)

def calculate_total_pnl(realized: float, unrealized: float) -> float:
    """Calculate total P&L = realized + unrealized"""
    return float(realized + unrealized)

def calculate_trade_pnl(transactions: pd.DataFrame) -> pd.DataFrame:
    """Calculate P&L for each trade"""
    if transactions is None or transactions.empty:
        return pd.DataFrame()

    trades = []
    positions = {}

    for _, txn in transactions.iterrows():
        symbol = txn['symbol']
        side = txn['side'].upper()
        qty = float(txn['quantity'])
        price = float(txn['price'])
        fee = float(txn['fee']) if not pd.isna(txn['fee']) else 0.0
        datetime = txn['datetime']

        if side == 'BUY':
            if symbol not in positions:
                positions[symbol] = []
            positions[symbol].append({
                'buy_date': datetime,
                'qty': qty,
                'buy_price': price,
                'buy_fee': fee
            })
        elif side == 'SELL':
            if symbol in positions and positions[symbol]:
                remaining_qty = qty
                while remaining_qty > 0 and positions[symbol]:
                    buy_position = positions[symbol][0]
                    sell_qty = min(remaining_qty, buy_position['qty'])

                    pnl = sell_qty * (price - buy_position['buy_price']) - \
                          (buy_position['buy_fee'] * sell_qty / buy_position['qty']) - \
                          (fee * sell_qty / qty)

                    trades.append({
                        'symbol': symbol,
                        'buy_date': buy_position['buy_date'],
                        'sell_date': datetime,
                        'quantity': sell_qty,
                        'buy_price': buy_position['buy_price'],
                        'sell_price': price,
                        'pnl': pnl,
                        'return_pct': (price / buy_position['buy_price']) - 1
                    })

                    buy_position['qty'] -= sell_qty
                    remaining_qty -= sell_qty

                    if buy_position['qty'] <= 0:
                        positions[symbol].pop(0)

    return pd.DataFrame(trades)

def calculate_twr(nav: pd.Series, cashflows: Optional[pd.DataFrame] = None) -> float:
    """Calculate Time-Weighted Return

    Args:
        nav: NAV time series
        cashflows: DataFrame with 'date' and 'amount' columns for deposits/withdrawals
    """
    if nav.empty:
        return 0.0

    if cashflows is None or cashflows.empty:
        return calculate_cagr(nav)

    periods = []
    cashflows = cashflows.sort_values('date')

    start_nav = nav.iloc[0]
    start_date = nav.index[0]

    for _, cf in cashflows.iterrows():
        cf_date = pd.to_datetime(cf['date'])
        if cf_date <= start_date or cf_date > nav.index[-1]:
            continue

        end_nav = nav[nav.index <= cf_date].iloc[-1]
        period_return = (end_nav / start_nav) - 1
        periods.append(1 + period_return)

        start_nav = end_nav + cf['amount']
        start_date = cf_date

    end_nav = nav.iloc[-1]
    period_return = (end_nav / start_nav) - 1
    periods.append(1 + period_return)

    twr = np.prod(periods) - 1
    return float(twr)

def calculate_irr(cashflows: pd.DataFrame) -> float:
    """Calculate Internal Rate of Return (IRR)

    Args:
        cashflows: DataFrame with 'date' and 'amount' columns
    """
    if cashflows is None or cashflows.empty:
        return 0.0

    try:
        import numpy_financial as npf

        cashflows = cashflows.sort_values('date').copy()
        amounts = cashflows['amount'].values

        return float(npf.irr(amounts))
    except ImportError:
        return 0.0
    except Exception:
        return 0.0
