'use client';

import { useEffect, useState, use } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Portfolio } from '@/types';
import { MetricsCard } from '@/components/MetricsCard';
import { NavChart } from '@/components/NavChart';
import { AddTransactionModal } from '@/components/AddTransactionModal';
import { EditSnapshotModal } from '@/components/EditSnapshotModal';
import { Eye, EyeOff, Download, Trash2 } from 'lucide-react';
import { getPortfolio, deletePortfolio, addTransaction, updatePortfolioData } from '@/lib/storage';
import { calculateNav, calculateIndicators, getPriceHistory, updatePrice } from '@/lib/api';

export default function PortfolioDetail({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
    const [navHistory, setNavHistory] = useState<any[]>([]);
    const [indicators, setIndicators] = useState<any>({});
    const [holdings, setHoldings] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [isAddTxnOpen, setIsAddTxnOpen] = useState(false);
    const [isEditSnapshotOpen, setIsEditSnapshotOpen] = useState(false);

    const [selectedTickers, setSelectedTickers] = useState<Set<string>>(new Set());
    const [comparisonData, setComparisonData] = useState<{ [key: string]: any[] }>({});

    useEffect(() => {
        loadData();
    }, [id]);

    async function loadData() {
        try {
            setLoading(true);
            const portfolioData = getPortfolio(id);
            if (!portfolioData) {
                throw new Error('Portfolio not found');
            }

            setPortfolio(portfolioData.meta);
            setHoldings(portfolioData.data);

            if (portfolioData.data.length > 0) {
                const symbols = Array.from(new Set(portfolioData.data.map((row: any) => row.symbol).filter((s: string) => s && s !== 'CASH')));
                for (const symbol of symbols) {
                    await updatePrice(symbol).catch(err => console.warn(`Failed to update price for ${symbol}:`, err));
                }

                const nav = await calculateNav(portfolioData.meta, portfolioData.data);
                setNavHistory(nav);

                const ind = await calculateIndicators(portfolioData.meta, portfolioData.data);
                setIndicators(ind);
            } else {
                setNavHistory([]);
                setIndicators({});
            }

        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    }

    async function handleAddTransaction(data: any) {
        try {
            addTransaction(id, data);
            loadData();
        } catch (err) {
            console.error(err);
            throw new Error('Failed to add transaction');
        }
    }

    async function handleUpdateSnapshot(data: any[]) {
        try {
            updatePortfolioData(id, data);
            loadData();
        } catch (err) {
            console.error(err);
            throw new Error('Failed to update snapshot');
        }
    }

    const router = useRouter();

    function handleExport() {
        try {
            const portfolioData = getPortfolio(id);
            if (!portfolioData) throw new Error('Portfolio not found');

            const exportData = {
                meta: portfolioData.meta,
                data: portfolioData.data
            };

            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `portfolio-${portfolio?.name || id}.json`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (e) {
            console.error(e);
            alert('Failed to export portfolio');
        }
    }

    function handleDelete() {
        if (!confirm('Are you sure you want to delete this portfolio? This action cannot be undone.')) return;

        try {
            deletePortfolio(id);
            router.push('/');
        } catch (e) {
            console.error(e);
            alert('Failed to delete portfolio');
        }
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
                    const history = await getPriceHistory(symbol);
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
                        <button
                            onClick={handleExport}
                            className="text-gray-600 hover:text-blue-600 p-2 rounded-lg hover:bg-gray-100 transition-colors"
                            title="Export Portfolio"
                        >
                            <Download size={20} />
                        </button>
                        <button
                            onClick={handleDelete}
                            className="text-gray-600 hover:text-red-600 p-2 rounded-lg hover:bg-gray-100 transition-colors"
                            title="Delete Portfolio"
                        >
                            <Trash2 size={20} />
                        </button>
                        <div className="w-px bg-gray-300 mx-1"></div>
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

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <MetricsCard title="Sortino" value={indicators.sortino || 0} />
                    <MetricsCard title="Calmar" value={indicators.calmar || 0} />
                    <MetricsCard title="VaR (95%)" value={`${(indicators.var_95 * 100 || 0).toFixed(2)}%`} />
                    <MetricsCard title="HHI (Concentration)" value={indicators.hhi || 0} />
                </div>

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
