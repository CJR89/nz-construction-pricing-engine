import pytest
from app.models.schemas import ConceptEstimateLineItem, RateRow


def test_concept_estimate_line_item_has_all_source_fields():
    """Test that ConceptEstimateLineItem includes all three standardized source fields"""
    line_item = ConceptEstimateLineItem(
        description="Base build - Office",
        quantity=5000.0,
        unit="m2",
        rate=3500.0,
        amount=17500000.0,
        source_file="Building Costs m2 NZ.xlsm",
        source_sheet="Office Buildings",
        source_row_index=42,
        note="Rate for Auckland"
    )
    
    # Verify all three source fields are present
    assert hasattr(line_item, 'source_file')
    assert hasattr(line_item, 'source_sheet')
    assert hasattr(line_item, 'source_row_index')
    
    # Verify values
    assert line_item.source_file == "Building Costs m2 NZ.xlsm"
    assert line_item.source_sheet == "Office Buildings"
    assert line_item.source_row_index == 42
    
    # Verify serialization includes these fields
    line_item_dict = line_item.dict()
    assert 'source_file' in line_item_dict
    assert 'source_sheet' in line_item_dict
    assert 'source_row_index' in line_item_dict
    
    # Ensure 'source_row' is NOT present
    assert 'source_row' not in line_item_dict


def test_rate_row_has_all_source_fields():
    """Test that RateRow includes all three standardized source fields"""
    rate_row = RateRow(
        description="Office Building - Standard Fitout",
        unit="m2",
        city_values={
            "Auckland": {"low": 3500.0, "high": 4200.0}
        },
        source_file="Building Costs m2 NZ.xlsm",
        source_sheet="Office Buildings",
        source_row_index=15
    )
    
    # Verify all three source fields are present
    assert hasattr(rate_row, 'source_file')
    assert hasattr(rate_row, 'source_sheet')
    assert hasattr(rate_row, 'source_row_index')
    
    # Verify values
    assert rate_row.source_file == "Building Costs m2 NZ.xlsm"
    assert rate_row.source_sheet == "Office Buildings"
    assert rate_row.source_row_index == 15
    
    # Verify serialization
    rate_dict = rate_row.dict()
    assert 'source_file' in rate_dict
    assert 'source_sheet' in rate_dict
    assert 'source_row_index' in rate_dict
    
    # Ensure 'source_row' is NOT present
    assert 'source_row' not in rate_dict


def test_concept_line_item_optional_source_fields():
    """Test that source fields are optional for non-priced line items"""
    # Line item without source (e.g., "Not priced" items)
    line_item = ConceptEstimateLineItem(
        description="Demolition (if required)",
        note="Not priced - provide if required"
    )
    
    # Should allow None for optional source fields
    assert line_item.source_file is None
    assert line_item.source_sheet is None
    assert line_item.source_row_index is None
    
    # Serialization should work
    line_item_dict = line_item.dict()
    assert 'source_file' in line_item_dict
    assert 'source_sheet' in line_item_dict
    assert 'source_row_index' in line_item_dict
