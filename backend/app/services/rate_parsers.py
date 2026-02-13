"""
Rate Parsers Module
Parses rate data from the 4 Excel rate libraries (BCM2, ELEM, CPR, DET).
Handles special notation like BCM2 hyphen-range and Detailed min/max patterns.
READ-ONLY: Uses openpyxl with data_only=True.
STRICT: Raises UncachedFormulaError when data rows contain None values.
"""

import openpyxl
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import re
from app.core.exceptions import UncachedFormulaError

logger = logging.getLogger(__name__)


class RateParser:
    """Base class for rate library parsers"""
    
    def __init__(self, workbook_path: str):
        self.workbook_path = Path(workbook_path)
        self.workbook = None
        self.source_filename = Path(workbook_path).name  # Store filename for source tracking
    
    def load_workbook(self):
        """Load Excel workbook (READ-ONLY: data_only=True)"""
        if not self.workbook_path.exists():
            raise FileNotFoundError(f"Workbook not found: {self.workbook_path}")
        
        # data_only=True ensures we read VALUES not formulas (read-only principle)
        # This may return None for uncached formulas - we handle this explicitly
        self.workbook = openpyxl.load_workbook(self.workbook_path, data_only=True)
        logger.info(f"Loaded workbook: {self.workbook_path}")
    
    def search_rates(self, search_text: str, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for rates matching text"""
        raise NotImplementedError("Subclasses must implement search_rates")
    
    def _is_header_or_note_row(self, row: tuple, row_idx: int, min_data_row: int = 5) -> bool:
        """
        Determine if row is a header, note, or section title (not data).
        Override in subclasses for library-specific logic.
        """
        # Rows before min_data_row are typically headers
        if row_idx < min_data_row:
            return True
        
        # Empty rows are not data
        if not any(row):
            return True
        
        return False


class BCM2Parser(RateParser):
    """Parser for Building Costs m2 NZ library"""
    
    def search_rates(self, search_text: str, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search BCM2 rates.
        Special handling: rows with '-' prefix are range-high, not negative.
        """
        if not self.workbook:
            self.load_workbook()
        
        results = []
        search_lower = search_text.lower()
        
        # Get sheets to search
        sheets_to_search = [sheet_name] if sheet_name else self.workbook.sheetnames
        
        for sheet_name in sheets_to_search:
            if sheet_name.startswith("_"):  # Skip internal sheets
                continue
            
            try:
                sheet = self.workbook[sheet_name]
            except KeyError:
                continue
            
            # Parse sheet rows
            previous_row_data = None
            
            for row_idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
                # Skip truly empty rows
                if not any(row):
                    continue
                
                # Skip header rows (first few rows)
                if row_idx < 5:
                    continue
                
                # Get description (usually first column)
                description = str(row[0]) if row[0] else ""
                
                # Check if this is a range-high row (starts with -)
                is_range_high = description.strip().startswith("-")
                
                if is_range_high and previous_row_data:
                    # This row defines the high range for previous row
                    # Update previous row with range-high values
                    previous_row_data["is_range"] = True
                    # Parse high values from this row
                    for i, cell in enumerate(row[1:], start=1):
                        if cell and isinstance(cell, (int, float)):
                            city_idx = i - 1
                            if city_idx < len(previous_row_data.get("city_columns", [])):
                                city_name = previous_row_data["city_columns"][city_idx]
                                if city_name in previous_row_data["city_values"]:
                                    previous_row_data["city_values"][city_name]["high"] = abs(float(cell))
                    continue
                
                # Check if description matches search
                if search_lower not in description.lower():
                    previous_row_data = None
                    continue
                
                # DATA ROW DETECTED (matched search)
                # Now check for None in critical fields - this indicates uncached formulas
                if row[0] is None:
                    # Description is None in a data row - this is an error
                    raise UncachedFormulaError(
                        f"Workbook contains formulas without cached values. "
                        f"Open '{self.source_filename}' in Excel, calculate (F9), save, and re-upload. "
                        f"Source: {self.source_filename}, Sheet: {sheet_name}, Row: {row_idx}, "
                        f"Column(s) with None: description"
                    )
                
                # Parse city values (assume columns after description)
                city_values = {}
                city_columns = ["Auckland", "Wellington", "Christchurch", "Hamilton", "Tauranga", "Dunedin"]
                none_columns = []
                
                for i, cell in enumerate(row[1:], start=1):
                    if i - 1 < len(city_columns):
                        city_name = city_columns[i - 1]
                        if cell is not None and isinstance(cell, (int, float)):
                            city_values[city_name] = {
                                "low": float(cell),
                                "high": None  # Will be filled if next row is range-high
                            }
                        elif cell is None:
                            # Track None columns for potential error
                            none_columns.append(city_name)
                
                # If this is a data row with matching search but has NO rate values at all, raise error
                # This indicates all rate columns have uncached formulas
                if none_columns and not city_values and len(none_columns) >= 2:
                    # Multiple None values in rate columns - likely uncached formulas
                    raise UncachedFormulaError(
                        f"Workbook contains formulas without cached values. "
                        f"Open '{self.source_filename}' in Excel, calculate (F9), save, and re-upload. "
                        f"Source: {self.source_filename}, Sheet: {sheet_name}, Row: {row_idx}, "
                        f"Column(s) with None: {', '.join(none_columns)}"
                    )
                
                # Create rate row
                rate_row = {
                    "description": description.strip(),
                    "unit": "m2",  # BCM2 is per m2
                    "city_values": city_values,
                    "city_columns": city_columns,
                    "hours": None,
                    "source_file": self.source_filename,  # Required for traceability
                    "source_sheet": sheet_name,
                    "source_row_index": row_idx,
                    "is_range": False
                }
                
                results.append(rate_row)
                previous_row_data = rate_row
        
        # Clean up temporary fields
        for result in results:
            result.pop("city_columns", None)
        
        logger.info(f"BCM2 search for '{search_text}' found {len(results)} results")
        return results


class ELEMParser(RateParser):
    """Parser for Elemental Costs of Building NZ library"""
    
    def search_rates(self, search_text: str, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search ELEM rates"""
        if not self.workbook:
            self.load_workbook()
        
        results = []
        search_lower = search_text.lower()
        
        sheets_to_search = [sheet_name] if sheet_name else self.workbook.sheetnames
        
        for sheet_name in sheets_to_search:
            if sheet_name.startswith("_"):
                continue
            
            try:
                sheet = self.workbook[sheet_name]
            except KeyError:
                continue
            
            for row_idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
                # Skip empty rows and header rows
                if not any(row) or row_idx < 3:
                    continue
                
                description = str(row[0]) if row[0] else ""
                
                # Skip if doesn't match search
                if search_lower not in description.lower():
                    continue
                
                # DATA ROW DETECTED (matched search) - check for None in critical fields
                if row[0] is None:
                    raise UncachedFormulaError(
                        f"Workbook contains formulas without cached values. "
                        f"Open '{self.source_filename}' in Excel, calculate (F9), save, and re-upload. "
                        f"Source: {self.source_filename}, Sheet: {sheet_name}, Row: {row_idx}, "
                        f"Column(s) with None: description"
                    )
                
                # Parse city values
                city_values = {}
                city_columns = ["Auckland", "Wellington", "Christchurch"]
                none_columns = []
                
                for i in range(1, min(4, len(row))):
                    if i - 1 < len(city_columns):
                        city_name = city_columns[i - 1]
                        cell = row[i]
                        if cell is not None and isinstance(cell, (int, float)):
                            city_values[city_name] = {
                                "low": float(cell),
                                "high": None
                            }
                        elif cell is None:
                            none_columns.append(city_name)
                
                # If all rate columns are None, likely uncached formulas
                if none_columns and not city_values:
                    raise UncachedFormulaError(
                        f"Workbook contains formulas without cached values. "
                        f"Open '{self.source_filename}' in Excel, calculate (F9), save, and re-upload. "
                        f"Source: {self.source_filename}, Sheet: {sheet_name}, Row: {row_idx}, "
                        f"Column(s) with None: {', '.join(none_columns)}"
                    )
                
                rate_row = {
                    "description": description.strip(),
                    "unit": row[4] if len(row) > 4 else None,
                    "city_values": city_values,
                    "hours": None,
                    "source_file": self.source_filename,  # Required for traceability
                    "source_sheet": sheet_name,
                    "source_row_index": row_idx
                }
                
                results.append(rate_row)
        
        logger.info(f"ELEM search for '{search_text}' found {len(results)} results")
        return results


class CPRParser(RateParser):
    """Parser for CostPlan NZ Rates library"""
    
    def search_rates(self, search_text: str, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search CPR rates"""
        if not self.workbook:
            self.load_workbook()
        
        results = []
        search_lower = search_text.lower()
        
        sheets_to_search = [sheet_name] if sheet_name else self.workbook.sheetnames
        
        for sheet_name in sheets_to_search:
            if sheet_name.startswith("_"):
                continue
            
            try:
                sheet = self.workbook[sheet_name]
            except KeyError:
                continue
            
            for row_idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
                # Skip empty rows and header rows
                if not any(row) or row_idx < 3:
                    continue
                
                description = str(row[0]) if row[0] else ""
                
                # Skip if doesn't match search
                if search_lower not in description.lower():
                    continue
                
                # DATA ROW DETECTED (matched search) - check for None in critical fields
                if row[0] is None:
                    raise UncachedFormulaError(
                        f"Workbook contains formulas without cached values. "
                        f"Open '{self.source_filename}' in Excel, calculate (F9), save, and re-upload. "
                        f"Source: {self.source_filename}, Sheet: {sheet_name}, Row: {row_idx}, "
                        f"Column(s) with None: description"
                    )
                
                # Parse rate value
                city_values = {}
                if len(row) > 1:
                    cell = row[1]
                    if cell is not None and isinstance(cell, (int, float)):
                        city_values["National"] = {
                            "low": float(cell),
                            "high": None
                        }
                    elif cell is None:
                        # Rate value is None in a data row - this is an error
                        raise UncachedFormulaError(
                            f"Workbook contains formulas without cached values. "
                            f"Open '{self.source_filename}' in Excel, calculate (F9), save, and re-upload. "
                            f"Source: {self.source_filename}, Sheet: {sheet_name}, Row: {row_idx}, "
                            f"Column(s) with None: rate_value"
                        )
                
                rate_row = {
                    "description": description.strip(),
                    "unit": row[2] if len(row) > 2 else None,
                    "city_values": city_values,
                    "hours": None,
                    "source_file": self.source_filename,  # Required for traceability
                    "source_sheet": sheet_name,
                    "source_row_index": row_idx
                }
                
                results.append(rate_row)
        
        logger.info(f"CPR search for '{search_text}' found {len(results)} results")
        return results


class DETParser(RateParser):
    """Parser for Detailed Rates NZ library"""
    
    def search_rates(self, search_text: str, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search DET rates.
        Special handling: (min)/(max) patterns and hyphen ranges.
        """
        if not self.workbook:
            self.load_workbook()
        
        results = []
        search_lower = search_text.lower()
        
        sheets_to_search = [sheet_name] if sheet_name else self.workbook.sheetnames
        
        for sheet_name in sheets_to_search:
            if sheet_name.startswith("_"):
                continue
            
            try:
                sheet = self.workbook[sheet_name]
            except KeyError:
                continue
            
            for row_idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
                # Skip empty rows and header rows
                if not any(row) or row_idx < 3:
                    continue
                
                description = str(row[0]) if row[0] else ""
                
                # Skip if doesn't match search
                if search_lower not in description.lower():
                    continue
                
                # DATA ROW DETECTED (matched search) - check for None in critical fields
                if row[0] is None:
                    raise UncachedFormulaError(
                        f"Workbook contains formulas without cached values. "
                        f"Open '{self.source_filename}' in Excel, calculate (F9), save, and re-upload. "
                        f"Source: {self.source_filename}, Sheet: {sheet_name}, Row: {row_idx}, "
                        f"Column(s) with None: description"
                    )
                
                # Parse rate with possible range notation
                rate_value = row[1] if len(row) > 1 else None
                low_val, high_val = self._parse_rate_value(rate_value)
                
                city_values = {}
                if low_val is not None:
                    city_values["National"] = {
                        "low": low_val,
                        "high": high_val
                    }
                
                rate_row = {
                    "description": description.strip(),
                    "unit": row[2] if len(row) > 2 else None,
                    "city_values": city_values,
                    "hours": row[3] if len(row) > 3 else None,
                    "source_file": self.source_filename,  # Required for traceability
                    "source_sheet": sheet_name,
                    "source_row_index": row_idx
                }
                
                results.append(rate_row)
        
        logger.info(f"DET search for '{search_text}' found {len(results)} results")
        return results
    
    def _parse_rate_value(self, value: Any) -> tuple:
        """Parse rate value that might contain range notation"""
        if value is None:
            return None, None
        
        if isinstance(value, (int, float)):
            return float(value), None
        
        # Check for patterns like "100-150" or "(min) 100 (max) 150"
        value_str = str(value)
        
        # Pattern: (min) X (max) Y
        min_max_pattern = r'\(min\)\s*([\d.]+)\s*\(max\)\s*([\d.]+)'
        match = re.search(min_max_pattern, value_str, re.IGNORECASE)
        if match:
            return float(match.group(1)), float(match.group(2))
        
        # Pattern: X-Y or X - Y
        range_pattern = r'([\d.]+)\s*-\s*([\d.]+)'
        match = re.search(range_pattern, value_str)
        if match:
            return float(match.group(1)), float(match.group(2))
        
        # Try to extract single number
        number_pattern = r'([\d.]+)'
        match = re.search(number_pattern, value_str)
        if match:
            return float(match.group(1)), None
        
        return None, None


# Parser factory
def get_parser(library: str, workbook_path: str) -> RateParser:
    """Get appropriate parser for library type"""
    parsers = {
        "BCM2": BCM2Parser,
        "ELEM": ELEMParser,
        "CPR": CPRParser,
        "DET": DETParser
    }
    
    parser_class = parsers.get(library.upper())
    if not parser_class:
        raise ValueError(f"Unknown library type: {library}")
    
    return parser_class(workbook_path)
