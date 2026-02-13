import pytest
from app.services.rules_engine import RulesEngine
from app.services.config_loader import ConfigLoader
from unittest.mock import Mock


@pytest.fixture
def mock_config_loader():
    """Mock config loader with rules"""
    loader = Mock(spec=ConfigLoader)
    loader.config = {
        "rules": [
            {
                "rule_id": "R-001",
                "applies_stage": "All",
                "condition": "shell_only=true AND fitout_required=true",
                "block_progress": "true",
                "message": "Cannot have shell_only and fitout_required both true without fitout allowance"
            },
            {
                "rule_id": "R-002",
                "applies_stage": "Concept",
                "condition": "gfa_m2>100000",
                "block_progress": "true",
                "message": "Projects over 100,000 m² require preliminary design stage minimum"
            },
            {
                "rule_id": "R-003",
                "applies_stage": "Detailed",
                "condition": "building_type=Warehouse",
                "block_progress": "false",
                "message": "Warehouse projects have simplified requirements"
            }
        ]
    }
    return loader


def test_rules_no_blocking(mock_config_loader, monkeypatch):
    """Test that valid projects pass rules evaluation"""
    monkeypatch.setattr('app.services.rules_engine.get_config_loader', lambda: mock_config_loader)
    
    engine = RulesEngine()
    
    project_data = {
        "project_stage": "Concept",
        "building_type": "Office",
        "gfa_m2": 5000,
        "shell_only": False,
        "fitout_required": False
    }
    
    is_blocked, reasons, audit = engine.evaluate_rules(project_data)
    
    assert is_blocked is False
    assert len(reasons) == 0


def test_rules_blocking_condition(mock_config_loader, monkeypatch):
    """Test that blocking rules are enforced"""
    monkeypatch.setattr('app.services.rules_engine.get_config_loader', lambda: mock_config_loader)
    
    engine = RulesEngine()
    
    project_data = {
        "project_stage": "Concept",
        "building_type": "Office",
        "gfa_m2": 5000,
        "shell_only": "true",  # String representation
        "fitout_required": "true"
    }
    
    is_blocked, reasons, audit = engine.evaluate_rules(project_data)
    
    assert is_blocked is True
    assert len(reasons) > 0
    assert any("shell_only" in reason for reason in reasons)


def test_rules_stage_specific(mock_config_loader, monkeypatch):
    """Test that rules only apply to relevant stages"""
    monkeypatch.setattr('app.services.rules_engine.get_config_loader', lambda: mock_config_loader)
    
    engine = RulesEngine()
    
    # This would block at Concept stage but shouldn't block at Preliminary
    project_data = {
        "project_stage": "Preliminary",  # Not Concept
        "building_type": "Office",
        "gfa_m2": 150000  # Over limit for Concept
    }
    
    is_blocked, reasons, audit = engine.evaluate_rules(project_data)
    
    # Should not be blocked because rule only applies to Concept stage
    assert is_blocked is False


def test_rules_non_blocking_rules_logged(mock_config_loader, monkeypatch):
    """Test that non-blocking rules are still logged in audit trail"""
    monkeypatch.setattr('app.services.rules_engine.get_config_loader', lambda: mock_config_loader)
    
    engine = RulesEngine()
    
    project_data = {
        "project_stage": "Detailed",
        "building_type": "Warehouse",
        "gfa_m2": 5000
    }
    
    is_blocked, reasons, audit = engine.evaluate_rules(project_data)
    
    assert is_blocked is False
    # Non-blocking rule should still appear in audit
    assert any("R-003" in entry.rule_id for entry in audit if entry.rule_id)
