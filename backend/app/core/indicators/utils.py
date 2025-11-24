import pandas as pd
import numpy as np

def rolling_normalize(series: pd.Series, window: int = 21) -> pd.Series:
    """Apply rolling window normalization to a time series"""
    rolling_mean = series.rolling(window=window, min_periods=1).mean()
    rolling_std = series.rolling(window=window, min_periods=1).std()
    eps = 1e-8
    normalized = (series - rolling_mean) / (rolling_std + eps)
    normalized = normalized.ffill().bfill()
    return normalized
