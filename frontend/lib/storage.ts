import { Portfolio } from '@/types';

const PORTFOLIOS_KEY = 'portfolios';

export interface PortfolioData {
    meta: Portfolio;
    data: any[];
}

export function getAllPortfolios(): Record<string, PortfolioData> {
    if (typeof window === 'undefined') return {};
    try {
        const stored = localStorage.getItem(PORTFOLIOS_KEY);
        return stored ? JSON.parse(stored) : {};
    } catch (error) {
        console.error('Failed to parse portfolios from localStorage:', error);
        return {};
    }
}

export function getPortfolio(id: string): PortfolioData | null {
    const portfolios = getAllPortfolios();
    return portfolios[id] || null;
}

export function savePortfolio(id: string, portfolioData: PortfolioData): void {
    if (typeof window === 'undefined') return;
    const portfolios = getAllPortfolios();
    portfolios[id] = portfolioData;
    localStorage.setItem(PORTFOLIOS_KEY, JSON.stringify(portfolios));
}

export function deletePortfolio(id: string): void {
    if (typeof window === 'undefined') return;
    const portfolios = getAllPortfolios();
    delete portfolios[id];
    localStorage.setItem(PORTFOLIOS_KEY, JSON.stringify(portfolios));
}

export function updatePortfolioData(id: string, data: any[]): void {
    if (typeof window === 'undefined') return;
    const portfolios = getAllPortfolios();
    if (portfolios[id]) {
        portfolios[id].data = data;
        localStorage.setItem(PORTFOLIOS_KEY, JSON.stringify(portfolios));
    }
}

export function addTransaction(id: string, transaction: any): void {
    if (typeof window === 'undefined') return;
    const portfolios = getAllPortfolios();
    if (portfolios[id]) {
        portfolios[id].data.push(transaction);
        localStorage.setItem(PORTFOLIOS_KEY, JSON.stringify(portfolios));
    }
}

export function updateTransaction(id: string, index: number, transaction: any): void {
    if (typeof window === 'undefined') return;
    const portfolios = getAllPortfolios();
    if (portfolios[id] && portfolios[id].data[index]) {
        portfolios[id].data[index] = transaction;
        localStorage.setItem(PORTFOLIOS_KEY, JSON.stringify(portfolios));
    }
}

export function deleteTransaction(id: string, index: number): void {
    if (typeof window === 'undefined') return;
    const portfolios = getAllPortfolios();
    if (portfolios[id] && portfolios[id].data[index] !== undefined) {
        portfolios[id].data.splice(index, 1);
        localStorage.setItem(PORTFOLIOS_KEY, JSON.stringify(portfolios));
    }
}
