'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useLocale, useTranslations } from 'next-intl';
import { Portfolio, PortfolioType } from '@/types';
import { getAllPortfolios, savePortfolio } from '@/lib/storage';
import { ImportCSVModal } from '@/components/ImportCSVModal';

export default function Home() {
  const t = useTranslations('Home');
  const locale = useLocale();
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCSVModal, setShowCSVModal] = useState(false);
  const [pendingCSVFile, setPendingCSVFile] = useState<File | null>(null);

  useEffect(() => {
    loadPortfolios();
  }, []);

  function loadPortfolios() {
    try {
      const allPortfoliosData = getAllPortfolios();
      const portfoliosList = Object.values(allPortfoliosData).map(p => p.meta);
      setPortfolios(portfoliosList);
    } finally {
      setLoading(false);
    }
  }

  async function handleImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    const isCSV = file.name.toLowerCase().endsWith('.csv');

    if (isCSV) {
      // Open CSV modal for column mapping
      setPendingCSVFile(file);
      setShowCSVModal(true);
      e.target.value = '';
      return;
    }

    // Handle JSON import
    try {
      const text = await file.text();
      const importData = JSON.parse(text);

      if (!importData.meta || !importData.data) {
        throw new Error('Invalid file format');
      }

      savePortfolio(importData.meta.id, {
        meta: importData.meta,
        data: importData.data
      });
      loadPortfolios();
    } catch (err) {
      console.error(err);
      alert(t('importError'));
    }
    e.target.value = '';
  }

  function handleCSVImport(data: Record<string, any>[], portfolioType: PortfolioType, portfolioName: string) {
    // Generate new portfolio ID with random suffix to prevent collisions
    const id = `p_${Date.now().toString(36)}_${Math.random().toString(36).substring(2, 9)}`;

    const meta: Portfolio = {
      id,
      name: portfolioName,
      type: portfolioType,
      base_currency: 'USD',
      created_at: new Date().toISOString(),
    };

    savePortfolio(id, { meta, data });
    loadPortfolios();
    setPendingCSVFile(null);
  }

  return (
    <main className="min-h-screen p-8 bg-gray-50 text-gray-900">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">{t('title')}</h1>
          <div className="flex gap-4">
            <label className="bg-white text-blue-600 border border-blue-600 px-4 py-2 rounded-lg hover:bg-blue-50 transition-colors cursor-pointer">
              {t('importPortfolio')}
              <input
                type="file"
                accept=".json,.csv"
                className="hidden"
                onChange={handleImport}
              />
            </label>
            <Link
              href={`/${locale}/create`}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              {t('newPortfolio')}
            </Link>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">{t('loading')}</div>
        ) : portfolios.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-gray-100">
            <p className="text-gray-500 mb-4">{t('noPortfolios')}</p>
            <Link
              href={`/${locale}/create`}
              className="text-blue-600 hover:underline"
            >
              {t('createFirst')}
            </Link>
          </div>
        ) : (
          <div className="grid gap-4">
            {portfolios.map((portfolio) => (
              <Link
                key={portfolio.id}
                href={`/${locale}/portfolio/${portfolio.id}`}
                className="block bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-1">
                      {portfolio.name}
                    </h2>
                    <div className="flex gap-2 text-sm text-gray-500">
                      <span className="bg-gray-100 px-2 py-0.5 rounded">
                        {portfolio.type}
                      </span>
                      <span>•</span>
                      <span>{portfolio.base_currency}</span>
                      <span>•</span>
                      <span>{new Date(portfolio.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="text-gray-400">→</div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      <ImportCSVModal
        isOpen={showCSVModal}
        onClose={() => {
          setShowCSVModal(false);
          setPendingCSVFile(null);
        }}
        onImport={handleCSVImport}
        initialFile={pendingCSVFile}
      />
    </main>
  );
}
