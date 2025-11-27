'use client';

import { useTranslations } from 'next-intl';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { formatPercentage, formatNumber } from '@/utils/formatters';
import { RiskDecompositionMetrics } from '@/types/indicators';

interface RiskDecompositionProps {
  riskDecomp: RiskDecompositionMetrics;
}

const COLORS = ['#2563eb', '#7c3aed', '#db2777', '#ea580c', '#ca8a04', '#16a34a', '#0891b2', '#6366f1'];

export default function RiskDecomposition({ riskDecomp }: RiskDecompositionProps) {
  const t = useTranslations('RiskDecomposition');

  if (!riskDecomp || !riskDecomp.by_asset) {
    return (
      <div className="text-sm text-gray-500 text-center py-4">
        {t('noData')}
      </div>
    );
  }

  const sortedAssets = Object.entries(riskDecomp.by_asset).sort(
    ([, a], [, b]) => Math.abs(b.pct_risk_contribution) - Math.abs(a.pct_risk_contribution)
  );

  const chartData = sortedAssets.map(([symbol, data]) => ({
    name: symbol,
    value: data.pct_risk_contribution * 100,
  }));

  return (
    <div className="space-y-6">
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-4 text-center">
          {t('riskContributionByAsset')}
        </h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis tickFormatter={(value) => `${value.toFixed(1)}%`} />
            <Tooltip formatter={(value: number) => `${value.toFixed(2)}%`} />
            <Bar dataKey="value" name={t('riskContribution')}>
              {chartData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">
          {t('riskMetricsByAsset')}
        </h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 font-medium">
              <tr>
                <th className="px-4 py-2 text-left rounded-tl-lg">Symbol</th>
                <th className="px-4 py-2 text-right">{t('mctr')}</th>
                <th className="px-4 py-2 text-right">{t('riskContribution')}</th>
                <th className="px-4 py-2 text-right rounded-tr-lg">{t('pctTotalRisk')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sortedAssets.map(([symbol, data]) => (
                <tr key={symbol} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-gray-700 font-medium">{symbol}</td>
                  <td className="px-4 py-2 text-right text-gray-900">
                    {formatNumber(data.mctr, 4)}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-900">
                    {formatNumber(data.risk_contribution, 4)}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-900 font-medium">
                    {formatPercentage(data.pct_risk_contribution)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {riskDecomp.by_sector && Object.keys(riskDecomp.by_sector).length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            {t('riskContributionBySector')}
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 font-medium">
                <tr>
                  <th className="px-4 py-2 text-left rounded-tl-lg">Sector</th>
                  <th className="px-4 py-2 text-right rounded-tr-lg">{t('pctTotalRisk')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {Object.entries(riskDecomp.by_sector)
                  .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
                  .map(([sector, contribution]) => (
                    <tr key={sector} className="hover:bg-gray-50">
                      <td className="px-4 py-2 text-gray-700">{sector}</td>
                      <td className="px-4 py-2 text-right text-gray-900 font-medium">
                        {formatPercentage(contribution)}
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
