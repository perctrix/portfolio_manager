'use client';

import { BenchmarkComparison } from '@/lib/api';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';

interface BenchmarkComparisonTableProps {
    comparison: BenchmarkComparison;
}

export function BenchmarkComparisonTable({ comparison }: BenchmarkComparisonTableProps) {
    const formatPercent = (value: number): string => {
        return `${(value * 100).toFixed(2)}%`;
    };

    const formatNumber = (value: number, decimals: number = 2): string => {
        return value.toFixed(decimals);
    };

    const renderMetricCell = (value: number, isPercent: boolean = false) => {
        const displayValue = isPercent ? formatPercent(value) : formatNumber(value);
        const isPositive = value > 0;
        const isNeutral = Math.abs(value) < 0.001;

        return (
            <div className="flex items-center gap-1">
                {!isNeutral && (
                    isPositive ? (
                        <TrendingUp className="w-4 h-4 text-green-600" />
                    ) : (
                        <TrendingDown className="w-4 h-4 text-red-600" />
                    )
                )}
                <span className={
                    isNeutral ? 'text-gray-600' :
                    isPositive ? 'text-green-600' :
                    'text-red-600'
                }>
                    {displayValue}
                </span>
            </div>
        );
    };

    const entries = Object.entries(comparison);

    if (entries.length === 0) {
        return (
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <div className="flex items-center gap-2 mb-4">
                    <Activity className="w-5 h-5 text-green-600" />
                    <h2 className="text-lg font-semibold">Benchmark Comparison</h2>
                </div>
                <p className="text-sm text-gray-400">No benchmark data available</p>
            </div>
        );
    }

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center gap-2 mb-4">
                <Activity className="w-5 h-5 text-green-600" />
                <h2 className="text-lg font-semibold">Benchmark Comparison</h2>
            </div>

            <p className="text-sm text-gray-500 mb-4">
                Portfolio performance relative to major market indices
            </p>

            <div className="overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-gray-200">
                            <th className="text-left py-3 px-3 font-semibold text-gray-700">Benchmark</th>
                            <th className="text-right py-3 px-3 font-semibold text-gray-700">Beta</th>
                            <th className="text-right py-3 px-3 font-semibold text-gray-700">Alpha</th>
                            <th className="text-right py-3 px-3 font-semibold text-gray-700">Treynor</th>
                            <th className="text-right py-3 px-3 font-semibold text-gray-700">M²</th>
                            <th className="text-right py-3 px-3 font-semibold text-gray-700">Up Cap</th>
                            <th className="text-right py-3 px-3 font-semibold text-gray-700">Down Cap</th>
                            <th className="text-right py-3 px-3 font-semibold text-gray-700">R²</th>
                            <th className="text-right py-3 px-3 font-semibold text-gray-700">Info Ratio</th>
                        </tr>
                    </thead>
                    <tbody>
                        {entries.map(([symbol, data]) => (
                            <tr key={symbol} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                                <td className="py-3 px-3">
                                    <div>
                                        <div className="font-medium text-gray-900">{data.name}</div>
                                        <div className="text-xs text-gray-400 font-mono">{symbol}</div>
                                    </div>
                                </td>
                                <td className="text-right py-3 px-3">
                                    {formatNumber(data.metrics.beta)}
                                </td>
                                <td className="text-right py-3 px-3">
                                    {renderMetricCell(data.metrics.alpha, true)}
                                </td>
                                <td className="text-right py-3 px-3">
                                    {data.metrics.treynor_ratio !== undefined ? renderMetricCell(data.metrics.treynor_ratio) : <span className="text-gray-400">-</span>}
                                </td>
                                <td className="text-right py-3 px-3">
                                    {data.metrics.m2_measure !== undefined ? renderMetricCell(data.metrics.m2_measure, true) : <span className="text-gray-400">-</span>}
                                </td>
                                <td className="text-right py-3 px-3">
                                    {data.metrics.upside_capture !== undefined ? (
                                        <span className={data.metrics.upside_capture > 100 ? 'text-green-600' : 'text-gray-600'}>
                                            {formatNumber(data.metrics.upside_capture)}%
                                        </span>
                                    ) : <span className="text-gray-400">-</span>}
                                </td>
                                <td className="text-right py-3 px-3">
                                    {data.metrics.downside_capture !== undefined ? (
                                        <span className={data.metrics.downside_capture < 100 ? 'text-green-600' : 'text-red-600'}>
                                            {formatNumber(data.metrics.downside_capture)}%
                                        </span>
                                    ) : <span className="text-gray-400">-</span>}
                                </td>
                                <td className="text-right py-3 px-3">
                                    <span className="text-gray-600">
                                        {formatNumber(data.metrics.r_squared, 3)}
                                    </span>
                                </td>
                                <td className="text-right py-3 px-3">
                                    {renderMetricCell(data.metrics.information_ratio)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                <div className="text-xs text-gray-600 space-y-1">
                    <p><strong>Beta:</strong> Systematic risk (1.0 = moves with benchmark)</p>
                    <p><strong>Alpha:</strong> Excess return above benchmark-predicted return</p>
                    <p><strong>Treynor:</strong> Return per unit of systematic risk (higher is better)</p>
                    <p><strong>M²:</strong> Risk-adjusted return vs benchmark in percentage terms</p>
                    <p><strong>Up Cap:</strong> Upside capture ratio ({'>'}100% = outperforms in bull markets)</p>
                    <p><strong>Down Cap:</strong> Downside capture ratio ({'<'}100% = outperforms in bear markets)</p>
                    <p><strong>R²:</strong> Proportion of variance explained by benchmark (0-1)</p>
                    <p><strong>Information Ratio:</strong> Excess return per unit of tracking error</p>
                </div>
            </div>
        </div>
    );
}
