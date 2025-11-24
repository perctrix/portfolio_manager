import { Portfolio, CreatePortfolioRequest, ImportPortfolioData } from '@/types';

const API_BASE_URL = 'http://localhost:8000/api';

async function safeJsonParse(response: Response): Promise<any> {
    try {
        return await response.json();
    } catch (error) {
        console.error('Failed to parse JSON response:', error);
        throw new Error('Invalid response format from server');
    }
}

export async function getPortfolios(): Promise<Portfolio[]> {
    const response = await fetch(`${API_BASE_URL}/portfolios`);
    if (!response.ok) {
        throw new Error('Failed to fetch portfolios');
    }
    return safeJsonParse(response);
}

export async function createPortfolio(data: CreatePortfolioRequest): Promise<Portfolio> {
    const response = await fetch(`${API_BASE_URL}/portfolios?name=${encodeURIComponent(data.name)}&type=${data.type}&base_currency=${data.base_currency}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    });
    if (!response.ok) {
        const error = await safeJsonParse(response);
        throw new Error(error.detail || 'Failed to create portfolio');
    }
    return safeJsonParse(response);
}

export async function importPortfolio(data: ImportPortfolioData): Promise<Portfolio> {
    const response = await fetch(`${API_BASE_URL}/portfolios/import`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        const error = await safeJsonParse(response);
        throw new Error(error.detail || 'Failed to import portfolio');
    }
    return safeJsonParse(response);
}

export async function deletePortfolio(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/portfolios/${id}`, {
        method: 'DELETE',
    });
    if (!response.ok) {
        const error = await safeJsonParse(response);
        throw new Error(error.detail || 'Failed to delete portfolio');
    }
}
