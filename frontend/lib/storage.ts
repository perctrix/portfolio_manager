const MY_PORTFOLIOS_KEY = 'myPortfolioIds';

export function getMyPortfolioIds(): string[] {
    if (typeof window === 'undefined') return [];
    const ids = localStorage.getItem(MY_PORTFOLIOS_KEY);
    return ids ? JSON.parse(ids) : [];
}

export function addMyPortfolio(id: string): void {
    if (typeof window === 'undefined') return;
    const ids = getMyPortfolioIds();
    if (!ids.includes(id)) {
        ids.push(id);
        localStorage.setItem(MY_PORTFOLIOS_KEY, JSON.stringify(ids));
    }
}

export function removeMyPortfolio(id: string): void {
    if (typeof window === 'undefined') return;
    const ids = getMyPortfolioIds();
    const filtered = ids.filter(i => i !== id);
    localStorage.setItem(MY_PORTFOLIOS_KEY, JSON.stringify(filtered));
}

export function isMyPortfolio(id: string): boolean {
    return getMyPortfolioIds().includes(id);
}
