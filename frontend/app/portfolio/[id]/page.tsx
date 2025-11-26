'use client';

import { useEffect, useState, use } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Portfolio } from '@/types';
import { AllIndicators } from '@/types/indicators';
import { MetricsCard } from '@/components/MetricsCard';
import { SkeletonCard } from '@/components/SkeletonCard';
import { LoadingProgress } from '@/components/LoadingProgress';
import { NavChart } from '@/components/NavChart';
import { AddTransactionModal } from '@/components/AddTransactionModal';
import { EditSnapshotModal } from '@/components/EditSnapshotModal';
import { BenchmarkPanel } from '@/components/BenchmarkPanel';
import { BenchmarkComparisonTable } from '@/components/BenchmarkComparisonTable';
import IndicatorCategory from '@/components/IndicatorCategory';
import IndicatorGrid from '@/components/IndicatorGrid';
import MonthlyReturnsTable from '@/components/MonthlyReturnsTable';
import AllocationBreakdown from '@/components/AllocationBreakdown';
import RiskDecomposition from '@/components/RiskDecomposition';
import { Eye, EyeOff, Download, Trash2 } from 'lucide-react';
import { getPortfolio, deletePortfolio, addTransaction, updatePortfolioData } from '@/lib/storage';
import { calculateNav, calculateIndicators, calculateAllIndicators, getPriceHistory, updatePrice, getBenchmarkHistory, calculateBenchmarkComparison, BenchmarkComparison } from '@/lib/api';
import { getTrendDirection } from '@/utils/formatters';

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
    const [selectedBenchmarks, setSelectedBenchmarks] = useState<Set<string>>(new Set());
    const [benchmarkData, setBenchmarkData] = useState<{ [key: string]: any[] }>({});
    const [benchmarkComparison, setBenchmarkComparison] = useState<BenchmarkComparison | null>(null);
    const [loadingBenchmarkComparison, setLoadingBenchmarkComparison] = useState(false);
    const [selectedBetaBenchmark, setSelectedBetaBenchmark] = useState<string>('^GSPC');
    const [allIndicators, setAllIndicators] = useState<AllIndicators | null>(null);
    const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['returns']));
    const [loadingStep, setLoadingStep] = useState(0);
    const totalLoadingSteps = 5;
    const [suggestedDeposit, setSuggestedDeposit] = useState<number | null>(null);
    const [showDepositPrompt, setShowDepositPrompt] = useState(false);
    const [dismissedDepositPrompt, setDismissedDepositPrompt] = useState(false);

    useEffect(() => {
        const dismissed = localStorage.getItem(`dismissed-deposit-${id}`) === 'true';
        setDismissedDepositPrompt(dismissed);
        loadData();
    }, [id]);

    async function loadData() {
        try {
            setLoading(true);
            setLoadingStep(0);
            
            const portfolioData = getPortfolio(id);
            if (!portfolioData) {
                throw new Error('Portfolio not found');
            }

            setPortfolio(portfolioData.meta);
            setHoldings(portfolioData.data);
            setLoadingStep(1);

            if (portfolioData.data.length > 0) {
                const symbols = Array.from(new Set(portfolioData.data.map((row: any) => row.symbol).filter((s: string) => s && s !== 'CASH')));
                for (const symbol of symbols) {
                    await updatePrice(symbol).catch(err => console.warn(`Failed to update price for ${symbol}:`, err));
                }
                setLoadingStep(2);

                const navResult = await calculateNav(portfolioData.meta, portfolioData.data);
                setNavHistory(navResult.nav);

                if (navResult.suggested_initial_deposit &&
                    navResult.suggested_initial_deposit > 0 &&
                    !dismissedDepositPrompt) {
                    setSuggestedDeposit(navResult.suggested_initial_deposit);
                    setShowDepositPrompt(true);
                }

                if (navResult.failed_tickers && navResult.failed_tickers.length > 0) {
                    alert(`Warning: The following tickers could not be found:\n${navResult.failed_tickers.join(', ')}\n\nPlease check the symbols and update your portfolio.`);
                }
                setLoadingStep(3);

                const ind = await calculateIndicators(portfolioData.meta, portfolioData.data);
                setIndicators(ind);
                setLoadingStep(4);

                const allInd = await calculateAllIndicators(portfolioData.meta, portfolioData.data);
                setAllIndicators(allInd);
                setLoadingStep(5);

                loadBenchmarkComparison(portfolioData.meta, portfolioData.data);
            } else {
                setNavHistory([]);
                setIndicators({});
                setAllIndicators(null);
                setBenchmarkComparison(null);
            }

        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    }

    async function loadBenchmarkComparison(portfolioMeta: Portfolio, portfolioData: any[]) {
        try {
            setLoadingBenchmarkComparison(true);
            const comparison = await calculateBenchmarkComparison(portfolioMeta, portfolioData);
            setBenchmarkComparison(comparison);
        } catch (error) {
            console.error('Failed to load benchmark comparison:', error);
            setBenchmarkComparison(null);
        } finally {
            setLoadingBenchmarkComparison(false);
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

    async function handleAcceptDeposit() {
        if (!suggestedDeposit || !portfolio) return;

        const earliestDate = holdings.length > 0
            ? holdings.reduce((earliest, h) => {
                const hDate = new Date(h.datetime || h.as_of);
                return hDate < earliest ? hDate : earliest;
            }, new Date(holdings[0].datetime || holdings[0].as_of))
            : new Date();

        const depositTxn = {
            datetime: earliestDate.toISOString().slice(0, 16),
            symbol: 'CASH',
            side: 'DEPOSIT',
            quantity: suggestedDeposit,
            price: 1,
            fee: 0
        };

        try {
            addTransaction(id, depositTxn);
            setShowDepositPrompt(false);
            setSuggestedDeposit(null);
            localStorage.removeItem(`dismissed-deposit-${id}`);
            setDismissedDepositPrompt(false);
            loadData();
        } catch (err) {
            console.error(err);
            alert('Failed to add deposit transaction');
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

    async function toggleBenchmark(symbol: string) {
        const newSelected = new Set(selectedBenchmarks);
        if (newSelected.has(symbol)) {
            newSelected.delete(symbol);
            const newBenchData = { ...benchmarkData };
            delete newBenchData[symbol];
            setBenchmarkData(newBenchData);
            setSelectedBenchmarks(newSelected);
        } else {
            newSelected.add(symbol);
            setSelectedBenchmarks(newSelected);

            if (!benchmarkData[symbol]) {
                try {
                    const history = await getBenchmarkHistory(symbol);
                    setBenchmarkData(prev => ({ ...prev, [symbol]: history }));
                } catch (e) {
                    console.error(`Failed to fetch benchmark ${symbol}:`, e);
                    newSelected.delete(symbol);
                    setSelectedBenchmarks(new Set(newSelected));
                    alert(`Unable to load benchmark data for ${symbol}. Please try again.`);
                }
            }
        }
    }

    function toggleSection(section: string) {
        const newExpanded = new Set(expandedSections);
        if (newExpanded.has(section)) {
            newExpanded.delete(section);
        } else {
            newExpanded.add(section);
        }
        setExpandedSections(newExpanded);
    }

    if (loading) {
        return (
            <main className="min-h-screen p-8 bg-gray-50 text-gray-900">
                <div className="max-w-6xl mx-auto space-y-8">
                    {/* Header skeleton */}
                    <div className="flex justify-between items-start">
                        <div>
                            <div className="h-4 w-32 bg-gray-200 rounded animate-pulse mb-2"></div>
                            <div className="h-8 w-48 bg-gray-200 rounded animate-pulse"></div>
                            <div className="flex gap-2 mt-2">
                                <div className="h-6 w-20 bg-gray-200 rounded-full animate-pulse"></div>
                                <div className="h-6 w-16 bg-gray-200 rounded-full animate-pulse"></div>
                            </div>
                        </div>
                        <div className="flex gap-3">
                            <div className="h-10 w-10 bg-gray-200 rounded-lg animate-pulse"></div>
                            <div className="h-10 w-10 bg-gray-200 rounded-lg animate-pulse"></div>
                            <div className="w-px bg-gray-300 mx-1"></div>
                            <div className="h-10 w-32 bg-gray-200 rounded-lg animate-pulse"></div>
                        </div>
                    </div>

                    {/* First row of metrics cards skeleton */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <SkeletonCard />
                        <SkeletonCard />
                        <SkeletonCard />
                        <SkeletonCard />
                    </div>

                    {/* Second row of metrics cards skeleton */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <SkeletonCard />
                        <SkeletonCard />
                        <SkeletonCard />
                        <SkeletonCard />
                    </div>

                    {/* NAV Chart skeleton with progress bar */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <div className="flex justify-between items-center mb-6">
                            <div className="h-6 w-32 bg-gray-200 rounded animate-pulse"></div>
                        </div>
                        <div className="h-96 flex flex-col items-center justify-center bg-gray-50 rounded-xl border border-dashed border-gray-200">
                            <div className="w-64">
                                <LoadingProgress 
                                    currentStep={loadingStep} 
                                    totalSteps={totalLoadingSteps}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Benchmark Panel skeleton */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <div className="h-6 w-48 bg-gray-200 rounded animate-pulse mb-4"></div>
                        <div className="flex gap-2">
                            <div className="h-8 w-24 bg-gray-200 rounded-lg animate-pulse"></div>
                            <div className="h-8 w-24 bg-gray-200 rounded-lg animate-pulse"></div>
                            <div className="h-8 w-24 bg-gray-200 rounded-lg animate-pulse"></div>
                        </div>
                    </div>

                    {/* Transaction/Positions table skeleton */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                        <div className="p-6 border-b border-gray-100">
                            <div className="h-6 w-48 bg-gray-200 rounded animate-pulse"></div>
                        </div>
                        <div className="p-4 space-y-3">
                            <div className="h-10 w-full bg-gray-100 rounded animate-pulse"></div>
                            <div className="h-10 w-full bg-gray-100 rounded animate-pulse"></div>
                            <div className="h-10 w-full bg-gray-100 rounded animate-pulse"></div>
                        </div>
                    </div>
                </div>
            </main>
        );
    }
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
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <div className="flex items-center justify-between mb-2">
                            <h3 className="text-sm text-gray-500">Beta</h3>
                            {benchmarkComparison && (
                                <select
                                    value={selectedBetaBenchmark}
                                    onChange={(e) => setSelectedBetaBenchmark(e.target.value)}
                                    className="text-xs border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-green-500"
                                >
                                    {Object.entries(benchmarkComparison).map(([symbol, data]) => (
                                        <option key={symbol} value={symbol}>
                                            vs {data.name}
                                        </option>
                                    ))}
                                </select>
                            )}
                        </div>
                        <div className="text-2xl font-bold text-gray-900">
                            {benchmarkComparison?.[selectedBetaBenchmark]?.metrics.beta?.toFixed(2) || 'N/A'}
                        </div>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-lg font-semibold">
                            {selectedTickers.size > 0 || selectedBenchmarks.size > 0 ? 'Performance Comparison (%)' : 'NAV History'}
                        </h2>
                        {(selectedTickers.size > 0 || selectedBenchmarks.size > 0) && (
                            <span className="text-xs text-gray-500">Normalized to 0% at start</span>
                        )}
                    </div>
                    <NavChart data={navHistory} comparisonData={comparisonData} benchmarkData={benchmarkData} />
                </div>

                <BenchmarkPanel
                    selectedBenchmarks={selectedBenchmarks}
                    onToggleBenchmark={toggleBenchmark}
                />

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

                {loadingBenchmarkComparison ? (
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <p className="text-sm text-gray-400">Loading benchmark comparison...</p>
                    </div>
                ) : benchmarkComparison && (
                    <BenchmarkComparisonTable comparison={benchmarkComparison} />
                )}

                {allIndicators && (
                    <>
                        <IndicatorCategory
                            title="Returns"
                            description="Return metrics including CAGR, YTD, MTD, and P&L"
                            isOpen={expandedSections.has('returns')}
                            onToggle={() => toggleSection('returns')}
                        >
                            <IndicatorGrid
                                indicators={[
                                    { label: 'Total Return', value: allIndicators.returns.total_return, format: 'percentage', trend: getTrendDirection(allIndicators.returns.total_return) },
                                    { label: 'CAGR', value: allIndicators.returns.cagr, format: 'percentage' },
                                    { label: 'YTD Return', value: allIndicators.returns.ytd_return, format: 'percentage', trend: getTrendDirection(allIndicators.returns.ytd_return) },
                                    { label: 'MTD Return', value: allIndicators.returns.mtd_return, format: 'percentage', trend: getTrendDirection(allIndicators.returns.mtd_return) },
                                    { label: 'Realized P&L', value: allIndicators.returns.realized_pnl, format: 'currency' },
                                    { label: 'Unrealized P&L', value: allIndicators.returns.unrealized_pnl, format: 'currency' },
                                    { label: 'Total P&L', value: allIndicators.returns.total_pnl, format: 'currency' },
                                    { label: 'TWR', value: allIndicators.returns.twr, format: 'percentage' },
                                    { label: 'IRR', value: allIndicators.returns.irr, format: 'percentage' },
                                ]}
                                columns={3}
                            />
                            {allIndicators.returns.monthly_returns && (
                                <MonthlyReturnsTable monthlyReturns={allIndicators.returns.monthly_returns} />
                            )}
                        </IndicatorCategory>

                        <IndicatorCategory
                            title="Risk & Volatility"
                            description="Volatility measures and risk metrics"
                            isOpen={expandedSections.has('risk')}
                            onToggle={() => toggleSection('risk')}
                        >
                            <IndicatorGrid
                                indicators={[
                                    { label: 'Daily Volatility', value: allIndicators.risk.daily_volatility, format: 'percentage' },
                                    { label: 'Annualized Volatility', value: allIndicators.risk.annualized_volatility, format: 'percentage' },
                                    { label: 'Rolling Volatility (30d)', value: allIndicators.risk.rolling_volatility_30d, format: 'percentage' },
                                    { label: 'Upside Volatility', value: allIndicators.risk.upside_volatility, format: 'percentage' },
                                    { label: 'Downside Volatility', value: allIndicators.risk.downside_volatility, format: 'percentage' },
                                    { label: 'Semivariance', value: allIndicators.risk.semivariance, format: 'number' },
                                ]}
                                columns={3}
                            />
                        </IndicatorCategory>

                        <IndicatorCategory
                            title="Drawdown"
                            description="Drawdown analysis and recovery metrics"
                            isOpen={expandedSections.has('drawdown')}
                            onToggle={() => toggleSection('drawdown')}
                        >
                            <IndicatorGrid
                                indicators={[
                                    { label: 'Max Drawdown', value: allIndicators.drawdown.max_drawdown, format: 'percentage', trend: 'down' },
                                    { label: 'Max Drawdown Duration', value: allIndicators.drawdown.max_drawdown_duration || 0, format: 'days' },
                                    { label: 'Average Drawdown', value: allIndicators.drawdown.avg_drawdown, format: 'percentage' },
                                    { label: 'Ulcer Index', value: allIndicators.drawdown.ulcer_index || 0, format: 'number', description: 'Downside risk (depth & duration)' },
                                    { label: 'Recovery Days', value: allIndicators.drawdown.recovery_days || 0, format: 'days' },
                                    { label: 'Consecutive Loss Days', value: allIndicators.drawdown.consecutive_loss_days, format: 'days' },
                                    { label: 'Consecutive Gain Days', value: allIndicators.drawdown.consecutive_gain_days, format: 'days' },
                                ]}
                                columns={3}
                            />
                        </IndicatorCategory>

                        <IndicatorCategory
                            title="Risk-Adjusted Ratios"
                            description="Performance adjusted for risk"
                            isOpen={expandedSections.has('ratios')}
                            onToggle={() => toggleSection('ratios')}
                        >
                            <IndicatorGrid
                                indicators={[
                                    { label: 'Sharpe Ratio', value: allIndicators.risk_adjusted_ratios.sharpe, format: 'number', trend: getTrendDirection(allIndicators.risk_adjusted_ratios.sharpe) },
                                    { label: 'Rolling Sharpe (30d)', value: allIndicators.risk_adjusted_ratios.rolling_sharpe_30d, format: 'number' },
                                    { label: 'Sortino Ratio', value: allIndicators.risk_adjusted_ratios.sortino, format: 'number', trend: getTrendDirection(allIndicators.risk_adjusted_ratios.sortino) },
                                    { label: 'Calmar Ratio', value: allIndicators.risk_adjusted_ratios.calmar, format: 'number', trend: getTrendDirection(allIndicators.risk_adjusted_ratios.calmar) },
                                    ...(allIndicators.risk_adjusted_ratios.treynor ? [{ label: 'Treynor Ratio', value: allIndicators.risk_adjusted_ratios.treynor, format: 'number' as const, trend: getTrendDirection(allIndicators.risk_adjusted_ratios.treynor), description: 'Return per unit of systematic risk' }] : []),
                                    ...(allIndicators.risk_adjusted_ratios.omega ? [{ label: 'Omega Ratio', value: allIndicators.risk_adjusted_ratios.omega, format: 'number' as const, trend: getTrendDirection(allIndicators.risk_adjusted_ratios.omega), description: 'Probability weighted gains/losses' }] : []),
                                    ...(allIndicators.risk_adjusted_ratios.m2_measure ? [{ label: 'M² Measure', value: allIndicators.risk_adjusted_ratios.m2_measure, format: 'percentage' as const, trend: getTrendDirection(allIndicators.risk_adjusted_ratios.m2_measure), description: 'Risk-adjusted return vs benchmark' }] : []),
                                    ...(allIndicators.risk_adjusted_ratios.gain_to_pain ? [{ label: 'Gain-to-Pain Ratio', value: allIndicators.risk_adjusted_ratios.gain_to_pain, format: 'number' as const, trend: getTrendDirection(allIndicators.risk_adjusted_ratios.gain_to_pain), description: 'Total gains / total losses' }] : []),
                                    ...(allIndicators.risk_adjusted_ratios.ulcer_performance_index ? [{ label: 'Ulcer Performance Index', value: allIndicators.risk_adjusted_ratios.ulcer_performance_index, format: 'number' as const, trend: getTrendDirection(allIndicators.risk_adjusted_ratios.ulcer_performance_index), description: 'Return / Ulcer Index' }] : []),
                                ]}
                                columns={4}
                            />
                        </IndicatorCategory>

                        <IndicatorCategory
                            title="Tail Risk"
                            description="Extreme risk measures"
                            isOpen={expandedSections.has('tail_risk')}
                            onToggle={() => toggleSection('tail_risk')}
                        >
                            <IndicatorGrid
                                indicators={[
                                    { label: 'VaR (95%)', value: allIndicators.tail_risk.var_95, format: 'percentage', trend: 'down' },
                                    { label: 'CVaR (95%)', value: allIndicators.tail_risk.cvar_95, format: 'percentage', trend: 'down' },
                                    { label: 'Skewness', value: allIndicators.tail_risk.skewness, format: 'number' },
                                    { label: 'Kurtosis', value: allIndicators.tail_risk.kurtosis, format: 'number' },
                                    ...(allIndicators.tail_risk.tail_ratio ? [{ label: 'Tail Ratio', value: allIndicators.tail_risk.tail_ratio, format: 'number' as const, trend: getTrendDirection(allIndicators.tail_risk.tail_ratio), description: '95th / 5th percentile returns' }] : []),
                                ]}
                                columns={4}
                            />
                        </IndicatorCategory>

                        {allIndicators.allocation && (
                            <IndicatorCategory
                                title="Allocation"
                                description="Portfolio composition and concentration"
                                isOpen={expandedSections.has('allocation')}
                                onToggle={() => toggleSection('allocation')}
                            >
                                <AllocationBreakdown allocation={allIndicators.allocation} />
                            </IndicatorCategory>
                        )}

                        {allIndicators.risk_decomposition && (
                            <IndicatorCategory
                                title="Risk Decomposition"
                                description="Risk contribution by asset and sector"
                                isOpen={expandedSections.has('risk_decomposition')}
                                onToggle={() => toggleSection('risk_decomposition')}
                            >
                                <RiskDecomposition riskDecomp={allIndicators.risk_decomposition} />
                            </IndicatorCategory>
                        )}

                        {allIndicators.trading && (
                            <IndicatorCategory
                                title="Trading Metrics"
                                description="Transaction-based performance metrics"
                                isOpen={expandedSections.has('trading')}
                                onToggle={() => toggleSection('trading')}
                            >
                                <IndicatorGrid
                                    indicators={[
                                        { label: 'Trade Count', value: allIndicators.trading.trade_count, format: 'number' },
                                        { label: 'Win Rate', value: allIndicators.trading.win_rate, format: 'percentage', trend: getTrendDirection(allIndicators.trading.win_rate) },
                                        { label: 'Profit/Loss Ratio', value: allIndicators.trading.profit_loss_ratio, format: 'number', trend: getTrendDirection(allIndicators.trading.profit_loss_ratio) },
                                        ...(allIndicators.trading.profit_factor ? [{ label: 'Profit Factor', value: allIndicators.trading.profit_factor, format: 'number' as const, trend: getTrendDirection(allIndicators.trading.profit_factor), description: 'Gross profit / gross loss' }] : []),
                                        { label: 'Turnover Rate', value: allIndicators.trading.turnover_rate, format: 'percentage' as const },
                                        { label: 'Avg Holding Period', value: allIndicators.trading.avg_holding_period, format: 'days' as const },
                                        ...(allIndicators.trading.recovery_factor ? [{ label: 'Recovery Factor', value: allIndicators.trading.recovery_factor, format: 'number' as const, trend: getTrendDirection(allIndicators.trading.recovery_factor), description: 'Net profit / max drawdown' }] : []),
                                        ...(allIndicators.trading.kelly_criterion ? [{ label: 'Kelly Criterion', value: allIndicators.trading.kelly_criterion, format: 'percentage' as const, description: 'Optimal position size' }] : []),
                                        { label: 'Consecutive Wins', value: allIndicators.trading.consecutive_winning_trades, format: 'number' },
                                        { label: 'Consecutive Losses', value: allIndicators.trading.consecutive_losing_trades, format: 'number' },
                                    ]}
                                    columns={3}
                                />
                            </IndicatorCategory>
                        )}
                    </>
                )}
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

            {showDepositPrompt && suggestedDeposit && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-xl shadow-xl max-w-md">
                        <h3 className="text-lg font-semibold mb-3">Missing Initial Deposit</h3>
                        <p className="text-sm text-gray-600 mb-4">
                            This portfolio has no initial deposit transaction. Based on your trading history,
                            we suggest an initial deposit of <strong>${suggestedDeposit.toLocaleString()}</strong>
                            to ensure accurate performance calculations.
                        </p>
                        <div className="space-y-3">
                            <button
                                onClick={handleAcceptDeposit}
                                className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                            >
                                Add Suggested Deposit (${suggestedDeposit.toLocaleString()})
                            </button>
                            <button
                                onClick={() => setIsAddTxnOpen(true)}
                                className="w-full bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200"
                            >
                                Manually Enter Deposit Amount
                            </button>
                            <button
                                onClick={() => {
                                    setShowDepositPrompt(false);
                                    setDismissedDepositPrompt(true);
                                    localStorage.setItem(`dismissed-deposit-${id}`, 'true');
                                }}
                                className="w-full text-gray-500 text-sm hover:text-gray-700"
                            >
                                Dismiss (don't show again)
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </main>
    );
}
