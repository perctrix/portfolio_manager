import { Portfolio } from '@/types';

const API_BASE_URL = 'http://localhost:8000/api';

async function safeJsonParse(response: Response): Promise<any> {
    try {
        return await response.json();
    } catch (error) {
        console.error('Failed to parse JSON response:', error);
        throw new Error('Invalid response format from server');
    }
}

export async function calculateNav(portfolio: Portfolio, data: any[]): Promise<Array<{date: string, value: number}>> {
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
