# Portfolio Manager

A lightweight, privacy-focused portfolio management and analysis tool with comprehensive performance metrics.

## Features

### Portfolio Types
- **Transaction Mode**: Track individual trades with full transaction history
- **Snapshot Mode**: Manage current positions with cost basis tracking

### Performance Analysis
- **79 Comprehensive Indicators**: Returns, risk metrics, drawdown analysis, risk-adjusted ratios, tail risk measures, allocation analysis, risk decomposition, and trading metrics
- **5 Basic Indicators**: Total return, CAGR, volatility, Sharpe ratio, and maximum drawdown for quick analysis
- **Benchmark Comparison**: Compare portfolio performance against 8 major market indices (S&P 500, NASDAQ, Dow Jones, Russell 2000, DAX, FTSE 100, Hang Seng, Shanghai Composite)

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
