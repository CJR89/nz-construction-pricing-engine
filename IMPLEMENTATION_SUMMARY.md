# Hard Fixes Implementation Summary

This document summarizes the strict configuration and error handling implementation.

## Requirements Delivered

### A) ConfigLoader: NO Fallback/Header Scanning ✅

**Requirement:** Remove all logic that scans sheets for headers, reads ranges by guessing, or tries table-first-then-falls-back.

**Implementation:**
- Created `ConfigError` exception in `backend/app/core/exceptions.py`
- Added `REQUIRED_TABLES` constant: `["tbl_SCHEMA", "tbl_Pricing_Flow", "tbl_Rules", "tbl_Rate_Library_Map"]`
- Added `_validate_required_tables()` method that checks ALL tables before loading
- Removed `sheet_name` parameter from `_load_table()` - NO fallback
- Enhanced error message format:

```python
raise ConfigError(
    f"Missing required tables in master workbook '{self.workbook_path.name}': "
    f"{', '.join(missing_tables)}. "
    f"Required tables: {', '.join(REQUIRED_TABLES)}. "
    f"Searched sheets: {', '.join(searched_sheets)}. "
    f"Found tables: {', '.join(sorted(found_tables)) if found_tables else 'none'}."
)
```

**Tests Added:**
- `test_missing_table_raises_config_error` - Comprehensive error message validation
- `test_all_tables_present_no_error` - Success case
- `test_config_error_on_missing_tbl_pricing_flow` - Specific table missing
- `test_config_error_on_missing_tbl_rules` - Specific table missing
- `test_config_error_lists_searched_sheets` - Error details validation

### B) Rate Parsers: NO Silent Skipping on None ✅

**Requirement:** Do NOT log + continue when data rows have None. Raise explicit error.

**Implementation:**
- Created `UncachedFormulaError` exception in `backend/app/core/exceptions.py`
- Updated all 4 parsers (BCM2, ELEM, CPR, DET) to raise errors instead of logging
- Logic distinction:
  - **Allowed (skipped):** Empty rows, header rows (< row 3-5), truly blank optional fields
  - **Error raised:** Data rows matching search with None in required fields

**Error Message Format:**
```python
raise UncachedFormulaError(
    f"Workbook contains formulas without cached values. "
    f"Open '{self.source_filename}' in Excel, calculate (F9), save, and re-upload. "
    f"Source: {self.source_filename}, Sheet: {sheet_name}, Row: {row_idx}, "
    f"Column(s) with None: {', '.join(none_columns)}"
)
```

**Parser-Specific Logic:**
- **BCM2:** Error if description is None OR all rate columns None (≥2 cities)
- **ELEM:** Error if description is None OR all 3 city columns None
- **CPR:** Error if description is None OR rate value is None
- **DET:** Error if description is None

**Tests Added:**
- `test_bcm2_raises_error_on_none_description`
- `test_bcm2_raises_error_on_all_none_rates`
- `test_elem_raises_error_on_none_description`
- `test_elem_raises_error_on_all_none_rates`
- `test_cpr_raises_error_on_none_rate_value`
- `test_det_raises_error_on_none_description`
- `test_parser_allows_empty_rows` - Ensures empty rows don't raise errors
- `test_parser_allows_header_rows` - Ensures header rows don't raise errors

### C) Standardize Source Fields ✅

**Requirement:** Remove `source_row`, use ONLY `source_file`, `source_sheet`, `source_row_index`.

**Verification:**
```bash
$ grep -r "source_row[^_]" --include="*.py" --include="*.ts" backend/ frontend/
# Result: No matches found (only source_row_index used)
```

**Confirmed in:**
- `backend/app/models/schemas.py` - All models use source_row_index
- `frontend/src/types/index.ts` - TypeScript types use source_row_index
- `backend/app/services/rate_parsers.py` - All parsers set source_row_index
- `backend/app/services/concept_calculator.py` - Calculator uses source_row_index

**Tests Added:**
- `test_concept_estimate_line_item_has_all_source_fields` - Validates all 3 fields present
- `test_rate_row_has_all_source_fields` - Validates RateRow schema
- `test_concept_line_item_optional_source_fields` - Validates optional behavior

### D) Final Validation ✅

**Documentation Updates:**

1. **EXCEL_REQUIREMENTS.md:**
   - Added CRITICAL section for mandatory tables
   - Changed "Verification" to "STRICT ENFORCEMENT"
   - Enhanced error resolution guidance
   - Clear distinction between errors and allowed scenarios

2. **README.md:**
   - Comprehensive troubleshooting section
   - ConfigError resolution steps
   - UncachedFormulaError resolution steps
   - Clear explanations and solutions

**Tests:**
```bash
$ python -m pytest tests/
========================== 31 passed, 12 warnings in 0.34s ==========================
```

**Backend Startup:**
```bash
$ python backend/main.py
INFO:     Application startup complete.
# Success - no errors
```

**.gitignore Verification:**
```
uploads/          # Excel upload directory
*.xlsm            # Excel macro-enabled
*.xlsx            # Excel workbook
*.xls             # Excel legacy
```

## Code Examples

### Config Loader - Strict Table Validation

```python
def _validate_required_tables(self):
    """Validate that ALL required tables exist in the workbook."""
    found_tables = set()
    searched_sheets = []
    
    for sheet in self.workbook.worksheets:
        searched_sheets.append(sheet.title)
        if hasattr(sheet, 'tables'):
            found_tables.update(sheet.tables.keys())
    
    missing_tables = [table for table in REQUIRED_TABLES if table not in found_tables]
    
    if missing_tables:
        raise ConfigError(
            f"Missing required tables in master workbook '{self.workbook_path.name}': "
            f"{', '.join(missing_tables)}. "
            f"Required tables: {', '.join(REQUIRED_TABLES)}. "
            f"Searched sheets: {', '.join(searched_sheets)}. "
            f"Found tables: {', '.join(sorted(found_tables)) if found_tables else 'none'}."
        )
```

### Rate Parser - Strict None Checking

```python
# Check if description matches search
if search_lower not in description.lower():
    previous_row_data = None
    continue

# DATA ROW DETECTED (matched search)
# Now check for None in critical fields
if row[0] is None:
    raise UncachedFormulaError(
        f"Workbook contains formulas without cached values. "
        f"Open '{self.source_filename}' in Excel, calculate (F9), save, and re-upload. "
        f"Source: {self.source_filename}, Sheet: {sheet_name}, Row: {row_idx}, "
        f"Column(s) with None: description"
    )

# Parse rate values...
if none_columns and not city_values and len(none_columns) >= 2:
    raise UncachedFormulaError(
        f"Workbook contains formulas without cached values. "
        f"Open '{self.source_filename}' in Excel, calculate (F9), save, and re-upload. "
        f"Source: {self.source_filename}, Sheet: {sheet_name}, Row: {row_idx}, "
        f"Column(s) with None: {', '.join(none_columns)}"
    )
```

## User Experience

### Before (Permissive)
```
WARNING: Table 'tbl_SCHEMA' row 5: None value (uncached formula?)
WARNING: BCM2 sheet 'Office' row 42: description is None (uncached formula?)
# App continues with incomplete data
```

### After (Strict)
```
ConfigError: Missing required tables in master workbook 'test.xlsm': tbl_Pricing_Flow, tbl_Rules. 
Required tables: tbl_SCHEMA, tbl_Pricing_Flow, tbl_Rules, tbl_Rate_Library_Map. 
Searched sheets: Sheet1, Sheet2. 
Found tables: tbl_SCHEMA.

UncachedFormulaError: Workbook contains formulas without cached values. 
Open 'Building Costs m2 NZ.xlsm' in Excel, calculate (F9), save, and re-upload. 
Source: Building Costs m2 NZ.xlsm, Sheet: Office Buildings, Row: 42, 
Column(s) with None: Auckland, Wellington
```

## Test Coverage Summary

| Category | Tests | Status |
|----------|-------|--------|
| Config Loader Strict | 5 | ✅ All Pass |
| Rate Parser Strict | 8 | ✅ All Pass |
| Source Fields | 3 | ✅ All Pass |
| Schema Validation | 4 | ✅ All Pass |
| Pricing Flow | 3 | ✅ All Pass |
| Rate Parsers | 4 | ✅ All Pass |
| Rules Engine | 4 | ✅ All Pass |
| **Total** | **31** | **✅ 100%** |

## Files Modified

### New Files
- `backend/app/core/exceptions.py` - Custom exception classes
- `tests/test_config_loader_strict.py` - Config loader strict tests
- `tests/test_rate_parsers_strict.py` - Rate parser strict tests
- `tests/test_source_fields.py` - Source field standardization tests

### Modified Files
- `backend/app/services/config_loader.py` - Strict table validation
- `backend/app/services/rate_parsers.py` - Strict None checking
- `EXCEL_REQUIREMENTS.md` - Mandatory table documentation
- `README.md` - Enhanced troubleshooting

## Verification Checklist

- [x] ConfigLoader has NO fallback logic
- [x] ConfigError raised when tables missing
- [x] Error lists all missing tables, searched sheets, found tables
- [x] Rate parsers raise UncachedFormulaError for None in data rows
- [x] Error includes source_file, source_sheet, row, columns
- [x] Empty rows and headers still allowed (not errors)
- [x] All code uses source_file, source_sheet, source_row_index
- [x] No "source_row" usage found
- [x] EXCEL_REQUIREMENTS.md documents mandatory tables
- [x] README.md has comprehensive troubleshooting
- [x] .gitignore excludes /uploads and *.xl*
- [x] All 31 tests pass
- [x] Backend starts successfully

## Conclusion

All hard fixes have been implemented with:
- **Zero tolerance** for missing tables or uncached formulas in data rows
- **Clear, actionable** error messages
- **Comprehensive** test coverage
- **Consistent** documentation

The application now enforces strict configuration requirements with no fallback behavior.
