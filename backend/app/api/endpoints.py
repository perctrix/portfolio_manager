from fastapi import APIRouter, HTTPException, Request
from typing import List
import logging
import re
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from pydantic import BaseModel
from app.models.portfolio import Portfolio
from app.core import prices, engine, ticker_validator

router = APIRouter()
logger = logging.getLogger(__name__)

# Simple in-memory rate limiting (per IP)
# In production, consider using Redis or a proper rate limiting library
rate_limit_store = defaultdict(list)
rate_limit_lock = threading.Lock()
RATE_LIMIT_REQUESTS = 10  # Max requests
RATE_LIMIT_WINDOW = 60  # Per 60 seconds


def check_rate_limit(client_ip: str) -> bool:
    """
    Check if client has exceeded rate limit.
    Returns True if within limits, False if exceeded.
    Thread-safe implementation.
    """
    with rate_limit_lock:
        now = datetime.now()
        cutoff = now - timedelta(seconds=RATE_LIMIT_WINDOW)
        
        # Clean old entries
        rate_limit_store[client_ip] = [
            timestamp for timestamp in rate_limit_store[client_ip]
            if timestamp > cutoff
        ]
        
        # Check if exceeded
        if len(rate_limit_store[client_ip]) >= RATE_LIMIT_REQUESTS:
            return False
        
        # Add current request
        rate_limit_store[client_ip].append(now)
        return True


class TickerValidateRequest(BaseModel):
    symbol: str

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
        return {
            "nav": [{"date": d.strftime("%Y-%m-%d") if hasattr(d, 'strftime') else str(d)[:10], "value": v} for d, v in nav.items()],
            "failed_tickers": eng.failed_tickers
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculate/indicators")
def calculate_indicators(portfolio: Portfolio, data: List[dict]):
    """
    Calculate performance indicators for a portfolio (legacy endpoint).

    This endpoint maintains backward compatibility with existing clients.
    For new implementations, use /calculate/indicators/all or /calculate/indicators/basic.
    """
    try:
        eng = engine.PortfolioEngine(portfolio, data)
        return eng.get_indicators()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculate/indicators/all")
def calculate_all_indicators(portfolio: Portfolio, data: List[dict]):
    """
    Calculate all performance indicators for a portfolio (approximately 79 indicators).

    Returns indicators organized by category:
    - returns: total_return, cagr, ytd, mtd, realized_pnl, etc.
    - risk: volatility, upside/downside volatility, semivariance
    - drawdown: max_drawdown, avg_drawdown, recovery_time, consecutive days
    - risk_adjusted_ratios: sharpe, sortino, calmar
    - tail_risk: VaR, CVaR, skewness, kurtosis
    - allocation: weights, HHI, concentration, sector allocation
    - risk_decomposition: MCTR, risk contribution by asset/sector
    - trading: (Transaction mode only) win_rate, turnover, profit_loss_ratio, etc.

    Request body: {
        "portfolio": {...portfolio metadata...},
        "data": [...transactions or positions...]
    }
    """
    try:
        eng = engine.PortfolioEngine(portfolio, data)
        return eng.get_all_indicators()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculate/indicators/basic")
def calculate_basic_indicators(portfolio: Portfolio, data: List[dict]):
    """
    Calculate 5 basic performance indicators for a portfolio (fast query).

    Returns:
    - total_return: Total return since inception
    - cagr: Compound Annual Growth Rate
    - volatility: Annualized volatility
    - sharpe: Sharpe ratio
    - max_drawdown: Maximum drawdown

    Request body: {
        "portfolio": {...portfolio metadata...},
        "data": [...transactions or positions...]
    }
    """
    try:
        eng = engine.PortfolioEngine(portfolio, data)
        return eng.get_basic_indicators()
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

@router.post("/tickers/validate")
def validate_ticker(request: TickerValidateRequest, req: Request):
    """
    Validate if a ticker exists via Yahoo Finance.
    If valid, adds it to dynamic.json for future use.
    Rate limited to prevent abuse.
    """
    # Get client IP for rate limiting
    client_ip = req.client.host if req.client else "unknown"
    
    # Check rate limit
    if not check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    symbol = request.symbol.upper().strip()

    # Validate symbol format
    if not symbol:
        logger.warning(f"Empty symbol submitted from IP: {client_ip}")
        raise HTTPException(status_code=400, detail="Symbol cannot be empty")
    
    # Check for whitespace
    if symbol != symbol.strip() or ' ' in symbol:
        logger.warning(f"Symbol with whitespace submitted: '{request.symbol}' from IP: {client_ip}")
        raise HTTPException(status_code=400, detail="Symbol cannot contain whitespace")
    
    # Validate allowed characters (alphanumeric, dots, hyphens, carets, equals, underscores)
    if not re.match(r'^[A-Z0-9.\-^=_]+$', symbol):
        logger.warning(f"Invalid symbol format submitted: '{symbol}' from IP: {client_ip}")
        raise HTTPException(
            status_code=400,
            detail="Symbol contains invalid characters. Only alphanumeric, dots, hyphens, carets, equals, and underscores are allowed."
        )
    
    # Check maximum length
    if len(symbol) > 20:
        logger.warning(f"Symbol too long submitted: '{symbol}' from IP: {client_ip}")
        raise HTTPException(status_code=400, detail="Symbol is too long (max 20 characters)")

    logger.info(f"Validating ticker: {symbol} from IP: {client_ip}")
    valid, info = ticker_validator.validate_ticker_via_yahoo(symbol)

    if valid:
        logger.info(f"Ticker {symbol} validated successfully: {info}")
        ticker_validator.add_to_dynamic_list(symbol, info)
        return {"valid": True, "info": info}
    else:
        logger.info(f"Ticker {symbol} validation failed")
        return {"valid": False, "info": None, "message": f"Ticker '{symbol}' not found"}
