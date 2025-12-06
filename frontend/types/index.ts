import type { AllIndicators } from './indicators';
export type { AllIndicators } from './indicators';

export type PortfolioType = 'transaction' | 'snapshot';

export type PaymentFrequency = 0 | 1 | 2 | 4 | 12;

export interface BondPosition {
    id: string;
    name: string;
    face_value: number;
    coupon_rate: number;
    maturity_date: string;
    payment_frequency: PaymentFrequency;
    purchase_price: number;
    purchase_quantity: number;
    purchase_date: string;
    current_price?: number;
    currency?: string;
}

export interface Portfolio {
    id: string;
    name: string;
    type: PortfolioType;
    base_currency: string;
    created_at: string;
    description?: string;
}

export interface CreatePortfolioRequest {
    name: string;
    type: PortfolioType;
    base_currency: string;
}

export interface ImportPortfolioData {
    meta: {
        id: string;
        name: string;
        type: PortfolioType;
        base_currency: string;
        created_at: string;
        description?: string;
    };
    data: Array<Record<string, any>>;
}

export interface NavDataPoint {
    date: string;
    value: number;
}

export interface BenchmarkMetrics {
    beta: number;
    alpha: number;
    r_squared: number;
    correlation: number;
    tracking_error: number;
    information_ratio: number;
    treynor_ratio?: number;
    m2_measure?: number;
    upside_capture?: number;
    downside_capture?: number;
}

export interface BenchmarkComparison {
    [symbol: string]: {
        name: string;
        metrics: BenchmarkMetrics;
    };
}

export interface AnalysisCache {
    version: string;
    calculatedAt: string;
    dataHash: string;
    navHistory: NavDataPoint[];
    cashHistory: NavDataPoint[];
    allIndicators: AllIndicators | null;
    benchmarkComparison: BenchmarkComparison | null;
}

export interface ExportPortfolioData {
    meta: Portfolio;
    data: Array<Record<string, unknown>>;
    bonds?: BondPosition[];
    analysis?: AnalysisCache;
}

export interface PortfolioData {
    meta: Portfolio;
    data: Array<Record<string, unknown>>;
    bonds?: BondPosition[];
    analysis?: AnalysisCache;
}

// Stale ticker types
export type StaleTickerAction = 'liquidate' | 'freeze' | 'remove';

export interface StaleTicker {
    symbol: string;
    last_date: string;
    last_price: number;
    quantity: number;
    market_value: number;
}

export interface StaleTickerHandling {
    symbol: string;
    action: StaleTickerAction;
}

export interface LiquidationEvent {
    date: string;
    symbol: string;
    price: number;
    quantity: number;
    cash_amount: number;
}

// Symbol resolution types
export interface UnresolvedSymbol {
    original: string;
    currency: string;
    attempted: string[];
    suggestions: Array<{ symbol: string; name: string; exchange: string }>;
}

export interface SymbolResolution {
    original: string;
    resolved: string;
}
