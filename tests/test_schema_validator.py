import pytest
from app.services.schema_validator import SchemaValidator
from app.services.config_loader import ConfigLoader
from unittest.mock import Mock


@pytest.fixture
def mock_config_loader():
    """Mock config loader with sample schema"""
    loader = Mock(spec=ConfigLoader)
    loader.config = {
        "schema": [
            {
                "entity": "Project_Input",
                "field_name": "project_id",
                "field_type": "string",
                "required": "yes",
                "applies_stage": "All"
            },
            {
                "entity": "Project_Input",
                "field_name": "building_type",
                "field_type": "string",
                "required": "yes",
                "applies_stage": "Concept,Preliminary,Developed,Detailed"
            },
            {
                "entity": "Project_Input",
                "field_name": "gfa_m2",
                "field_type": "number",
                "required": "yes",
                "applies_stage": "Concept"
            },
            {
                "entity": "Project_Input",
                "field_name": "optional_field",
                "field_type": "string",
                "required": "no",
                "applies_stage": "All"
            }
        ]
    }
    
    def get_schema_for_entity(entity):
        return [f for f in loader.config["schema"] if f.get("entity") == entity]
    
    loader.get_schema_for_entity = get_schema_for_entity
    return loader


def test_validate_project_input_success(mock_config_loader, monkeypatch):
    """Test successful validation of project input"""
    monkeypatch.setattr('app.services.schema_validator.get_config_loader', lambda: mock_config_loader)
    
    validator = SchemaValidator()
    
    project_data = {
        "project_id": "PROJ-001",
        "project_stage": "Concept",
        "building_type": "Office",
        "gfa_m2": 5000.0
    }
    
    is_valid, errors, missing = validator.validate_project_input(project_data)
    
    assert is_valid is True
    assert len(errors) == 0
    assert len(missing) == 0


def test_validate_project_input_missing_required(mock_config_loader, monkeypatch):
    """Test validation fails when required fields missing"""
    monkeypatch.setattr('app.services.schema_validator.get_config_loader', lambda: mock_config_loader)
    
    validator = SchemaValidator()
    
    project_data = {
        "project_id": "PROJ-001",
        "project_stage": "Concept"
        # Missing building_type and gfa_m2
    }
    
    is_valid, errors, missing = validator.validate_project_input(project_data)
    
    assert is_valid is False
    assert "building_type" in missing
    assert "gfa_m2" in missing


def test_validate_project_input_type_error(mock_config_loader, monkeypatch):
    """Test validation fails on type mismatch"""
    monkeypatch.setattr('app.services.schema_validator.get_config_loader', lambda: mock_config_loader)
    
    validator = SchemaValidator()
    
    project_data = {
        "project_id": "PROJ-001",
        "project_stage": "Concept",
        "building_type": "Office",
        "gfa_m2": "not_a_number"  # Type error
    }
    
    is_valid, errors, missing = validator.validate_project_input(project_data)
    
    assert is_valid is False
    assert len(errors) > 0
    assert any("gfa_m2" in error for error in errors)


def test_validate_stage_specific_fields(mock_config_loader, monkeypatch):
    """Test that fields required only for specific stages are handled correctly"""
    monkeypatch.setattr('app.services.schema_validator.get_config_loader', lambda: mock_config_loader)
    
    validator = SchemaValidator()
    
    # Preliminary stage - gfa_m2 not required
    project_data = {
        "project_id": "PROJ-001",
        "project_stage": "Preliminary",
        "building_type": "Office"
        # gfa_m2 not provided, but only required for Concept
    }
    
    is_valid, errors, missing = validator.validate_project_input(project_data)
    
    assert is_valid is True
    assert "gfa_m2" not in missing
