export function formatPercentage(value: number | null | undefined, decimals: number = 2): string {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatCurrency(value: number | null | undefined, currency: string = 'USD'): string {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatNumber(value: number | null | undefined, decimals: number = 2): string {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  return value.toFixed(decimals);
}

export function formatDays(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  if (!isFinite(value)) {
    return 'Not recovered';
  }
  const days = Math.round(value);
  return `${days} ${days === 1 ? 'day' : 'days'}`;
}

export function formatIndicatorValue(
  value: number | null | undefined,
  format: 'percentage' | 'number' | 'currency' | 'days' = 'number',
  decimals: number = 2
): string {
  switch (format) {
    case 'percentage':
      return formatPercentage(value, decimals);
    case 'currency':
      return formatCurrency(value);
    case 'days':
      return formatDays(value);
    case 'number':
    default:
      return formatNumber(value, decimals);
  }
}

export function getTrendDirection(value: number | null | undefined): 'up' | 'down' | 'neutral' {
  if (value === null || value === undefined || isNaN(value)) {
    return 'neutral';
  }
  if (value > 0) return 'up';
  if (value < 0) return 'down';
  return 'neutral';
}

export function getTrendColor(trend: 'up' | 'down' | 'neutral', inverse: boolean = false): string {
  if (trend === 'neutral') return 'text-gray-500';

  if (inverse) {
    return trend === 'up' ? 'text-red-600' : 'text-green-600';
  }

  return trend === 'up' ? 'text-green-600' : 'text-red-600';
}

export function formatMonthYear(dateString: string): string {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
  } catch {
    return dateString;
  }
}
