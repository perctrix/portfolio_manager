import { Portfolio, CreatePortfolioRequest } from '@/types';

const API_BASE_URL = 'http://localhost:8000/api';

export async function getPortfolios(): Promise<Portfolio[]> {
    const response = await fetch(`${API_BASE_URL}/portfolios`);
    if (!response.ok) {
        throw new Error('Failed to fetch portfolios');
    }
    return response.json();
}

export async function createPortfolio(data: CreatePortfolioRequest): Promise<Portfolio> {
    const response = await fetch(`${API_BASE_URL}/portfolios?name=${encodeURIComponent(data.name)}&type=${data.type}&base_currency=${data.base_currency}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create portfolio');
    }
    return response.json();
}

export async function importPortfolio(data: any): Promise<Portfolio> {
    const response = await fetch(`${API_BASE_URL}/portfolios/import`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to import portfolio');
    }
    return response.json();
}

export async function deletePortfolio(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/portfolios/${id}`, {
        method: 'DELETE',
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete portfolio');
    }
}
