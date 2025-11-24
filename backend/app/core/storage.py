import os

DATA_DIR = "data"
PRICES_DIR = os.path.join(DATA_DIR, "prices")

os.makedirs(PRICES_DIR, exist_ok=True)

