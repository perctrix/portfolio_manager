'use client';

import { useMemo } from 'react';
import { useTranslations } from 'next-intl';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine
} from 'recharts';
import { formatPercentage, formatNumber } from '@/utils/formatters';
import { EfficientFrontierData, PortfolioPoint } from '@/lib/api';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface EfficientFrontierProps {
  data: EfficientFrontierData | null;
  loading: boolean;
  onToggleShortSelling: (allow: boolean) => void;
  allowShortSelling: boolean;
}

interface ChartDataPoint {
  x: number;
  y: number;
  name: string;
  sharpe: number;
}

const COLORS = {
  frontier: '#2563eb',
  current: '#ef4444',
  gmv: '#10b981',
  tangent: '#f59e0b'
};

function PortfolioCard({
  title,
  portfolio,
  color,
  comparePortfolio
}: {
  title: string;
  portfolio: PortfolioPoint;
  color: string;
  comparePortfolio?: PortfolioPoint;
}) {
  const t = useTranslations('EfficientFrontier');

  const sharpeDiff = comparePortfolio
    ? portfolio.sharpe_ratio - comparePortfolio.sharpe_ratio
    : 0;

  return (
    <div className={`bg-white border rounded-lg p-4 border-l-4`} style={{ borderLeftColor: color }}>
      <h5 className="text-sm font-medium text-gray-700 mb-3">{title}</h5>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">{t('expectedReturn')}</span>
          <span className="font-medium text-gray-900">
            {formatPercentage(portfolio.expected_return)}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">{t('volatility')}</span>
          <span className="font-medium text-gray-900">
            {formatPercentage(portfolio.volatility)}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">{t('sharpeRatio')}</span>
          <span className="font-medium text-gray-900 flex items-center gap-1">
            {formatNumber(portfolio.sharpe_ratio, 3)}
            {comparePortfolio && sharpeDiff !== 0 && (
              <span className={sharpeDiff > 0 ? 'text-green-600' : 'text-red-600'}>
                ({sharpeDiff > 0 ? '+' : ''}{formatNumber(sharpeDiff, 3)})
              </span>
            )}
          </span>
        </div>
      </div>
    </div>
  );
}

function OptimalWeightsTable({
  gmvPortfolio,
  tangentPortfolio,
  currentPortfolio
}: {
  gmvPortfolio: PortfolioPoint;
  tangentPortfolio: PortfolioPoint | null;
  currentPortfolio: PortfolioPoint;
}) {
  const t = useTranslations('EfficientFrontier');

  const symbols = Object.keys(currentPortfolio.weights).sort();

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-gray-500 font-medium">
          <tr>
            <th className="px-4 py-2 text-left rounded-tl-lg">{t('symbol')}</th>
            <th className="px-4 py-2 text-right">{t('currentWeight')}</th>
            <th className="px-4 py-2 text-right">{t('gmvWeight')}</th>
            {tangentPortfolio && (
              <th className="px-4 py-2 text-right">{t('tangentWeight')}</th>
            )}
            <th className="px-4 py-2 text-right rounded-tr-lg">{t('diffToOptimal')}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {symbols.map((symbol) => {
            const currentWeight = currentPortfolio.weights[symbol] || 0;
            const gmvWeight = gmvPortfolio.weights[symbol] || 0;
            const tangentWeight = tangentPortfolio?.weights[symbol] || 0;
            const optimalWeight = tangentPortfolio ? tangentWeight : gmvWeight;
            const diff = optimalWeight - currentWeight;

            return (
              <tr key={symbol} className="hover:bg-gray-50">
                <td className="px-4 py-2 text-gray-700 font-medium">{symbol}</td>
                <td className="px-4 py-2 text-right text-gray-900">
                  {formatPercentage(currentWeight)}
                </td>
                <td className="px-4 py-2 text-right text-gray-900">
                  {formatPercentage(gmvWeight)}
                </td>
                {tangentPortfolio && (
                  <td className="px-4 py-2 text-right text-gray-900">
                    {formatPercentage(tangentWeight)}
                  </td>
                )}
                <td className="px-4 py-2 text-right">
                  <span className={`flex items-center justify-end gap-1 font-medium ${
                    diff > 0.001 ? 'text-green-600' :
                    diff < -0.001 ? 'text-red-600' :
                    'text-gray-500'
                  }`}>
                    {diff > 0.001 ? <TrendingUp className="w-3 h-3" /> :
                     diff < -0.001 ? <TrendingDown className="w-3 h-3" /> :
                     <Minus className="w-3 h-3" />}
                    {diff > 0 ? '+' : ''}{formatPercentage(diff)}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
        <tfoot className="bg-gray-50 font-medium">
          <tr>
            <td className="px-4 py-2 text-gray-700">{t('portfolioReturn')}</td>
            <td className="px-4 py-2 text-right text-gray-900">
              {formatPercentage(currentPortfolio.expected_return)}
            </td>
            <td className="px-4 py-2 text-right text-gray-900">
              {formatPercentage(gmvPortfolio.expected_return)}
            </td>
            {tangentPortfolio && (
              <td className="px-4 py-2 text-right text-gray-900">
                {formatPercentage(tangentPortfolio.expected_return)}
              </td>
            )}
            <td className="px-4 py-2 text-right"></td>
          </tr>
          <tr>
            <td className="px-4 py-2 text-gray-700">{t('portfolioVolatility')}</td>
            <td className="px-4 py-2 text-right text-gray-900">
              {formatPercentage(currentPortfolio.volatility)}
            </td>
            <td className="px-4 py-2 text-right text-gray-900">
              {formatPercentage(gmvPortfolio.volatility)}
            </td>
            {tangentPortfolio && (
              <td className="px-4 py-2 text-right text-gray-900">
                {formatPercentage(tangentPortfolio.volatility)}
              </td>
            )}
            <td className="px-4 py-2 text-right"></td>
          </tr>
          <tr>
            <td className="px-4 py-2 text-gray-700">{t('portfolioSharpe')}</td>
            <td className="px-4 py-2 text-right text-gray-900">
              {formatNumber(currentPortfolio.sharpe_ratio, 3)}
            </td>
            <td className="px-4 py-2 text-right text-gray-900">
              {formatNumber(gmvPortfolio.sharpe_ratio, 3)}
            </td>
            {tangentPortfolio && (
              <td className="px-4 py-2 text-right text-gray-900">
                {formatNumber(tangentPortfolio.sharpe_ratio, 3)}
              </td>
            )}
            <td className="px-4 py-2 text-right"></td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

function AssetStatsTable({
  assetStats
}: {
  assetStats: { [symbol: string]: { expected_return: number; volatility: number } };
}) {
  const t = useTranslations('EfficientFrontier');

  const sortedAssets = Object.entries(assetStats).sort(
    ([, a], [, b]) => b.expected_return - a.expected_return
  );

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-gray-500 font-medium">
          <tr>
            <th className="px-4 py-2 text-left rounded-tl-lg">{t('symbol')}</th>
            <th className="px-4 py-2 text-right">{t('expectedReturn')}</th>
            <th className="px-4 py-2 text-right rounded-tr-lg">{t('volatility')}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {sortedAssets.map(([symbol, stats]) => (
            <tr key={symbol} className="hover:bg-gray-50">
              <td className="px-4 py-2 text-gray-700 font-medium">{symbol}</td>
              <td className="px-4 py-2 text-right text-gray-900">
                {formatPercentage(stats.expected_return)}
              </td>
              <td className="px-4 py-2 text-right text-gray-900">
                {formatPercentage(stats.volatility)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: ChartDataPoint }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  const t = useTranslations('EfficientFrontier');

  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
        <p className="font-medium text-gray-900 mb-2">{data.name}</p>
        <div className="space-y-1 text-sm">
          <p className="text-gray-600">
            {t('expectedReturn')}: <span className="font-medium text-gray-900">{data.y.toFixed(2)}%</span>
          </p>
          <p className="text-gray-600">
            {t('volatility')}: <span className="font-medium text-gray-900">{data.x.toFixed(2)}%</span>
          </p>
          <p className="text-gray-600">
            {t('sharpeRatio')}: <span className="font-medium text-gray-900">{data.sharpe.toFixed(3)}</span>
          </p>
        </div>
      </div>
    );
  }
  return null;
}

export default function EfficientFrontier({
  data,
  loading,
  onToggleShortSelling,
  allowShortSelling
}: EfficientFrontierProps) {
  const t = useTranslations('EfficientFrontier');

  const chartData = useMemo(() => {
    if (!data) return { frontier: [], special: [] };

    const frontier: ChartDataPoint[] = data.frontier_points.map((p, i) => ({
      x: p.volatility * 100,
      y: p.expected_return * 100,
      name: `${t('frontierPoint')} ${i + 1}`,
      sharpe: p.sharpe_ratio
    }));

    const special: ChartDataPoint[] = [
      {
        x: data.current_portfolio.volatility * 100,
        y: data.current_portfolio.expected_return * 100,
        name: t('currentPortfolio'),
        sharpe: data.current_portfolio.sharpe_ratio
      },
      {
        x: data.gmv_portfolio.volatility * 100,
        y: data.gmv_portfolio.expected_return * 100,
        name: t('gmvPortfolio'),
        sharpe: data.gmv_portfolio.sharpe_ratio
      }
    ];

    if (data.tangent_portfolio) {
      special.push({
        x: data.tangent_portfolio.volatility * 100,
        y: data.tangent_portfolio.expected_return * 100,
        name: t('tangentPortfolio'),
        sharpe: data.tangent_portfolio.sharpe_ratio
      });
    }

    return { frontier, special };
  }, [data, t]);

  if (loading) {
    return (
      <div className="h-96 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500">
        {t('noData')}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS.frontier }}></div>
            <span>{t('efficientFrontier')}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS.current }}></div>
            <span>{t('currentPortfolio')}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS.gmv }}></div>
            <span>{t('gmvPortfolio')}</span>
          </div>
          {data.tangent_portfolio && (
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS.tangent }}></div>
              <span>{t('tangentPortfolio')}</span>
            </div>
          )}
        </div>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={allowShortSelling}
            onChange={(e) => onToggleShortSelling(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          {t('allowShortSelling')}
        </label>
      </div>

      <div className="bg-gray-50 rounded-lg p-4">
        <ResponsiveContainer width="100%" height={400}>
          <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              type="number"
              dataKey="x"
              name="Volatility"
              domain={['auto', 'auto']}
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `${value.toFixed(0)}%`}
              label={{ value: t('volatilityAxis'), position: 'bottom', offset: 0 }}
            />
            <YAxis
              type="number"
              dataKey="y"
              name="Return"
              domain={['auto', 'auto']}
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `${value.toFixed(0)}%`}
              label={{ value: t('returnAxis'), angle: -90, position: 'insideLeft' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={0} stroke="#9ca3af" strokeDasharray="3 3" />

            <Scatter
              name={t('efficientFrontier')}
              data={chartData.frontier}
              fill={COLORS.frontier}
              line={{ stroke: COLORS.frontier, strokeWidth: 2 }}
              lineType="joint"
            />

            <Scatter
              name={t('currentPortfolio')}
              data={[chartData.special[0]]}
              fill={COLORS.current}
              shape="star"
            />

            <Scatter
              name={t('gmvPortfolio')}
              data={[chartData.special[1]]}
              fill={COLORS.gmv}
              shape="diamond"
            />

            {chartData.special[2] && (
              <Scatter
                name={t('tangentPortfolio')}
                data={[chartData.special[2]]}
                fill={COLORS.tangent}
                shape="triangle"
              />
            )}
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <PortfolioCard
          title={t('currentPortfolio')}
          portfolio={data.current_portfolio}
          color={COLORS.current}
        />
        <PortfolioCard
          title={t('gmvPortfolio')}
          portfolio={data.gmv_portfolio}
          color={COLORS.gmv}
          comparePortfolio={data.current_portfolio}
        />
        {data.tangent_portfolio && (
          <PortfolioCard
            title={t('tangentPortfolio')}
            portfolio={data.tangent_portfolio}
            color={COLORS.tangent}
            comparePortfolio={data.current_portfolio}
          />
        )}
      </div>

      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">
          {t('optimalWeights')}
        </h4>
        <OptimalWeightsTable
          gmvPortfolio={data.gmv_portfolio}
          tangentPortfolio={data.tangent_portfolio}
          currentPortfolio={data.current_portfolio}
        />
      </div>

      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">
          {t('assetStatistics')}
        </h4>
        <AssetStatsTable assetStats={data.asset_stats} />
      </div>
    </div>
  );
}
