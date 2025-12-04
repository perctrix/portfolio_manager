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

export interface AnalysisCache {
    version: string;
    calculatedAt: string;
    dataHash: string;
    navHistory: NavDataPoint[];
    cashHistory: NavDataPoint[];
    allIndicators: Record<string, unknown> | null;
    benchmarkComparison: Record<string, unknown> | null;
}

export interface ExportPortfolioData {
    meta: Portfolio;
    data: Array<Record<string, unknown>>;
    analysis?: AnalysisCache;
}
