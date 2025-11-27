'use client';

import { useTranslations } from 'next-intl';
import { BenchmarkComparison } from '@/lib/api';
import { TrendingUp, TrendingDown, Activity, ChevronDown, ChevronUp } from 'lucide-react';

interface BenchmarkComparisonTableProps {
    comparison: BenchmarkComparison;
    isOpen: boolean;
    onToggle: () => void;
}

export function BenchmarkComparisonTable({ comparison, isOpen, onToggle }: BenchmarkComparisonTableProps) {
    const t = useTranslations('BenchmarkTable');
    const tPortfolio = useTranslations('Portfolio');

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
            <div className="flex items-center gap-1 justify-end">
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
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <button
                    onClick={onToggle}
                    className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                    <div className="flex items-center gap-2">
                        <Activity className="w-5 h-5 text-green-600" />
                        <h2 className="text-lg font-semibold">{t('title')}</h2>
                    </div>
                    <div className="text-gray-400">
                        {isOpen ? (
                            <ChevronUp className="w-5 h-5" />
                        ) : (
                            <ChevronDown className="w-5 h-5" />
                        )}
                    </div>
                </button>
                {isOpen && (
                    <div className="px-6 pb-6 pt-2 border-t border-gray-100">
                        <p className="text-sm text-gray-400">{t('noData')}</p>
                    </div>
                )}
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <button
                onClick={onToggle}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
            >
                <div className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-green-600" />
                    <h2 className="text-lg font-semibold">{t('title')}</h2>
                </div>
                <div className="text-gray-400">
                    {isOpen ? (
                        <ChevronUp className="w-5 h-5" />
                    ) : (
                        <ChevronDown className="w-5 h-5" />
                    )}
                </div>
            </button>

            {isOpen && (
                <div className="px-6 pb-6 pt-2 border-t border-gray-100">
                    <p className="text-sm text-gray-500 mb-4">
                        {t('description')}
                    </p>

                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-gray-200">
                                    <th className="text-left py-3 px-3 font-semibold text-gray-700">{t('benchmark')}</th>
                                    <th className="text-right py-3 px-3 font-semibold text-gray-700">{tPortfolio('beta')}</th>
                                    <th className="text-right py-3 px-3 font-semibold text-gray-700">{t('alpha')}</th>
                                    <th className="text-right py-3 px-3 font-semibold text-gray-700">{t('treynor')}</th>
                                    <th className="text-right py-3 px-3 font-semibold text-gray-700">{t('m2')}</th>
                                    <th className="text-right py-3 px-3 font-semibold text-gray-700">{t('upCap')}</th>
                                    <th className="text-right py-3 px-3 font-semibold text-gray-700">{t('downCap')}</th>
                                    <th className="text-right py-3 px-3 font-semibold text-gray-700">{t('rSquared')}</th>
                                    <th className="text-right py-3 px-3 font-semibold text-gray-700">{t('infoRatio')}</th>
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
                                            {data.metrics.treynor_ratio !== undefined ? renderMetricCell(data.metrics.treynor_ratio * 100) : <span className="text-gray-400">-</span>}
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
                            <p><strong>{tPortfolio('beta')}:</strong> {t('betaDesc')}</p>
                            <p><strong>{t('alpha')}:</strong> {t('alphaDesc')}</p>
                            <p><strong>{t('treynor')}:</strong> {t('treynorDesc')}</p>
                            <p><strong>{t('m2')}:</strong> {t('m2Desc')}</p>
                            <p><strong>{t('upCap')}:</strong> {t('upCapDesc')}</p>
                            <p><strong>{t('downCap')}:</strong> {t('downCapDesc')}</p>
                            <p><strong>{t('rSquared')}:</strong> {t('rSquaredDesc')}</p>
                            <p><strong>{t('infoRatio')}:</strong> {t('infoRatioDesc')}</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
