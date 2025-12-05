import { Portfolio, AnalysisCache, BondPosition } from '@/types';

const PORTFOLIOS_KEY = 'portfolios';

export interface PortfolioData {
    meta: Portfolio;
    data: any[];
    bonds?: BondPosition[];
    analysis?: AnalysisCache;
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
        delete portfolios[id].analysis;
        localStorage.setItem(PORTFOLIOS_KEY, JSON.stringify(portfolios));
    }
}

export function addTransaction(id: string, transaction: any): void {
    if (typeof window === 'undefined') return;
    const portfolios = getAllPortfolios();
    if (portfolios[id]) {
        portfolios[id].data.push(transaction);
        delete portfolios[id].analysis;
        localStorage.setItem(PORTFOLIOS_KEY, JSON.stringify(portfolios));
    }
}

export function updateTransaction(id: string, index: number, transaction: any): void {
    if (typeof window === 'undefined') return;
    const portfolios = getAllPortfolios();
    if (portfolios[id] && portfolios[id].data[index]) {
        portfolios[id].data[index] = transaction;
        delete portfolios[id].analysis;
        localStorage.setItem(PORTFOLIOS_KEY, JSON.stringify(portfolios));
    }
}

export function deleteTransaction(id: string, index: number): void {
    if (typeof window === 'undefined') return;
    const portfolios = getAllPortfolios();
    if (portfolios[id] && portfolios[id].data[index] !== undefined) {
        portfolios[id].data.splice(index, 1);
        delete portfolios[id].analysis;
        localStorage.setItem(PORTFOLIOS_KEY, JSON.stringify(portfolios));
    }
}

export function saveAnalysisCache(id: string, analysis: AnalysisCache): void {
    if (typeof window === 'undefined') return;
    const portfolios = getAllPortfolios();
    if (portfolios[id]) {
        portfolios[id].analysis = analysis;
        localStorage.setItem(PORTFOLIOS_KEY, JSON.stringify(portfolios));
    }
}

export function clearAnalysisCache(id: string): void {
    if (typeof window === 'undefined') return;
    const portfolios = getAllPortfolios();
    if (portfolios[id]) {
        delete portfolios[id].analysis;
        localStorage.setItem(PORTFOLIOS_KEY, JSON.stringify(portfolios));
    }
}

export function getBonds(portfolioId: string): BondPosition[] {
    const portfolio = getPortfolio(portfolioId);
    return portfolio?.bonds || [];
}

export function addBond(portfolioId: string, bond: BondPosition): void {
    if (typeof window === 'undefined') return;
    const portfolios = getAllPortfolios();
    if (portfolios[portfolioId]) {
        if (!portfolios[portfolioId].bonds) {
            portfolios[portfolioId].bonds = [];
        }
        portfolios[portfolioId].bonds!.push(bond);
        delete portfolios[portfolioId].analysis;
        localStorage.setItem(PORTFOLIOS_KEY, JSON.stringify(portfolios));
    }
}

export function updateBond(portfolioId: string, bondId: string, bond: BondPosition): void {
    if (typeof window === 'undefined') return;
    const portfolios = getAllPortfolios();
    if (portfolios[portfolioId] && portfolios[portfolioId].bonds) {
        const index = portfolios[portfolioId].bonds!.findIndex(b => b.id === bondId);
        if (index !== -1) {
            portfolios[portfolioId].bonds![index] = bond;
            delete portfolios[portfolioId].analysis;
            localStorage.setItem(PORTFOLIOS_KEY, JSON.stringify(portfolios));
        }
    }
}

export function deleteBond(portfolioId: string, bondId: string): void {
    if (typeof window === 'undefined') return;
    const portfolios = getAllPortfolios();
    if (portfolios[portfolioId] && portfolios[portfolioId].bonds) {
        portfolios[portfolioId].bonds = portfolios[portfolioId].bonds!.filter(b => b.id !== bondId);
        delete portfolios[portfolioId].analysis;
        localStorage.setItem(PORTFOLIOS_KEY, JSON.stringify(portfolios));
    }
}

export function updateBonds(portfolioId: string, bonds: BondPosition[]): void {
    if (typeof window === 'undefined') return;
    const portfolios = getAllPortfolios();
    if (portfolios[portfolioId]) {
        portfolios[portfolioId].bonds = bonds;
        delete portfolios[portfolioId].analysis;
        localStorage.setItem(PORTFOLIOS_KEY, JSON.stringify(portfolios));
    }
}
