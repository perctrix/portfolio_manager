# Stale Ticker Detection and Handling Feature

## Overview
Detect stocks with incomplete/stale price data and provide users with options to handle them gracefully.

## Problem
- Some stocks have historical data but no current data (e.g., delisted, acquired, or data source issues)
- When combining multiple stocks with different date ranges, `dropna()` can result in empty DataFrame
- Users need visibility and control over how to handle these situations

## Solution

### 1. Backend Changes

#### 1.1 Detection Logic (`backend/app/core/engine.py`)
- After loading price data for all symbols, find the latest date across all symbols
- Any symbol whose last data date < latest date is marked as "stale"
- Return stale ticker info: `{symbol, last_date, last_price, quantity}`

#### 1.2 New Data Structures (`backend/app/models/portfolio.py`)
```python
class StaleTicker(BaseModel):
    symbol: str
    last_date: str  # YYYY-MM-DD
    last_price: float
    quantity: float

class StaleTickerAction(str, Enum):
    LIQUIDATE = "liquidate"      # Convert to cash at last price
    FREEZE = "freeze"            # Keep last price unchanged
    REMOVE = "remove"            # Remove from portfolio (value = 0)

class StaleTickerHandling(BaseModel):
    symbol: str
    action: StaleTickerAction
```

#### 1.3 API Changes (`backend/app/api/endpoints.py`)
- Modify `/calculate/portfolio-full` to return stale tickers in a new SSE event
- Add new event: `stale_tickers_detected` with list of StaleTicker objects
- Accept `stale_ticker_handling: List[StaleTickerHandling]` in request to apply user choices

#### 1.4 NAV Calculation Changes (`backend/app/core/engine.py`)
- Apply stale ticker handling before NAV calculation:
  - LIQUIDATE: On last_date, convert position to cash (last_price * quantity)
  - FREEZE: Use last_price for all dates after last_date
  - REMOVE: Exclude from NAV calculation
- Track liquidation events: `{date, symbol, price, quantity, cash_amount}`
- Return liquidation events for chart markers

### 2. Frontend Changes

#### 2.1 New Types (`frontend/types/index.ts`)
```typescript
interface StaleTicker {
  symbol: string;
  last_date: string;
  last_price: number;
  quantity: number;
}

type StaleTickerAction = 'liquidate' | 'freeze' | 'remove';

interface StaleTickerHandling {
  symbol: string;
  action: StaleTickerAction;
}

interface LiquidationEvent {
  date: string;
  symbol: string;
  price: number;
  quantity: number;
  cash_amount: number;
}
```

#### 2.2 New Component: StaleTickerModal (`frontend/components/StaleTickerModal.tsx`)
- Display list of stale tickers with:
  - Symbol
  - Last valid date
  - Last price
  - Quantity held
  - Market value at last price
- Per-ticker action selector:
  - "Convert to cash" (default)
  - "Keep last price"
  - "Remove from portfolio"
- "Apply to all" quick actions
- Confirm button to proceed

#### 2.3 NavChart Enhancement (`frontend/components/NavChart.tsx`)
- Add markers for liquidation events
- Marker style: distinct point (e.g., diamond or square) with different color
- Tooltip on hover:
  - Date
  - Symbol
  - "Converted to cash"
  - Quantity and amount

#### 2.4 Page Integration (`frontend/app/[locale]/portfolio/[id]/page.tsx`)
- Handle new SSE event `stale_tickers_detected`
- If stale tickers detected, pause loading and show StaleTickerModal
- After user confirms, restart calculation with stale ticker handling
- Pass liquidation events to NavChart

### 3. Implementation Order

1. **Backend: Data structures and detection** (models, engine detection logic)
2. **Backend: API changes** (new SSE event, request handling)
3. **Backend: NAV calculation with stale handling** (apply user choices, return liquidation events)
4. **Frontend: Types and StaleTickerModal component**
5. **Frontend: API integration** (handle new event, restart flow)
6. **Frontend: NavChart markers** (display liquidation events)
7. **Testing and i18n**

### 4. Files to Modify/Create

#### Backend
- `backend/app/models/portfolio.py` - Add new models
- `backend/app/core/engine.py` - Detection and handling logic
- `backend/app/api/endpoints.py` - API changes

#### Frontend
- `frontend/types/index.ts` - Add new types
- `frontend/components/StaleTickerModal.tsx` - New component
- `frontend/components/NavChart.tsx` - Add markers
- `frontend/app/[locale]/portfolio/[id]/page.tsx` - Integration
- `frontend/lib/api.ts` - Update API types
- `frontend/messages/en.json` - English translations
- `frontend/messages/zh.json` - Chinese translations
