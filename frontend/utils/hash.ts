export async function calculateDataHash(data: unknown[], bonds?: unknown[]): Promise<string> {
    const dataToHash = bonds && bonds.length > 0 ? { data, bonds } : data;
    const normalized = JSON.stringify(dataToHash, (key, value) => {
        if (value && typeof value === 'object' && !Array.isArray(value)) {
            return Object.keys(value).sort().reduce((sorted: Record<string, unknown>, k) => {
                sorted[k] = value[k];
                return sorted;
            }, {});
        }
        return value;
    });

    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(normalized);
    const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

export function isToday(isoDateString: string): boolean {
    const calculatedDate = new Date(isoDateString);
    const today = new Date();
    return calculatedDate.toDateString() === today.toDateString();
}

export function formatCalculatedDate(isoDateString: string): string {
    const date = new Date(isoDateString);
    return date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

export function getDaysSince(isoDateString: string): number {
    const calculatedDate = new Date(isoDateString);
    const today = new Date();
    const diffTime = today.getTime() - calculatedDate.getTime();
    return Math.floor(diffTime / (1000 * 60 * 60 * 24));
}
