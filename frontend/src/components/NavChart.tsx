'use client';

import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea, Legend } from 'recharts';

interface NavChartProps {
    data: { date: string; value: number }[];
    comparisonData?: { [symbol: string]: { date: string; value: number }[] };
}

// Helper type for chart data
interface ChartPoint {
    date: string;
    value: number;
    normalizedValue?: number;
    [key: string]: any;
}

export function NavChart({ data, comparisonData = {} }: NavChartProps) {
    const [refAreaLeft, setRefAreaLeft] = useState<string | null>(null);
    const [refAreaRight, setRefAreaRight] = useState<string | null>(null);

    if (!data || data.length === 0) {
        return (
            <div className="h-64 flex items-center justify-center bg-gray-50 rounded-xl border border-dashed border-gray-200 text-gray-400">
                No data available
            </div>
        );
    }

    // Prepare data for chart
    // If comparisonData is present, we need to normalize everything to % change
    const isComparisonMode = Object.keys(comparisonData).length > 0;

    let chartData: ChartPoint[] = [...data];

    if (isComparisonMode) {
        // Normalize base data
        const baseValue = data[0]?.value || 1;
        chartData = data.map(d => ({
            ...d,
            normalizedValue: ((d.value - baseValue) / baseValue) * 100
        }));

        // Merge comparison data
        chartData = chartData.map(d => {
            const point: ChartPoint = { ...d };
            Object.entries(comparisonData).forEach(([sym, history]) => {
                // Find closest date match
                const match = history.find((h: any) => h.date === d.date);
                if (match) {
                    const symBase = history[0]?.value || 1;
                    point[sym] = ((match.value - symBase) / symBase) * 100;
                }
            });
            return point;
        });
    }

    const formatValue = (val: number) => {
        if (isComparisonMode) return `${val.toFixed(2)}%`;
        return `$${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
    };

    // Calculate change if range selected
    let selectionInfo = null;
    if (refAreaLeft && refAreaRight) {
        const leftIndex = chartData.findIndex(d => d.date === refAreaLeft);
        const rightIndex = chartData.findIndex(d => d.date === refAreaRight);

        if (leftIndex >= 0 && rightIndex >= 0) {
            const start = chartData[Math.min(leftIndex, rightIndex)];
            const end = chartData[Math.max(leftIndex, rightIndex)];

            const startVal = isComparisonMode ? (start.normalizedValue ?? 0) : start.value;
            const endVal = isComparisonMode ? (end.normalizedValue ?? 0) : end.value;

            const change = endVal - startVal;
            const pctChange = isComparisonMode ? change : ((change / startVal) * 100);

            selectionInfo = {
                startDate: start.date,
                endDate: end.date,
                change,
                pctChange: isComparisonMode ? change : pctChange
            };
        }
    }

    return (
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
                    onMouseDown={(e: any) => e && e.activeLabel && setRefAreaLeft(e.activeLabel)}
                    onMouseMove={(e: any) => refAreaLeft && e && e.activeLabel && setRefAreaRight(e.activeLabel)}
                    onMouseUp={() => {
                        if (refAreaLeft === refAreaRight) {
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
                        formatter={(value: number) => [formatValue(value), isComparisonMode ? 'Change' : 'NAV']}
                        labelFormatter={(label: any) => new Date(label).toLocaleDateString()}
                    />
                    <Legend />

                    <Line
                        type="monotone"
                        dataKey={isComparisonMode ? "normalizedValue" : "value"}
                        name="Portfolio"
                        stroke="#2563eb"
                        strokeWidth={2}
                        dot={false}
                        activeDot={{ r: 6 }}
                    />

                    {Object.keys(comparisonData).map((sym, idx) => (
                        <Line
                            key={sym}
                            type="monotone"
                            dataKey={sym}
                            name={sym}
                            stroke={`hsl(${(idx * 137.5) % 360}, 70%, 50%)`}
                            strokeWidth={2}
                            dot={false}
                        />
                    ))}

                    {refAreaLeft && refAreaRight ? (
                        <ReferenceArea x1={refAreaLeft} x2={refAreaRight} strokeOpacity={0.3} fill="#2563eb" fillOpacity={0.1} />
                    ) : null}
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}
