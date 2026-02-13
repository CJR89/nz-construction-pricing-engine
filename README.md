# NZ Construction Pricing Engine

Production-ready web application for pricing construction projects using 4 Excel rate libraries and a master knowledge/rules workbook.

**Critical Principle:** Excel is a READ-ONLY configuration and data source. No formula execution, no VBA, no hidden logic. All behavior is driven from parsed tables and schema.

## Overview

This application provides:
- **Schema-driven validation** of project inputs
- **Rule-based evaluation** with blocking conditions
- **Pricing flow selection** based on project stage
- **Rate library querying** with full traceability
- **Concept stage estimates** with audit trails
- **Strict blocking** when required inputs are missing (no guessing)

## Architecture

- **Backend:** Python FastAPI with SQLite database
- **Frontend:** React (TypeScript) with Vite
- **Excel Parsing:** openpyxl (read-only, data_only=True)
- **Configuration:** Loaded from named Excel tables, not fixed cell positions

## Required Excel Files

1. `Construction_Knowledge_Base_FINALIZED_WITH_SCHEMA.xlsm` - Master config workbook
   - **tbl_SCHEMA** - Field definitions, types, validation rules
   - **tbl_Pricing_Flow** - Rate library selection rules
   - **tbl_Rules** - Governance rules and blocking conditions
   - **tbl_Rate_Library_Map** - Rate library parsing rules

2. `Building Costs m2 NZ.xlsm` (BCM2) - Building costs per m²
3. `Elemental Costs of Building NZ.xlsm` (ELEM) - Elemental costing
4. `CostPlan NZ Rates.xlsx` (CPR) - CostPlan rates
5. `Detailed Rates NZ.xlsm` (DET) - Detailed unit rates

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/CJR89/nz-construction-pricing-engine.git
   cd nz-construction-pricing-engine
   ```

2. **Setup environment:**
   ```bash
   cp .env.example .env
   # Edit .env if needed (defaults should work for local development)
   ```

3. **Install backend dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies:**
   ```bash
   cd ../frontend
   npm install
   ```

### Running the Application

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```
Backend runs on http://localhost:8000

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```
Frontend runs on http://localhost:5173

### First Time Setup

1. Open http://localhost:5173 in your browser
2. **Upload all 5 required Excel files** via the File Upload page
3. Wait for confirmation that all files are uploaded
4. Navigate to Create Project to begin

## Usage Workflow

### 1. File Upload
- Upload all required Excel files
- System validates and stores files in `/uploads` directory
- Config is automatically loaded from master workbook

### 2. Create Project
- Fill in project details (ID, stage, building type, location, GFA)
- System validates against schema
- Project is saved to SQLite database

### 3. Evaluate Project
- Click "Evaluate Project" after creation
- System checks:
  - Required inputs for stage
  - Rules and blocking conditions
  - Determines primary/secondary rate libraries
- Returns evaluation with audit trail

### 4. Generate Estimate (Concept Stage Only)
- Navigate to Concept Estimate page
- Enter project ID
- System:
  - Validates all required inputs present
  - Looks up BCM2 rates for building type and location
  - Calculates base build cost
  - Adds fitout if required (with allowance)
  - Shows breakdown with source traceability
  - **BLOCKS if data missing - no guessing**

### 5. Rate Lookup (Optional)
- Search any rate library
- Filter by description
- View rates with full source references (file, sheet, row)

## API Endpoints

### File Management
- `POST /api/upload` - Upload Excel files
- `GET /api/config/summary` - Get config summary

### Projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project details
- `POST /api/projects/{id}/evaluate` - Evaluate project

### Rates
- `POST /api/rates/search` - Search rate libraries

### Estimates
- `POST /api/estimate/concept` - Calculate concept estimate

### Health
- `GET /health` - Health check and file status

## Testing

### Run all tests:
```bash
python run_tests.py
```

Or with pytest directly:
```bash
cd backend
python -m pytest ../tests/ -v
```

### Test Coverage
- Schema validation
- Pricing flow selection
- Range parsing (BCM2 hyphen notation, DET min/max)
- Rule blocking behavior

## Key Features

### Strict Validation
- **No guessing:** If required input missing, system blocks and lists missing fields
- **Type checking:** Validates field types against schema
- **Stage-aware:** Different requirements for different project stages

### Full Traceability
Every output includes:
- `source_file` - Excel filename
- `source_sheet` - Sheet name
- `source_row_index` - Row number

### Audit Logging
Every decision is logged:
- Which rule matched
- Which library selected
- What fields were missing
- Timestamps for all actions

### Excel Read-Only
- Uses `openpyxl` with `data_only=True`
- Reads VALUES only, never executes formulas
- Loads from named tables (tbl_*), not fixed positions
- Handles None from uncached formulas with clear warnings

## Directory Structure

```
nz-construction-pricing-engine/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Config and settings
│   │   ├── models/       # Database models and schemas
│   │   ├── services/     # Business logic
│   │   └── utils/        # Utilities
│   ├── main.py           # FastAPI application
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/        # React pages
│   │   ├── services/     # API client
│   │   └── types/        # TypeScript types
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── tests/                # Unit tests
├── uploads/              # Excel file storage (gitignored)
├── .env.example          # Environment template
└── README.md
```

## Configuration

### Environment Variables

See `.env.example` for all available settings:

- `BACKEND_PORT` - Backend server port (default: 8000)
- `UPLOAD_DIR` - Excel file storage (default: ./uploads)
- `DATABASE_URL` - SQLite database location
- `CORS_ORIGINS` - Allowed frontend origins

### Database

SQLite database is created automatically on first run at `./nz_pricing_engine.db`

Tables:
- `projects` - Project data and cached evaluations
- `uploaded_files` - Track uploaded Excel files

## Security

- No Excel formula execution
- No VBA macros
- Files stored locally (not in git)
- CORS configured for allowed origins only
- Input validation on all API endpoints

## Troubleshooting

### "Config not loaded" error
- Ensure master workbook is uploaded via /api/upload
- Check that workbook contains required tables: tbl_SCHEMA, tbl_Pricing_Flow, tbl_Rules, tbl_Rate_Library_Map

### "None value (uncached formula)" warnings
- Open Excel file and save with calculated values
- Ensure formulas are cached before uploading

### "Rate not found" errors
- Verify building type matches descriptions in BCM2
- Check location city is valid (Auckland, Wellington, etc.)
- Use Rate Lookup page to explore available rates

### CORS errors
- Check CORS_ORIGINS in .env includes frontend URL
- Default includes http://localhost:5173

## Development

### Adding New Rate Libraries
1. Create parser in `backend/app/services/rate_parsers.py`
2. Add library to `get_parser()` factory function
3. Update frontend types in `frontend/src/types/index.ts`

### Adding New Calculators
1. Create calculator in `backend/app/services/`
2. Add endpoint in `backend/app/api/routes.py`
3. Create frontend page in `frontend/src/pages/`

## License

Copyright (c) 2026. All rights reserved.

## Support

For issues and feature requests, please use GitHub Issues.