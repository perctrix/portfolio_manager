'use client';

import { useTranslations } from 'next-intl';
import { formatCalculatedDate, getDaysSince } from '@/utils/hash';

interface ImportCacheDecisionModalProps {
    isOpen: boolean;
    onClose: () => void;
    onUseCache: () => void;
    onRecalculate: () => void;
    calculatedAt: string;
    portfolioName: string;
}

export function ImportCacheDecisionModal({
    isOpen,
    onClose,
    onUseCache,
    onRecalculate,
    calculatedAt,
    portfolioName
}: ImportCacheDecisionModalProps) {
    const t = useTranslations('Import');

    if (!isOpen) return null;

    const daysSince = getDaysSince(calculatedAt);
    const formattedDate = formatCalculatedDate(calculatedAt);

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-md">
                <h2 className="text-xl font-bold mb-4">{t('cacheDecisionTitle')}</h2>

                <div className="mb-6">
                    <p className="text-gray-700 mb-3">
                        {t('cacheDecisionDescription', { name: portfolioName })}
                    </p>
                    <div className="bg-gray-50 rounded-lg p-3 mb-3">
                        <p className="text-sm text-gray-600">
                            {t('calculatedOn')}: <span className="font-medium text-gray-800">{formattedDate}</span>
                        </p>
                        {daysSince > 0 && (
                            <p className="text-sm text-amber-600 mt-1">
                                {t('daysAgo', { days: daysSince })}
                            </p>
                        )}
                    </div>
                    <p className="text-sm text-gray-500">
                        {t('cacheInfo')}
                    </p>
                </div>

                <div className="flex gap-3">
                    <button
                        onClick={() => {
                            onUseCache();
                            onClose();
                        }}
                        className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        {t('useCachedResults')}
                    </button>
                    <button
                        onClick={() => {
                            onRecalculate();
                            onClose();
                        }}
                        className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                        {t('recalculate')}
                    </button>
                </div>

                <button
                    onClick={onClose}
                    className="mt-3 w-full px-4 py-2 text-gray-500 hover:text-gray-700 transition-colors text-sm"
                >
                    {t('cancel')}
                </button>
            </div>
        </div>
    );
}
