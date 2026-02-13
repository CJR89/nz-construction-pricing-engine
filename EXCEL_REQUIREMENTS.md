# Excel Workbook Requirements

This document specifies the exact requirements for the Excel workbooks used by the NZ Construction Pricing Engine.

## Critical Principles

1. **Read-Only Access**: Excel files are configuration and data sources only
2. **No Formula Execution**: Application reads VALUES, never executes formulas
3. **Table-Based Loading**: Configuration loaded from named Excel tables, not fixed cell positions
4. **Data Caching**: Formulas must be cached (saved with calculated values)
5. **MANDATORY TABLES**: Master workbook MUST contain all required named tables or the application will fail to start

## Master Workbook

**Filename:** `Construction_Knowledge_Base_FINALIZED_WITH_SCHEMA.xlsm`

### ⚠️ CRITICAL: Required Tables

The application will **FAIL TO START** if any of these tables are missing. All four tables MUST exist as named Excel Tables:

- `tbl_SCHEMA`
- `tbl_Pricing_Flow`
- `tbl_Rules`
- `tbl_Rate_Library_Map`

**Error Handling:** If any required table is missing, the application will raise a `ConfigError` with:
- List of missing table names
- Workbook filename
- Sheets that were searched
- Tables that were found (if any)

**No Fallback:** The application will NOT attempt to load data from sheets if tables are missing. Tables must be explicitly defined in Excel.

### Required Tables

#### 1. tbl_SCHEMA
Defines field structure, types, and validation rules.

**Required Columns:**
- `entity` - Entity name (e.g., "Project_Input")
- `field_name` - Field identifier
- `field_type` - Data type (string, number, boolean, etc.)
- `required` - "yes"/"no" indicating if field is mandatory
- `applies_stage` - Comma-separated list of stages where field applies (or "All")
- `allowed_values` - Optional comma-separated list of valid values

**Example Row:**
| entity | field_name | field_type | required | applies_stage | allowed_values |
|--------|------------|------------|----------|---------------|----------------|
| Project_Input | building_type | string | yes | Concept,Preliminary,Developed,Detailed | Office,Warehouse,Residential |

#### 2. tbl_Pricing_Flow
Defines which rate library to use for each project stage.

**Required Columns:**
- `project_stage` - Stage name (Concept, Preliminary, Developed, Detailed)
- `primary_library` - Primary rate library (BCM2, ELEM, CPR, DET)
- `secondary_library` - Optional secondary library
- `rule_id` - Optional identifier for audit trail

**Example Row:**
| project_stage | primary_library | secondary_library | rule_id |
|--------------|-----------------|-------------------|---------|
| Concept | BCM2 | | PF-001 |

#### 3. tbl_Rules
Governance rules and blocking conditions.

**Required Columns:**
- `rule_id` - Unique rule identifier
- `applies_stage` - Stage(s) where rule applies (or "All")
- `condition` - Condition expression (e.g., "shell_only=true AND fitout_required=true")
- `block_progress` - "true"/"false" - whether rule blocks progression
- `message` - User-facing message when rule triggers
- `description` - Optional detailed description

**Example Row:**
| rule_id | applies_stage | condition | block_progress | message |
|---------|--------------|-----------|----------------|---------|
| R-001 | All | shell_only=true AND fitout_required=true | true | Fitout allowance required when shell_only and fitout_required are both true |

#### 4. tbl_Rate_Library_Map
Describes how to parse each rate library.

**Required Columns:**
- `library` - Library identifier (BCM2, ELEM, CPR, DET)
- `detection_rule` - How to identify data rows vs headers
- `notes` - Parsing notes (e.g., "hyphen-prefix indicates range-high")

**Example Row:**
| library | detection_rule | notes |
|---------|---------------|-------|
| BCM2 | Skip first 5 rows, data starts row 6 | Rows starting with '-' are range-high values |

## Rate Libraries

### 1. Building Costs m² NZ (BCM2)

**Filename:** `Building Costs m2 NZ.xlsm`

**Structure:**
- Multiple sheets by building type
- Columns: Description, Auckland, Wellington, Christchurch, Hamilton, Tauranga, Dunedin
- Special notation: Rows with description starting with "-" indicate range-high (not negative)
- Unit: Always m²

**Example:**
| Description | Auckland | Wellington | Christchurch |
|------------|----------|------------|--------------|
| Office Building - Standard Fitout | 3500 | 3400 | 3200 |
| - | 4200 | 4100 | 3900 |

(Second row defines high range: Auckland $3500-$4200)

### 2. Elemental Costs of Building NZ (ELEM)

**Filename:** `Elemental Costs of Building NZ.xlsm`

**Structure:**
- Multiple sheets by element
- Columns: Description, Auckland, Wellington, Christchurch, Unit
- Values are elemental costs

### 3. CostPlan NZ Rates (CPR)

**Filename:** `CostPlan NZ Rates.xlsx` (Note: .xlsx not .xlsm)

**Structure:**
- Multiple sheets by category
- Columns: Description, Rate, Unit
- Single national rate (not city-specific)

### 4. Detailed Rates NZ (DET)

**Filename:** `Detailed Rates NZ.xlsm`

**Structure:**
- Multiple sheets by trade
- Columns: Description, Rate, Unit, Hours
- Special notation: "(min) 100 (max) 150" or "100-150" for ranges
- Most detailed rate library

## Data Integrity Requirements

### Formula Caching

**Problem:** `openpyxl` with `data_only=True` returns `None` for uncached formulas.

**Solution:** Before uploading Excel files:
1. Open each workbook in Excel
2. Press F9 to recalculate all formulas
3. Save the workbook
4. This caches all formula values

**STRICT ENFORCEMENT:** The application will **RAISE AN ERROR** (UncachedFormulaError) if it encounters None values in data rows that appear to be from uncached formulas. The error message will include:
- Workbook filename
- Sheet name
- Row number
- Column(s) with None values
- Instructions to open in Excel, calculate (F9), save, and re-upload

**What's Allowed:**
- Empty rows (all cells empty) - skipped automatically
- Header rows (first few rows in each sheet) - skipped automatically
- Truly empty data cells (optional fields)

**What Causes Errors:**
- Data rows with None in required fields (description, rates, etc.)
- Any row that matches search criteria but has None values indicating uncached formulas

### Table Names

All tables must be defined as Excel Tables (Insert → Table) with exact names:
- `tbl_SCHEMA`
- `tbl_Pricing_Flow`
- `tbl_Rules`
- `tbl_Rate_Library_Map`

**Verification:** In Excel, go to Formulas → Name Manager to see all table names.

**MANDATORY:** These tables are not optional. The application performs validation on startup and will fail immediately with a clear error message if tables are missing.

### Data Types

Ensure correct data types in cells:
- Numbers stored as numbers (not text)
- Booleans as TRUE/FALSE or yes/no (not "yes" text)
- Dates in proper date format if used

### Sheet Names

- Avoid starting sheet names with underscore (\_) as these are treated as internal sheets and skipped
- Use descriptive names for rate library sheets

## Upload Process

1. Navigate to File Upload page in application
2. Upload each file to its designated file type:
   - Master → master
   - BCM2 → bcm2
   - ELEM → elem
   - CPR → cpr
   - DET → det
3. Wait for confirmation message
4. System automatically loads configuration from master workbook

## Source Traceability

All outputs include source references:
- `source_file` - Exact filename
- `source_sheet` - Sheet name where data found
- `source_row_index` - Row number (1-indexed)

This enables full audit trail back to source data.

## Common Issues

### "Missing required tables" Error
**Error:** `ConfigError: Missing required tables in master workbook 'xxx.xlsm': tbl_XXX...`

**Solution:**
- Open master workbook in Excel
- Verify table names are exactly: tbl_SCHEMA, tbl_Pricing_Flow, tbl_Rules, tbl_Rate_Library_Map
- Check tables are defined as Excel Tables (Insert → Table), not just named ranges
- Use Formulas → Name Manager to verify table names
- Ensure table names match exactly (case-sensitive)

**Important:** The application will NOT fall back to reading sheets directly. Tables MUST exist.

### "Uncached formula" Error
**Error:** `UncachedFormulaError: Workbook contains formulas without cached values...`

**Solution:**
- Open the workbook mentioned in error
- Go to the sheet mentioned in error  
- Press F9 to recalculate all formulas
- Save the workbook
- Re-upload to application

**Why This Happens:** Excel formulas are not cached when:
- File saved without calculating
- Formulas were edited but not recalculated
- File was programmatically generated

### "Rate not found" Errors
- Check building type spelling matches descriptions in workbook
- Verify city names match exactly (Auckland not auckland)
- Use Rate Lookup page to explore available rates
- Ensure rate library workbook has cached formula values

## Best Practices

1. **Consistent Naming**: Use same terminology across all workbooks
2. **Complete Data**: Fill all cells in table columns (use 0 or N/A, not blank)
3. **Regular Updates**: Maintain a versioning system for rate libraries
4. **Backup**: Keep copies of workbooks before major changes
5. **Documentation**: Add notes sheets explaining structure and update history
