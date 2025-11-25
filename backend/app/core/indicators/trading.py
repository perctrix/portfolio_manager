import pandas as pd
import numpy as np
from typing import Dict
from .returns import calculate_trade_pnl

def calculate_trade_count(transactions: pd.DataFrame) -> int:
    """Calculate total number of trades"""
    if transactions is None or transactions.empty:
        return 0

    buy_count = len(transactions[transactions['side'].str.upper() == 'BUY'])
    sell_count = len(transactions[transactions['side'].str.upper() == 'SELL'])

    return int(min(buy_count, sell_count))

def calculate_turnover_rate(transactions: pd.DataFrame, nav_history: pd.Series) -> float:
    """Calculate annualized turnover rate = trading_volume / average_nav"""
    if transactions is None or transactions.empty or nav_history.empty:
        return 0.0

    trade_txns = transactions[transactions['side'].str.upper().isin(['BUY', 'SELL'])]

    if trade_txns.empty:
        return 0.0

    trading_volume = 0.0
    for _, txn in trade_txns.iterrows():
        qty = float(txn['quantity'])
        price = float(txn['price'])
        trading_volume += abs(qty * price)

    avg_nav = nav_history.mean()

    if avg_nav == 0:
        return 0.0

    days = (nav_history.index[-1] - nav_history.index[0]).days
    if days <= 0:
        return 0.0

    annual_factor = 365.0 / days
    turnover = (trading_volume / avg_nav) * annual_factor

    return float(turnover)

def calculate_avg_holding_period(transactions: pd.DataFrame) -> float:
    """Calculate average holding period in days"""
    trades_df = calculate_trade_pnl(transactions)

    if trades_df.empty:
        return 0.0

    holding_periods = []
    for _, trade in trades_df.iterrows():
        buy_date = pd.to_datetime(trade['buy_date'])
        sell_date = pd.to_datetime(trade['sell_date'])
        days = (sell_date - buy_date).days
        holding_periods.append(days)

    return float(np.mean(holding_periods)) if holding_periods else 0.0

def calculate_win_rate(transactions: pd.DataFrame) -> float:
    """Calculate win rate = winning_trades / total_trades"""
    trades_df = calculate_trade_pnl(transactions)

    if trades_df.empty:
        return 0.0

    total_trades = len(trades_df)
    winning_trades = len(trades_df[trades_df['pnl'] > 0])

    return float(winning_trades / total_trades)

def calculate_profit_loss_ratio(transactions: pd.DataFrame) -> float:
    """Calculate profit/loss ratio = avg_win / abs(avg_loss)"""
    trades_df = calculate_trade_pnl(transactions)

    if trades_df.empty:
        return 0.0

    winning_trades = trades_df[trades_df['pnl'] > 0]
    losing_trades = trades_df[trades_df['pnl'] < 0]

    if winning_trades.empty or losing_trades.empty:
        return 0.0

    avg_win = winning_trades['pnl'].mean()
    avg_loss = abs(losing_trades['pnl'].mean())

    if avg_loss == 0:
        return 0.0

    return float(avg_win / avg_loss)

def calculate_max_trade_profit(transactions: pd.DataFrame) -> float:
    """Calculate maximum single trade profit"""
    trades_df = calculate_trade_pnl(transactions)

    if trades_df.empty:
        return 0.0

    return float(trades_df['pnl'].max())

def calculate_max_trade_loss(transactions: pd.DataFrame) -> float:
    """Calculate maximum single trade loss"""
    trades_df = calculate_trade_pnl(transactions)

    if trades_df.empty:
        return 0.0

    return float(trades_df['pnl'].min())

def calculate_consecutive_winning_trades(transactions: pd.DataFrame) -> int:
    """Calculate maximum consecutive winning trades"""
    trades_df = calculate_trade_pnl(transactions)

    if trades_df.empty:
        return 0

    is_win = trades_df['pnl'] > 0
    consecutive = 0
    max_consecutive = 0

    for win in is_win:
        if win:
            consecutive += 1
            max_consecutive = max(max_consecutive, consecutive)
        else:
            consecutive = 0

    return int(max_consecutive)

def calculate_consecutive_losing_trades(transactions: pd.DataFrame) -> int:
    """Calculate maximum consecutive losing trades"""
    trades_df = calculate_trade_pnl(transactions)

    if trades_df.empty:
        return 0

    is_loss = trades_df['pnl'] < 0
    consecutive = 0
    max_consecutive = 0

    for loss in is_loss:
        if loss:
            consecutive += 1
            max_consecutive = max(max_consecutive, consecutive)
        else:
            consecutive = 0

    return int(max_consecutive)

def calculate_all_trading_metrics(transactions: pd.DataFrame, nav_history: pd.Series) -> Dict[str, float]:
    """Calculate all trading behavior metrics at once"""
    if transactions is None or transactions.empty:
        return {
            'trade_count': 0,
            'turnover_rate': 0.0,
            'avg_holding_period': 0.0,
            'win_rate': 0.0,
            'profit_loss_ratio': 0.0,
            'max_trade_profit': 0.0,
            'max_trade_loss': 0.0,
            'consecutive_winning_trades': 0,
            'consecutive_losing_trades': 0
        }

    return {
        'trade_count': calculate_trade_count(transactions),
        'turnover_rate': calculate_turnover_rate(transactions, nav_history),
        'avg_holding_period': calculate_avg_holding_period(transactions),
        'win_rate': calculate_win_rate(transactions),
        'profit_loss_ratio': calculate_profit_loss_ratio(transactions),
        'max_trade_profit': calculate_max_trade_profit(transactions),
        'max_trade_loss': calculate_max_trade_loss(transactions),
        'consecutive_winning_trades': calculate_consecutive_winning_trades(transactions),
        'consecutive_losing_trades': calculate_consecutive_losing_trades(transactions)
    }
