'use client';

import { useState, useMemo, useCallback, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea, Legend, ReferenceDot } from 'recharts';
import type { LiquidationEvent } from '@/types';

interface NavChartProps {
    data: { date: string; value: number }[];
    cashData?: { date: string; value: number }[];
    comparisonData?: { [symbol: string]: { date: string; value: number }[] };
    benchmarkData?: { [symbol: string]: { date: string; value: number }[] };
    liquidationEvents?: LiquidationEvent[];
}

interface ChartPoint {
    date: string;
    value: number;
    normalizedValue?: number;
    [key: string]: number | string | undefined;
}

type TimeRange = 'YTD' | '6M' | '1Y' | '2Y' | '3Y' | '5Y' | 'ALL' | 'CUSTOM';

const MIN_DATE = '2008-01-01';

const BENCHMARK_COLORS = [
    '#10b981',
    '#059669',
    '#047857',
    '#065f46',
    '#6ee7b7',
    '#34d399',
    '#14532d',
];

export function NavChart({ data, cashData = [], comparisonData = {}, benchmarkData = {}, liquidationEvents = [] }: NavChartProps) {
    const t = useTranslations('NavChart');
    const [refAreaLeft, setRefAreaLeft] = useState<string | null>(null);
    const [refAreaRight, setRefAreaRight] = useState<string | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const rafRef = useRef<number | null>(null);
    const pendingRightRef = useRef<string | null>(null);

    const [timeRange, setTimeRange] = useState<TimeRange>('ALL');
    const [customStartDate, setCustomStartDate] = useState<string>('');
    const [customEndDate, setCustomEndDate] = useState<string>('');
    const [showCash, setShowCash] = useState(false);

    if (!data || data.length === 0) {
        return (
            <div className="h-64 flex items-center justify-center bg-gray-50 rounded-xl border border-dashed border-gray-200 text-gray-400">
                {t('noData')}
            </div>
        );
    }

    const isComparisonMode = Object.keys(comparisonData).length > 0 || Object.keys(benchmarkData).length > 0;

    const filteredData = useMemo(() => {
        if (!data || data.length === 0) return [];
        if (timeRange === 'ALL') return data;

        const today = new Date();
        today.setHours(23, 59, 59, 999);
        let startDate: Date;

        if (timeRange === 'CUSTOM') {
            if (!customStartDate || !customEndDate) return data;
            startDate = new Date(customStartDate);
            const endDate = new Date(customEndDate);
            endDate.setHours(23, 59, 59, 999);

            return data.filter(d => {
                const date = new Date(d.date);
                return date >= startDate && date <= endDate;
            });
        }

        if (timeRange === 'YTD') {
            // Year-to-Date: from January 1st of current year to today
            startDate = new Date(today.getFullYear(), 0, 1);
            startDate.setHours(0, 0, 0, 0);

            return data.filter(d => {
                const date = new Date(d.date);
                return date >= startDate && date <= today;
            });
        }

        const monthsMap: Record<string, number> = {
            '6M': 6,
            '1Y': 12,
            '2Y': 24,
            '3Y': 36,
            '5Y': 60
        };

        startDate = new Date(today);
        startDate.setMonth(today.getMonth() - monthsMap[timeRange]);
        startDate.setHours(0, 0, 0, 0);

        return data.filter(d => {
            const date = new Date(d.date);
            return date >= startDate && date <= today;
        });
    }, [data, timeRange, customStartDate, customEndDate]);

    const maxDrawdown = useMemo(() => {
        if (filteredData.length === 0 || isComparisonMode) return null;

        let peak = filteredData[0].value;
        let peakDate = filteredData[0].date;
        let maxDD = 0;
        let maxDDStart = filteredData[0].date;
        let maxDDEnd = filteredData[0].date;
        let maxDDPeakValue = filteredData[0].value;
        let maxDDTroughValue = filteredData[0].value;

        for (let i = 1; i < filteredData.length; i++) {
            const current = filteredData[i].value;
            const currentDate = filteredData[i].date;

            if (current > peak) {
                peak = current;
                peakDate = currentDate;
            }

            const drawdown = (current - peak) / peak;
            if (drawdown < maxDD) {
                maxDD = drawdown;
                maxDDStart = peakDate;
                maxDDEnd = currentDate;
                maxDDPeakValue = peak;
                maxDDTroughValue = current;
            }
        }

        if (maxDD >= 0) return null;

        return {
            startDate: maxDDStart,
            endDate: maxDDEnd,
            drawdown: maxDD,
            peakValue: maxDDPeakValue,
            troughValue: maxDDTroughValue
        };
    }, [filteredData, isComparisonMode]);

    const sampledData = useMemo(() => {
        if (filteredData.length <= 300) return filteredData;

        const keyIndices = new Set<number>();
        keyIndices.add(0);
        keyIndices.add(filteredData.length - 1);

        if (maxDrawdown) {
            const peakIdx = filteredData.findIndex(d => d.date === maxDrawdown.startDate);
            const troughIdx = filteredData.findIndex(d => d.date === maxDrawdown.endDate);
            if (peakIdx >= 0) keyIndices.add(peakIdx);
            if (troughIdx >= 0) keyIndices.add(troughIdx);
        }

        const step = Math.ceil(filteredData.length / 300);
        return filteredData.filter((_, idx) =>
            idx % step === 0 || keyIndices.has(idx)
        );
    }, [filteredData, maxDrawdown]);

    const handleMouseMove = useCallback((e: any) => {
        if (!isDragging || !e || !e.activeLabel) return;

        pendingRightRef.current = e.activeLabel;

        if (rafRef.current === null) {
            rafRef.current = requestAnimationFrame(() => {
                if (pendingRightRef.current) {
                    setRefAreaRight(pendingRightRef.current);
                }
                rafRef.current = null;
            });
        }
    }, [isDragging]);

    const chartData: ChartPoint[] = useMemo(() => {
        const sourceData = sampledData;

        // Add cash data if available and enabled
        let dataWithCash = sourceData;
        if (showCash && cashData.length > 0 && !isComparisonMode) {
            const cashMap = new Map<string, number>();
            cashData.forEach((c: any) => {
                const normalizedDate = c.date.substring(0, 10);
                cashMap.set(normalizedDate, c.value);
            });

            dataWithCash = sourceData.map(d => {
                const normalizedDate = d.date.substring(0, 10);
                const cashValue = cashMap.get(normalizedDate);
                if (cashValue !== undefined) {
                    return { ...d, cash: cashValue };
                }
                return d;
            });
        }

        if (!isComparisonMode) {
            return dataWithCash;
        }

        const baseValue = sourceData[0]?.value || 1;
        const startDate = sourceData[0]?.date;
        const endDate = sourceData[sourceData.length - 1]?.date;

        const comparisonMaps = new Map<string, Map<string, number>>();
        Object.entries(comparisonData).forEach(([sym, history]) => {
            const filteredHistory = history.filter((h: any) => {
                const hDate = h.date.substring(0, 10);
                return hDate >= startDate && hDate <= endDate;
            });

            if (filteredHistory.length === 0) return;

            const dateMap = new Map<string, number>();
            const symBase = filteredHistory[0]?.value || 1;
            filteredHistory.forEach((h: any) => {
                const normalizedDate = h.date.substring(0, 10);
                dateMap.set(normalizedDate, ((h.value - symBase) / symBase) * 100);
            });
            comparisonMaps.set(`ticker_${sym}`, dateMap);
        });

        const benchmarkMaps = new Map<string, Map<string, number>>();
        Object.entries(benchmarkData).forEach(([sym, history]) => {
            const filteredHistory = history.filter((h: any) => {
                const hDate = h.date.substring(0, 10);
                return hDate >= startDate && hDate <= endDate;
            });

            if (filteredHistory.length === 0) return;

            const dateMap = new Map<string, number>();
            const symBase = filteredHistory[0]?.value || 1;
            filteredHistory.forEach((h: any) => {
                const normalizedDate = h.date.substring(0, 10);
                dateMap.set(normalizedDate, ((h.value - symBase) / symBase) * 100);
            });
            benchmarkMaps.set(`benchmark_${sym}`, dateMap);
        });

        return sourceData.map(d => {
            const normalizedDate = d.date.substring(0, 10);
            const point: ChartPoint = {
                ...d,
                normalizedValue: ((d.value - baseValue) / baseValue) * 100
            };

            comparisonMaps.forEach((dateMap, key) => {
                const value = dateMap.get(normalizedDate);
                if (value !== undefined) {
                    point[key] = value;
                }
            });

            benchmarkMaps.forEach((dateMap, key) => {
                const value = dateMap.get(normalizedDate);
                if (value !== undefined) {
                    point[key] = value;
                }
            });

            return point;
        });
    }, [sampledData, comparisonData, benchmarkData, isComparisonMode, showCash, cashData]);

    const formatValue = (val: number): string => {
        if (isComparisonMode) return `${val.toFixed(2)}%`;
        return `$${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
    };

    const selectionInfo = useMemo(() => {
        if (!refAreaLeft || !refAreaRight) return null;

        const leftIndex = filteredData.findIndex(d => d.date.substring(0, 10) === refAreaLeft.substring(0, 10));
        const rightIndex = filteredData.findIndex(d => d.date.substring(0, 10) === refAreaRight.substring(0, 10));

        if (leftIndex < 0 || rightIndex < 0) return null;

        const start = filteredData[Math.min(leftIndex, rightIndex)];
        const end = filteredData[Math.max(leftIndex, rightIndex)];

        const startVal = isComparisonMode
            ? ((start.value - (filteredData[0]?.value || 1)) / (filteredData[0]?.value || 1)) * 100
            : start.value;
        const endVal = isComparisonMode
            ? ((end.value - (filteredData[0]?.value || 1)) / (filteredData[0]?.value || 1)) * 100
            : end.value;

        const change = endVal - startVal;
        const pctChange = isComparisonMode ? change : ((change / startVal) * 100);

        return {
            startDate: start.date,
            endDate: end.date,
            change,
            pctChange: isComparisonMode ? change : pctChange
        };
    }, [refAreaLeft, refAreaRight, filteredData, isComparisonMode]);

    const timeRanges: TimeRange[] = ['YTD', '6M', '1Y', '2Y', '3Y', '5Y', 'ALL', 'CUSTOM'];

    const handleTimeRangeChange = (range: TimeRange) => {
        setTimeRange(range);
        if (range !== 'CUSTOM') {
            setCustomStartDate('');
            setCustomEndDate('');
        }
    };

    const handleCustomDateApply = () => {
        if (customStartDate && customEndDate) {
            const start = new Date(customStartDate);
            const end = new Date(customEndDate);
            const minAllowed = new Date(MIN_DATE);

            if (start < minAllowed) {
                alert(`${t('startDateError')} ${MIN_DATE}`);
                return;
            }

            if (start >= end) {
                alert(t('endDateError'));
                return;
            }

            setTimeRange('CUSTOM');
        }
    };

    const getTodayString = () => {
        const today = new Date();
        return today.toISOString().split('T')[0];
    };

    return (
        <div className="w-full space-y-4">
            <div className="flex flex-wrap items-center gap-3">
                <div className="flex gap-2">
                    {timeRanges.map((range) => (
                        <button
                            key={range}
                            onClick={() => handleTimeRangeChange(range)}
                            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                                timeRange === range
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                        >
                            {range}
                        </button>
                    ))}
                </div>

                {!isComparisonMode && cashData.length > 0 && (
                    <button
                        onClick={() => setShowCash(!showCash)}
                        className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                            showCash
                                ? 'bg-green-600 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                        title="Toggle cash display"
                    >
                        {showCash ? t('hideCash') : t('showCash')}
                    </button>
                )}

                {timeRange === 'CUSTOM' && (
                    <div className="flex items-center gap-2 ml-4">
                        <label className="text-sm text-gray-600">{t('from')}</label>
                        <input
                            type="date"
                            value={customStartDate}
                            onChange={(e) => setCustomStartDate(e.target.value)}
                            min={MIN_DATE}
                            max={getTodayString()}
                            className="px-2 py-1 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <label className="text-sm text-gray-600">{t('to')}</label>
                        <input
                            type="date"
                            value={customEndDate}
                            onChange={(e) => setCustomEndDate(e.target.value)}
                            min={customStartDate || MIN_DATE}
                            max={getTodayString()}
                            className="px-2 py-1 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <button
                            onClick={handleCustomDateApply}
                            disabled={!customStartDate || !customEndDate}
                            className="px-3 py-1 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                        >
                            {t('apply')}
                        </button>
                    </div>
                )}
            </div>

            <div className="h-96 w-full relative select-none">
                {selectionInfo && (
                    <div className="absolute top-2 right-16 z-10 bg-white/90 backdrop-blur p-3 rounded-lg shadow-lg border border-gray-200 text-sm">
                        <div className="font-medium text-gray-500 mb-1">
                            {new Date(selectionInfo.startDate).toLocaleDateString()} - {new Date(selectionInfo.endDate).toLocaleDateString()}
                        </div>
                        <div className="flex items-baseline gap-2">
                            <span className={`text-lg font-bold ${selectionInfo.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {selectionInfo.change >= 0 ? '+' : ''}{formatValue(selectionInfo.change)}
                            </span>
                            {!isComparisonMode && (
                                <span className={`text-xs ${selectionInfo.pctChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                    ({selectionInfo.pctChange >= 0 ? '+' : ''}{selectionInfo.pctChange.toFixed(2)}%)
                                </span>
                            )}
                        </div>
                    </div>
                )}

            <ResponsiveContainer width="100%" height="100%">
                <LineChart
                    data={chartData}
                    margin={{ top: 20, right: 20, bottom: 20, left: 0 }}
                    onMouseDown={(e: any) => {
                        if (e && e.activeLabel) {
                            setIsDragging(true);
                            setRefAreaLeft(e.activeLabel);
                            setRefAreaRight(null);
                        }
                    }}
                    onMouseMove={handleMouseMove}
                    onMouseUp={() => {
                        setIsDragging(false);
                        setRefAreaLeft(null);
                        setRefAreaRight(null);
                    }}
                    onMouseLeave={() => {
                        if (isDragging) {
                            setIsDragging(false);
                            setRefAreaLeft(null);
                            setRefAreaRight(null);
                        }
                    }}
                >
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                    <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12, fill: '#9ca3af' }}
                        axisLine={false}
                        tickLine={false}
                        minTickGap={30}
                        tickFormatter={(str: any) => new Date(str).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                    />
                    <YAxis
                        tick={{ fontSize: 12, fill: '#9ca3af' }}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={(val: any) => isComparisonMode ? `${val.toFixed(0)}%` : `$${val.toLocaleString()}`}
                        domain={['auto', 'auto']}
                    />
                    <Tooltip
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        formatter={(value: number) => [formatValue(value), isComparisonMode ? t('change') : t('nav')]}
                        labelFormatter={(label: any) => new Date(label).toLocaleDateString()}
                    />
                    <Legend />

                    <Line
                        type="monotone"
                        dataKey={isComparisonMode ? "normalizedValue" : "value"}
                        name={t('portfolio')}
                        stroke="#2563eb"
                        strokeWidth={2}
                        dot={false}
                        activeDot={{ r: 6 }}
                    />

                    {showCash && !isComparisonMode && (
                        <Line
                            type="monotone"
                            dataKey="cash"
                            name={t('cash')}
                            stroke="#10b981"
                            strokeWidth={2}
                            strokeDasharray="5 5"
                            dot={false}
                            activeDot={{ r: 6 }}
                        />
                    )}

                    {Object.keys(comparisonData).map((sym, idx) => (
                        <Line
                            key={`ticker_${sym}`}
                            type="monotone"
                            dataKey={`ticker_${sym}`}
                            name={sym}
                            stroke={`hsl(${(idx * 137.5) % 360}, 70%, 50%)`}
                            strokeWidth={2}
                            dot={false}
                        />
                    ))}

                    {Object.keys(benchmarkData).map((sym, idx) => (
                        <Line
                            key={`benchmark_${sym}`}
                            type="monotone"
                            dataKey={`benchmark_${sym}`}
                            name={sym}
                            stroke={BENCHMARK_COLORS[idx % BENCHMARK_COLORS.length]}
                            strokeWidth={2}
                            strokeDasharray="5 5"
                            dot={false}
                        />
                    ))}

                    {refAreaLeft && refAreaRight ? (
                        <ReferenceArea x1={refAreaLeft} x2={refAreaRight} strokeOpacity={0.3} fill="#2563eb" fillOpacity={0.1} />
                    ) : null}

                    {maxDrawdown && (
                        <>
                            <ReferenceDot
                                x={maxDrawdown.startDate}
                                y={maxDrawdown.peakValue}
                                r={6}
                                fill="#ef4444"
                                stroke="#fff"
                                strokeWidth={2}
                                label={{
                                    value: 'Peak',
                                    position: 'top',
                                    fill: '#ef4444',
                                    fontSize: 11,
                                    fontWeight: 'bold'
                                }}
                            />
                            <ReferenceDot
                                x={maxDrawdown.endDate}
                                y={maxDrawdown.troughValue}
                                r={6}
                                fill="#ef4444"
                                stroke="#fff"
                                strokeWidth={2}
                                label={{
                                    value: `${(maxDrawdown.drawdown * 100).toFixed(2)}%`,
                                    position: 'bottom',
                                    fill: '#ef4444',
                                    fontSize: 11,
                                    fontWeight: 'bold'
                                }}
                            />
                        </>
                    )}

                    {/* Liquidation event markers */}
                    {!isComparisonMode && liquidationEvents.map((event, idx) => {
                        const dataPoint = chartData.find(d => d.date.substring(0, 10) === event.date.substring(0, 10));
                        if (!dataPoint) return null;
                        return (
                            <ReferenceDot
                                key={`liquidation-${idx}`}
                                x={event.date}
                                y={dataPoint.value}
                                r={8}
                                fill="#f59e0b"
                                stroke="#fff"
                                strokeWidth={2}
                                label={{
                                    value: event.symbol,
                                    position: 'top',
                                    fill: '#f59e0b',
                                    fontSize: 10,
                                    fontWeight: 'bold'
                                }}
                            />
                        );
                    })}
                </LineChart>
            </ResponsiveContainer>
            </div>
        </div>
    );
}
