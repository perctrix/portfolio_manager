import os

DATA_DIR = "data"
PRICES_DIR = os.path.join(DATA_DIR, "prices")
TICKERS_DIR = os.path.join(DATA_DIR, "tickers")
FRONTEND_DATA_DIR = os.path.join("..", "..", "frontend", "public", "data")

os.makedirs(PRICES_DIR, exist_ok=True)
os.makedirs(TICKERS_DIR, exist_ok=True)

