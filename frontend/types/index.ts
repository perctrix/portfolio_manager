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
