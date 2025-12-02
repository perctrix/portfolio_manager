# PR #51 Copilot Review Summary (Updated)

## Overview
- **PR Title**: feat(import): add CSV import with fuzzy column matching
- **Files Changed**: 5
- **Total Comments**: 30 (21 original + 9 new after update)

## Fixed Issues (11 items)

| File | Issue | Status |
|------|-------|--------|
| `page.tsx:69` | ID collision using `Date.now().toString(36)` | FIXED - Added random suffix |
| `ImportCSVModal.tsx:86` | Missing file size validation | FIXED - Added 10MB limit |
| `ImportCSVModal.tsx:111` | Error state not cleared on type change | FIXED - Added `setError(null)` |
| `ImportCSVModal.tsx:134` | Error state not cleared on mapping change | FIXED - Added `setError(null)` |
| `ImportCSVModal.tsx:161` | Missing ESC key support | FIXED - Added keydown listener |
| `ImportCSVModal.tsx:164` | Missing ARIA attributes | FIXED - Added role, aria-modal, aria-labelledby |
| `csvParser.ts:64` | No duplicate column header handling | FIXED - Auto-rename with suffix |
| `csvParser.ts:33` | 'cost' alias conflict in fee field | FIXED - Removed 'cost' from fee aliases |
| `csvParser.ts:207` | Unused variable `mappings` | FIXED - Removed dead code |
| `csvParser.ts:188` | No early exit on exact match | FIXED - Added early termination |
| `ImportCSVModal.tsx:93` | useEffect potential infinite loop | FIXED - Added processedFileRef |

---

## Remaining Issues (19 items)

### High Priority

| File | Line | Issue | Suggestion |
|------|------|-------|------------|
| `page.tsx` | 44 | No MIME type validation for file upload | Add: `if (file.type && file.type !== 'text/csv' && file.type !== 'application/csv')` |
| `csvParser.ts` | 349 | `normalizeDateTime` timezone issue | Use date-fns or handle timezone explicitly |
| `csvParser.ts` | 363 | `normalizeDate` same timezone issue | Same as above |
| `csvParser.ts` | 372 | `parseNumber` returns 0 for invalid data, masks issues | Return `NaN` instead of 0 |
| `csvParser.ts` | 387 | `normalizeSide` doesn't handle unrecognized types | Throw error or validate against allowed list |
| `csvParser.ts` | 306 | Missing validation in `convertToPortfolioData` | Add validation for negative values, empty symbols, etc. |

### Medium Priority

| File | Line | Issue | Suggestion |
|------|------|-------|------------|
| `csvParser.ts` | 113 | `parseCSVLine` doesn't handle escaped quotes correctly | Fix quote handling, add unclosed quote error |
| `csvParser.ts` | 111 | No handling for unclosed quotes | Add: `if (inQuotes) throw new Error('Malformed CSV')` |
| `csvParser.ts` | 409 | `detectPortfolioType` favors transaction too heavily | Compare scores, don't default to transaction |
| `page.tsx` | 76 | Hardcoded currency 'USD' | Add currency selection in modal |
| `csvParser.ts` | 76 | No limit on columns/rows (memory exhaustion) | Add max 100 columns, 100,000 rows limits |
| `csvParser.ts` | 311 | `portfolioType` parameter unused in `convertValue` | Remove unused parameter or document future use |
| `ImportCSVModal.tsx` | 118 | `handleKeyDown` closure may reference stale state | Add `handleClose` to dependency array |

### Low Priority (Nitpicks)

| File | Line | Issue | Suggestion |
|------|------|-------|------------|
| `csvParser.ts` | 138 | Levenshtein O(m*n) for every alias comparison | Early exit already added, could further optimize |
| `csvParser.ts` | 203 | O(n^2) complexity in field matching | Pre-compute normalized aliases, use Map |
| `csvParser.ts` | 247 | `autoDetectMappings` O(n*m*k) complexity | Cache normalized strings |
| `csvParser.ts` | 120 | `normalizeString` behavior not documented | Add unit tests for edge cases |
| `ImportCSVModal.tsx` | 212 | File input missing aria-label | Add aria-label for accessibility |
| `ImportCSVModal.tsx` | 323 | Select dropdowns missing accessible labels | Add aria-label or htmlFor |

---

## Summary

- **Fixed**: 11/30 issues (37%)
- **Remaining High Priority**: 6 issues
- **Remaining Medium Priority**: 7 issues
- **Remaining Low Priority (Nitpicks)**: 6 issues

### Recommended Next Steps

1. Add MIME type validation in page.tsx
2. Fix timezone handling in date functions (consider using date-fns)
3. Return NaN instead of 0 in parseNumber
4. Add validation for unrecognized transaction sides
5. Fix CSV parser quote handling edge cases
6. Add data validation in convertToPortfolioData
