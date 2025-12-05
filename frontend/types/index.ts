import type { AllIndicators } from './indicators';
export type { AllIndicators } from './indicators';

export type PortfolioType = 'transaction' | 'snapshot';

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
    analysis?: AnalysisCache;
}
