from fastapi import APIRouter, HTTPException
from typing import List
from app.models.portfolio import Portfolio
from app.core import prices, engine

router = APIRouter()

@router.post("/calculate/nav")
def calculate_nav(portfolio: Portfolio, data: List[dict]):
    """
    Calculate NAV history for a portfolio.
    Request body: {
        "portfolio": {...portfolio metadata...},
        "data": [...transactions or positions...]
    }
    """
    try:
        eng = engine.PortfolioEngine(portfolio, data)
        nav = eng.calculate_nav_history()
        return [{"date": d.strftime("%Y-%m-%d") if hasattr(d, 'strftime') else str(d)[:10], "value": v} for d, v in nav.items()]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculate/indicators")
def calculate_indicators(portfolio: Portfolio, data: List[dict]):
    """
    Calculate performance indicators for a portfolio.
    Request body: {
        "portfolio": {...portfolio metadata...},
        "data": [...transactions or positions...]
    }
    """
    try:
        eng = engine.PortfolioEngine(portfolio, data)
        return eng.get_indicators()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/prices/{symbol}/history")
def get_price_history(symbol: str):
    """Get historical prices for a symbol"""
    df = prices.get_price_history(symbol)
    if df.empty:
        prices.update_price_cache(symbol)
        df = prices.get_price_history(symbol)

    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

    return [{"date": d.strftime("%Y-%m-%d"), "value": v} for d, v in df['Close'].items()]

@router.post("/prices/update")
def update_price(symbol: str):
    """Update price cache for a symbol"""
    success = prices.update_price_cache(symbol)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to update price for {symbol}")
    return {"message": f"Price updated for {symbol}"}
