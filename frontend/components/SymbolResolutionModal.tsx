'use client';

import { useState, useCallback, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { AlertTriangle, Check, SkipForward } from 'lucide-react';
import type { UnresolvedSymbol, SymbolResolution } from '@/types';

interface SymbolResolutionModalProps {
    isOpen: boolean;
    unresolvedSymbols: UnresolvedSymbol[];
    onConfirm: (resolutions: SymbolResolution[]) => void;
    onCancel: () => void;
}

export function SymbolResolutionModal({
    isOpen,
    unresolvedSymbols,
    onConfirm,
    onCancel,
}: SymbolResolutionModalProps) {
    const t = useTranslations('SymbolResolution');

    const [resolutions, setResolutions] = useState<Record<string, string>>({});
    const [customInputs, setCustomInputs] = useState<Record<string, string>>({});
    const [skipped, setSkipped] = useState<Record<string, boolean>>({});

    // Initialize with first suggestion or empty
    useEffect(() => {
        const initial: Record<string, string> = {};
        unresolvedSymbols.forEach((item) => {
            if (item.suggestions.length > 0) {
                initial[item.original] = item.suggestions[0].symbol;
            }
        });
        setResolutions(initial);
        setCustomInputs({});
        setSkipped({});
    }, [unresolvedSymbols]);

    const handleSuggestionSelect = useCallback((original: string, resolved: string) => {
        setResolutions(prev => ({ ...prev, [original]: resolved }));
        setCustomInputs(prev => ({ ...prev, [original]: '' }));
        setSkipped(prev => ({ ...prev, [original]: false }));
    }, []);

    const handleCustomInputChange = useCallback((original: string, value: string) => {
        const upperValue = value.toUpperCase();
        setCustomInputs(prev => ({ ...prev, [original]: upperValue }));
        setResolutions(prev => ({ ...prev, [original]: upperValue }));
        setSkipped(prev => ({ ...prev, [original]: false }));
    }, []);

    const handleSkip = useCallback((original: string) => {
        setSkipped(prev => ({ ...prev, [original]: true }));
        setResolutions(prev => {
            const newResolutions = { ...prev };
            delete newResolutions[original];
            return newResolutions;
        });
    }, []);

    const handleConfirm = useCallback(() => {
        const result: SymbolResolution[] = unresolvedSymbols
            .filter((item) => !skipped[item.original] && resolutions[item.original]?.trim())
            .map((item) => ({
                original: item.original,
                resolved: resolutions[item.original].trim(),
            }));

        onConfirm(result);
    }, [unresolvedSymbols, resolutions, skipped, onConfirm]);

    const getSymbolStatus = (original: string): 'resolved' | 'skipped' | 'pending' => {
        if (skipped[original]) return 'skipped';
        if (resolutions[original]?.trim()) return 'resolved';
        return 'pending';
    };

    const allHandled = unresolvedSymbols.every(
        (item) => skipped[item.original] || resolutions[item.original]?.trim()
    );

    const resolvedCount = unresolvedSymbols.filter(
        (item) => !skipped[item.original] && resolutions[item.original]?.trim()
    ).length;

    const skippedCount = unresolvedSymbols.filter((item) => skipped[item.original]).length;

    if (!isOpen || unresolvedSymbols.length === 0) return null;

    return (
        <div
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="symbol-resolution-title"
        >
            <div className="bg-white rounded-xl w-full max-w-3xl max-h-[85vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="p-6 border-b bg-amber-50">
                    <div className="flex items-start gap-3">
                        <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
                        <div>
                            <h2 id="symbol-resolution-title" className="text-xl font-bold text-gray-900">
                                {t('title')}
                            </h2>
                            <p className="text-sm text-gray-600 mt-1">
                                {t('description')}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-auto p-6 space-y-6">
                    {unresolvedSymbols.map((item) => {
                        const status = getSymbolStatus(item.original);
                        return (
                            <div
                                key={item.original}
                                className={`border rounded-lg p-4 ${
                                    status === 'resolved'
                                        ? 'border-green-300 bg-green-50'
                                        : status === 'skipped'
                                        ? 'border-gray-300 bg-gray-50'
                                        : 'border-amber-300 bg-amber-50'
                                }`}
                            >
                                <div className="flex items-center gap-2 mb-3">
                                    <span className="font-mono font-bold text-lg">{item.original}</span>
                                    <span className="text-sm text-gray-500">({item.currency})</span>
                                    <div className="ml-auto flex items-center gap-2">
                                        {status === 'resolved' && (
                                            <span className="flex items-center gap-1 text-green-600 text-sm">
                                                <Check className="w-4 h-4" />
                                                {resolutions[item.original]}
                                            </span>
                                        )}
                                        {status === 'skipped' && (
                                            <span className="flex items-center gap-1 text-gray-500 text-sm">
                                                <SkipForward className="w-4 h-4" />
                                                {t('skipped')}
                                            </span>
                                        )}
                                    </div>
                                </div>

                                {/* Attempted variants */}
                                {item.attempted.length > 0 && (
                                    <p className="text-xs text-gray-400 mb-2">
                                        {t('attempted')}: {item.attempted.join(', ')}
                                    </p>
                                )}

                                {/* Suggestions */}
                                {item.suggestions.length > 0 && (
                                    <div className="mb-3">
                                        <p className="text-sm text-gray-600 mb-2">{t('suggestions')}:</p>
                                        <div className="flex flex-wrap gap-2">
                                            {item.suggestions.map((sug) => (
                                                <button
                                                    key={sug.symbol}
                                                    type="button"
                                                    onClick={() => handleSuggestionSelect(item.original, sug.symbol)}
                                                    className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                                                        resolutions[item.original] === sug.symbol && !customInputs[item.original]
                                                            ? 'bg-blue-600 text-white border-blue-600'
                                                            : 'bg-white hover:bg-gray-50 border-gray-300'
                                                    }`}
                                                >
                                                    <span className="font-mono font-medium">{sug.symbol}</span>
                                                    {sug.name && (
                                                        <span className="text-xs opacity-75 ml-1">
                                                            ({sug.name.substring(0, 20)}{sug.name.length > 20 ? '...' : ''})
                                                        </span>
                                                    )}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Custom input and skip button */}
                                <div className="flex items-center gap-2">
                                    <span className="text-sm text-gray-500">{t('orEnterManually')}:</span>
                                    <input
                                        type="text"
                                        value={customInputs[item.original] || ''}
                                        onChange={(e) => handleCustomInputChange(item.original, e.target.value)}
                                        placeholder="e.g., RHM.DE"
                                        className={`flex-1 px-3 py-1.5 border rounded-lg text-sm font-mono ${
                                            customInputs[item.original]
                                                ? 'border-blue-500 ring-2 ring-blue-200'
                                                : 'border-gray-300'
                                        }`}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => handleSkip(item.original)}
                                        className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                                            skipped[item.original]
                                                ? 'bg-gray-200 text-gray-700 border-gray-400'
                                                : 'bg-white hover:bg-gray-100 border-gray-300 text-gray-600'
                                        }`}
                                    >
                                        <SkipForward className="w-4 h-4 inline mr-1" />
                                        {t('skip')}
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Footer */}
                <div className="p-6 border-t bg-gray-50 flex justify-between items-center">
                    <p className="text-sm text-gray-500">
                        {resolvedCount > 0 && (
                            <span className="text-green-600 mr-2">
                                {t('resolvedCount', { count: resolvedCount })}
                            </span>
                        )}
                        {skippedCount > 0 && (
                            <span className="text-gray-500">
                                {t('skippedCount', { count: skippedCount })}
                            </span>
                        )}
                        {!allHandled && (
                            <span className="text-amber-600 ml-2">
                                {t('pendingCount', { count: unresolvedSymbols.length - resolvedCount - skippedCount })}
                            </span>
                        )}
                    </p>
                    <div className="flex gap-3">
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
                            disabled={!allHandled}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            {t('confirm')}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
