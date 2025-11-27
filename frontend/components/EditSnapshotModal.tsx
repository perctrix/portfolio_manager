'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { TickerAutocomplete } from './TickerAutocomplete';

interface EditSnapshotModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (data: any[]) => Promise<void>;
    initialData?: any[];
}

export function EditSnapshotModal({ isOpen, onClose, onSubmit, initialData = [] }: EditSnapshotModalProps) {
    const t = useTranslations('SnapshotModal');
    const [positions, setPositions] = useState(initialData.length > 0 ? initialData : [{ symbol: '', quantity: 0, cost_basis: 0 }]);
    const [isSubmitting, setIsSubmitting] = useState(false);

    if (!isOpen) return null;

    const addRow = () => {
        setPositions([...positions, { symbol: '', quantity: 0, cost_basis: 0 }]);
    };

    const removeRow = (index: number) => {
        setPositions(positions.filter((_, i) => i !== index));
    };

    const updateRow = (index: number, field: string, value: any) => {
        const newPositions = [...positions];
        newPositions[index] = { ...newPositions[index], [field]: value };
        setPositions(newPositions);
    };

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setIsSubmitting(true);

        const validPositions = positions.filter(p => p.symbol && p.quantity !== 0).map(p => ({
            ...p,
            as_of: new Date().toISOString().slice(0, 10), // Today
            quantity: Number(p.quantity),
            cost_basis: Number(p.cost_basis)
        }));

        try {
            await onSubmit(validPositions);
            onClose();
        } catch (error) {
            console.error(error);
            alert(t('saveError'));
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-bold">{t('title')}</h2>
                    <button type="button" onClick={addRow} className="text-sm text-blue-600 hover:underline">{t('addRow')}</button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                        {positions.map((pos, index) => (
                            <div key={index} className="flex gap-3 items-end">
                                <div className="flex-1">
                                    <label className="block text-xs text-gray-500 mb-1">{t('symbol')}</label>
                                    <TickerAutocomplete
                                        value={pos.symbol}
                                        onChange={(value) => updateRow(index, 'symbol', value)}
                                        placeholder="AAPL"
                                    />
                                </div>
                                <div className="flex-1">
                                    <label className="block text-xs text-gray-500 mb-1">{t('quantity')}</label>
                                    <input
                                        type="number"
                                        step="any"
                                        value={pos.quantity}
                                        onChange={(e) => updateRow(index, 'quantity', e.target.value)}
                                        className="w-full px-3 py-2 border rounded-lg"
                                    />
                                </div>
                                <div className="flex-1">
                                    <label className="block text-xs text-gray-500 mb-1">{t('costBasisTotal')}</label>
                                    <input
                                        type="number"
                                        step="any"
                                        value={pos.cost_basis}
                                        onChange={(e) => updateRow(index, 'cost_basis', e.target.value)}
                                        className="w-full px-3 py-2 border rounded-lg"
                                    />
                                </div>
                                <button
                                    type="button"
                                    onClick={() => removeRow(index)}
                                    className="p-2 text-red-500 hover:bg-red-50 rounded-lg"
                                >
                                    ✕
                                </button>
                            </div>
                        ))}
                    </div>

                    <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
                        <button type="button" onClick={onClose} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">{t('cancel')}</button>
                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                        >
                            {isSubmitting ? t('saving') : t('saveChanges')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
