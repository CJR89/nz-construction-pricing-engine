"""
Evaluation Engine Module
Coordinates validation, pricing flow selection, and rules evaluation.
STRICT BLOCKING: No guessing - if inputs missing, block and report.
"""

from typing import Dict, Any
from app.services.schema_validator import SchemaValidator
from app.services.pricing_flow_selector import PricingFlowSelector
from app.services.rules_engine import RulesEngine
from app.models.schemas import EngineOutput, AuditLogEntry
import logging

logger = logging.getLogger(__name__)


class EvaluationEngine:
    """Main evaluation engine coordinating all validation and selection logic"""
    
    def __init__(self):
        self.validator = SchemaValidator()
        self.flow_selector = PricingFlowSelector()
        self.rules_engine = RulesEngine()
    
    def evaluate(self, project_data: Dict[str, Any]) -> EngineOutput:
        """
        Evaluate project and determine pricing approach.
        STRICT: Block if required inputs missing or rules violated.
        """
        project_id = project_data.get("project_id", "unknown")
        project_stage = project_data.get("project_stage", "Concept")
        audit_log = []
        
        # Step 1: Validate schema
        is_valid, errors, missing_required = self.validator.validate_project_input(project_data)
        
        if errors:
            audit_log.append(AuditLogEntry(
                action="schema_validation",
                decision="Validation errors found",
                reason=f"Errors: {'; '.join(errors)}",
                source="schema_validator"
            ))
        
        if missing_required:
            # BLOCK: Required inputs missing
            audit_log.append(AuditLogEntry(
                action="schema_validation",
                decision="BLOCKED - Required inputs missing",
                reason=f"Missing: {', '.join(missing_required)}",
                source="schema_validator"
            ))
            
            return EngineOutput(
                project_id=project_id,
                project_stage=project_stage,
                selected_primary_library=None,
                selected_secondary_library=None,
                blocked_reason="Missing required inputs",
                required_missing_inputs=missing_required,
                next_action=f"Please provide the following required fields: {', '.join(missing_required)}",
                audit_log=audit_log
            )
        
        if errors:
            # BLOCK: Validation errors
            return EngineOutput(
                project_id=project_id,
                project_stage=project_stage,
                selected_primary_library=None,
                selected_secondary_library=None,
                blocked_reason="Validation errors",
                required_missing_inputs=[],
                next_action=f"Fix validation errors: {'; '.join(errors)}",
                audit_log=audit_log
            )
        
        # Validation passed
        audit_log.append(AuditLogEntry(
            action="schema_validation",
            decision="Passed",
            reason="All required fields present and valid",
            source="schema_validator"
        ))
        
        # Step 2: Evaluate rules
        is_blocked, blocking_reasons, rule_audit = self.rules_engine.evaluate_rules(project_data)
        audit_log.extend(rule_audit)
        
        if is_blocked:
            # BLOCK: Rules violated
            audit_log.append(AuditLogEntry(
                action="rules_evaluation",
                decision="BLOCKED - Rules violated",
                reason="; ".join(blocking_reasons),
                source="rules_engine"
            ))
            
            return EngineOutput(
                project_id=project_id,
                project_stage=project_stage,
                selected_primary_library=None,
                selected_secondary_library=None,
                blocked_reason="Rules violation: " + "; ".join(blocking_reasons),
                required_missing_inputs=[],
                next_action=f"Address rule violations: {'; '.join(blocking_reasons)}",
                audit_log=audit_log
            )
        
        # Step 3: Select pricing libraries
        primary_lib, secondary_lib, flow_audit = self.flow_selector.select_libraries(project_data)
        audit_log.append(flow_audit)
        
        # Success: Can proceed
        next_action_msg = f"Proceed with {primary_lib} pricing"
        if secondary_lib:
            next_action_msg += f" (with {secondary_lib} as secondary reference)"
        
        if project_stage == "Concept":
            next_action_msg += ". Use /api/estimate/concept to generate feasibility estimate."
        
        audit_log.append(AuditLogEntry(
            action="evaluation_complete",
            decision="Success - Can proceed",
            reason="All validations passed, pricing flow determined",
            source="evaluation_engine"
        ))
        
        return EngineOutput(
            project_id=project_id,
            project_stage=project_stage,
            selected_primary_library=primary_lib,
            selected_secondary_library=secondary_lib,
            blocked_reason=None,
            required_missing_inputs=[],
            next_action=next_action_msg,
            audit_log=audit_log
        )
