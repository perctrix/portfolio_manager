'use client';

import { useTranslations } from 'next-intl';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { formatPercentage } from '@/utils/formatters';
import { AllocationMetrics } from '@/types/indicators';

interface AllocationBreakdownProps {
  allocation: AllocationMetrics;
}

const COLORS = ['#2563eb', '#7c3aed', '#db2777', '#ea580c', '#ca8a04', '#16a34a', '#0891b2', '#6366f1'];

export default function AllocationBreakdown({ allocation }: AllocationBreakdownProps) {
  const t = useTranslations('AllocationBreakdown');

  if (!allocation || !allocation.weights) {
    return (
      <div className="text-sm text-gray-500 text-center py-4">
        {t('noData')}
      </div>
    );
  }

  const chartData = Object.entries(allocation.weights)
    .map(([symbol, weight]) => ({
      name: symbol,
      value: weight * 100,
    }))
    .sort((a, b) => b.value - a.value);

  const sortedWeights = Object.entries(allocation.weights).sort(
    ([, a], [, b]) => b - a
  );

  return (
    <div className="space-y-6">
      {chartData.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-4 text-center">
            {t('portfolioAllocation')}
          </h4>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => `${value.toFixed(2)}%`} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}

      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">
          {t('positionWeights')}
        </h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 font-medium">
              <tr>
                <th className="px-4 py-2 text-left rounded-tl-lg">{t('symbol') || 'Symbol'}</th>
                <th className="px-4 py-2 text-right rounded-tr-lg">{t('weight')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sortedWeights.map(([symbol, weight]) => (
                <tr key={symbol} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-gray-700 font-medium">{symbol}</td>
                  <td className="px-4 py-2 text-right text-gray-900">
                    {formatPercentage(weight)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {allocation.sector_allocation && Object.keys(allocation.sector_allocation).length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            {t('sectorAllocation')}
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 font-medium">
                <tr>
                  <th className="px-4 py-2 text-left rounded-tl-lg">{t('sector')}</th>
                  <th className="px-4 py-2 text-right rounded-tr-lg">{t('weight')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {Object.entries(allocation.sector_allocation)
                  .sort(([, a], [, b]) => b - a)
                  .map(([sector, weight]) => (
                    <tr key={sector} className="hover:bg-gray-50">
                      <td className="px-4 py-2 text-gray-700">{sector}</td>
                      <td className="px-4 py-2 text-right text-gray-900">
                        {formatPercentage(weight)}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
