'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { Upload, AlertCircle, CheckCircle2, ArrowRight } from 'lucide-react';
import { Portfolio, PortfolioType } from '@/types';
import {
  parseCSV,
  autoDetectMappings,
  validateMappings,
  convertToPortfolioData,
  validateConvertedData,
  getTargetFields,
  detectPortfolioType,
  ColumnMapping,
  ParsedCSV,
  TargetField,
  REQUIRED_FIELDS,
  DataValidationWarning,
} from '@/utils/csvParser';

interface ImportCSVModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImport: (data: Record<string, any>[], portfolioType: PortfolioType, portfolioName: string, currency: string, targetPortfolioId?: string) => void;
  initialFile?: File | null;
  existingPortfolios?: Portfolio[];
}

const SUPPORTED_CURRENCIES = ['USD', 'CNY', 'EUR', 'GBP', 'JPY', 'HKD', 'CAD', 'AUD', 'CHF', 'SGD'] as const;

type Step = 'upload' | 'mapping' | 'preview';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export function ImportCSVModal({ isOpen, onClose, onImport, initialFile, existingPortfolios = [] }: ImportCSVModalProps) {
  const t = useTranslations('ImportCSV');

  const [step, setStep] = useState<Step>('upload');
  const [csvData, setCsvData] = useState<ParsedCSV | null>(null);
  const [mappings, setMappings] = useState<ColumnMapping[]>([]);
  const [portfolioType, setPortfolioType] = useState<PortfolioType>('transaction');
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string>('');
  const [portfolioName, setPortfolioName] = useState<string>('');
  const [currency, setCurrency] = useState<string>('USD');
  const [warnings, setWarnings] = useState<DataValidationWarning[]>([]);
  const [targetPortfolioId, setTargetPortfolioId] = useState<string>('new');

  // Track processed file to prevent duplicate processing
  const processedFileRef = useRef<File | null>(null);

  const resetState = useCallback(() => {
    setStep('upload');
    setCsvData(null);
    setMappings([]);
    setPortfolioType('transaction');
    setError(null);
    setFileName('');
    setPortfolioName('');
    setCurrency('USD');
    setWarnings([]);
    setTargetPortfolioId('new');
    processedFileRef.current = null;
  }, []);

  const handleClose = useCallback(() => {
    resetState();
    onClose();
  }, [resetState, onClose]);

  // Process file
  const processFile = useCallback(async (file: File) => {
    setError(null);
    setFileName(file.name);
    // Set default portfolio name from filename (without .csv extension)
    setPortfolioName(file.name.replace(/\.csv$/i, ''));

    // File size validation
    if (file.size > MAX_FILE_SIZE) {
      setError(t('errorFileTooLarge'));
      return;
    }

    try {
      const content = await file.text();
      const parsed = parseCSV(content);

      if (parsed.headers.length === 0) {
        setError(t('errorEmptyFile'));
        return;
      }

      if (parsed.rows.length === 0) {
        setError(t('errorNoData'));
        return;
      }

      setCsvData(parsed);

      // Auto-detect portfolio type and mappings
      const detectedType = detectPortfolioType(parsed.headers);
      setPortfolioType(detectedType);

      const detectedMappings = autoDetectMappings(parsed.headers, detectedType);
      setMappings(detectedMappings);

      setStep('mapping');
      processedFileRef.current = file;
    } catch (err) {
      setError(t('errorParseFailed'));
      console.error('CSV parse error:', err);
    }
  }, [t]);

  // Handle initial file - only process if not already processed
  useEffect(() => {
    if (isOpen && initialFile && processedFileRef.current !== initialFile) {
      processFile(initialFile);
    }
  }, [isOpen, initialFile, processFile]);

  // Keyboard navigation - Escape to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        handleClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, handleClose]);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    await processFile(file);

    // Reset file input
    e.target.value = '';
  };

  const handleTargetChange = (newTargetId: string) => {
    setError(null);
    setTargetPortfolioId(newTargetId);

    if (newTargetId !== 'new') {
      // When selecting existing portfolio, use its type and currency
      const selectedPortfolio = existingPortfolios.find(p => p.id === newTargetId);
      if (selectedPortfolio) {
        setPortfolioType(selectedPortfolio.type);
        setCurrency(selectedPortfolio.base_currency);
        if (csvData) {
          const newMappings = autoDetectMappings(csvData.headers, selectedPortfolio.type);
          setMappings(newMappings);
        }
      }
    }
  };

  const handleTypeChange = (newType: PortfolioType) => {
    setError(null); // Clear error on type change
    setPortfolioType(newType);
    if (csvData) {
      const newMappings = autoDetectMappings(csvData.headers, newType);
      setMappings(newMappings);
    }
  };

  const handleMappingChange = (index: number, newTarget: TargetField | null) => {
    setError(null); // Clear error on mapping change
    setMappings(prev => {
      const updated = [...prev];

      // If this field is already used elsewhere, clear it
      if (newTarget) {
        updated.forEach((m, i) => {
          if (i !== index && m.targetField === newTarget) {
            updated[i] = { ...m, targetField: null, confidence: 0 };
          }
        });
      }

      updated[index] = {
        ...updated[index],
        targetField: newTarget,
        confidence: newTarget ? 1 : 0,
      };

      return updated;
    });
  };

  const handleConfirm = (forceImport = false) => {
    if (!csvData) return;

    const validation = validateMappings(mappings, portfolioType);
    if (!validation.valid) {
      setError(t('errorMissingFields', { fields: validation.missingFields.join(', ') }));
      return;
    }

    const convertedData = convertToPortfolioData(csvData.rows, mappings, portfolioType);

    // Validate data and check for warnings
    const dataWarnings = validateConvertedData(convertedData, portfolioType);

    // If there are warnings and user hasn't confirmed, show warnings first
    if (dataWarnings.length > 0 && !forceImport) {
      setWarnings(dataWarnings);
      return;
    }

    // Clear warnings and proceed with import
    setWarnings([]);
    onImport(
      convertedData,
      portfolioType,
      portfolioName.trim() || 'Imported Portfolio',
      currency,
      targetPortfolioId === 'new' ? undefined : targetPortfolioId
    );
    handleClose();
  };

  if (!isOpen) return null;

  const targetFields = getTargetFields(portfolioType);
  const requiredFields = REQUIRED_FIELDS[portfolioType];
  const validation = validateMappings(mappings, portfolioType);

  // Get used fields
  const usedFields = new Set(mappings.map(m => m.targetField).filter(Boolean));

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="csv-import-title"
    >
      <div className="bg-white rounded-xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b">
          <h2 id="csv-import-title" className="text-xl font-bold">{t('title')}</h2>
          <p className="text-sm text-gray-500 mt-1">{t('subtitle')}</p>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {step === 'upload' && (
            <div className="space-y-4">
              <label className="flex flex-col items-center justify-center w-full h-48 border-2 border-dashed border-gray-300 rounded-xl cursor-pointer hover:bg-gray-50 transition-colors">
                <Upload className="w-12 h-12 text-gray-400 mb-3" />
                <span className="text-gray-600 font-medium">{t('dropzone')}</span>
                <span className="text-sm text-gray-400 mt-1">{t('dropzoneHint')}</span>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>

              {error && (
                <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg">
                  <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}
            </div>
          )}

          {step === 'mapping' && csvData && (
            <div className="space-y-6">
              {/* File info */}
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span>{t('fileLoaded', { name: fileName, rows: csvData.rows.length })}</span>
              </div>

              {/* Target portfolio selector */}
              {existingPortfolios.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('importTarget')}
                  </label>
                  <select
                    value={targetPortfolioId}
                    onChange={(e) => handleTargetChange(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  >
                    <option value="new">{t('createNewPortfolio')}</option>
                    <optgroup label={t('existingPortfolios')}>
                      {existingPortfolios.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({p.type}, {p.base_currency})
                        </option>
                      ))}
                    </optgroup>
                  </select>
                </div>
              )}

              {/* Portfolio name input - only for new portfolios */}
              {targetPortfolioId === 'new' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('portfolioName')}
                  </label>
                  <input
                    type="text"
                    value={portfolioName}
                    onChange={(e) => setPortfolioName(e.target.value)}
                    placeholder={t('portfolioNamePlaceholder')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  />
                </div>
              )}

              {/* Currency selector - only for new portfolios */}
              {targetPortfolioId === 'new' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('baseCurrency')}
                  </label>
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  >
                    {SUPPORTED_CURRENCIES.map((cur) => (
                      <option key={cur} value={cur}>
                        {cur}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Portfolio type selector - only for new portfolios */}
              {targetPortfolioId === 'new' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('portfolioType')}
                  </label>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => handleTypeChange('transaction')}
                      className={`px-4 py-2 rounded-lg border transition-colors ${
                        portfolioType === 'transaction'
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {t('typeTransaction')}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleTypeChange('snapshot')}
                      className={`px-4 py-2 rounded-lg border transition-colors ${
                        portfolioType === 'snapshot'
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {t('typeSnapshot')}
                    </button>
                  </div>
                </div>
              )}

              {/* Column mappings */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  {t('columnMapping')}
                </label>
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">
                          {t('csvColumn')}
                        </th>
                        <th className="px-4 py-3 text-center text-sm font-medium text-gray-400 w-12">
                          <ArrowRight className="w-4 h-4 mx-auto" />
                        </th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">
                          {t('targetField')}
                        </th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">
                          {t('preview')}
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {mappings.map((mapping, index) => (
                        <tr key={mapping.csvColumn} className="hover:bg-gray-50">
                          <td className="px-4 py-3">
                            <span className="font-mono text-sm">{mapping.csvColumn}</span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <ArrowRight className="w-4 h-4 mx-auto text-gray-400" />
                          </td>
                          <td className="px-4 py-3">
                            <select
                              value={mapping.targetField || ''}
                              onChange={(e) => handleMappingChange(
                                index,
                                e.target.value ? e.target.value as TargetField : null
                              )}
                              className={`w-full px-3 py-1.5 border rounded-lg text-sm ${
                                mapping.targetField && requiredFields.includes(mapping.targetField as any)
                                  ? 'border-green-300 bg-green-50'
                                  : mapping.targetField
                                  ? 'border-blue-300 bg-blue-50'
                                  : 'border-gray-300'
                              }`}
                            >
                              <option value="">{t('ignoreColumn')}</option>
                              {targetFields.map(field => (
                                <option
                                  key={field}
                                  value={field}
                                  disabled={usedFields.has(field) && mapping.targetField !== field}
                                >
                                  {field}
                                  {requiredFields.includes(field as any) ? ' *' : ''}
                                  {usedFields.has(field) && mapping.targetField !== field ? ` (${t('alreadyMapped')})` : ''}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500 truncate max-w-[150px]">
                            {csvData.rows[0]?.[mapping.csvColumn] || '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="mt-2 text-xs text-gray-500">
                  {t('requiredHint')}
                </p>
              </div>

              {/* Validation error */}
              {error && (
                <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg">
                  <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {/* Data preview */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  {t('dataPreview')} ({Math.min(3, csvData.rows.length)} {t('rows')})
                </label>
                <div className="border rounded-lg overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        {mappings
                          .filter(m => m.targetField)
                          .map(m => (
                            <th key={m.targetField} className="px-3 py-2 text-left font-medium text-gray-600">
                              {m.targetField}
                            </th>
                          ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {csvData.rows.slice(0, 3).map((row, rowIndex) => (
                        <tr key={rowIndex}>
                          {mappings
                            .filter(m => m.targetField)
                            .map(m => (
                              <td key={m.targetField} className="px-3 py-2 text-gray-700">
                                {row[m.csvColumn] || '-'}
                              </td>
                            ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Data validation warnings */}
              {warnings.length > 0 && (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="font-medium text-amber-800">{t('warningsFound', { count: warnings.length })}</p>
                      <ul className="mt-2 text-sm text-amber-700 space-y-1">
                        {warnings.slice(0, 5).map((w, i) => (
                          <li key={i}>
                            {t('warningRow', { row: w.row })}: {w.message} ({w.field})
                          </li>
                        ))}
                        {warnings.length > 5 && (
                          <li className="text-amber-600">
                            {t('moreWarnings', { count: warnings.length - 5 })}
                          </li>
                        )}
                      </ul>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 flex justify-between items-center">
          <div className="text-sm text-gray-500">
            {step === 'mapping' && !validation.valid && (
              <span className="text-amber-600">
                {t('missingRequired', { fields: validation.missingFields.join(', ') })}
              </span>
            )}
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
            >
              {t('cancel')}
            </button>
            {step === 'mapping' && (
              warnings.length > 0 ? (
                <button
                  type="button"
                  onClick={() => handleConfirm(true)}
                  className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
                >
                  {t('importWithWarnings')}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => handleConfirm(false)}
                  disabled={!validation.valid}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {t('import')}
                </button>
              )
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
