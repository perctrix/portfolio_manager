'use client';

import { useEffect, useState, use } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useLocale, useTranslations } from 'next-intl';
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
import { Eye, EyeOff, Download, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import { getPortfolio, deletePortfolio, addTransaction, updateTransaction, deleteTransaction, updatePortfolioData } from '@/lib/storage';
import { calculatePortfolioFullStream, getPriceHistory, getBenchmarkHistory, BenchmarkComparison } from '@/lib/api';
import { getTrendDirection } from '@/utils/formatters';

export default function PortfolioDetail({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const t = useTranslations('Portfolio');
    const tIndicators = useTranslations('Indicators');
    const tDeposit = useTranslations('DepositPrompt');
    const currentLocale = useLocale();
    const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
    const [navHistory, setNavHistory] = useState<any[]>([]);
    const [cashHistory, setCashHistory] = useState<any[]>([]);
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
    const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['returns', 'positions', 'benchmarkPanel', 'benchmarkComparison']));
    const [loadingStep, setLoadingStep] = useState(0);
    const totalLoadingSteps = 6;
    const [suggestedDeposit, setSuggestedDeposit] = useState<number | null>(null);
    const [showDepositPrompt, setShowDepositPrompt] = useState(false);
    const [dismissedDepositPrompt, setDismissedDepositPrompt] = useState(false);
    const [editingTransactionIndex, setEditingTransactionIndex] = useState<number | null>(null);
    const [editingTransactionData, setEditingTransactionData] = useState<any | null>(null);

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
            const sortedData = portfolioData.meta?.type === 'transaction'
                ? portfolioData.data.map((item: any, index: number) => ({ ...item, _originalIndex: index }))
                    .sort((a, b) => {
                        const dateA = new Date(a.datetime || a.as_of);
                        const dateB = new Date(b.datetime || b.as_of);
                        return dateB.getTime() - dateA.getTime();
                    })
                : portfolioData.data;
            setHoldings(sortedData);

            if (portfolioData.data.length > 0) {
                await calculatePortfolioFullStream(
                    portfolioData.meta,
                    portfolioData.data,
                    {
                        onPricesLoaded: (data) => {
                            setLoadingStep(1);
                        },

                        onNavCalculated: (data) => {
                            setNavHistory(data.nav);
                            setCashHistory(data.cash || []);
                            setLoadingStep(2);
                        },

                        onIndicatorsBasicCalculated: (data) => {
                            setIndicators(data);
                            setLoadingStep(3);
                        },

                        onIndicatorsAllCalculated: (data) => {
                            setAllIndicators(data);
                            setLoadingStep(4);
                        },

                        onBenchmarkComparisonCalculated: (data) => {
                            setBenchmarkComparison(data.benchmarks);
                            setLoadingBenchmarkComparison(false);
                            setLoadingStep(5);
                        },

                        onComplete: (data) => {
                            setLoadingStep(6);

                            const isDismissed = localStorage.getItem(`dismissed-deposit-${id}`) === 'true';
                            if (data.suggested_initial_deposit &&
                                data.suggested_initial_deposit > 0 &&
                                !isDismissed) {
                                setSuggestedDeposit(data.suggested_initial_deposit);
                                setShowDepositPrompt(true);
                            }

                            if (data.failed_tickers && data.failed_tickers.length > 0) {
                                alert(`${t('tickerWarning')}\n${data.failed_tickers.join(', ')}\n\n${t('tickerWarningHint')}`);
                            }

                            setLoading(false);
                        },

                        onError: (error) => {
                            console.error('Stream error:', error);
                            alert(t('loadError') || 'Failed to load portfolio data');
                            setLoading(false);
                        }
                    }
                );
            } else {
                setNavHistory([]);
                setIndicators({});
                setAllIndicators(null);
                setBenchmarkComparison(null);
                setLoading(false);
            }

        } catch (error) {
            console.error(error);
            setLoading(false);
        }
    }

    async function handleAddTransaction(data: any) {
        try {
            if (editingTransactionIndex !== null) {
                updateTransaction(id, editingTransactionIndex, data);
                setEditingTransactionIndex(null);
            } else {
                addTransaction(id, data);
            }
            loadData();
        } catch (err) {
            console.error(err);
            throw new Error('Failed to add transaction');
        }
    }

    function handleEditTransaction(displayIndex: number) {
        const originalIndex = holdings[displayIndex]?._originalIndex ?? displayIndex;
        const portfolioData = getPortfolio(id);
        if (portfolioData && portfolioData.data[originalIndex]) {
            setEditingTransactionIndex(originalIndex);
            setEditingTransactionData(portfolioData.data[originalIndex]);
            setIsAddTxnOpen(true);
        }
    }

    function handleDeleteTransaction(displayIndex: number) {
        if (confirm(t('deleteTransactionConfirm'))) {
            try {
                const originalIndex = holdings[displayIndex]?._originalIndex ?? displayIndex;
                deleteTransaction(id, originalIndex);
                loadData();
            } catch (err) {
                console.error(err);
                alert(t('deleteTransactionError'));
            }
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

        // Set to first day of the month at 00:00
        const firstDayOfMonth = new Date(earliestDate.getFullYear(), earliestDate.getMonth(), 1);
        firstDayOfMonth.setHours(0, 0, 0, 0);

        const depositTxn = {
            datetime: firstDayOfMonth.toISOString().slice(0, 16),
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
            localStorage.setItem(`dismissed-deposit-${id}`, 'true');
            setDismissedDepositPrompt(true);
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
            alert(t('exportError'));
        }
    }

    function handleDelete() {
        if (!confirm(t('deleteConfirm'))) return;

        try {
            deletePortfolio(id);
            router.push(`/${currentLocale}`);
        } catch (e) {
            console.error(e);
            alert(t('deleteError'));
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
                    alert(t('unableToLoad', { symbol }));
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
                    alert(t('unableToLoadBenchmark', { symbol }));
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
    if (!portfolio) return <div className="p-8 text-center text-red-500">{t('notFound')}</div>;

    return (
        <main className="min-h-screen p-8 bg-gray-50 text-gray-900">
            <div className="max-w-6xl mx-auto space-y-8">
                <div className="flex justify-between items-start">
                    <div>
                        <Link href={`/${currentLocale}`} className="text-sm text-gray-500 hover:text-gray-900 mb-2 inline-block">{t('backToPortfolios')}</Link>
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
                            title={t('exportPortfolio')}
                        >
                            <Download size={20} />
                        </button>
                        <button
                            onClick={handleDelete}
                            className="text-gray-600 hover:text-red-600 p-2 rounded-lg hover:bg-gray-100 transition-colors"
                            title={t('deletePortfolio')}
                        >
                            <Trash2 size={20} />
                        </button>
                        <div className="w-px bg-gray-300 mx-1"></div>
                        {portfolio.type === 'transaction' ? (
                            <button
                                onClick={() => setIsAddTxnOpen(true)}
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                {t('addTransaction')}
                            </button>
                        ) : (
                            <button
                                onClick={() => setIsEditSnapshotOpen(true)}
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                {t('editPositions')}
                            </button>
                        )}
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <MetricsCard
                        title={t('totalReturn')}
                        value={`${(indicators.total_return * 100 || 0).toFixed(2)}%`}
                        trend={indicators.total_return > 0 ? 'up' : 'down'}
                    />
                    <MetricsCard
                        title={t('cagr')}
                        value={`${(indicators.cagr * 100 || 0).toFixed(2)}%`}
                    />
                    <MetricsCard
                        title={t('sharpeRatio')}
                        value={indicators.sharpe || 0}
                    />
                    <MetricsCard
                        title={t('maxDrawdown')}
                        value={`${(indicators.max_drawdown * 100 || 0).toFixed(2)}%`}
                        trend="down"
                    />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <MetricsCard title={t('sortino')} value={indicators.sortino || 0} />
                    <MetricsCard title={t('calmar')} value={indicators.calmar || 0} />
                    <MetricsCard title={t('var95')} value={`${(indicators.var_95 * 100 || 0).toFixed(2)}%`} />
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <div className="flex items-center justify-between mb-2">
                            <h3 className="text-sm text-gray-500">{t('beta')}</h3>
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
                            {selectedTickers.size > 0 || selectedBenchmarks.size > 0 ? t('performanceComparison') : t('navHistory')}
                        </h2>
                        {(selectedTickers.size > 0 || selectedBenchmarks.size > 0) && (
                            <span className="text-xs text-gray-500">{t('normalizedNote')}</span>
                        )}
                    </div>
                    <NavChart data={navHistory} cashData={cashHistory} comparisonData={comparisonData} benchmarkData={benchmarkData} />
                </div>

                <BenchmarkPanel
                    selectedBenchmarks={selectedBenchmarks}
                    onToggleBenchmark={toggleBenchmark}
                    isOpen={expandedSections.has('benchmarkPanel')}
                    onToggle={() => toggleSection('benchmarkPanel')}
                />

                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <button
                        onClick={() => toggleSection('positions')}
                        className="w-full p-6 flex items-center justify-between hover:bg-gray-50 transition-colors border-b border-gray-100"
                    >
                        <h2 className="text-lg font-semibold">
                            {portfolio.type === 'transaction' ? t('transactionHistory') : t('currentPositions')}
                        </h2>
                        <div className="text-gray-400">
                            {expandedSections.has('positions') ? (
                                <ChevronUp className="w-5 h-5" />
                            ) : (
                                <ChevronDown className="w-5 h-5" />
                            )}
                        </div>
                    </button>
                    {expandedSections.has('positions') && (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-gray-50 text-gray-500 font-medium">
                                    <tr>
                                        <th className="px-6 py-3 w-10"></th>
                                        {portfolio.type === 'transaction' ? (
                                            <>
                                                <th className="px-6 py-3">{t('date')}</th>
                                                <th className="px-6 py-3">{t('symbol')}</th>
                                                <th className="px-6 py-3">{t('side')}</th>
                                                <th className="px-6 py-3 text-right">{t('qty')}</th>
                                                <th className="px-6 py-3 text-right">{t('price')}</th>
                                                <th className="px-6 py-3 text-right">{t('fee')}</th>
                                                <th className="px-6 py-3 text-center">{t('actions')}</th>
                                            </>
                                        ) : (
                                            <>
                                                <th className="px-6 py-3">{t('symbol')}</th>
                                                <th className="px-6 py-3 text-right">{t('quantity')}</th>
                                                <th className="px-6 py-3 text-right">{t('costBasis')}</th>
                                                <th className="px-6 py-3">{t('asOf')}</th>
                                            </>
                                        )}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {holdings.length === 0 ? (
                                        <tr>
                                            <td colSpan={7} className="px-6 py-8 text-center text-gray-400">
                                                {t('noDataAvailable')}
                                            </td>
                                        </tr>
                                    ) : (
                                        holdings.map((row, i) => (
                                            <tr key={`${row.datetime || row.as_of}-${row.symbol}-${i}`} className="hover:bg-gray-50">
                                                <td className="px-6 py-3">
                                                    {row.symbol && row.symbol !== 'CASH' && (
                                                        <button
                                                            onClick={() => toggleTicker(row.symbol)}
                                                            className={`p-1 rounded hover:bg-gray-200 ${selectedTickers.has(row.symbol) ? 'text-blue-600' : 'text-gray-400'}`}
                                                            title={t('toggleOnChart')}
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
                                                        <td className="px-6 py-3">
                                                            <div className="flex items-center justify-center gap-2">
                                                                <button
                                                                    onClick={() => handleEditTransaction(i)}
                                                                    className="p-1 rounded hover:bg-blue-100 text-blue-600"
                                                                    title={t('editTransaction')}
                                                                >
                                                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                                                    </svg>
                                                                </button>
                                                                <button
                                                                    onClick={() => handleDeleteTransaction(i)}
                                                                    className="p-1 rounded hover:bg-red-100 text-red-600"
                                                                    title={t('deleteTransaction')}
                                                                >
                                                                    <Trash2 size={16} />
                                                                </button>
                                                            </div>
                                                        </td>
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
                    )}
                </div>

                {loadingBenchmarkComparison ? (
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <p className="text-sm text-gray-400">{t('loadingBenchmark')}</p>
                    </div>
                ) : benchmarkComparison && (
                    <BenchmarkComparisonTable 
                        comparison={benchmarkComparison}
                        isOpen={expandedSections.has('benchmarkComparison')}
                        onToggle={() => toggleSection('benchmarkComparison')}
                    />
                )}

                {allIndicators && (
                    <>
                        <IndicatorCategory
                            title={tIndicators('returns')}
                            description={tIndicators('returnsDesc')}
                            isOpen={expandedSections.has('returns')}
                            onToggle={() => toggleSection('returns')}
                        >
                            <IndicatorGrid
                                indicators={[
                                    { label: tIndicators('totalReturn'), value: allIndicators.returns.total_return, format: 'percentage', trend: getTrendDirection(allIndicators.returns.total_return) },
                                    { label: t('cagr'), value: allIndicators.returns.cagr, format: 'percentage' },
                                    { label: tIndicators('ytdReturn'), value: allIndicators.returns.ytd_return, format: 'percentage', trend: getTrendDirection(allIndicators.returns.ytd_return) },
                                    { label: tIndicators('mtdReturn'), value: allIndicators.returns.mtd_return, format: 'percentage', trend: getTrendDirection(allIndicators.returns.mtd_return) },
                                    { label: tIndicators('realizedPnl'), value: allIndicators.returns.realized_pnl, format: 'currency' },
                                    { label: tIndicators('unrealizedPnl'), value: allIndicators.returns.unrealized_pnl, format: 'currency' },
                                    { label: tIndicators('totalPnl'), value: allIndicators.returns.total_pnl, format: 'currency' },
                                    { label: tIndicators('twr'), value: allIndicators.returns.twr, format: 'percentage' },
                                    { label: tIndicators('irr'), value: allIndicators.returns.irr, format: 'percentage' },
                                ]}
                                columns={3}
                            />
                            {allIndicators.returns.monthly_returns && (
                                <MonthlyReturnsTable monthlyReturns={allIndicators.returns.monthly_returns} />
                            )}
                        </IndicatorCategory>

                        <IndicatorCategory
                            title={tIndicators('riskVolatility')}
                            description={tIndicators('riskVolatilityDesc')}
                            isOpen={expandedSections.has('risk')}
                            onToggle={() => toggleSection('risk')}
                        >
                            <IndicatorGrid
                                indicators={[
                                    { label: tIndicators('dailyVolatility'), value: allIndicators.risk.daily_volatility, format: 'percentage' },
                                    { label: tIndicators('annualizedVolatility'), value: allIndicators.risk.annualized_volatility, format: 'percentage' },
                                    { label: tIndicators('rollingVolatility30d'), value: allIndicators.risk.rolling_volatility_30d, format: 'percentage' },
                                    { label: tIndicators('upsideVolatility'), value: allIndicators.risk.upside_volatility, format: 'percentage' },
                                    { label: tIndicators('downsideVolatility'), value: allIndicators.risk.downside_volatility, format: 'percentage' },
                                    { label: tIndicators('semivariance'), value: allIndicators.risk.semivariance, format: 'number' },
                                ]}
                                columns={3}
                            />
                        </IndicatorCategory>

                        <IndicatorCategory
                            title={tIndicators('drawdown')}
                            description={tIndicators('drawdownDesc')}
                            isOpen={expandedSections.has('drawdown')}
                            onToggle={() => toggleSection('drawdown')}
                        >
                            <IndicatorGrid
                                indicators={[
                                    { label: t('maxDrawdown'), value: allIndicators.drawdown.max_drawdown, format: 'percentage', trend: 'down' },
                                    { label: tIndicators('maxDrawdownDuration'), value: allIndicators.drawdown.max_drawdown_duration || 0, format: 'days' },
                                    { label: tIndicators('averageDrawdown'), value: allIndicators.drawdown.avg_drawdown, format: 'percentage' },
                                    { label: tIndicators('ulcerIndex'), value: allIndicators.drawdown.ulcer_index || 0, format: 'number', description: tIndicators('ulcerIndexDesc') },
                                    { label: tIndicators('recoveryDays'), value: allIndicators.drawdown.recovery_days || 0, format: 'days' },
                                    { label: tIndicators('consecutiveLossDays'), value: allIndicators.drawdown.consecutive_loss_days, format: 'days' },
                                    { label: tIndicators('consecutiveGainDays'), value: allIndicators.drawdown.consecutive_gain_days, format: 'days' },
                                ]}
                                columns={3}
                            />
                        </IndicatorCategory>

                        <IndicatorCategory
                            title={tIndicators('riskAdjustedRatios')}
                            description={tIndicators('riskAdjustedRatiosDesc')}
                            isOpen={expandedSections.has('ratios')}
                            onToggle={() => toggleSection('ratios')}
                        >
                            <IndicatorGrid
                                indicators={[
                                    { label: t('sharpeRatio'), value: allIndicators.risk_adjusted_ratios.sharpe, format: 'number', trend: getTrendDirection(allIndicators.risk_adjusted_ratios.sharpe) },
                                    { label: tIndicators('rollingSharpe30d'), value: allIndicators.risk_adjusted_ratios.rolling_sharpe_30d, format: 'number' },
                                    { label: tIndicators('sortinoRatio'), value: allIndicators.risk_adjusted_ratios.sortino, format: 'number', trend: getTrendDirection(allIndicators.risk_adjusted_ratios.sortino) },
                                    { label: tIndicators('calmarRatio'), value: allIndicators.risk_adjusted_ratios.calmar, format: 'number', trend: getTrendDirection(allIndicators.risk_adjusted_ratios.calmar) },
                                    ...(allIndicators.risk_adjusted_ratios.treynor ? [{ label: tIndicators('treynorRatio'), value: allIndicators.risk_adjusted_ratios.treynor, format: 'number' as const, trend: getTrendDirection(allIndicators.risk_adjusted_ratios.treynor), description: tIndicators('treynorRatioDesc') }] : []),
                                    ...(allIndicators.risk_adjusted_ratios.omega ? [{ label: tIndicators('omegaRatio'), value: allIndicators.risk_adjusted_ratios.omega, format: 'number' as const, trend: getTrendDirection(allIndicators.risk_adjusted_ratios.omega), description: tIndicators('omegaRatioDesc') }] : []),
                                    ...(allIndicators.risk_adjusted_ratios.m2_measure ? [{ label: tIndicators('m2Measure'), value: allIndicators.risk_adjusted_ratios.m2_measure, format: 'percentage' as const, trend: getTrendDirection(allIndicators.risk_adjusted_ratios.m2_measure), description: tIndicators('m2MeasureDesc') }] : []),
                                    ...(allIndicators.risk_adjusted_ratios.gain_to_pain ? [{ label: tIndicators('gainToPain'), value: allIndicators.risk_adjusted_ratios.gain_to_pain, format: 'number' as const, trend: getTrendDirection(allIndicators.risk_adjusted_ratios.gain_to_pain), description: tIndicators('gainToPainDesc') }] : []),
                                    ...(allIndicators.risk_adjusted_ratios.ulcer_performance_index ? [{ label: tIndicators('ulcerPerformanceIndex'), value: allIndicators.risk_adjusted_ratios.ulcer_performance_index, format: 'number' as const, trend: getTrendDirection(allIndicators.risk_adjusted_ratios.ulcer_performance_index), description: tIndicators('ulcerPerformanceIndexDesc') }] : []),
                                ]}
                                columns={4}
                            />
                        </IndicatorCategory>

                        <IndicatorCategory
                            title={tIndicators('tailRisk')}
                            description={tIndicators('tailRiskDesc')}
                            isOpen={expandedSections.has('tail_risk')}
                            onToggle={() => toggleSection('tail_risk')}
                        >
                            <IndicatorGrid
                                indicators={[
                                    { label: t('var95'), value: allIndicators.tail_risk.var_95, format: 'percentage', trend: 'down' },
                                    { label: tIndicators('cvar95'), value: allIndicators.tail_risk.cvar_95, format: 'percentage', trend: 'down' },
                                    { label: tIndicators('skewness'), value: allIndicators.tail_risk.skewness, format: 'number' },
                                    { label: tIndicators('kurtosis'), value: allIndicators.tail_risk.kurtosis, format: 'number' },
                                    ...(allIndicators.tail_risk.tail_ratio ? [{ label: tIndicators('tailRatio'), value: allIndicators.tail_risk.tail_ratio, format: 'number' as const, trend: getTrendDirection(allIndicators.tail_risk.tail_ratio), description: tIndicators('tailRatioDesc') }] : []),
                                ]}
                                columns={4}
                            />
                        </IndicatorCategory>

                        {allIndicators.allocation && (
                            <IndicatorCategory
                                title={tIndicators('allocation')}
                                description={tIndicators('allocationDesc')}
                                isOpen={expandedSections.has('allocation')}
                                onToggle={() => toggleSection('allocation')}
                            >
                                <AllocationBreakdown allocation={allIndicators.allocation} />
                            </IndicatorCategory>
                        )}

                        {allIndicators.risk_decomposition && (
                            <IndicatorCategory
                                title={tIndicators('riskDecomposition')}
                                description={tIndicators('riskDecompositionDesc')}
                                isOpen={expandedSections.has('risk_decomposition')}
                                onToggle={() => toggleSection('risk_decomposition')}
                            >
                                <RiskDecomposition riskDecomp={allIndicators.risk_decomposition} />
                            </IndicatorCategory>
                        )}

                        {allIndicators.trading && (
                            <IndicatorCategory
                                title={tIndicators('tradingMetrics')}
                                description={tIndicators('tradingMetricsDesc')}
                                isOpen={expandedSections.has('trading')}
                                onToggle={() => toggleSection('trading')}
                            >
                                <IndicatorGrid
                                    indicators={[
                                        { label: tIndicators('tradeCount'), value: allIndicators.trading.trade_count, format: 'number' },
                                        { label: tIndicators('winRate'), value: allIndicators.trading.win_rate, format: 'percentage', trend: getTrendDirection(allIndicators.trading.win_rate) },
                                        { label: tIndicators('profitLossRatio'), value: allIndicators.trading.profit_loss_ratio, format: 'number', trend: getTrendDirection(allIndicators.trading.profit_loss_ratio) },
                                        ...(allIndicators.trading.profit_factor ? [{ label: tIndicators('profitFactor'), value: allIndicators.trading.profit_factor, format: 'number' as const, trend: getTrendDirection(allIndicators.trading.profit_factor), description: tIndicators('profitFactorDesc') }] : []),
                                        { label: tIndicators('turnoverRate'), value: allIndicators.trading.turnover_rate, format: 'percentage' as const },
                                        { label: tIndicators('avgHoldingPeriod'), value: allIndicators.trading.avg_holding_period, format: 'days' as const },
                                        ...(allIndicators.trading.recovery_factor ? [{ label: tIndicators('recoveryFactor'), value: allIndicators.trading.recovery_factor, format: 'number' as const, trend: getTrendDirection(allIndicators.trading.recovery_factor), description: tIndicators('recoveryFactorDesc') }] : []),
                                        ...(allIndicators.trading.kelly_criterion ? [{ label: tIndicators('kellyCriterion'), value: allIndicators.trading.kelly_criterion, format: 'percentage' as const, description: tIndicators('kellyCriterionDesc') }] : []),
                                        { label: tIndicators('consecutiveWins'), value: allIndicators.trading.consecutive_winning_trades, format: 'number' },
                                        { label: tIndicators('consecutiveLosses'), value: allIndicators.trading.consecutive_losing_trades, format: 'number' },
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
                onClose={() => {
                    setIsAddTxnOpen(false);
                    setEditingTransactionIndex(null);
                    setEditingTransactionData(null);
                }}
                onSubmit={handleAddTransaction}
                initialData={editingTransactionData}
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
                        <h3 className="text-lg font-semibold mb-3">{tDeposit('title')}</h3>
                        <p className="text-sm text-gray-600 mb-4">
                            {tDeposit('description')} <strong>${suggestedDeposit.toLocaleString()}</strong> {tDeposit('descriptionSuffix')}
                        </p>
                        <div className="space-y-3">
                            <button
                                onClick={handleAcceptDeposit}
                                className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                            >
                                {tDeposit('addSuggested')} (${suggestedDeposit.toLocaleString()})
                            </button>
                            <button
                                onClick={() => setIsAddTxnOpen(true)}
                                className="w-full bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200"
                            >
                                {tDeposit('manualEnter')}
                            </button>
                            <button
                                onClick={() => {
                                    setShowDepositPrompt(false);
                                    setDismissedDepositPrompt(true);
                                    localStorage.setItem(`dismissed-deposit-${id}`, 'true');
                                }}
                                className="w-full text-gray-500 text-sm hover:text-gray-700"
                            >
                                {tDeposit('dismiss')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </main>
    );
}
