'use client';

import { useState, useMemo, useCallback, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea, Legend } from 'recharts';

interface NavChartProps {
    data: { date: string; value: number }[];
    comparisonData?: { [symbol: string]: { date: string; value: number }[] };
}

interface ChartPoint {
    date: string;
    value: number;
    normalizedValue?: number;
    [key: string]: number | string | undefined;
}

export function NavChart({ data, comparisonData = {} }: NavChartProps) {
    const [refAreaLeft, setRefAreaLeft] = useState<string | null>(null);
    const [refAreaRight, setRefAreaRight] = useState<string | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const rafRef = useRef<number | null>(null);
    const pendingRightRef = useRef<string | null>(null);

    if (!data || data.length === 0) {
        return (
            <div className="h-64 flex items-center justify-center bg-gray-50 rounded-xl border border-dashed border-gray-200 text-gray-400">
                No data available
            </div>
        );
    }

    const isComparisonMode = Object.keys(comparisonData).length > 0;

    const sampledData = useMemo(() => {
        if (data.length <= 300) return data;
        const step = Math.ceil(data.length / 300);
        return data.filter((_, idx) => idx % step === 0 || idx === data.length - 1);
    }, [data]);

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

        if (!isComparisonMode) {
            return sourceData;
        }

        const baseValue = sourceData[0]?.value || 1;

        const comparisonMaps = new Map<string, Map<string, number>>();
        Object.entries(comparisonData).forEach(([sym, history]) => {
            const dateMap = new Map<string, number>();
            const symBase = history[0]?.value || 1;
            history.forEach((h: any) => {
                const normalizedDate = h.date.substring(0, 10);
                dateMap.set(normalizedDate, ((h.value - symBase) / symBase) * 100);
            });
            comparisonMaps.set(sym, dateMap);
        });

        return sourceData.map(d => {
            const normalizedDate = d.date.substring(0, 10);
            const point: ChartPoint = {
                ...d,
                normalizedValue: ((d.value - baseValue) / baseValue) * 100
            };

            comparisonMaps.forEach((dateMap, sym) => {
                const value = dateMap.get(normalizedDate);
                if (value !== undefined) {
                    point[sym] = value;
                }
            });

            return point;
        });
    }, [sampledData, comparisonData, isComparisonMode]);

    const formatValue = (val: number): string => {
        if (isComparisonMode) return `${val.toFixed(2)}%`;
        return `$${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
    };

    const selectionInfo = useMemo(() => {
        if (!refAreaLeft || !refAreaRight) return null;

        const leftIndex = data.findIndex(d => d.date.substring(0, 10) === refAreaLeft.substring(0, 10));
        const rightIndex = data.findIndex(d => d.date.substring(0, 10) === refAreaRight.substring(0, 10));

        if (leftIndex < 0 || rightIndex < 0) return null;

        const start = data[Math.min(leftIndex, rightIndex)];
        const end = data[Math.max(leftIndex, rightIndex)];

        const startVal = isComparisonMode
            ? ((start.value - (data[0]?.value || 1)) / (data[0]?.value || 1)) * 100
            : start.value;
        const endVal = isComparisonMode
            ? ((end.value - (data[0]?.value || 1)) / (data[0]?.value || 1)) * 100
            : end.value;

        const change = endVal - startVal;
        const pctChange = isComparisonMode ? change : ((change / startVal) * 100);

        return {
            startDate: start.date,
            endDate: end.date,
            change,
            pctChange: isComparisonMode ? change : pctChange
        };
    }, [refAreaLeft, refAreaRight, data, isComparisonMode]);

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
