'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useLocale, useTranslations } from 'next-intl';
import { PortfolioType, Portfolio } from '@/types';
import { savePortfolio } from '@/lib/storage';

export default function CreatePortfolio() {
    const t = useTranslations('Create');
    const locale = useLocale();
    const router = useRouter();
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setIsSubmitting(true);
        setError(null);

        const formData = new FormData(e.currentTarget);

        try {
            const portfolioId = `p_${Math.random().toString(16).slice(2, 10)}`;
            const newPortfolio: Portfolio = {
                id: portfolioId,
                name: formData.get('name') as string,
                type: formData.get('type') as PortfolioType,
                base_currency: formData.get('base_currency') as string,
                created_at: new Date().toISOString(),
            };

            savePortfolio(portfolioId, {
                meta: newPortfolio,
                data: []
            });

            router.push(`/${locale}`);
        } catch (err) {
            setError(err instanceof Error ? err.message : t('failedToCreate'));
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <main className="min-h-screen p-8 bg-gray-50 text-gray-900">
            <div className="max-w-2xl mx-auto">
                <Link
                    href={`/${locale}`}
                    className="text-gray-500 hover:text-gray-900 mb-8 inline-block"
                >
                    {t('backToPortfolios')}
                </Link>

                <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
                    <h1 className="text-2xl font-bold text-gray-900 mb-6">{t('title')}</h1>

                    {error && (
                        <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6 text-sm">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                                {t('portfolioName')}
                            </label>
                            <input
                                type="text"
                                id="name"
                                name="name"
                                required
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                placeholder={t('portfolioNamePlaceholder')}
                            />
                        </div>

                        <div>
                            <label htmlFor="type" className="block text-sm font-medium text-gray-700 mb-1">
                                {t('portfolioType')}
                            </label>
                            <select
                                id="type"
                                name="type"
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            >
                                <option value="transaction">{t('transactionBased')}</option>
                                <option value="snapshot">{t('snapshotBased')}</option>
                            </select>
                            <p className="mt-1 text-sm text-gray-500">
                                {t('typeDescription')}
                            </p>
                        </div>

                        <div>
                            <label htmlFor="base_currency" className="block text-sm font-medium text-gray-700 mb-1">
                                {t('baseCurrency')}
                            </label>
                            <select
                                id="base_currency"
                                name="base_currency"
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            >
                                <option value="USD">USD</option>
                                <option value="EUR">EUR</option>
                                <option value="CNY">CNY</option>
                                <option value="HKD">HKD</option>
                            </select>
                        </div>

                        <div className="pt-4">
                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="w-full bg-blue-600 text-white py-2.5 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                            >
                                {isSubmitting ? t('creating') : t('createPortfolio')}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </main>
    );
}
