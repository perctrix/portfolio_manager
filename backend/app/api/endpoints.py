from fastapi import APIRouter, HTTPException, Request
from typing import List
import logging
import re
import threading
import json
import os
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
        result = {
            "nav": [{"date": d.strftime("%Y-%m-%d") if hasattr(d, 'strftime') else str(d)[:10], "value": v} for d, v in nav.items()],
            "cash": [{"date": d.strftime("%Y-%m-%d") if hasattr(d, 'strftime') else str(d)[:10], "value": v} for d, v in eng.cash_history.items()],
            "failed_tickers": eng.failed_tickers
        }
        if eng.suggested_initial_deposit > 0:
            result["suggested_initial_deposit"] = eng.suggested_initial_deposit
        return result
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


@router.post("/calculate/benchmark-comparison")
def portfolio_benchmark_comparison(portfolio: Portfolio, data: List[dict]):
    """
    Calculate portfolio performance relative to all available benchmark indices.

    Returns metrics for each benchmark:
    - beta: Systematic risk relative to benchmark
    - alpha: Excess return (annualized)
    - r_squared: Proportion of variance explained by benchmark
    - correlation: Correlation coefficient with benchmark
    - tracking_error: Standard deviation of excess returns
    - information_ratio: Excess return / tracking error

    Request body: {
        "portfolio": {...portfolio metadata...},
        "data": [...transactions or positions...]
    }
    """
    try:
        from app.core.benchmarks import get_benchmark_loader
        from app.core.indicators.aggregator import calculate_benchmark_comparison

        eng = engine.PortfolioEngine(portfolio, data)
        nav = eng.calculate_nav_history()

        if nav.empty:
            raise HTTPException(status_code=400, detail="Portfolio NAV is empty")

        portfolio_returns = nav.pct_change().dropna()

        benchmark_loader = get_benchmark_loader()
        start_date = nav.index[0]
        end_date = nav.index[-1]

        benchmark_returns = benchmark_loader.load_all_benchmark_returns(
            start_date=start_date,
            end_date=end_date
        )

        if not benchmark_returns:
            raise HTTPException(status_code=404, detail="No benchmark data available")

        comparison = calculate_benchmark_comparison(
            portfolio_returns,
            benchmark_returns,
            risk_free_rate=0.0
        )

        result = {}
        for symbol, metrics in comparison.items():
            benchmark_name = benchmark_loader.get_benchmark_name(symbol)
            result[symbol] = {
                "name": benchmark_name,
                "metrics": metrics
            }

        return {"benchmarks": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Benchmark comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

@router.get("/benchmarks/list")
def get_benchmarks():
    """
    Get list of available benchmark indices.

    Returns:
        List of benchmark configurations with symbol, name, region, category, description
    """
    try:
        benchmarks_file = os.path.join(
            os.path.dirname(__file__), '..', '..', 'data', 'benchmarks.json'
        )
        with open(benchmarks_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {"benchmarks": data.get("benchmarks", [])}
    except Exception as e:
        logger.error(f"Failed to load benchmarks: {e}")
        raise HTTPException(status_code=500, detail="Failed to load benchmarks")

@router.get("/benchmarks/{symbol}/history")
def get_benchmark_history(symbol: str):
    """
    Get historical price data for a benchmark index.
    Reuses existing price history mechanism.

    This is functionally identical to /prices/{symbol}/history but semantically separate.
    """
    try:
        benchmarks_file = os.path.join(
            os.path.dirname(__file__), '..', '..', 'data', 'benchmarks.json'
        )
        with open(benchmarks_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            valid_symbols = [b['symbol'] for b in data.get('benchmarks', [])]
            if symbol not in valid_symbols:
                raise HTTPException(status_code=400, detail=f"{symbol} is not a valid benchmark")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate benchmark: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate benchmark")

    df = prices.get_price_history(symbol)
    if df.empty:
        prices.update_price_cache(symbol)
        df = prices.get_price_history(symbol)

    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

    return [{"date": d.strftime("%Y-%m-%d"), "value": v} for d, v in df['Close'].items()]


@router.get("/scheduler/status")
def get_scheduler_status():
    """Get benchmark scheduler status and next run times

    Note: The scheduler.get_status_info() method should return the running status and next run times atomically.
    """
    from app.core.scheduler import get_scheduler

    try:
        scheduler = get_scheduler()
        # get_status_info() should return a dict like:
        # {"is_running": bool, "next_runs": [...], "update_times": [...]}
        status_info = scheduler.get_status_info()
        return {
            "status": "running" if status_info.get("is_running") else "stopped",
            "next_scheduled_updates": status_info.get("next_runs", []),
            "update_times": status_info.get("update_times", [])
        }

    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/update-now")
def trigger_benchmark_update():
    """Manually trigger benchmark data update"""
    from app.core.scheduler import get_scheduler

    try:
        scheduler = get_scheduler()
        scheduler.scheduler.add_job(
            scheduler.update_all_benchmarks,
            'date',
            run_date=datetime.now(),
            id=f'manual_update_{datetime.now().timestamp()}'
        )

        return {
            "status": "success",
            "message": "Benchmark update scheduled successfully"
        }

    except Exception as e:
        logger.error(f"Failed to trigger benchmark update: {e}")
        raise HTTPException(status_code=500, detail=str(e))
