import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
PRICES_DIR = os.path.join(DATA_DIR, "prices")
TICKERS_DIR = os.path.join(DATA_DIR, "tickers")
FRONTEND_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "public", "data"))

os.makedirs(PRICES_DIR, exist_ok=True)
os.makedirs(TICKERS_DIR, exist_ok=True)

