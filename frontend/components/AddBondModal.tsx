'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { BondPosition, PaymentFrequency } from '@/types';

interface AddBondModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (bond: BondPosition) => Promise<void>;
    initialData?: BondPosition;
}

function generateBondId(): string {
    return `bond_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;
}

function formatDateForInput(dateStr: string | undefined): string {
    if (!dateStr) {
        return new Date().toISOString().slice(0, 10);
    }
    try {
        return dateStr.slice(0, 10);
    } catch {
        return new Date().toISOString().slice(0, 10);
    }
}

export function AddBondModal({ isOpen, onClose, onSubmit, initialData }: AddBondModalProps) {
    const t = useTranslations('BondModal');
    const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
    const [paymentFrequency, setPaymentFrequency] = useState<PaymentFrequency>(2);

    useEffect(() => {
        if (isOpen && initialData) {
            setPaymentFrequency(initialData.payment_frequency);
        } else if (isOpen) {
            setPaymentFrequency(2);
        }
    }, [initialData, isOpen]);

    if (!isOpen) return null;

    async function handleSubmit(e: React.FormEvent<HTMLFormElement>): Promise<void> {
        e.preventDefault();
        setIsSubmitting(true);

        const formData = new FormData(e.currentTarget);

        const bond: BondPosition = {
            id: initialData?.id || generateBondId(),
            name: formData.get('name') as string,
            face_value: Number(formData.get('face_value')),
            coupon_rate: Number(formData.get('coupon_rate')),
            maturity_date: formData.get('maturity_date') as string,
            payment_frequency: paymentFrequency,
            purchase_price: Number(formData.get('purchase_price')),
            purchase_quantity: Number(formData.get('purchase_quantity')),
            purchase_date: formData.get('purchase_date') as string,
            current_price: formData.get('current_price') ? Number(formData.get('current_price')) : undefined,
        };

        try {
            await onSubmit(bond);
            onClose();
        } catch (error) {
            console.error(error);
            alert(t('addError'));
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
                <h2 className="text-xl font-bold mb-4">
                    {initialData ? t('editTitle') : t('addTitle')}
                </h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            {t('name')}
                        </label>
                        <input
                            type="text"
                            name="name"
                            required
                            defaultValue={initialData?.name}
                            placeholder={t('namePlaceholder')}
                            className="w-full px-3 py-2 border rounded-lg"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('faceValue')}
                            </label>
                            <input
                                type="number"
                                step="any"
                                name="face_value"
                                required
                                defaultValue={initialData?.face_value || 1000}
                                className="w-full px-3 py-2 border rounded-lg"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('couponRate')}
                            </label>
                            <input
                                type="number"
                                step="any"
                                name="coupon_rate"
                                required
                                min="0"
                                defaultValue={initialData?.coupon_rate || 0}
                                placeholder="2.5"
                                className="w-full px-3 py-2 border rounded-lg"
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('maturityDate')}
                            </label>
                            <input
                                type="date"
                                name="maturity_date"
                                required
                                defaultValue={formatDateForInput(initialData?.maturity_date)}
                                className="w-full px-3 py-2 border rounded-lg"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('paymentFrequency')}
                            </label>
                            <select
                                value={paymentFrequency}
                                onChange={(e) => setPaymentFrequency(Number(e.target.value) as PaymentFrequency)}
                                className="w-full px-3 py-2 border rounded-lg"
                            >
                                <option value={0}>{t('frequencyZero')}</option>
                                <option value={1}>{t('frequencyAnnual')}</option>
                                <option value={2}>{t('frequencySemi')}</option>
                                <option value={4}>{t('frequencyQuarterly')}</option>
                                <option value={12}>{t('frequencyMonthly')}</option>
                            </select>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('purchasePrice')}
                            </label>
                            <input
                                type="number"
                                step="any"
                                name="purchase_price"
                                required
                                defaultValue={initialData?.purchase_price || 100}
                                placeholder="98.5"
                                className="w-full px-3 py-2 border rounded-lg"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('purchaseQuantity')}
                            </label>
                            <input
                                type="number"
                                step="any"
                                name="purchase_quantity"
                                required
                                min="0"
                                defaultValue={initialData?.purchase_quantity || 1}
                                className="w-full px-3 py-2 border rounded-lg"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            {t('purchaseDate')}
                        </label>
                        <input
                            type="date"
                            name="purchase_date"
                            required
                            defaultValue={formatDateForInput(initialData?.purchase_date)}
                            className="w-full px-3 py-2 border rounded-lg"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            {t('currentPrice')}
                        </label>
                        <input
                            type="number"
                            step="any"
                            name="current_price"
                            defaultValue={initialData?.current_price}
                            placeholder={t('currentPricePlaceholder')}
                            className="w-full px-3 py-2 border rounded-lg"
                        />
                        <p className="text-xs text-gray-500 mt-1">{t('currentPriceHint')}</p>
                    </div>

                    <div className="flex justify-end gap-3 mt-6">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                        >
                            {t('cancel')}
                        </button>
                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                        >
                            {isSubmitting
                                ? (initialData ? t('updating') : t('adding'))
                                : (initialData ? t('update') : t('add'))
                            }
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
