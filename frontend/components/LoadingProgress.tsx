'use client';

import React from 'react';
import { useTranslations } from 'next-intl';

interface LoadingProgressProps {
    currentStep: number;
    totalSteps: number;
    stepLabels?: string[];
}

export function LoadingProgress({ currentStep, totalSteps, stepLabels }: LoadingProgressProps) {
    const t = useTranslations('LoadingProgress');
    const progress = Math.round((currentStep / totalSteps) * 100);
    
    const defaultLabels = [
        t('loadingPortfolio'),
        t('loadingPrices'),
        t('calculatingNav'),
        t('computingBasicIndicators'),
        t('computingAllMetrics'),
        t('comparingBenchmarks')
    ];
    
    const labels = stepLabels || defaultLabels;
    const currentLabel = labels[Math.min(currentStep, labels.length - 1)] || t('processing');

    return (
        <div className="w-full space-y-3">
            <div className="flex justify-between items-center text-sm">
                <span className="text-gray-600 font-medium">{currentLabel}</span>
                <span className="text-gray-400">{progress}%</span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                    className="h-full bg-blue-600 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${progress}%` }}
                />
            </div>
        </div>
    );
}
