'use client';

import { useState, useEffect } from 'react';
import { TickerAutocomplete } from './TickerAutocomplete';

interface AddTransactionModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (data: any) => Promise<void>;
    initialData?: any;
}

export function AddTransactionModal({ isOpen, onClose, onSubmit, initialData }: AddTransactionModalProps) {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [symbol, setSymbol] = useState('');
    const [side, setSide] = useState<'BUY' | 'SELL' | 'DEPOSIT' | 'WITHDRAW'>('BUY');

    useEffect(() => {
        if (isOpen) {
            if (initialData) {
                const actualSymbol = (initialData.side === 'DEPOSIT' || initialData.side === 'WITHDRAW') ? '' : (initialData.symbol || '');
                setSymbol(actualSymbol);
                setSide(initialData.side || 'BUY');
            } else {
                setSymbol('');
                setSide('BUY');
            }
        }
    }, [initialData, isOpen]);

    if (!isOpen) return null;

    const formatDatetimeLocal = (dateStr: string | undefined): string => {
        if (!dateStr) {
            return new Date().toISOString().slice(0, 16);
        }
        try {
            const date = new Date(dateStr);
            return date.toISOString().slice(0, 16);
        } catch {
            return new Date().toISOString().slice(0, 16);
        }
    };

    async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setIsSubmitting(true);
        const formData = new FormData(e.currentTarget);

        const data = {
            datetime: formData.get('datetime'),
            symbol: side === 'DEPOSIT' || side === 'WITHDRAW' ? 'CASH' : symbol,
            side: side,
            quantity: Number(formData.get('quantity')),
            price: side === 'DEPOSIT' || side === 'WITHDRAW' ? 1 : Number(formData.get('price')),
            fee: Number(formData.get('fee')),
        };

        try {
            await onSubmit(data);
            setSymbol('');
            onClose();
        } catch (error) {
            console.error(error);
            alert('Failed to add transaction');
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-md">
                <h2 className="text-xl font-bold mb-4">{initialData ? 'Edit Transaction' : 'Add Transaction'}</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Date & Time</label>
                        <input
                            type="datetime-local"
                            name="datetime"
                            required
                            key={initialData?.datetime || 'new'}
                            defaultValue={formatDatetimeLocal(initialData?.datetime)}
                            className="w-full px-3 py-2 border rounded-lg"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                        <select
                            value={side}
                            onChange={(e) => setSide(e.target.value as any)}
                            className="w-full px-3 py-2 border rounded-lg"
                        >
                            <option value="BUY">BUY</option>
                            <option value="SELL">SELL</option>
                            <option value="DEPOSIT">DEPOSIT</option>
                            <option value="WITHDRAW">WITHDRAW</option>
                        </select>
                    </div>

                    {(side === 'BUY' || side === 'SELL') && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Symbol</label>
                            <TickerAutocomplete
                                value={symbol}
                                onChange={setSymbol}
                                placeholder="AAPL"
                                required
                            />
                        </div>
                    )}
                    {(side === 'BUY' || side === 'SELL') ? (
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
                                <input
                                    type="number"
                                    step="any"
                                    name="quantity"
                                    required
                                    key={`quantity-${initialData?.datetime || 'new'}`}
                                    defaultValue={initialData?.quantity}
                                    className="w-full px-3 py-2 border rounded-lg"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Price</label>
                                <input
                                    type="number"
                                    step="any"
                                    name="price"
                                    required
                                    key={`price-${initialData?.datetime || 'new'}`}
                                    defaultValue={initialData?.price}
                                    className="w-full px-3 py-2 border rounded-lg"
                                />
                            </div>
                        </div>
                    ) : (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Amount</label>
                            <input
                                type="number"
                                step="any"
                                name="quantity"
                                required
                                key={`amount-${initialData?.datetime || 'new'}`}
                                defaultValue={initialData?.quantity}
                                className="w-full px-3 py-2 border rounded-lg"
                                placeholder="10000.00"
                            />
                        </div>
                    )}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Fee</label>
                        <input
                            type="number"
                            step="any"
                            name="fee"
                            key={`fee-${initialData?.datetime || 'new'}`}
                            defaultValue={initialData?.fee || "0"}
                            className="w-full px-3 py-2 border rounded-lg"
                        />
                    </div>

                    <div className="flex justify-end gap-3 mt-6">
                        <button type="button" onClick={onClose} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                        >
                            {isSubmitting ? (initialData ? 'Updating...' : 'Adding...') : (initialData ? 'Update Transaction' : 'Add Transaction')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
