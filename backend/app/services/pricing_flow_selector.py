"""
Pricing Flow Selector Module
Determines primary and secondary rate libraries based on project stage and conditions.
"""

from typing import Dict, Any, Optional, Tuple
from app.services.config_loader import get_config_loader
from app.models.schemas import AuditLogEntry
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PricingFlowSelector:
    """Selects appropriate rate libraries based on pricing flow rules"""
    
    def __init__(self):
        self.config_loader = get_config_loader()
    
    def select_libraries(self, project_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], AuditLogEntry]:
        """
        Select primary and secondary libraries for project.
        
        Returns:
            Tuple of (primary_library, secondary_library, audit_entry)
        """
        if not self.config_loader:
            logger.error("Config loader not initialized")
            audit = AuditLogEntry(
                action="pricing_flow_selection",
                decision="Failed",
                reason="Configuration not loaded",
                source="pricing_flow_selector"
            )
            return None, None, audit
        
        project_stage = project_data.get("project_stage", "Concept")
        building_type = project_data.get("building_type")
        
        # Get pricing flow for stage
        flow_rule = self.config_loader.get_pricing_flow_for_stage(project_stage)
        
        if not flow_rule:
            # Default fallback based on stage
            primary = self._get_default_library_for_stage(project_stage)
            audit = AuditLogEntry(
                action="pricing_flow_selection",
                decision=f"Selected {primary} as primary library (default)",
                reason=f"No specific flow rule found for stage '{project_stage}'",
                source="pricing_flow_selector (default)"
            )
            return primary, None, audit
        
        # Extract libraries from flow rule
        primary_library = flow_rule.get("primary_library")
        secondary_library = flow_rule.get("secondary_library")
        
        # Create audit entry
        audit = AuditLogEntry(
            action="pricing_flow_selection",
            decision=f"Selected {primary_library} as primary library" + 
                     (f", {secondary_library} as secondary" if secondary_library else ""),
            reason=f"project_stage={project_stage}" + 
                   (f", building_type={building_type}" if building_type else ""),
            rule_id=flow_rule.get("rule_id") or flow_rule.get("id"),
            source=f"Pricing_Flow sheet, row matched for stage {project_stage}"
        )
        
        logger.info(f"Selected libraries: primary={primary_library}, secondary={secondary_library}")
        return primary_library, secondary_library, audit
    
    def _get_default_library_for_stage(self, stage: str) -> str:
        """Get default library when no flow rule exists"""
        stage_defaults = {
            "Concept": "BCM2",
            "Preliminary": "ELEM",
            "Developed": "CPR",
            "Detailed": "DET"
        }
        return stage_defaults.get(stage, "BCM2")
