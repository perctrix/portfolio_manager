import { formatPercentage, formatMonthYear } from '@/utils/formatters';

interface MonthlyReturnsTableProps {
  monthlyReturns: { [key: string]: number };
}

export default function MonthlyReturnsTable({ monthlyReturns }: MonthlyReturnsTableProps) {
  if (!monthlyReturns || Object.keys(monthlyReturns).length === 0) {
    return (
      <div className="text-sm text-gray-500 text-center py-4">
        No monthly returns data available
      </div>
    );
  }

  const sortedEntries = Object.entries(monthlyReturns).sort(
    ([dateA], [dateB]) => new Date(dateB).getTime() - new Date(dateA).getTime()
  );

  const recentEntries = sortedEntries.slice(0, 12);

  return (
    <div className="mt-4">
      <h4 className="text-sm font-medium text-gray-700 mb-3">
        Recent Monthly Returns
      </h4>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-500 font-medium">
            <tr>
              <th className="px-4 py-2 text-left rounded-tl-lg">Month</th>
              <th className="px-4 py-2 text-right rounded-tr-lg">Return</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {recentEntries.map(([date, value]) => {
              const isPositive = value > 0;
              const isNegative = value < 0;
              const colorClass = isPositive
                ? 'text-green-600'
                : isNegative
                ? 'text-red-600'
                : 'text-gray-900';

              return (
                <tr key={date} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-gray-700">
                    {formatMonthYear(date)}
                  </td>
                  <td className={`px-4 py-2 text-right font-medium ${colorClass}`}>
                    {formatPercentage(value)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {sortedEntries.length > 12 && (
        <p className="text-xs text-gray-400 mt-2 text-center">
          Showing most recent 12 months
        </p>
      )}
    </div>
  );
}
