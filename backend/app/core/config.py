import os


class Config:
    """Centralized configuration management with environment variable support"""

    STOCK_CACHE_TTL_HOURS: float = float(os.environ.get("STOCK_CACHE_TTL_HOURS", "6"))
    FILE_LOCK_TIMEOUT: int = int(os.environ.get("FILE_LOCK_TIMEOUT", "10"))
    DEFAULT_START_DATE: str = os.environ.get("DEFAULT_START_DATE", "2020-01-01")
    DEFAULT_INTERVAL: str = os.environ.get("DEFAULT_INTERVAL", "1d")
    YAHOO_API_URL: str = os.environ.get(
        "YAHOO_API_URL",
        "https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?period1={period1}&period2={period2}&interval={interval}"
    )


config = Config()
