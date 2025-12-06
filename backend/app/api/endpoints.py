from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Any, Dict, List, Tuple
import logging
import re
import threading
import json
import os
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from pydantic import BaseModel
from app.models.portfolio import (
    Portfolio, BondPosition, StaleTicker, StaleTickerHandling
)
from app.core import prices, engine, ticker_validator
from app.core.symbol_resolver import get_resolver, UnresolvedSymbol
from app.core.indicators.aggregator import calculate_markowitz_analysis

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


class MarkowitzRequest(BaseModel):
    allow_short_selling: bool = False
    risk_free_rate: float = 0.0
    num_frontier_points: int = 50


class PortfolioCalculateRequest(BaseModel):
    portfolio: Portfolio
    data: List[dict]
    bonds: List[BondPosition] = []

@router.post("/calculate/nav")
def calculate_nav(request: PortfolioCalculateRequest):
    """
    Calculate NAV history for a portfolio.
    Request body: {
        "portfolio": {...portfolio metadata...},
        "data": [...transactions or positions...],
        "bonds": [...bond positions (optional)...]
    }
    """
    try:
        eng = engine.PortfolioEngine(request.portfolio, request.data, request.bonds)
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
def calculate_indicators(request: PortfolioCalculateRequest):
    """
    Calculate performance indicators for a portfolio (legacy endpoint).

    This endpoint maintains backward compatibility with existing clients.
    For new implementations, use /calculate/indicators/all or /calculate/indicators/basic.
    """
    try:
        eng = engine.PortfolioEngine(request.portfolio, request.data, request.bonds)
        return eng.get_indicators()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculate/indicators/all")
def calculate_all_indicators(request: PortfolioCalculateRequest):
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
        "data": [...transactions or positions...],
        "bonds": [...bond positions (optional)...]
    }
    """
    try:
        eng = engine.PortfolioEngine(request.portfolio, request.data, request.bonds)
        return eng.get_all_indicators()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculate/indicators/basic")
def calculate_basic_indicators(request: PortfolioCalculateRequest):
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
        "data": [...transactions or positions...],
        "bonds": [...bond positions (optional)...]
    }
    """
    try:
        eng = engine.PortfolioEngine(request.portfolio, request.data, request.bonds)
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
def portfolio_benchmark_comparison(request: PortfolioCalculateRequest):
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
        "data": [...transactions or positions...],
        "bonds": [...bond positions (optional)...]
    }
    """
    try:
        from app.core.benchmarks import get_benchmark_loader
        from app.core.indicators.aggregator import calculate_benchmark_comparison

        eng = engine.PortfolioEngine(request.portfolio, request.data, request.bonds)
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


class MarkowitzCalculateRequest(BaseModel):
    portfolio: Portfolio
    data: List[dict]
    bonds: List[BondPosition] = []
    params: MarkowitzRequest = MarkowitzRequest()


@router.post("/calculate/markowitz")
def calculate_markowitz(request: MarkowitzCalculateRequest):
    """
    Calculate Markowitz Efficient Frontier analysis for a portfolio.

    Returns:
    - frontier_points: List of (return, volatility, sharpe, weights) on efficient frontier
    - gmv_portfolio: Global Minimum Variance portfolio
    - tangent_portfolio: Maximum Sharpe Ratio portfolio (if feasible)
    - current_portfolio: Current portfolio position
    - asset_stats: Per-asset expected return and volatility

    Request body: {
        "portfolio": {...portfolio metadata...},
        "data": [...transactions or positions...],
        "bonds": [...bond positions (optional)...],
        "params": {
            "allow_short_selling": false,
            "risk_free_rate": 0.0,
            "num_frontier_points": 50
        }
    }
    """
    try:
        eng = engine.PortfolioEngine(request.portfolio, request.data, request.bonds)
        base_data = eng._prepare_base_data()

        if base_data['price_history'].empty:
            raise HTTPException(status_code=400, detail="Insufficient price history")

        if len(base_data['weights']) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 assets required for efficient frontier analysis"
            )

        result = calculate_markowitz_analysis(
            price_history=base_data['price_history'],
            weights=base_data['weights'],
            risk_free_rate=request.params.risk_free_rate,
            allow_short_selling=request.params.allow_short_selling,
            num_frontier_points=request.params.num_frontier_points
        )

        if result is None:
            raise HTTPException(
                status_code=400,
                detail="Unable to calculate efficient frontier. Check if there is sufficient price history."
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Markowitz calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def load_prices_batch(symbols: List[str]) -> Dict[str, pd.DataFrame]:
    """Load multiple symbols' prices in parallel.

    Args:
        symbols: List of stock ticker symbols

    Returns:
        Dictionary mapping symbol -> price DataFrame
    """
    async def load_one(sym: str) -> Tuple[str, pd.DataFrame]:
        df = await asyncio.to_thread(prices.get_price_history, sym)
        return sym, df

    results = await asyncio.gather(*[load_one(sym) for sym in symbols])
    return {sym: df for sym, df in results if not df.empty}


async def load_benchmarks_batch(
    benchmark_loader: Any
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, pd.DataFrame]]:
    """Load benchmark prices in parallel.

    Args:
        benchmark_loader: BenchmarkLoader instance

    Returns:
        Tuple of:
        - formatted: Dict for frontend {symbol: {name, data: [{date, value}]}}
        - raw_cache: Dict for calculations {symbol: DataFrame}
    """
    benchmarks_list = benchmark_loader.get_available_benchmarks()[:5]

    async def load_one(bm: dict) -> Tuple[str, str, pd.DataFrame]:
        sym = bm['symbol']
        df = await asyncio.to_thread(prices.get_price_history, sym)
        return sym, bm['name'], df

    results = await asyncio.gather(*[load_one(bm) for bm in benchmarks_list])

    formatted: Dict[str, Dict[str, Any]] = {}
    raw_cache: Dict[str, pd.DataFrame] = {}

    for sym, name, df in results:
        if not df.empty:
            raw_cache[sym] = df
            formatted[sym] = {
                "name": name,
                "data": [
                    {"date": d.strftime("%Y-%m-%d"), "value": float(v)}
                    for d, v in df['Close'].items()
                ]
            }

    return formatted, raw_cache


class SymbolResolution(BaseModel):
    original: str
    resolved: str


class PortfolioFullRequest(BaseModel):
    portfolio: Portfolio
    data: List[dict]
    bonds: List[BondPosition] = []
    stale_ticker_handling: List[StaleTickerHandling] = []
    symbol_resolutions: List[SymbolResolution] = []
    skipped_symbols: List[str] = []


@router.post("/calculate/portfolio-full")
async def calculate_portfolio_full_stream(request: PortfolioFullRequest):
    """
    SSE streaming endpoint with parallel I/O and caching.

    Event flow:
    1. symbols_unresolved - (optional) symbols need resolution
    2. awaiting_symbol_resolution - pause for user input
    3. prices_loaded - price data (parallel loaded)
    4. stale_tickers_detected - (optional) stale tickers found
    5. nav_calculated - NAV history
    6. indicators_basic_calculated - basic indicators
    7. benchmark_comparison_calculated - benchmark comparison
    8. indicators_all_calculated - all indicators
    9. complete - completion marker with liquidation_events
    """
    portfolio = request.portfolio
    data = request.data
    bonds = request.bonds
    stale_ticker_handling = request.stale_ticker_handling
    symbol_resolutions = request.symbol_resolutions
    skipped_symbols = [s.upper() for s in request.skipped_symbols]

    async def event_generator():
        nonlocal data

        try:
            from app.core.benchmarks import get_benchmark_loader
            from app.core.indicators.aggregator import calculate_benchmark_comparison

            # Track skipped symbols as failed tickers
            user_skipped_tickers: List[str] = list(skipped_symbols)

            # Extract unique symbols from portfolio data
            symbols = list(set([
                row['symbol'] for row in data
                if row.get('symbol') and row['symbol'] != 'CASH'
            ]))

            # ============================================
            # PHASE 0: Symbol Resolution
            # Resolve foreign stock symbols using currency hints
            # ============================================
            # If user has already dealt with resolution (provided resolutions or skipped symbols),
            # don't try automatic resolution again
            # Debug: Log data sample to see if currency field is present
            sample_data = data[:3] if len(data) >= 3 else data
            logger.info(f"Symbol resolution phase: resolutions={len(symbol_resolutions)}, skipped={skipped_symbols}")
            logger.info(f"Symbols to resolve: {symbols}")
            logger.info(f"Sample data rows: {sample_data}")
            if symbol_resolutions or skipped_symbols:
                # Apply user-provided resolutions
                resolution_map = {r.original.upper(): r.resolved.upper() for r in symbol_resolutions}
                resolved_symbols = []
                for sym in symbols:
                    # Skip symbols that user explicitly skipped
                    if sym in skipped_symbols:
                        continue
                    resolved = resolution_map.get(sym, sym)
                    resolved_symbols.append(resolved)
                symbols = resolved_symbols

                # Update data with resolved symbols and filter out skipped symbols
                updated_data = []
                for row in data:
                    original_sym = row.get('symbol', '').upper()
                    # Skip rows with skipped symbols
                    if original_sym in skipped_symbols:
                        continue
                    if original_sym in resolution_map:
                        row['symbol'] = resolution_map[original_sym]
                    updated_data.append(row)
                data = updated_data
            else:
                # Try automatic symbol resolution
                resolver = get_resolver()
                symbol_currencies: Dict[str, str] = {}
                for row in data:
                    sym = row.get('symbol', '').upper()
                    if sym and sym != 'CASH':
                        currency = row.get('currency', portfolio.base_currency)
                        if currency:
                            symbol_currencies[sym] = currency.upper()

                resolved_map: Dict[str, str] = {}
                unresolved_list: List[UnresolvedSymbol] = []

                for sym in symbols:
                    currency = symbol_currencies.get(sym, portfolio.base_currency)
                    result, unresolved = resolver.resolve(sym, currency)
                    if result:
                        resolved_map[sym] = result.resolved
                    elif unresolved:
                        unresolved_list.append(unresolved)

                # If there are unresolved symbols, send event and pause
                if unresolved_list:
                    unresolved_data = [
                        {
                            'original': u.original,
                            'currency': u.currency,
                            'attempted': u.attempted,
                            'suggestions': u.suggestions
                        }
                        for u in unresolved_list
                    ]
                    yield f"event: symbols_unresolved\n"
                    yield f"data: {json.dumps({'unresolved_symbols': unresolved_data})}\n\n"
                    yield f"event: awaiting_symbol_resolution\n"
                    yield f"data: {json.dumps({'message': 'Waiting for symbol resolution'})}\n\n"
                    return

                # Apply resolved symbols
                if resolved_map:
                    resolved_symbols = []
                    for sym in symbols:
                        resolved = resolved_map.get(sym, sym)
                        resolved_symbols.append(resolved)
                    symbols = resolved_symbols

                    # Update data with resolved symbols
                    for row in data:
                        original_sym = row.get('symbol', '').upper()
                        if original_sym in resolved_map:
                            row['symbol'] = resolved_map[original_sym]

            benchmark_loader = get_benchmark_loader()

            # ============================================
            # PHASE 1: Parallel I/O
            # Load portfolio prices and benchmark prices concurrently
            # ============================================
            price_task = asyncio.create_task(load_prices_batch(symbols))
            benchmark_task = asyncio.create_task(load_benchmarks_batch(benchmark_loader))

            price_cache, (benchmark_formatted, benchmark_cache) = await asyncio.gather(
                price_task, benchmark_task
            )

            # Format price data for frontend
            price_data = {
                sym: [
                    {"date": d.strftime("%Y-%m-%d"), "value": float(v)}
                    for d, v in df['Close'].items()
                ]
                for sym, df in price_cache.items()
            }

            # ============================================
            # PHASE 2: Send prices_loaded, detect stale tickers
            # ============================================
            yield f"event: prices_loaded\n"
            yield f"data: {json.dumps({'prices': price_data, 'benchmarks': benchmark_formatted})}\n\n"

            # Create engine with pre-loaded price cache
            eng = engine.PortfolioEngine(portfolio, data, bonds)
            eng.set_price_cache(price_cache)

            # Detect stale tickers (only if no handling provided yet)
            if not stale_ticker_handling:
                stale_tickers = eng.detect_stale_tickers()
                if stale_tickers:
                    stale_data = [t.model_dump() for t in stale_tickers]
                    yield f"event: stale_tickers_detected\n"
                    yield f"data: {json.dumps({'stale_tickers': stale_data})}\n\n"
                    # Stop here and wait for user to provide handling
                    yield f"event: awaiting_stale_ticker_handling\n"
                    yield f"data: {json.dumps({'message': 'Waiting for stale ticker handling'})}\n\n"
                    return
            else:
                # Apply user-provided stale ticker handling
                eng.set_stale_ticker_handling(stale_ticker_handling)

            nav = eng.calculate_nav_history()

            nav_result = {
                "nav": [
                    {"date": d.strftime("%Y-%m-%d"), "value": float(v)}
                    for d, v in nav.items()
                ],
                "cash": [
                    {"date": d.strftime("%Y-%m-%d"), "value": float(v)}
                    for d, v in eng.cash_history.items()
                ],
                "failed_tickers": eng.failed_tickers
            }

            # ============================================
            # PHASE 3: Send nav_calculated, start parallel calculations
            # ============================================
            yield f"event: nav_calculated\n"
            yield f"data: {json.dumps(nav_result)}\n\n"

            # Parallel: basic indicators + benchmark comparison
            async def calc_basic() -> Dict[str, Any]:
                return await asyncio.to_thread(eng.get_indicators)

            async def calc_benchmark_comparison() -> Dict[str, Any]:
                if nav.empty:
                    return {"benchmarks": {}}
                try:
                    portfolio_returns = nav.pct_change(fill_method=None).dropna()

                    # Use cached benchmark data instead of re-fetching
                    benchmark_returns = benchmark_loader.load_all_benchmark_returns_from_cache(
                        benchmark_cache, nav.index[0], nav.index[-1]
                    )

                    if not benchmark_returns:
                        return {"benchmarks": {}}

                    comparison = calculate_benchmark_comparison(
                        portfolio_returns, benchmark_returns, 0.0
                    )

                    return {"benchmarks": {
                        sym: {
                            "name": benchmark_loader.get_benchmark_name(sym),
                            "metrics": metrics
                        }
                        for sym, metrics in comparison.items()
                    }}
                except Exception as e:
                    logger.warning(f"Benchmark comparison failed: {e}")
                    return {"benchmarks": {}}

            indicators_basic, benchmark_comparison = await asyncio.gather(
                calc_basic(), calc_benchmark_comparison()
            )

            # ============================================
            # PHASE 4: Send basic + benchmark, calculate all_indicators
            # ============================================
            yield f"event: indicators_basic_calculated\n"
            yield f"data: {json.dumps(indicators_basic)}\n\n"

            yield f"event: benchmark_comparison_calculated\n"
            yield f"data: {json.dumps(benchmark_comparison)}\n\n"

            # Calculate all indicators (uses cached base data)
            indicators_all = await asyncio.to_thread(eng.get_all_indicators)

            yield f"event: indicators_all_calculated\n"
            yield f"data: {json.dumps(indicators_all)}\n\n"

            # ============================================
            # PHASE 5: Complete
            # ============================================
            liquidation_events = eng.get_liquidation_events()
            # Combine engine's failed_tickers with user-skipped symbols
            all_failed_tickers = list(set(eng.failed_tickers + user_skipped_tickers))
            completion_data = {
                "failed_tickers": all_failed_tickers,
                "suggested_initial_deposit": (
                    eng.suggested_initial_deposit
                    if eng.suggested_initial_deposit > 0 else None
                ),
                "liquidation_events": [e.model_dump() for e in liquidation_events]
            }

            yield f"event: complete\n"
            yield f"data: {json.dumps(completion_data)}\n\n"

            # Background price update
            async def update_prices_background() -> None:
                for sym in symbols:
                    try:
                        await asyncio.to_thread(prices.update_price_cache, sym)
                    except Exception as e:
                        logger.warning(f"Background price update failed for {sym}: {e}")

            asyncio.create_task(update_prices_background())

        except Exception as e:
            logger.error(f"Stream error: {e}")
            error_data = {"error": "Internal server error"}
            yield f"event: error\n"
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

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
