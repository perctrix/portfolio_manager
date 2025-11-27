'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { Activity, ChevronDown, ChevronUp } from 'lucide-react';
import { getBenchmarkList, Benchmark } from '@/lib/api';

interface BenchmarkPanelProps {
    selectedBenchmarks: Set<string>;
    onToggleBenchmark: (symbol: string) => void;
}

export function BenchmarkPanel({ selectedBenchmarks, onToggleBenchmark }: BenchmarkPanelProps) {
    const t = useTranslations('BenchmarkPanel');
    const [benchmarks, setBenchmarks] = useState<Benchmark[]>([]);
    const [loading, setLoading] = useState(true);
    const [categoryExpanded, setCategoryExpanded] = useState<{ [key: string]: boolean }>({
        us_indices: true,
        european_indices: false,
        asian_indices: false,
    });

    useEffect(() => {
        loadBenchmarks();
    }, []);

    async function loadBenchmarks() {
        try {
            const data = await getBenchmarkList();
            setBenchmarks(data);
        } catch (error) {
            console.error('Failed to load benchmarks:', error);
        } finally {
            setLoading(false);
        }
    }

    const groupedBenchmarks = benchmarks.reduce((acc, benchmark) => {
        if (!acc[benchmark.category]) {
            acc[benchmark.category] = [];
        }
        acc[benchmark.category].push(benchmark);
        return acc;
    }, {} as { [key: string]: Benchmark[] });

    const categoryNames: { [key: string]: string } = {
        us_indices: t('usIndices'),
        european_indices: t('europeanIndices'),
        asian_indices: t('asianIndices'),
    };

    const toggleCategory = (category: string) => {
        setCategoryExpanded(prev => ({ ...prev, [category]: !prev[category] }));
    };

    const handleClearAll = () => {
        selectedBenchmarks.forEach(symbol => onToggleBenchmark(symbol));
    };

    if (loading) {
        return (
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <div className="flex items-center gap-2 mb-4">
                    <Activity className="w-5 h-5 text-green-600" />
                    <h2 className="text-lg font-semibold">{t('title')}</h2>
                </div>
                <p className="text-sm text-gray-400">{t('loading')}</p>
            </div>
        );
    }

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center gap-2 mb-4">
                <Activity className="w-5 h-5 text-green-600" />
                <h2 className="text-lg font-semibold">{t('title')}</h2>
            </div>
            <p className="text-sm text-gray-500 mb-4">
                {t('description')}
            </p>

            <div className="space-y-3">
                {Object.entries(groupedBenchmarks).map(([category, items]) => (
                    <div key={category} className="border border-gray-200 rounded-lg overflow-hidden">
                        <button
                            onClick={() => toggleCategory(category)}
                            className="w-full px-4 py-2 bg-gray-50 hover:bg-gray-100 text-left font-medium text-sm flex justify-between items-center transition-colors"
                        >
                            <span className="flex items-center gap-2">
                                {categoryExpanded[category] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                {categoryNames[category] || category}
                            </span>
                            <span className="text-gray-400 text-xs">
                                {items.filter(b => selectedBenchmarks.has(b.symbol)).length}/{items.length} {t('selected')}
                            </span>
                        </button>

                        {categoryExpanded[category] && (
                            <div className="p-3 space-y-2">
                                {items.map(benchmark => (
                                    <label
                                        key={benchmark.symbol}
                                        className="flex items-start gap-3 p-2 rounded hover:bg-gray-50 cursor-pointer transition-colors"
                                    >
                                        <input
                                            type="checkbox"
                                            checked={selectedBenchmarks.has(benchmark.symbol)}
                                            onChange={() => onToggleBenchmark(benchmark.symbol)}
                                            className="mt-1 h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                                        />
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2">
                                                <span className="font-medium text-sm">{benchmark.name}</span>
                                                <span className="text-xs text-gray-400 font-mono">{benchmark.symbol}</span>
                                            </div>
                                            <p className="text-xs text-gray-500 mt-0.5">{benchmark.description}</p>
                                        </div>
                                    </label>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {selectedBenchmarks.size > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">
                            {selectedBenchmarks.size} {selectedBenchmarks.size > 1 ? t('benchmarksSelected') : t('benchmarkSelected')}
                        </span>
                        <button
                            onClick={handleClearAll}
                            className="text-green-600 hover:text-green-700 font-medium transition-colors"
                        >
                            {t('clearAll')}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
