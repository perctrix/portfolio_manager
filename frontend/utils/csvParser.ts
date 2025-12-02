import { PortfolioType } from '@/types';

// Target fields for each portfolio type
export const TRANSACTION_FIELDS = ['datetime', 'symbol', 'side', 'quantity', 'price', 'fee'] as const;
export const SNAPSHOT_FIELDS = ['symbol', 'quantity', 'cost_basis', 'as_of'] as const;

export type TransactionField = typeof TRANSACTION_FIELDS[number];
export type SnapshotField = typeof SNAPSHOT_FIELDS[number];
export type TargetField = TransactionField | SnapshotField;

// Column mapping result
export interface ColumnMapping {
  csvColumn: string;
  targetField: TargetField | null;
  confidence: number; // 0-1, higher means more confident match
}

// Parsed CSV result
export interface ParsedCSV {
  headers: string[];
  rows: Record<string, string>[];
  rawRows: string[][];
}

// Fuzzy match aliases for each field (all lowercase for comparison)
const FIELD_ALIASES: Record<TargetField, string[]> = {
  // Transaction fields
  datetime: ['datetime', 'date', 'time', 'trade_date', 'transaction_date', 'trade_time', 'timestamp', 'traded_at', 'executed_at', 'execution_date'],
  symbol: ['symbol', 'ticker', 'stock', 'code', 'asset', 'instrument', 'security', 'stock_code', 'ticker_symbol', 'asset_code'],
  side: ['side', 'type', 'action', 'transaction_type', 'direction', 'trade_type', 'order_type', 'buy_sell', 'operation'],
  quantity: ['quantity', 'qty', 'shares', 'volume', 'amount', 'units', 'size', 'num_shares', 'share_count', 'lot'],
  price: ['price', 'cost', 'unit_price', 'price_per_share', 'share_price', 'execution_price', 'trade_price', 'avg_price', 'average_price'],
  fee: ['fee', 'commission', 'charge', 'transaction_fee', 'trading_fee', 'brokerage', 'fees', 'commissions'],
  // Snapshot fields
  cost_basis: ['cost_basis', 'total_cost', 'cost', 'basis', 'costbasis', 'average_cost', 'avg_cost', 'book_value', 'investment'],
  as_of: ['as_of', 'date', 'snapshot_date', 'asof', 'position_date', 'value_date', 'reporting_date'],
};

// Required fields for each type
export const REQUIRED_FIELDS: Record<PortfolioType, TargetField[]> = {
  transaction: ['datetime', 'symbol', 'side', 'quantity', 'price'],
  snapshot: ['symbol', 'quantity'],
};

// Supported date formats
export const DATE_FORMATS = ['auto', 'YYYY-MM-DD', 'MM/DD/YYYY', 'DD/MM/YYYY', 'DD.MM.YYYY'] as const;
export type DateFormat = typeof DATE_FORMATS[number];

/**
 * Parse CSV content into structured data
 */
export function parseCSV(content: string): ParsedCSV {
  const lines = content.split(/\r?\n/).filter(line => line.trim());
  if (lines.length === 0) {
    return { headers: [], rows: [], rawRows: [] };
  }

  const rawRows: string[][] = lines.map(line => parseCSVLine(line));
  const rawHeaders = rawRows[0] || [];
  const dataRows = rawRows.slice(1);

  // Handle duplicate column headers by appending suffix
  const headerCounts = new Map<string, number>();
  const headers = rawHeaders.map(header => {
    const trimmed = header.trim() || 'column';
    const count = headerCounts.get(trimmed) || 0;
    headerCounts.set(trimmed, count + 1);
    return count === 0 ? trimmed : `${trimmed}_${count + 1}`;
  });

  const rows = dataRows.map(row => {
    const record: Record<string, string> = {};
    headers.forEach((header, index) => {
      record[header] = row[index] || '';
    });
    return record;
  });

  return { headers, rows, rawRows: dataRows };
}

/**
 * Parse a single CSV line, handling quoted values
 * Handles unclosed quotes gracefully by treating them as literal characters
 */
function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;
  let quoteStart = -1;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    const nextChar = line[i + 1];

    if (inQuotes) {
      if (char === '"' && nextChar === '"') {
        // Escaped quote
        current += '"';
        i++; // Skip next quote
      } else if (char === '"') {
        // End of quoted section
        inQuotes = false;
      } else {
        current += char;
      }
    } else {
      if (char === '"') {
        // Start of quoted section
        inQuotes = true;
        quoteStart = i;
      } else if (char === ',') {
        result.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
  }

  // Handle unclosed quotes: treat the opening quote as a literal character
  if (inQuotes && quoteStart >= 0) {
    // Re-parse from quote start, treating quote as literal
    current = '';
    for (let i = quoteStart; i < line.length; i++) {
      const char = line[i];
      if (char === ',') {
        result.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
  }

  result.push(current.trim());

  return result;
}

/**
 * Normalize string for comparison (lowercase, remove special chars)
 */
function normalizeString(str: string): string {
  return str.toLowerCase().replace(/[^a-z0-9]/g, '');
}

/**
 * Calculate similarity between two strings (0-1)
 */
function calculateSimilarity(str1: string, str2: string): number {
  const s1 = normalizeString(str1);
  const s2 = normalizeString(str2);

  if (s1 === s2) return 1;
  if (s1.includes(s2) || s2.includes(s1)) return 0.8;

  // Levenshtein distance based similarity
  const maxLen = Math.max(s1.length, s2.length);
  if (maxLen === 0) return 1;

  const distance = levenshteinDistance(s1, s2);
  return 1 - distance / maxLen;
}

/**
 * Calculate Levenshtein distance between two strings
 */
function levenshteinDistance(str1: string, str2: string): number {
  const m = str1.length;
  const n = str2.length;
  const dp: number[][] = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

  for (let i = 0; i <= m; i++) dp[i][0] = i;
  for (let j = 0; j <= n; j++) dp[0][j] = j;

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (str1[i - 1] === str2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1];
      } else {
        dp[i][j] = Math.min(
          dp[i - 1][j] + 1,     // deletion
          dp[i][j - 1] + 1,     // insertion
          dp[i - 1][j - 1] + 1  // substitution
        );
      }
    }
  }

  return dp[m][n];
}

/**
 * Find the best matching target field for a CSV column
 */
function findBestMatch(csvColumn: string, targetFields: readonly TargetField[]): { field: TargetField | null; confidence: number } {
  let bestMatch: TargetField | null = null;
  let bestConfidence = 0;

  const normalizedColumn = normalizeString(csvColumn);

  for (const field of targetFields) {
    const aliases = FIELD_ALIASES[field];

    for (const alias of aliases) {
      const normalizedAlias = normalizeString(alias);

      // Early exit on exact match
      if (normalizedColumn === normalizedAlias) {
        return { field, confidence: 1 };
      }

      const similarity = calculateSimilarity(normalizedColumn, normalizedAlias);

      if (similarity > bestConfidence) {
        bestConfidence = similarity;
        bestMatch = field;
      }
    }
  }

  // Only return match if confidence is above threshold
  if (bestConfidence < 0.5) {
    return { field: null, confidence: 0 };
  }

  return { field: bestMatch, confidence: bestConfidence };
}

/**
 * Auto-detect column mappings for CSV headers
 */
export function autoDetectMappings(
  headers: string[],
  portfolioType: PortfolioType
): ColumnMapping[] {
  const targetFields = portfolioType === 'transaction' ? TRANSACTION_FIELDS : SNAPSHOT_FIELDS;
  const usedFields = new Set<TargetField>();

  // First pass: find best matches
  const initialMappings = headers.map(header => {
    const { field, confidence } = findBestMatch(header, targetFields);
    return { csvColumn: header, targetField: field, confidence };
  });

  // Second pass: resolve conflicts (same field matched by multiple columns)
  // Sort by confidence to prioritize better matches
  const sortedIndices = initialMappings
    .map((m, i) => ({ ...m, index: i }))
    .sort((a, b) => b.confidence - a.confidence);

  const finalMappings = new Array(headers.length).fill(null);

  for (const mapping of sortedIndices) {
    if (mapping.targetField && !usedFields.has(mapping.targetField)) {
      usedFields.add(mapping.targetField);
      finalMappings[mapping.index] = {
        csvColumn: mapping.csvColumn,
        targetField: mapping.targetField,
        confidence: mapping.confidence,
      };
    } else {
      finalMappings[mapping.index] = {
        csvColumn: mapping.csvColumn,
        targetField: null,
        confidence: 0,
      };
    }
  }

  return finalMappings;
}

/**
 * Get available target fields for a portfolio type
 */
export function getTargetFields(portfolioType: PortfolioType): readonly TargetField[] {
  return portfolioType === 'transaction' ? TRANSACTION_FIELDS : SNAPSHOT_FIELDS;
}

/**
 * Validate that all required fields are mapped
 */
export function validateMappings(
  mappings: ColumnMapping[],
  portfolioType: PortfolioType
): { valid: boolean; missingFields: TargetField[] } {
  const requiredFields = REQUIRED_FIELDS[portfolioType];
  const mappedFields = new Set(mappings.map(m => m.targetField).filter(Boolean));

  const missingFields = requiredFields.filter(field => !mappedFields.has(field));

  return {
    valid: missingFields.length === 0,
    missingFields,
  };
}

/**
 * Convert CSV rows to portfolio data using mappings
 */
export function convertToPortfolioData(
  rows: Record<string, string>[],
  mappings: ColumnMapping[],
  portfolioType: PortfolioType,
  dateFormat: DateFormat = 'auto'
): Record<string, any>[] {
  const fieldMap = new Map<string, TargetField>();
  mappings.forEach(m => {
    if (m.targetField) {
      fieldMap.set(m.csvColumn, m.targetField);
    }
  });

  return rows.map(row => {
    const record: Record<string, any> = {};

    for (const [csvColumn, value] of Object.entries(row)) {
      const targetField = fieldMap.get(csvColumn);
      if (targetField) {
        record[targetField] = convertValue(value, targetField, dateFormat);
      }
    }

    // Set defaults for missing optional fields
    if (portfolioType === 'transaction') {
      if (record.fee === undefined) record.fee = 0;
    }

    return record;
  });
}

// Valid transaction sides
const VALID_SIDES = ['BUY', 'SELL', 'DEPOSIT', 'WITHDRAW'];

export interface DataValidationWarning {
  row: number;
  field: string;
  value: any;
  message: string;
}

/**
 * Validate converted portfolio data and return warnings
 */
export function validateConvertedData(
  data: Record<string, any>[],
  portfolioType: PortfolioType
): DataValidationWarning[] {
  const warnings: DataValidationWarning[] = [];

  data.forEach((record, index) => {
    const rowNum = index + 1;

    // Check for empty symbol
    if (!record.symbol || record.symbol.trim() === '') {
      warnings.push({
        row: rowNum,
        field: 'symbol',
        value: record.symbol,
        message: 'Empty symbol',
      });
    }

    // Check for negative or zero quantity
    if (typeof record.quantity === 'number' && record.quantity <= 0) {
      warnings.push({
        row: rowNum,
        field: 'quantity',
        value: record.quantity,
        message: 'Quantity must be positive',
      });
    }

    // Check for negative price
    if (typeof record.price === 'number' && record.price < 0) {
      warnings.push({
        row: rowNum,
        field: 'price',
        value: record.price,
        message: 'Price cannot be negative',
      });
    }

    // Check for negative fee
    if (typeof record.fee === 'number' && record.fee < 0) {
      warnings.push({
        row: rowNum,
        field: 'fee',
        value: record.fee,
        message: 'Fee cannot be negative',
      });
    }

    // For transactions, validate side
    if (portfolioType === 'transaction') {
      if (record.side && !VALID_SIDES.includes(record.side)) {
        warnings.push({
          row: rowNum,
          field: 'side',
          value: record.side,
          message: `Unrecognized transaction type: ${record.side}`,
        });
      }
    }

    // For snapshots, check cost_basis
    if (portfolioType === 'snapshot') {
      if (typeof record.cost_basis === 'number' && record.cost_basis < 0) {
        warnings.push({
          row: rowNum,
          field: 'cost_basis',
          value: record.cost_basis,
          message: 'Cost basis cannot be negative',
        });
      }
    }
  });

  return warnings;
}

/**
 * Convert string value to appropriate type
 */
function convertValue(value: string, field: TargetField, dateFormat: DateFormat = 'auto'): any {
  const trimmed = value.trim();

  switch (field) {
    case 'datetime':
      return normalizeDateTime(trimmed, dateFormat);
    case 'as_of':
      return normalizeDate(trimmed, dateFormat);
    case 'quantity':
    case 'price':
    case 'fee':
    case 'cost_basis':
      return parseNumber(trimmed);
    case 'side':
      return normalizeSide(trimmed);
    case 'symbol':
      return trimmed.toUpperCase();
    default:
      return trimmed;
  }
}

/**
 * Parse date string according to specified format
 */
function parseDateWithFormat(value: string, dateFormat: DateFormat): Date | null {
  if (dateFormat === 'auto') {
    const date = new Date(value);
    return isNaN(date.getTime()) ? null : date;
  }

  // Extract date and optional time parts
  const dateTimeParts = value.split(/[T\s]+/);
  const datePart = dateTimeParts[0];
  const timePart = dateTimeParts[1] || '00:00';

  let year: number, month: number, day: number;

  if (dateFormat === 'YYYY-MM-DD') {
    const parts = datePart.split('-');
    if (parts.length !== 3) return null;
    year = parseInt(parts[0], 10);
    month = parseInt(parts[1], 10) - 1;
    day = parseInt(parts[2], 10);
  } else if (dateFormat === 'MM/DD/YYYY') {
    const parts = datePart.split('/');
    if (parts.length !== 3) return null;
    month = parseInt(parts[0], 10) - 1;
    day = parseInt(parts[1], 10);
    year = parseInt(parts[2], 10);
  } else if (dateFormat === 'DD/MM/YYYY') {
    const parts = datePart.split('/');
    if (parts.length !== 3) return null;
    day = parseInt(parts[0], 10);
    month = parseInt(parts[1], 10) - 1;
    year = parseInt(parts[2], 10);
  } else if (dateFormat === 'DD.MM.YYYY') {
    const parts = datePart.split('.');
    if (parts.length !== 3) return null;
    day = parseInt(parts[0], 10);
    month = parseInt(parts[1], 10) - 1;
    year = parseInt(parts[2], 10);
  } else {
    return null;
  }

  // Parse time
  const timeParts = timePart.split(':');
  const hours = parseInt(timeParts[0], 10) || 0;
  const minutes = parseInt(timeParts[1], 10) || 0;

  const date = new Date(year, month, day, hours, minutes);
  return isNaN(date.getTime()) ? null : date;
}

/**
 * Normalize datetime string to ISO format
 */
function normalizeDateTime(value: string, dateFormat: DateFormat = 'auto'): string {
  const date = parseDateWithFormat(value, dateFormat);
  if (date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  }
  return value;
}

/**
 * Normalize date string to YYYY-MM-DD format
 */
function normalizeDate(value: string, dateFormat: DateFormat = 'auto'): string {
  const date = parseDateWithFormat(value, dateFormat);
  if (date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }
  return value;
}

/**
 * Parse number from string, handling common formats
 */
function parseNumber(value: string): number {
  // Remove currency symbols, commas, spaces
  const cleaned = value.replace(/[$€£¥,\s]/g, '');
  const num = parseFloat(cleaned);
  return isNaN(num) ? 0 : num;
}

/**
 * Normalize transaction side value
 */
function normalizeSide(value: string): string {
  const upper = value.toUpperCase().trim();

  // Map common variations
  if (['BUY', 'B', 'BOUGHT', 'PURCHASE', 'LONG'].includes(upper)) return 'BUY';
  if (['SELL', 'S', 'SOLD', 'SALE', 'SHORT'].includes(upper)) return 'SELL';
  if (['DEPOSIT', 'DEP', 'D', 'IN', 'TRANSFER_IN', 'CASH_IN'].includes(upper)) return 'DEPOSIT';
  if (['WITHDRAW', 'WITHDRAWAL', 'W', 'OUT', 'TRANSFER_OUT', 'CASH_OUT'].includes(upper)) return 'WITHDRAW';

  return upper;
}

/**
 * Detect if CSV data looks more like transactions or snapshots
 */
export function detectPortfolioType(headers: string[]): PortfolioType {
  const transactionScore = autoDetectMappings(headers, 'transaction')
    .filter(m => m.targetField !== null).length;
  const snapshotScore = autoDetectMappings(headers, 'snapshot')
    .filter(m => m.targetField !== null).length;

  // If transaction-specific fields are found, prefer transaction
  const hasTransactionFields = headers.some(h => {
    const normalized = normalizeString(h);
    return ['side', 'type', 'action', 'datetime', 'fee', 'commission'].some(
      keyword => normalized.includes(keyword)
    );
  });

  if (hasTransactionFields) return 'transaction';
  if (snapshotScore > transactionScore) return 'snapshot';
  return 'transaction'; // Default
}
