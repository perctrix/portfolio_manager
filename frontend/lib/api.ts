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

export async function calculateNav(portfolio: Portfolio, data: any[]): Promise<{nav: Array<{date: string, value: number}>, failed_tickers: string[]}> {
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
