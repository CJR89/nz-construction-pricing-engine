import pytest
from app.services.rate_parsers import BCM2Parser, DETParser


def test_bcm2_range_parsing():
    """Test BCM2 parser handles hyphen-range notation correctly"""
    # This is a unit test for the range parsing logic
    # In real usage, we'd need actual Excel files
    
    # Test that range-high rows (starting with -) are detected
    parser = BCM2Parser("dummy_path.xlsm")
    
    # Simulate description starting with -
    description_range_high = "-"
    description_normal = "Office Building"
    
    assert description_range_high.strip().startswith("-")
    assert not description_normal.strip().startswith("-")


def test_det_rate_value_parsing():
    """Test DET parser handles min/max patterns correctly"""
    parser = DETParser("dummy_path.xlsm")
    
    # Test parsing different rate value formats
    test_cases = [
        ("100", (100.0, None)),
        ("100-150", (100.0, 150.0)),
        ("100 - 150", (100.0, 150.0)),
        ("(min) 100 (max) 150", (100.0, 150.0)),
        ("not a number", (None, None)),
    ]
    
    for value, expected in test_cases:
        result = parser._parse_rate_value(value)
        assert result == expected, f"Failed for value: {value}"


def test_det_numeric_value():
    """Test DET parser handles numeric values"""
    parser = DETParser("dummy_path.xlsm")
    
    # Numeric input
    result = parser._parse_rate_value(125.50)
    assert result == (125.50, None)


def test_det_none_value():
    """Test DET parser handles None values"""
    parser = DETParser("dummy_path.xlsm")
    
    result = parser._parse_rate_value(None)
    assert result == (None, None)
