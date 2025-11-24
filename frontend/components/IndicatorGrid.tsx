import { ArrowUp, ArrowDown, Minus } from 'lucide-react';
import { IndicatorItem } from '@/types/indicators';
import { formatIndicatorValue, getTrendColor } from '@/utils/formatters';

interface IndicatorGridProps {
  indicators: IndicatorItem[];
  columns?: 2 | 3 | 4;
}

export default function IndicatorGrid({ indicators, columns = 3 }: IndicatorGridProps) {
  const gridCols = {
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'neutral') => {
    switch (trend) {
      case 'up':
        return <ArrowUp className="w-4 h-4" />;
      case 'down':
        return <ArrowDown className="w-4 h-4" />;
      default:
        return <Minus className="w-4 h-4" />;
    }
  };

  return (
    <div className={`grid ${gridCols[columns]} gap-4`}>
      {indicators.map((indicator, index) => {
        const formattedValue =
          typeof indicator.value === 'string'
            ? indicator.value
            : formatIndicatorValue(indicator.value, indicator.format);

        const trendColor = indicator.trend
          ? getTrendColor(indicator.trend, indicator.format === 'percentage' && indicator.label.toLowerCase().includes('drawdown'))
          : '';

        return (
          <div
            key={index}
            className="bg-white p-4 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm text-gray-500 mb-1">{indicator.label}</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {formattedValue}
                </p>
                {indicator.description && (
                  <p className="text-xs text-gray-400 mt-1">
                    {indicator.description}
                  </p>
                )}
              </div>
              {indicator.trend && indicator.trend !== 'neutral' && (
                <div className={`${trendColor}`}>
                  {getTrendIcon(indicator.trend)}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
