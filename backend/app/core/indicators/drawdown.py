import pandas as pd
import numpy as np
from typing import Dict

def calculate_drawdown_series(nav: pd.Series) -> pd.Series:
    """Calculate daily drawdown series from NAV"""
    if nav.empty:
        return pd.Series()

    running_max = nav.expanding().max()
    drawdown = (nav - running_max) / running_max
    return drawdown

def calculate_max_drawdown(nav: pd.Series) -> float:
    """Calculate maximum drawdown"""
    if nav.empty:
        return 0.0

    drawdown = calculate_drawdown_series(nav)
    return float(drawdown.min())

def calculate_drawdown_duration(nav: pd.Series) -> Dict[str, float]:
    """Calculate drawdown duration metrics"""
    if nav.empty:
        return {}

    running_max = nav.expanding().max()
    drawdown = (nav - running_max) / running_max

    in_drawdown = drawdown < 0
    drawdown_periods = []
    current_duration = 0
    max_duration = 0
    max_dd_duration = 0
    max_dd_value = 0

    for i, is_dd in enumerate(in_drawdown):
        if is_dd:
            current_duration += 1
            max_duration = max(max_duration, current_duration)

            if drawdown.iloc[i] < max_dd_value:
                max_dd_value = drawdown.iloc[i]
                max_dd_duration = current_duration
        else:
            if current_duration > 0:
                drawdown_periods.append(current_duration)
            current_duration = 0

    if current_duration > 0:
        drawdown_periods.append(current_duration)

    return {
        'max_drawdown_duration': float(max_dd_duration),
        'longest_drawdown_period': float(max_duration),
        'avg_drawdown_duration': float(np.mean(drawdown_periods)) if drawdown_periods else 0.0
    }

def calculate_avg_drawdown(nav: pd.Series) -> float:
    """Calculate average drawdown depth"""
    if nav.empty:
        return 0.0

    drawdown = calculate_drawdown_series(nav)
    drawdown_values = drawdown[drawdown < 0]

    if drawdown_values.empty:
        return 0.0

    return float(drawdown_values.mean())

def calculate_recovery_time(nav: pd.Series) -> Dict[str, float]:
    """Calculate recovery time from trough to previous peak"""
    if nav.empty or len(nav) < 2:
        return {}

    running_max = nav.expanding().max()
    drawdown = (nav - running_max) / running_max

    trough_idx = drawdown.idxmin()
    trough_value = drawdown.min()

    if trough_value == 0:
        return {'recovery_days': 0.0}

    recovery_nav = nav[nav.index > trough_idx]
    peak_value = running_max[trough_idx]

    recovery_idx = None
    for idx, value in recovery_nav.items():
        if value >= peak_value:
            recovery_idx = idx
            break

    if recovery_idx is None:
        return {
            'recovery_days': float('inf'),
            'recovered': False
        }

    recovery_days = (recovery_idx - trough_idx).days

    return {
        'recovery_days': float(recovery_days),
        'recovered': True
    }

def calculate_max_daily_loss(returns: pd.Series) -> float:
    """Calculate maximum single-day loss"""
    if returns.empty:
        return 0.0
    return float(returns.min())

def calculate_max_daily_gain(returns: pd.Series) -> float:
    """Calculate maximum single-day gain"""
    if returns.empty:
        return 0.0
    return float(returns.max())

def calculate_consecutive_loss_days(returns: pd.Series) -> int:
    """Calculate maximum consecutive losing days"""
    if returns.empty:
        return 0

    is_loss = returns < 0
    consecutive = 0
    max_consecutive = 0

    for loss in is_loss:
        if loss:
            consecutive += 1
            max_consecutive = max(max_consecutive, consecutive)
        else:
            consecutive = 0

    return int(max_consecutive)

def calculate_consecutive_gain_days(returns: pd.Series) -> int:
    """Calculate maximum consecutive gaining days"""
    if returns.empty:
        return 0

    is_gain = returns > 0
    consecutive = 0
    max_consecutive = 0

    for gain in is_gain:
        if gain:
            consecutive += 1
            max_consecutive = max(max_consecutive, consecutive)
        else:
            consecutive = 0

    return int(max_consecutive)
