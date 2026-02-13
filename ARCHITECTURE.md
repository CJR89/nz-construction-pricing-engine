# NZ Construction Pricing Engine - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  http://localhost:5173                                      │
├─────────────────────────────────────────────────────────────┤
│  Pages:                                                      │
│  • FileUpload        - Upload 5 Excel files                 │
│  • ProjectForm       - Create & evaluate projects           │
│  • RateLookup        - Search rate libraries                │
│  • ConceptEstimate   - Generate estimates                   │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                   Backend API (FastAPI)                      │
│  http://localhost:8000/api                                  │
├─────────────────────────────────────────────────────────────┤
│  Routes:                                                     │
│  • POST   /upload                                           │
│  • GET    /config/summary                                   │
│  • POST   /projects                                         │
│  • GET    /projects/:id                                     │
│  • POST   /projects/:id/evaluate                           │
│  • POST   /rates/search                                     │
│  • POST   /estimate/concept                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
├─────────────────────────────────────────────────────────────┤
│  • ConfigLoader          - Read master workbook tables       │
│  • SchemaValidator       - Validate project inputs          │
│  • RulesEngine          - Evaluate blocking conditions       │
│  • PricingFlowSelector  - Select rate libraries             │
│  • RateParsers          - Parse 4 rate libraries            │
│  • ConceptCalculator    - Calculate estimates               │
│  • EvaluationEngine     - Coordinate all services           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources                              │
├─────────────────────────────────────────────────────────────┤
│  Excel Files (Read-Only):                                   │
│  • Construction_Knowledge_Base.xlsm (Master)                │
│    - tbl_SCHEMA         - Field definitions                 │
│    - tbl_Pricing_Flow   - Library selection                 │
│    - tbl_Rules          - Governance rules                  │
│    - tbl_Rate_Library_Map - Parsing rules                   │
│  • Building Costs m2 NZ.xlsm (BCM2)                         │
│  • Elemental Costs of Building NZ.xlsm (ELEM)               │
│  • CostPlan NZ Rates.xlsx (CPR)                             │
│  • Detailed Rates NZ.xlsm (DET)                             │
│                                                              │
│  Database (SQLite):                                          │
│  • projects          - Project data                          │
│  • uploaded_files    - File tracking                         │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow: Project Evaluation

```
1. User Input
   ↓
2. Schema Validation
   - Check required fields for stage
   - Validate data types
   - Check allowed values
   ↓
3. Rules Evaluation
   - Apply governance rules
   - Check blocking conditions
   - Log all rule matches
   ↓
4. Pricing Flow Selection
   - Determine project stage
   - Select primary library (BCM2/ELEM/CPR/DET)
   - Select secondary library (optional)
   ↓
5. Output with Audit Trail
   - Selected libraries
   - Blocking status
   - Missing inputs (if any)
   - Complete audit log
```

## Data Flow: Concept Estimate

```
1. Project Data
   ↓
2. Validate Required Inputs
   - building_type ✓
   - location_city ✓
   - gfa_m2 ✓
   - fitout_allowance_per_m2 (if shell+fitout) ✓
   ↓
3. Rate Lookup (BCM2)
   - Find matching building type
   - Get rate for location city
   - Extract low/high range
   ↓
4. Calculate Base Cost
   - base_build_cost = rate × gfa_m2
   ↓
5. Add Fitout (if required)
   - fitout_cost = allowance × gfa_m2
   ↓
6. Generate Line Items
   - Base build (with source reference)
   - Fitout (with source reference)
   - Placeholders (demo, services, fees, GST)
   ↓
7. Output Estimate
   - Line item breakdown
   - Source traceability
   - Disclaimer
   - Audit log
```

## Key Design Principles

### 1. Excel as READ-ONLY Configuration

```python
# ✅ CORRECT: Read values only
workbook = openpyxl.load_workbook(path, data_only=True)
value = cell.value  # Read cached value

# ❌ WRONG: Execute formulas
workbook = openpyxl.load_workbook(path, data_only=False)
result = workbook.calculate()  # NEVER DO THIS
```

### 2. Table-Based Loading

```python
# ✅ CORRECT: Use table names
for sheet in workbook.worksheets:
    if 'tbl_SCHEMA' in sheet.tables:
        table = sheet.tables['tbl_SCHEMA']
        data_range = table.ref

# ❌ WRONG: Fixed cell positions
data = sheet['A1:F100']  # NEVER USE FIXED RANGES
```

### 3. Strict Blocking

```python
# ✅ CORRECT: Block and explain
if missing_inputs:
    return {
        "blocked_reason": "Missing required inputs",
        "required_missing_inputs": missing_inputs,
        "next_action": f"Provide: {', '.join(missing_inputs)}"
    }

# ❌ WRONG: Guess or use defaults
if not gfa_m2:
    gfa_m2 = 1000  # NEVER GUESS VALUES
```

### 4. Source Traceability

```python
# ✅ CORRECT: Include source references
rate_row = {
    "description": "Office Building",
    "rate": 3500,
    "source_file": "Building Costs m2 NZ.xlsm",
    "source_sheet": "Office Buildings",
    "source_row_index": 42
}

# ❌ WRONG: No traceability
rate_row = {
    "description": "Office Building",
    "rate": 3500
    # Missing source information
}
```

## Error Handling Strategy

### 1. Missing Required Files
```
ERROR: Configuration not loaded. 
ACTION: Upload master workbook via /api/upload
```

### 2. Uncached Formulas
```
WARNING: Table 'tbl_SCHEMA' row 5: None value (uncached formula)
ACTION: Open Excel, press F9, save, re-upload
```

### 3. Missing Required Inputs
```
BLOCKED: Missing required inputs
INPUTS: building_type, location_city, gfa_m2
ACTION: Provide missing fields
```

### 4. Rate Not Found
```
BLOCKED: Rate not found for building_type='Office', location='Auckland'
ACTION: Verify inputs or use Rate Lookup to explore available rates
```

## Testing Strategy

```
tests/
├── test_schema_validator.py
│   ✓ Success case
│   ✓ Missing required fields
│   ✓ Type validation
│   ✓ Stage-specific fields
│
├── test_pricing_flow.py
│   ✓ Concept stage → BCM2
│   ✓ Preliminary stage → ELEM + BCM2
│   ✓ Default fallback
│
├── test_rate_parsers.py
│   ✓ BCM2 hyphen-range detection
│   ✓ DET min/max parsing
│   ✓ Numeric value handling
│   ✓ None value handling
│
└── test_rules_engine.py
    ✓ No blocking (valid project)
    ✓ Blocking condition enforced
    ✓ Stage-specific rules
    ✓ Non-blocking rules logged
```

## Deployment Checklist

### Prerequisites
- [ ] Python 3.9+ installed
- [ ] Node.js 18+ installed
- [ ] All 5 Excel files prepared with cached formulas

### Setup
- [ ] Run `./setup.sh` or manual installation
- [ ] Copy `.env.example` to `.env`
- [ ] Create `/uploads` directory

### Verification
- [ ] Backend starts: `cd backend && python main.py`
- [ ] Frontend starts: `cd frontend && npm run dev`
- [ ] Tests pass: `python run_tests.py`
- [ ] Upload all Excel files via UI
- [ ] Create test project
- [ ] Generate concept estimate

### Production Considerations
- [ ] Use production WSGI server (gunicorn/uvicorn)
- [ ] Configure proper CORS origins
- [ ] Set up file backup strategy
- [ ] Implement user authentication (if required)
- [ ] Set up monitoring and logging
- [ ] Regular rate library updates

## Maintenance

### Updating Rate Libraries
1. Open Excel file
2. Update rates
3. Press F9 to recalculate
4. Save file
5. Upload via /api/upload

### Adding New Rules
1. Open master workbook
2. Add row to tbl_Rules table
3. Save file
4. Upload via /api/upload
5. System automatically reloads config

### Adding New Fields
1. Add row to tbl_SCHEMA table
2. Update relevant services if needed
3. Update frontend forms if needed
4. Add to validation logic if needed

## Performance Characteristics

- **Config Loading**: ~1-2 seconds (cached after first load)
- **Rate Search**: ~0.1-0.5 seconds (depends on workbook size)
- **Concept Estimate**: ~0.2-0.8 seconds
- **Project Evaluation**: ~0.1-0.3 seconds

## Security Considerations

✅ **Implemented:**
- No formula execution (data_only=True)
- No VBA execution
- Input validation on all endpoints
- CORS configuration
- Files stored outside git

🔒 **Consider for Production:**
- User authentication
- Role-based access control
- API rate limiting
- Encrypted file storage
- Audit log retention policy
