import React from 'react';

interface MetricsCardProps {
    title: string;
    value: string | number;
    subValue?: string;
    trend?: 'up' | 'down' | 'neutral';
}

export function MetricsCard({ title, value, subValue, trend }: MetricsCardProps) {
    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-sm font-medium text-gray-500 mb-2">{title}</h3>
            <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-gray-900">
                    {typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : value}
                </span>
                {subValue && (
                    <span className={`text-sm ${trend === 'up' ? 'text-green-600' :
                            trend === 'down' ? 'text-red-600' : 'text-gray-500'
                        }`}>
                        {subValue}
                    </span>
                )}
            </div>
        </div>
    );
}
