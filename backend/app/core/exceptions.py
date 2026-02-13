"""
Custom exceptions for the NZ Construction Pricing Engine
"""


class ConfigError(Exception):
    """Raised when configuration loading fails due to missing or invalid tables"""
    pass


class UncachedFormulaError(Exception):
    """Raised when Excel workbook contains uncached formulas in data rows"""
    pass
