'use client';

import { useState, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { AlertTriangle, DollarSign, Pause, Trash2, ChevronDown } from 'lucide-react';
import type { StaleTicker, StaleTickerAction, StaleTickerHandling } from '@/types';

interface StaleTickerModalProps {
    isOpen: boolean;
    staleTickers: StaleTicker[];
    currency: string;
    onConfirm: (handling: StaleTickerHandling[]) => void;
    onCancel: () => void;
}

const ACTION_OPTIONS: { value: StaleTickerAction; icon: React.ReactNode }[] = [
    { value: 'liquidate', icon: <DollarSign className="w-4 h-4" /> },
    { value: 'freeze', icon: <Pause className="w-4 h-4" /> },
    { value: 'remove', icon: <Trash2 className="w-4 h-4" /> },
];

export function StaleTickerModal({
    isOpen,
    staleTickers,
    currency,
    onConfirm,
    onCancel,
}: StaleTickerModalProps) {
    const t = useTranslations('StaleTickerModal');
    const [actions, setActions] = useState<Record<string, StaleTickerAction>>(() => {
        const initial: Record<string, StaleTickerAction> = {};
        staleTickers.forEach((ticker) => {
            initial[ticker.symbol] = 'liquidate';
        });
        return initial;
    });

    const handleActionChange = useCallback((symbol: string, action: StaleTickerAction) => {
        setActions((prev) => ({ ...prev, [symbol]: action }));
    }, []);

    const handleApplyToAll = useCallback((action: StaleTickerAction) => {
        const newActions: Record<string, StaleTickerAction> = {};
        staleTickers.forEach((ticker) => {
            newActions[ticker.symbol] = action;
        });
        setActions(newActions);
    }, [staleTickers]);

    const handleConfirm = useCallback(() => {
        const handling: StaleTickerHandling[] = staleTickers.map((ticker) => ({
            symbol: ticker.symbol,
            action: actions[ticker.symbol] || 'liquidate',
        }));
        onConfirm(handling);
    }, [staleTickers, actions, onConfirm]);

    const formatCurrency = (value: number): string => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency || 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(value);
    };

    const formatDate = (dateStr: string): string => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    };

    if (!isOpen || staleTickers.length === 0) return null;

    return (
        <div
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="stale-ticker-title"
        >
            <div className="bg-white rounded-xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="p-6 border-b bg-amber-50">
                    <div className="flex items-start gap-3">
                        <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
                        <div>
                            <h2 id="stale-ticker-title" className="text-xl font-bold text-gray-900">
                                {t('title')}
                            </h2>
                            <p className="text-sm text-gray-600 mt-1">
                                {t('description')}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-auto p-6">
                    {/* Quick apply buttons */}
                    <div className="mb-4 flex items-center gap-2">
                        <span className="text-sm text-gray-600">{t('applyToAll')}:</span>
                        <div className="flex gap-2">
                            {ACTION_OPTIONS.map(({ value, icon }) => (
                                <button
                                    key={value}
                                    type="button"
                                    onClick={() => handleApplyToAll(value)}
                                    className="inline-flex items-center gap-1 px-3 py-1.5 text-sm border rounded-lg hover:bg-gray-50 transition-colors"
                                >
                                    {icon}
                                    {t(`action.${value}`)}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Ticker list */}
                    <div className="border rounded-lg overflow-hidden">
                        <table className="w-full">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">
                                        {t('column.symbol')}
                                    </th>
                                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">
                                        {t('column.lastDate')}
                                    </th>
                                    <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">
                                        {t('column.lastPrice')}
                                    </th>
                                    <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">
                                        {t('column.quantity')}
                                    </th>
                                    <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">
                                        {t('column.marketValue')}
                                    </th>
                                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">
                                        {t('column.action')}
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y">
                                {staleTickers.map((ticker) => (
                                    <tr key={ticker.symbol} className="hover:bg-gray-50">
                                        <td className="px-4 py-3">
                                            <span className="font-mono font-medium">{ticker.symbol}</span>
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-600">
                                            {formatDate(ticker.last_date)}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-right font-mono">
                                            {formatCurrency(ticker.last_price)}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-right font-mono">
                                            {ticker.quantity.toLocaleString()}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-right font-mono font-medium">
                                            {formatCurrency(ticker.market_value)}
                                        </td>
                                        <td className="px-4 py-3">
                                            <div className="relative">
                                                <select
                                                    value={actions[ticker.symbol] || 'liquidate'}
                                                    onChange={(e) =>
                                                        handleActionChange(ticker.symbol, e.target.value as StaleTickerAction)
                                                    }
                                                    className="w-full appearance-none pl-3 pr-8 py-1.5 text-sm border rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                                >
                                                    <option value="liquidate">{t('action.liquidate')}</option>
                                                    <option value="freeze">{t('action.freeze')}</option>
                                                    <option value="remove">{t('action.remove')}</option>
                                                </select>
                                                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Action descriptions */}
                    <div className="mt-4 space-y-2 text-sm text-gray-600">
                        <p className="flex items-center gap-2">
                            <DollarSign className="w-4 h-4 text-green-600" />
                            <strong>{t('action.liquidate')}:</strong> {t('actionDesc.liquidate')}
                        </p>
                        <p className="flex items-center gap-2">
                            <Pause className="w-4 h-4 text-blue-600" />
                            <strong>{t('action.freeze')}:</strong> {t('actionDesc.freeze')}
                        </p>
                        <p className="flex items-center gap-2">
                            <Trash2 className="w-4 h-4 text-red-600" />
                            <strong>{t('action.remove')}:</strong> {t('actionDesc.remove')}
                        </p>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-6 border-t bg-gray-50 flex justify-end gap-3">
                    <button
                        type="button"
                        onClick={onCancel}
                        className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
                    >
                        {t('cancel')}
                    </button>
                    <button
                        type="button"
                        onClick={handleConfirm}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        {t('confirm')}
                    </button>
                </div>
            </div>
        </div>
    );
}
