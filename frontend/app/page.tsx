'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Portfolio } from '@/types';
import { getPortfolios, importPortfolio } from '@/lib/api';
import { getMyPortfolioIds, addMyPortfolio } from '@/lib/storage';

export default function Home() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPortfolios();
  }, []);

  async function loadPortfolios() {
    try {
      const allPortfolios = await getPortfolios();
      const myIds = getMyPortfolioIds();
      const myPortfolios = allPortfolios.filter(p => myIds.includes(p.id));
      setPortfolios(myPortfolios);
    } catch (err) {
      setError('Failed to load portfolios');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const data = JSON.parse(text);
      const importedPortfolio = await importPortfolio(data);
      addMyPortfolio(importedPortfolio.id);
      loadPortfolios();
    } catch (err) {
      console.error(err);
      alert('Failed to import portfolio. Invalid file format or portfolio already exists.');
    }
    // Reset input
    e.target.value = '';
  }

  return (
    <main className="min-h-screen p-8 bg-gray-50 text-gray-900">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">My Portfolios</h1>
          <div className="flex gap-4">
            <label className="bg-white text-blue-600 border border-blue-600 px-4 py-2 rounded-lg hover:bg-blue-50 transition-colors cursor-pointer">
              Import Portfolio
              <input
                type="file"
                accept=".json"
                className="hidden"
                onChange={handleImport}
              />
            </label>
            <Link
              href="/create"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              + New Portfolio
            </Link>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">Loading...</div>
        ) : error ? (
          <div className="text-red-500 text-center py-12">{error}</div>
        ) : portfolios.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-gray-100">
            <p className="text-gray-500 mb-4">No portfolios found.</p>
            <Link
              href="/create"
              className="text-blue-600 hover:underline"
            >
              Create your first portfolio
            </Link>
          </div>
        ) : (
          <div className="grid gap-4">
            {portfolios.map((portfolio) => (
              <Link
                key={portfolio.id}
                href={`/portfolio/${portfolio.id}`}
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
    </main>
  );
}
