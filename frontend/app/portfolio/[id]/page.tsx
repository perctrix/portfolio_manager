'use client';

import { useEffect, useState, use } from 'react';
import Link from 'next/link';
import { Portfolio } from '@/types';
import { MetricsCard } from '@/components/MetricsCard';
import { NavChart } from '@/components/NavChart';
import { AddTransactionModal } from '@/components/AddTransactionModal';
import { EditSnapshotModal } from '@/components/EditSnapshotModal';
import { Eye, EyeOff } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api';

export default function PortfolioDetail({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
    const [navHistory, setNavHistory] = useState<any[]>([]);
    const [indicators, setIndicators] = useState<any>({});
    const [holdings, setHoldings] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [isAddTxnOpen, setIsAddTxnOpen] = useState(false);
    const [isEditSnapshotOpen, setIsEditSnapshotOpen] = useState(false);

    // Comparison State
    const [selectedTickers, setSelectedTickers] = useState<Set<string>>(new Set());
    const [comparisonData, setComparisonData] = useState<{ [key: string]: any[] }>({});

    useEffect(() => {
        loadData();
    }, [id]);

    async function loadData() {
        try {
            setLoading(true);
            // Fetch Portfolio Info
            const pRes = await fetch(`${API_BASE_URL}/portfolios/${id}`);
            if (!pRes.ok) throw new Error('Failed to load portfolio');
            const pData = await pRes.json();
            setPortfolio(pData);

            // Fetch NAV
            const navRes = await fetch(`${API_BASE_URL}/portfolios/${id}/nav`);
            if (navRes.ok) setNavHistory(await navRes.json());

            // Fetch Indicators
            const indRes = await fetch(`${API_BASE_URL}/portfolios/${id}/indicators`);
            if (indRes.ok) setIndicators(await indRes.json());

            // Fetch Holdings/Data
            const dataRes = await fetch(`${API_BASE_URL}/portfolios/${id}/data`);
            if (dataRes.ok) setHoldings(await dataRes.json());

        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    }

    async function handleAddTransaction(data: any) {
        const res = await fetch(`${API_BASE_URL}/portfolios/${id}/transactions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error('Failed');
        loadData(); // Reload
    }

    async function handleUpdateSnapshot(data: any[]) {
        const res = await fetch(`${API_BASE_URL}/portfolios/${id}/positions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error('Failed');
        loadData(); // Reload
    }

    async function toggleTicker(symbol: string) {
        const newSelected = new Set(selectedTickers);
        if (newSelected.has(symbol)) {
            newSelected.delete(symbol);
            const newCompData = { ...comparisonData };
            delete newCompData[symbol];
            setComparisonData(newCompData);
            setSelectedTickers(newSelected);
        } else {
            newSelected.add(symbol);
            setSelectedTickers(newSelected);

            if (!comparisonData[symbol]) {
                try {
                    const res = await fetch(`${API_BASE_URL}/prices/${symbol}/history`);
                    if (!res.ok) {
                        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                    }
                    const history = await res.json();
                    setComparisonData(prev => ({ ...prev, [symbol]: history }));
                } catch (e) {
                    console.error(`Failed to fetch history for ${symbol}:`, e);
                    newSelected.delete(symbol);
                    setSelectedTickers(new Set(newSelected));
                    alert(`Unable to load data for ${symbol}. Please try again.`);
                }
            }
        }
    }

    if (loading) return <div className="p-8 text-center">Loading...</div>;
    if (!portfolio) return <div className="p-8 text-center text-red-500">Portfolio not found</div>;

    return (
        <main className="min-h-screen p-8 bg-gray-50 text-gray-900">
            <div className="max-w-6xl mx-auto space-y-8">
                {/* Header */}
                <div className="flex justify-between items-start">
                    <div>
                        <Link href="/" className="text-sm text-gray-500 hover:text-gray-900 mb-2 inline-block">← Back to Portfolios</Link>
                        <h1 className="text-3xl font-bold text-gray-900">{portfolio.name}</h1>
                        <div className="flex gap-2 mt-2">
                            <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full uppercase font-medium">{portfolio.type}</span>
                            <span className="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded-full">{portfolio.base_currency}</span>
                        </div>
                    </div>
                    <div className="flex gap-3">
                        {portfolio.type === 'transaction' ? (
                            <button
                                onClick={() => setIsAddTxnOpen(true)}
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                + Add Transaction
                            </button>
                        ) : (
                            <button
                                onClick={() => setIsEditSnapshotOpen(true)}
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                Edit Positions
                            </button>
                        )}
                    </div>
                </div>

                {/* Key Metrics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <MetricsCard
                        title="Total Return"
                        value={`${(indicators.total_return * 100 || 0).toFixed(2)}%`}
                        trend={indicators.total_return > 0 ? 'up' : 'down'}
                    />
                    <MetricsCard
                        title="CAGR"
                        value={`${(indicators.cagr * 100 || 0).toFixed(2)}%`}
                    />
                    <MetricsCard
                        title="Sharpe Ratio"
                        value={indicators.sharpe || 0}
                    />
                    <MetricsCard
                        title="Max Drawdown"
                        value={`${(indicators.max_drawdown * 100 || 0).toFixed(2)}%`}
                        trend="down"
                    />
                </div>

                {/* Advanced Metrics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <MetricsCard title="Sortino" value={indicators.sortino || 0} />
                    <MetricsCard title="Calmar" value={indicators.calmar || 0} />
                    <MetricsCard title="VaR (95%)" value={`${(indicators.var_95 * 100 || 0).toFixed(2)}%`} />
                    <MetricsCard title="HHI (Concentration)" value={indicators.hhi || 0} />
                </div>

                {/* Charts Section */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-lg font-semibold">
                            {selectedTickers.size > 0 ? 'Performance Comparison (%)' : 'NAV History'}
                        </h2>
                        {selectedTickers.size > 0 && (
                            <span className="text-xs text-gray-500">Normalized to 0% at start</span>
                        )}
                    </div>
                    <NavChart data={navHistory} comparisonData={comparisonData} />
                </div>

                {/* Holdings / Transactions Table */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="p-6 border-b border-gray-100">
                        <h2 className="text-lg font-semibold">
                            {portfolio.type === 'transaction' ? 'Transaction History' : 'Current Positions'}
                        </h2>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="bg-gray-50 text-gray-500 font-medium">
                                <tr>
                                    <th className="px-6 py-3 w-10"></th>
                                    {portfolio.type === 'transaction' ? (
                                        <>
                                            <th className="px-6 py-3">Date</th>
                                            <th className="px-6 py-3">Symbol</th>
                                            <th className="px-6 py-3">Side</th>
                                            <th className="px-6 py-3 text-right">Qty</th>
                                            <th className="px-6 py-3 text-right">Price</th>
                                            <th className="px-6 py-3 text-right">Fee</th>
                                        </>
                                    ) : (
                                        <>
                                            <th className="px-6 py-3">Symbol</th>
                                            <th className="px-6 py-3 text-right">Quantity</th>
                                            <th className="px-6 py-3 text-right">Cost Basis</th>
                                            <th className="px-6 py-3">As Of</th>
                                        </>
                                    )}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {holdings.length === 0 ? (
                                    <tr>
                                        <td colSpan={7} className="px-6 py-8 text-center text-gray-400">
                                            No data available
                                        </td>
                                    </tr>
                                ) : (
                                    holdings.map((row, i) => (
                                        <tr key={i} className="hover:bg-gray-50">
                                            <td className="px-6 py-3">
                                                {/* Only show toggle for valid symbols (not CASH) */}
                                                {row.symbol && row.symbol !== 'CASH' && (
                                                    <button
                                                        onClick={() => toggleTicker(row.symbol)}
                                                        className={`p-1 rounded hover:bg-gray-200 ${selectedTickers.has(row.symbol) ? 'text-blue-600' : 'text-gray-400'}`}
                                                        title="Toggle on Chart"
                                                    >
                                                        {selectedTickers.has(row.symbol) ? <Eye size={16} /> : <EyeOff size={16} />}
                                                    </button>
                                                )}
                                            </td>
                                            {portfolio.type === 'transaction' ? (
                                                <>
                                                    <td className="px-6 py-3">{new Date(row.datetime).toLocaleDateString()}</td>
                                                    <td className="px-6 py-3 font-medium">{row.symbol}</td>
                                                    <td className="px-6 py-3">
                                                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${row.side === 'BUY' ? 'bg-green-100 text-green-800' :
                                                            row.side === 'SELL' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'
                                                            }`}>
                                                            {row.side}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-3 text-right">{row.quantity}</td>
                                                    <td className="px-6 py-3 text-right">{row.price}</td>
                                                    <td className="px-6 py-3 text-right">{row.fee}</td>
                                                </>
                                            ) : (
                                                <>
                                                    <td className="px-6 py-3 font-medium">{row.symbol}</td>
                                                    <td className="px-6 py-3 text-right">{row.quantity}</td>
                                                    <td className="px-6 py-3 text-right">{row.cost_basis}</td>
                                                    <td className="px-6 py-3">{row.as_of}</td>
                                                </>
                                            )}
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <AddTransactionModal
                isOpen={isAddTxnOpen}
                onClose={() => setIsAddTxnOpen(false)}
                onSubmit={handleAddTransaction}
            />

            <EditSnapshotModal
                isOpen={isEditSnapshotOpen}
                onClose={() => setIsEditSnapshotOpen(false)}
                onSubmit={handleUpdateSnapshot}
                initialData={holdings}
            />
        </main>
    );
}
