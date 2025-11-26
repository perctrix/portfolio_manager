# Portfolio Manager

[English](README.md) | [中文](README_zh.md)

A lightweight, privacy-focused portfolio management and analysis tool with comprehensive performance metrics.

## Features

### Portfolio Types
- **Transaction Mode**: Track individual trades with full transaction history
- **Snapshot Mode**: Manage current positions with cost basis tracking

### Performance Analysis
- **95+ Comprehensive Indicators**: Returns, risk metrics, drawdown analysis, risk-adjusted ratios, tail risk measures, allocation analysis, risk decomposition, and trading metrics
- **5 Basic Indicators**: Total return, CAGR, volatility, Sharpe ratio, and maximum drawdown for quick analysis
- **Benchmark Comparison**: Compare portfolio performance against 8 major market indices with advanced metrics (Beta, Alpha, Treynor Ratio, M2 Measure, Capture Ratios, etc.)

<details>
<summary><b>📊 Complete Indicator List (Click to expand)</b></summary>

#### Returns Metrics (16 indicators)
- Simple Returns, Log Returns, Cumulative Returns
- Annualized Return, CAGR (Compound Annual Growth Rate)
- Monthly Returns, Yearly Returns
- YTD Return (Year-to-Date), MTD Return (Month-to-Date)
- Rolling Return
- Realized P&L, Unrealized P&L, Total P&L
- Trade P&L
- TWR (Time-Weighted Return)
- IRR (Internal Rate of Return)

#### Risk Metrics (6 indicators)
- Daily Volatility, Annualized Volatility
- Rolling Volatility
- Upside Volatility, Downside Volatility
- Semivariance

#### Drawdown Analysis (10 indicators)
- Drawdown Series
- Max Drawdown, Average Drawdown, Ulcer Index
- Drawdown Duration, Recovery Time
- Max Daily Loss, Max Daily Gain
- Consecutive Loss Days, Consecutive Gain Days

#### Risk-Adjusted Ratios (9 indicators)
- Sharpe Ratio, Rolling Sharpe
- Sortino Ratio
- Calmar Ratio
- Treynor Ratio
- Omega Ratio
- M2 Measure (Modigliani-Modigliani)
- Gain-to-Pain Ratio
- Ulcer Performance Index

#### Tail Risk Measures (5 indicators)
- VaR (Value at Risk) at 95% confidence
- CVaR (Conditional Value at Risk) at 95% confidence
- Skewness
- Kurtosis
- Tail Ratio (95th / 5th percentile)

#### Allocation Analysis (13 indicators)
- Portfolio Weights, Weight History
- Top N Concentration, HHI (Herfindahl Index)
- Sector Allocation, Industry Allocation
- Max Weight, Weight Deviation from Equal
- Long/Short Exposure
- Portfolio Volatility
- MCTR (Marginal Contribution to Risk)
- Risk Contribution by Asset
- Risk Contribution by Sector

#### Trading Metrics (14 indicators - Transaction mode only)
- Trade Count
- Turnover Rate, Turnover Rate by Asset
- Average Holding Period
- Win Rate, Profit/Loss Ratio
- Max Trade Profit, Max Trade Loss
- Consecutive Winning Trades, Consecutive Losing Trades
- Profit Factor (Gross Profit / Gross Loss)
- Recovery Factor (Net Profit / Max Drawdown)
- Kelly Criterion (Optimal Position Sizing)
- Comprehensive Trading Metrics

#### Correlation & Beta Analysis (16 indicators)
- Correlation to Portfolio
- Correlation Matrix, Covariance Matrix
- Beta, Alpha, R-Squared
- Tracking Error, Information Ratio
- Treynor Ratio (vs Benchmark)
- M2 Measure (vs Benchmark)
- Upside Capture Ratio
- Downside Capture Ratio
- All Benchmark Metrics
- Multi-Benchmark Metrics
- Mean Pairwise Correlation
- Max/Min Correlation

</details>

### Technical Analysis
- Moving averages (SMA, EMA, WMA)
- Momentum indicators (RSI, MACD, Stochastic, CCI, Williams %R, Connors RSI)
- Volatility indicators (Bollinger Bands, Donchian Channel, ATR)
- Advanced filtering (Kalman filter, FFT filter)

### Data Management
- Automatic benchmark data updates via scheduler (weekdays at 6:00, 10:00, 12:00, 14:00, 16:00, 18:00 server time)
- Yahoo Finance integration for real-time price data
- Ticker validation with rate limiting
- Local CSV storage for price history

## Architecture

- **Backend**: Python (FastAPI) with pandas, numpy, scipy, TA-Lib
- **Frontend**: Next.js 16 (React 19) with TypeScript, TailwindCSS, Recharts
- **Storage**: Local CSV/JSON files (no database required)
- **Scheduler**: APScheduler for automated benchmark updates

## Setup

### Backend

1. Navigate to `backend/`
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   uvicorn main:app --reload
   ```
   API will be available at `http://localhost:8000`

### Frontend

1. Navigate to `frontend/`
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   App will be available at `http://localhost:3001`

## API Endpoints

### Portfolio Analysis
- `POST /api/calculate/nav` - Calculate NAV history
- `POST /api/calculate/indicators` - Calculate performance indicators (legacy)
- `POST /api/calculate/indicators/all` - Calculate all 79 indicators
- `POST /api/calculate/indicators/basic` - Calculate 5 basic indicators (fast)
- `POST /api/calculate/benchmark-comparison` - Compare portfolio vs benchmarks

### Market Data
- `GET /api/prices/{symbol}/history` - Get historical prices for a symbol
- `POST /api/prices/update` - Update price cache for a symbol
- `GET /api/benchmarks/list` - List available benchmark indices
- `GET /api/benchmarks/{symbol}/history` - Get benchmark historical data

### Ticker Management
- `POST /api/tickers/validate` - Validate ticker symbol (rate limited)

### Scheduler
- `GET /api/scheduler/status` - Get scheduler status and next run times
- `POST /api/scheduler/update-now` - Manually trigger benchmark update

## Data Storage

All data is stored locally in `backend/data/`:
- `prices/` - Historical price data (CSV files)
- `benchmarks.json` - Benchmark index configurations
- `tickers/` - Ticker validation and metadata
- `cache/` - Temporary cache files

## Project Structure

```
portfolio_manager/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints.py          # API route handlers
│   │   ├── core/
│   │   │   ├── engine.py             # Portfolio calculation engine
│   │   │   ├── prices.py             # Price data management
│   │   │   ├── benchmarks.py         # Benchmark loader
│   │   │   ├── scheduler.py          # Automated update scheduler
│   │   │   ├── ticker_validator.py   # Ticker validation
│   │   │   └── indicators/           # Performance indicators
│   │   │       ├── returns.py        # Return metrics
│   │   │       ├── risk.py           # Risk metrics
│   │   │       ├── drawdown.py       # Drawdown analysis
│   │   │       ├── ratios.py         # Sharpe, Sortino, Calmar
│   │   │       ├── tail_risk.py      # VaR, CVaR, skewness, kurtosis
│   │   │       ├── allocation.py     # Position allocation & risk decomposition
│   │   │       ├── trading.py        # Trading metrics
│   │   │       ├── technical.py      # Technical indicators
│   │   │       ├── correlation_beta.py # Benchmark comparison
│   │   │       └── aggregator.py     # Indicator aggregation
│   │   └── models/
│   │       └── portfolio.py          # Portfolio data models
│   ├── data/
│   │   ├── fetch_data.py             # Yahoo Finance data fetcher
│   │   ├── benchmarks.json           # Benchmark configurations
│   │   └── prices/                   # Price data cache
│   └── main.py                       # FastAPI application
└── frontend/
    ├── app/
    │   ├── page.tsx                  # Portfolio list
    │   ├── create/page.tsx           # Create portfolio
    │   └── portfolio/[id]/page.tsx   # Portfolio detail view
    └── lib/
        └── storage.ts                # Local storage management
```

## Dependencies

### Backend
- fastapi - Web framework
- uvicorn - ASGI server
- pandas - Data manipulation
- numpy - Numerical computing
- scipy - Scientific computing
- yfinance - Yahoo Finance API
- TA-Lib - Technical analysis library
- apscheduler - Task scheduling
- portalocker - File locking
- pydantic - Data validation

### Frontend
- next - React framework
- react - UI library
- typescript - Type safety
- tailwindcss - Styling
- recharts - Charting library
- lucide-react - Icons
