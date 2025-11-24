from fastapi import APIRouter, HTTPException
from typing import List
import csv
import os
import uuid
from datetime import datetime
from app.models.portfolio import Portfolio, PortfolioType
from app.core import storage, prices, engine
router = APIRouter()

@router.get("/portfolios", response_model=List[Portfolio])
def list_portfolios():
    return storage.get_all_portfolios()

@router.post("/portfolios", response_model=Portfolio)
def create_portfolio(name: str, type: PortfolioType, base_currency: str = "USD"):
    portfolio_id = f"p_{str(uuid.uuid4())[:8]}"
    new_portfolio = Portfolio(
        id=portfolio_id,
        name=name,
        type=type,
        base_currency=base_currency,
        created_at=datetime.now()
    )
    try:
        return storage.create_portfolio(new_portfolio)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/portfolios/{portfolio_id}", response_model=Portfolio)
def get_portfolio(portfolio_id: str):
    portfolio = storage.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio

@router.post("/prices/update")
def update_price(symbol: str):
    success = prices.update_price_cache(symbol)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to update price for {symbol}")
    return {"message": f"Price updated for {symbol}"}

@router.get("/portfolios/{portfolio_id}/nav")
def get_portfolio_nav(portfolio_id: str):
    try:
        eng = engine.PortfolioEngine(portfolio_id)
        nav = eng.calculate_nav_history()
        # Convert to list of {date, value} for frontend - ensure consistent date format
        return [{"date": d.strftime("%Y-%m-%d") if hasattr(d, 'strftime') else str(d)[:10], "value": v} for d, v in nav.items()]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/portfolios/{portfolio_id}/indicators")
def get_portfolio_indicators(portfolio_id: str):
    try:
        eng = engine.PortfolioEngine(portfolio_id)
        return eng.get_indicators()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/portfolios/{portfolio_id}/transactions")
def add_transaction(portfolio_id: str, transaction: dict):
    """
    Add a transaction to the portfolio.
    Expected dict: {datetime, symbol, side, quantity, price, fee, currency, account, note}
    """
    portfolio = storage.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.type != PortfolioType.TRANSACTION:
        raise HTTPException(status_code=400, detail="Portfolio is not Transaction type")
        
    # Validate fields
    required = ["datetime", "symbol", "side", "quantity", "price"]
    for field in required:
        if field not in transaction:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")
            
    # Default optional fields
    transaction.setdefault("fee", 0)
    transaction.setdefault("currency", portfolio.base_currency)
    transaction.setdefault("account", "default")
    transaction.setdefault("note", "")
    
    fieldnames = ["datetime", "symbol", "side", "quantity", "price", "fee", "currency", "account", "note"]
    storage.save_portfolio_data(portfolio_id, fieldnames, [transaction], append=True)
    
    # Trigger price update for the new symbol
    prices.update_price_cache(transaction["symbol"])
    
    return {"message": "Transaction added"}

@router.post("/portfolios/{portfolio_id}/positions")
def update_positions(portfolio_id: str, positions: List[dict]):
    """
    Update snapshot positions (Replace all).
    Expected list of dicts: {as_of, symbol, quantity, cost_basis, currency, note}
    """
    portfolio = storage.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.type != PortfolioType.SNAPSHOT:
        raise HTTPException(status_code=400, detail="Portfolio is not Snapshot type")
        
    if not positions:
        # Clear positions? Allow empty list.
        pass
        
    # Validate fields
    required = ["as_of", "symbol", "quantity", "cost_basis"]
    for pos in positions:
        for field in required:
            if field not in pos:
                raise HTTPException(status_code=400, detail=f"Missing field: {field} in position {pos}")
        pos.setdefault("currency", portfolio.base_currency)
        pos.setdefault("note", "")
        
    fieldnames = ["as_of", "symbol", "quantity", "cost_basis", "currency", "note"]
    storage.save_portfolio_data(portfolio_id, fieldnames, positions, append=False)
    
    # Trigger price updates
    for pos in positions:
        prices.update_price_cache(pos["symbol"])
        
    return {"message": "Positions updated"}

@router.get("/portfolios/{portfolio_id}/data")
def get_portfolio_data(portfolio_id: str):
    """Get raw CSV data (transactions or positions)"""
    portfolio = storage.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    csv_path = f"data/portfolios/{portfolio_id}.csv"
    if not os.path.exists(csv_path):
        return []
        
    import csv
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)


@router.get("/prices/{symbol}/history")
def get_price_history(symbol: str):
    """Get historical prices for a symbol"""
    df = prices.get_price_history(symbol)
    if df.empty:
        # Try to fetch if not in cache
        prices.update_price_cache(symbol)
        df = prices.get_price_history(symbol)
        
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
    # Return list of {date, value}
    return [{"date": d.strftime("%Y-%m-%d"), "value": v} for d, v in df['Close'].items()]

@router.get("/portfolios/{portfolio_id}/export")
def export_portfolio(portfolio_id: str):
    """Export portfolio as JSON (meta + data)"""
    if not storage.validate_portfolio_id(portfolio_id):
        raise HTTPException(status_code=400, detail="Invalid portfolio ID")

    portfolio = storage.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Get data
    csv_path = os.path.join(storage.PORTFOLIOS_DIR, f"{portfolio_id}.csv")
    data = []
    if os.path.exists(csv_path):
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            data = list(reader)

    export_data = {
        "meta": portfolio.dict(),
        "data": data
    }
    return export_data

@router.post("/portfolios/import", response_model=Portfolio)
def import_portfolio(data: dict):
    """Import portfolio from JSON"""
    try:
        meta = data.get("meta")
        rows = data.get("data")

        if not meta or rows is None:
            raise HTTPException(status_code=400, detail="Invalid import format")

        # Create Portfolio object
        # Keep the ID for restore functionality
        # If user imports same file twice, it will error
        p = Portfolio(**meta)
        try:
            storage.create_portfolio(p)
        except ValueError:
            # Portfolio already exists
            raise HTTPException(status_code=400, detail="Portfolio already exists. Delete it first to re-import.")

        # Save data
        if rows:
            # Determine fieldnames based on type
            if p.type == PortfolioType.TRANSACTION:
                fieldnames = ["datetime", "symbol", "side", "quantity", "price", "fee", "currency", "account", "note"]
            else:
                fieldnames = ["as_of", "symbol", "quantity", "cost_basis", "currency", "note"]

            storage.save_portfolio_data(p.id, fieldnames, rows, append=False)

            # Trigger price updates
            for row in rows:
                if "symbol" in row:
                    prices.update_price_cache(row["symbol"])

        return p

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/portfolios/{portfolio_id}")
def delete_portfolio(portfolio_id: str):
    """Delete portfolio"""
    success = storage.delete_portfolio(portfolio_id)
    if not success:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return {"message": "Portfolio deleted"}
