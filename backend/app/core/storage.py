import json
import csv
import os
import re
from typing import Optional
from app.models.portfolio import Portfolio
from datetime import datetime

DATA_DIR = "data"
META_DIR = os.path.join(DATA_DIR, "meta")
PORTFOLIOS_DIR = os.path.join(DATA_DIR, "portfolios")
PRICES_DIR = os.path.join(DATA_DIR, "prices")

# Ensure directories exist
os.makedirs(META_DIR, exist_ok=True)
os.makedirs(PORTFOLIOS_DIR, exist_ok=True)
os.makedirs(PRICES_DIR, exist_ok=True)

PORTFOLIOS_FILE = os.path.join(META_DIR, "portfolios.json")

def validate_portfolio_id(portfolio_id: str) -> bool:
    """
    Validate portfolio ID to prevent path injection attacks.
    Format: p_ followed by 8 hexadecimal characters (from UUID).
    Example: p_a1b2c3d4
    """
    if not portfolio_id:
        return False
    return bool(re.match(r'^p_[a-f0-9]{8}$', portfolio_id))

def _load_portfolios_meta() -> list[dict]:
    if not os.path.exists(PORTFOLIOS_FILE):
        return []
    with open(PORTFOLIOS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def _save_portfolios_meta(data: list[dict]) -> None:
    with open(PORTFOLIOS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

def get_all_portfolios() -> list[Portfolio]:
    data = _load_portfolios_meta()
    return [Portfolio(**item) for item in data]

def get_portfolio(portfolio_id: str) -> Optional[Portfolio]:
    portfolios = get_all_portfolios()
    for p in portfolios:
        if p.id == portfolio_id:
            return p
    return None

def create_portfolio(portfolio: Portfolio) -> Portfolio:
    portfolios = _load_portfolios_meta()
    # Check if exists
    if any(p['id'] == portfolio.id for p in portfolios):
        raise ValueError(f"Portfolio with ID {portfolio.id} already exists")
    
    portfolios.append(portfolio.dict())
    _save_portfolios_meta(portfolios)
    
    # Create the CSV file for the portfolio
    csv_path = os.path.join(PORTFOLIOS_DIR, f"{portfolio.id}.csv")
    if not os.path.exists(csv_path):
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            if portfolio.type == "transaction":
                writer.writerow(["datetime", "symbol", "side", "quantity", "price", "fee", "currency", "account", "note"])
            else:
                writer.writerow(["as_of", "symbol", "quantity", "cost_basis", "currency", "note"])
                
    return portfolio

def save_portfolio_data(portfolio_id: str, fieldnames: list[str], rows: list[dict], append: bool = False):
    """Save data to the portfolio's CSV file"""
    if not validate_portfolio_id(portfolio_id):
        raise ValueError(f"Invalid portfolio ID: {portfolio_id}")

    csv_path = os.path.join(PORTFOLIOS_DIR, f"{portfolio_id}.csv")
    mode = "a" if append else "w"

    # If appending and file doesn't exist, switch to write to include header
    if append and not os.path.exists(csv_path):
        mode = "w"

    with open(csv_path, mode, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if mode == "w":
            writer.writeheader()
        writer.writerows(rows)

def delete_portfolio(portfolio_id: str) -> bool:
    """Delete portfolio metadata and data file"""
    if not validate_portfolio_id(portfolio_id):
        return False

    portfolios = _load_portfolios_meta()

    # Filter out the portfolio
    new_portfolios = [p for p in portfolios if p['id'] != portfolio_id]

    if len(new_portfolios) == len(portfolios):
        return False  # Not found

    _save_portfolios_meta(new_portfolios)

    # Delete CSV
    csv_path = os.path.join(PORTFOLIOS_DIR, f"{portfolio_id}.csv")
    if os.path.exists(csv_path):
        os.remove(csv_path)

    return True

