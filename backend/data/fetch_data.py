"""
This module aims to fetch financial (exchange rate) data from Yahoo Finance.
"""
import time
import random
import requests
import pandas as pd
from datetime import datetime

def get_stealth_headers() -> dict:
    """
    Returns a dictionary containing HTTP headers that mimic a real browser request.

    These headers are designed to be stealthy and avoid detection by websites that
    block requests from known crawlers or bots.

    The headers are chosen randomly from a predefined list of user agents and other
    headers that are commonly found in real browser requests.

    This function is useful for web scraping and other applications where you need to
    make requests to a website without being blocked or detected.

    Returns:
        dict: A dictionary containing the HTTP headers.
    """
    user_agents = [
        ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
         '(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'),
        ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
         '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
        ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
         '(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0'),
        ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
         '(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'),
        ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
         '(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'),
        ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
         '(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0'),
    ]

    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
                  "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Charset': 'UTF-8,*;q=0.5',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'DNT': '1',
        'Pragma': 'no-cache',
        'X-Forwarded-For': (f"{random.randint(1,255)}.{random.randint(1,255)}."
                            f"{random.randint(1,255)}.{random.randint(1,255)}"),
        'X-Real-IP': (f"{random.randint(1,255)}.{random.randint(1,255)}."
                      f"{random.randint(1,255)}.{random.randint(1,255)}"),
        'X-Requested-With': 'XMLHttpRequest'
    }

    return headers

def get_historical_close(ticker: str, start_date: str = None, interval: str = '1d') -> pd.DataFrame | float | None:
    """
    Downloads price data for a given ticker.

    Parameters:
    ticker (str): The ticker symbol to retrieve data for.
    start_date (str): Optional start date in format 'YYYY-MM-DD'. If None, fetches last 24h only and returns float.
    interval (str): The time interval for the data. Defaults to '1d'.

    Returns:
    pd.DataFrame | float | None:
        - If start_date provided: DataFrame with columns [Open, High, Low, Close, Volume] and datetime index
        - If start_date is None: historical close price as float
        - None if error occurs
    """
    current_time: int = int(time.time())

    if start_date:
        period1 = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
    else:
        period1 = current_time - 86400

    url = (f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
           f"?period1={period1}&period2={current_time}&interval={interval}")
    try:
        response = requests.get(url, headers=get_stealth_headers(), timeout=30)
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code} for {ticker}")
            return None if not start_date else pd.DataFrame()

        data = response.json()
        result = data['chart']['result'][0]

        if start_date:
            timestamps = result['timestamp']
            quotes = result['indicators']['quote'][0]

            df = pd.DataFrame({
                'Open': quotes['open'],
                'High': quotes['high'],
                'Low': quotes['low'],
                'Close': quotes['close'],
                'Volume': quotes['volume']
            })

            df.index = pd.to_datetime(timestamps, unit='s')
            df.index = df.index.normalize()
            df.index.name = 'Date'
            df = df.dropna(subset=['Close'])

            return df
        else:
            close_prices = result['indicators']['quote'][0]['close']
            for price in reversed(close_prices):
                if price is not None:
                    return price
            return None

    except (requests.RequestException, KeyError, ValueError, TypeError) as e:
        print(f"Error: {e}")
        return None if not start_date else pd.DataFrame()

def get_latest_foreign_currency(currency_1: str, currency_2: str, interval: str = '1m') -> float | None:
    """
    Downloads the latest closing price for a given ticker.

    Parameters:
    ticker (str): The ticker symbol to retrieve the latest price for. Defaults to 'CADCNY=X'.
    interval (str): The time interval for the data. Defaults to '1m'.

    Returns:
    float | None: The latest closing price for the given ticker, or None if an error occurs.
    """
    ticker = f"{currency_1}{currency_2}=X"
    current_time: int = int(time.time())
    yesterday_time: int = current_time - 86400
    url = (f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
           f"?period1={yesterday_time}&period2={current_time}&interval={interval}")
    try:
        response = requests.get(url, headers=get_stealth_headers(), timeout=30)
        if response.status_code == 200:
            data = response.json()
            result = data['chart']['result'][0]
            close_prices = result['indicators']['quote'][0]['close']

            for price in reversed(close_prices):
                if price is not None:
                    return price
        return None
    except (requests.RequestException, KeyError, ValueError, TypeError) as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    SYMBOL = 'NVDA'
    historical_price = get_historical_close(SYMBOL)
    print(f"historical {SYMBOL} close price: {historical_price}")
