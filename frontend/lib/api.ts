import { Portfolio } from '@/types';
import { AllIndicators, BasicIndicators } from '@/types/indicators';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

async function safeJsonParse(response: Response): Promise<any> {
    try {
        return await response.json();
    } catch (error) {
        console.error('Failed to parse JSON response:', error);
        throw new Error('Invalid response format from server');
    }
}

export async function calculateNav(portfolio: Portfolio, data: any[]): Promise<{nav: Array<{date: string, value: number}>, cash: Array<{date: string, value: number}>, failed_tickers: string[], suggested_initial_deposit?: number}> {
    const response = await fetch(`${API_BASE_URL}/calculate/nav`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ portfolio, data }),
    });
    if (!response.ok) {
        const error = await safeJsonParse(response);
        throw new Error(error.detail || 'Failed to calculate NAV');
    }
    return safeJsonParse(response);
}

export async function calculateIndicators(portfolio: Portfolio, data: any[]): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/calculate/indicators`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ portfolio, data }),
    });
    if (!response.ok) {
        const error = await safeJsonParse(response);
        throw new Error(error.detail || 'Failed to calculate indicators');
    }
    return safeJsonParse(response);
}

export async function getPriceHistory(symbol: string): Promise<Array<{date: string, value: number}>> {
    const response = await fetch(`${API_BASE_URL}/prices/${symbol}/history`);
    if (!response.ok) {
        throw new Error('Failed to fetch price history');
    }
    return safeJsonParse(response);
}

export async function updatePrice(symbol: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/prices/update?symbol=${encodeURIComponent(symbol)}`, {
        method: 'POST',
    });
    if (!response.ok) {
        const error = await safeJsonParse(response);
        throw new Error(error.detail || 'Failed to update price');
    }
}

export async function calculateAllIndicators(portfolio: Portfolio, data: any[]): Promise<AllIndicators> {
    const response = await fetch(`${API_BASE_URL}/calculate/indicators/all`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ portfolio, data }),
    });
    if (!response.ok) {
        const error = await safeJsonParse(response);
        throw new Error(error.detail || 'Failed to calculate all indicators');
    }
    return safeJsonParse(response);
}

export async function calculateBasicIndicators(portfolio: Portfolio, data: any[]): Promise<BasicIndicators> {
    const response = await fetch(`${API_BASE_URL}/calculate/indicators/basic`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ portfolio, data }),
    });
    if (!response.ok) {
        const error = await safeJsonParse(response);
        throw new Error(error.detail || 'Failed to calculate basic indicators');
    }
    return safeJsonParse(response);
}

export interface Benchmark {
    symbol: string;
    name: string;
    region: string;
    category: string;
    description: string;
}

export async function getBenchmarkList(): Promise<Benchmark[]> {
    const response = await fetch(`${API_BASE_URL}/benchmarks/list`);
    if (!response.ok) {
        throw new Error('Failed to fetch benchmark list');
    }
    const data = await safeJsonParse(response);
    return data.benchmarks;
}

export async function getBenchmarkHistory(symbol: string): Promise<Array<{date: string, value: number}>> {
    const response = await fetch(`${API_BASE_URL}/benchmarks/${encodeURIComponent(symbol)}/history`);
    if (!response.ok) {
        throw new Error('Failed to fetch benchmark history');
    }
    return safeJsonParse(response);
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

export async function calculateBenchmarkComparison(portfolio: Portfolio, data: any[]): Promise<BenchmarkComparison> {
    const response = await fetch(`${API_BASE_URL}/calculate/benchmark-comparison`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ portfolio, data }),
    });
    if (!response.ok) {
        const error = await safeJsonParse(response);
        throw new Error(error.detail || 'Failed to calculate benchmark comparison');
    }
    const result = await safeJsonParse(response);
    return result.benchmarks;
}

export interface PortfolioStreamCallbacks {
    onPricesLoaded?: (data: { prices: any, benchmarks: any }) => void;
    onNavCalculated?: (data: { nav: any[], cash: any[], failed_tickers: string[] }) => void;
    onIndicatorsBasicCalculated?: (data: any) => void;
    onIndicatorsAllCalculated?: (data: AllIndicators) => void;
    onBenchmarkComparisonCalculated?: (data: { benchmarks: BenchmarkComparison }) => void;
    onComplete?: (data: { failed_tickers: string[], suggested_initial_deposit?: number }) => void;
    onError?: (error: string) => void;
}

export async function calculatePortfolioFullStream(
    portfolio: Portfolio,
    data: any[],
    callbacks: PortfolioStreamCallbacks
): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/calculate/portfolio-full`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ portfolio, data }),
    });

    if (!response.ok) {
        throw new Error('Failed to start stream');
    }

    const reader = response.body?.getReader();
    if (!reader) {
        throw new Error('Response body is not readable');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line.trim()) continue;

                const parts = line.split('\n');
                if (parts.length < 2) continue;

                const eventLine = parts[0];
                const dataLine = parts[1];

                const event = eventLine.replace('event: ', '');
                const dataStr = dataLine.replace('data: ', '');

                let data;
                try {
                    data = JSON.parse(dataStr);
                } catch (e) {
                    console.error('Failed to parse SSE data:', e);
                    continue;
                }

                switch (event) {
                    case 'prices_loaded':
                        callbacks.onPricesLoaded?.(data);
                        break;
                    case 'nav_calculated':
                        callbacks.onNavCalculated?.(data);
                        break;
                    case 'indicators_basic_calculated':
                        callbacks.onIndicatorsBasicCalculated?.(data);
                        break;
                    case 'indicators_all_calculated':
                        callbacks.onIndicatorsAllCalculated?.(data);
                        break;
                    case 'benchmark_comparison_calculated':
                        callbacks.onBenchmarkComparisonCalculated?.(data);
                        break;
                    case 'complete':
                        callbacks.onComplete?.(data);
                        break;
                    case 'error':
                        callbacks.onError?.(data.error);
                        break;
                }
            }
        }
    } finally {
        reader.releaseLock();
    }
}

export interface PortfolioPoint {
    expected_return: number;
    volatility: number;
    sharpe_ratio: number;
    weights: { [symbol: string]: number };
}

export interface AssetStats {
    expected_return: number;
    volatility: number;
}

export interface EfficientFrontierData {
    frontier_points: PortfolioPoint[];
    gmv_portfolio: PortfolioPoint;
    tangent_portfolio: PortfolioPoint | null;
    current_portfolio: PortfolioPoint;
    asset_stats: { [symbol: string]: AssetStats };
    allow_short_selling: boolean;
}

export interface MarkowitzParams {
    allow_short_selling?: boolean;
    risk_free_rate?: number;
    num_frontier_points?: number;
}

export async function calculateMarkowitz(
    portfolio: Portfolio,
    data: any[],
    params: MarkowitzParams = {}
): Promise<EfficientFrontierData> {
    const response = await fetch(`${API_BASE_URL}/calculate/markowitz`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            portfolio,
            data,
            params: {
                allow_short_selling: params.allow_short_selling ?? false,
                risk_free_rate: params.risk_free_rate ?? 0.0,
                num_frontier_points: params.num_frontier_points ?? 50
            }
        }),
    });
    if (!response.ok) {
        const error = await safeJsonParse(response);
        throw new Error(error.detail || 'Failed to calculate efficient frontier');
    }
    return safeJsonParse(response);
}
