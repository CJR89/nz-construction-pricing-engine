import pytest
from app.services.pricing_flow_selector import PricingFlowSelector
from app.services.config_loader import ConfigLoader
from unittest.mock import Mock


@pytest.fixture
def mock_config_loader():
    """Mock config loader with pricing flow data"""
    loader = Mock(spec=ConfigLoader)
    loader.config = {
        "pricing_flow": [
            {
                "project_stage": "Concept",
                "primary_library": "BCM2",
                "secondary_library": None,
                "rule_id": "PF-001"
            },
            {
                "project_stage": "Preliminary",
                "primary_library": "ELEM",
                "secondary_library": "BCM2",
                "rule_id": "PF-002"
            },
            {
                "project_stage": "Developed",
                "primary_library": "CPR",
                "secondary_library": "ELEM",
                "rule_id": "PF-003"
            },
            {
                "project_stage": "Detailed",
                "primary_library": "DET",
                "secondary_library": "CPR",
                "rule_id": "PF-004"
            }
        ]
    }
    
    def get_pricing_flow_for_stage(stage):
        for flow in loader.config["pricing_flow"]:
            if flow.get("project_stage") == stage:
                return flow
        return None
    
    loader.get_pricing_flow_for_stage = get_pricing_flow_for_stage
    return loader


def test_select_libraries_concept(mock_config_loader, monkeypatch):
    """Test library selection for Concept stage"""
    monkeypatch.setattr('app.services.pricing_flow_selector.get_config_loader', lambda: mock_config_loader)
    
    selector = PricingFlowSelector()
    
    project_data = {
        "project_stage": "Concept",
        "building_type": "Office"
    }
    
    primary, secondary, audit = selector.select_libraries(project_data)
    
    assert primary == "BCM2"
    assert secondary is None
    assert "BCM2" in audit.decision


def test_select_libraries_preliminary(mock_config_loader, monkeypatch):
    """Test library selection for Preliminary stage"""
    monkeypatch.setattr('app.services.pricing_flow_selector.get_config_loader', lambda: mock_config_loader)
    
    selector = PricingFlowSelector()
    
    project_data = {
        "project_stage": "Preliminary",
        "building_type": "Office"
    }
    
    primary, secondary, audit = selector.select_libraries(project_data)
    
    assert primary == "ELEM"
    assert secondary == "BCM2"
    assert "ELEM" in audit.decision


def test_select_libraries_default_fallback(mock_config_loader, monkeypatch):
    """Test fallback behavior when no flow rule matches"""
    monkeypatch.setattr('app.services.pricing_flow_selector.get_config_loader', lambda: mock_config_loader)
    
    selector = PricingFlowSelector()
    
    project_data = {
        "project_stage": "UnknownStage",
        "building_type": "Office"
    }
    
    primary, secondary, audit = selector.select_libraries(project_data)
    
    # Should fallback to BCM2 for unknown stages
    assert primary == "BCM2"
    assert "default" in audit.decision.lower()
