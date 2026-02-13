"""
Rules Engine Module
Evaluates governance rules and blocking conditions.
"""

from typing import Dict, Any, List, Tuple
from app.services.config_loader import get_config_loader
from app.models.schemas import AuditLogEntry
import logging

logger = logging.getLogger(__name__)


class RulesEngine:
    """Evaluates governance rules and blocking conditions"""
    
    def __init__(self):
        self.config_loader = get_config_loader()
    
    def evaluate_rules(self, project_data: Dict[str, Any]) -> Tuple[bool, List[str], List[AuditLogEntry]]:
        """
        Evaluate all rules against project data.
        
        Returns:
            Tuple of (is_blocked, blocking_reasons, audit_entries)
        """
        if not self.config_loader:
            logger.error("Config loader not initialized")
            return True, ["Configuration not loaded"], []
        
        is_blocked = False
        blocking_reasons = []
        audit_entries = []
        
        # Get all rules
        all_rules = self.config_loader.config.get("rules", [])
        
        project_stage = project_data.get("project_stage", "Concept")
        
        for rule in all_rules:
            # Check if rule applies to current stage
            rule_stage = rule.get("applies_stage") or rule.get("stage")
            if rule_stage and str(rule_stage).strip():
                applicable_stages = [s.strip() for s in str(rule_stage).split(",")]
                if project_stage not in applicable_stages and "All" not in applicable_stages:
                    continue
            
            # Evaluate rule condition
            rule_matches = self._evaluate_rule_condition(rule, project_data)
            
            if rule_matches:
                rule_id = rule.get("rule_id") or rule.get("id") or "unknown"
                rule_type = rule.get("rule_type", "").lower()
                block_progress = str(rule.get("block_progress", "")).lower() in ["true", "yes", "1"]
                
                # Create audit entry
                audit_entry = AuditLogEntry(
                    action="rule_evaluation",
                    decision=f"Rule {rule_id} triggered",
                    reason=rule.get("description") or rule.get("message") or "Rule condition met",
                    rule_id=rule_id,
                    source=f"Rules sheet"
                )
                audit_entries.append(audit_entry)
                
                # Check if this rule blocks progress
                if block_progress:
                    is_blocked = True
                    reason = rule.get("message") or rule.get("description") or f"Rule {rule_id} blocks progress"
                    blocking_reasons.append(reason)
                    logger.warning(f"Blocking rule triggered: {rule_id}")
        
        return is_blocked, blocking_reasons, audit_entries
    
    def _evaluate_rule_condition(self, rule: Dict[str, Any], project_data: Dict[str, Any]) -> bool:
        """
        Evaluate if a rule's condition is met.
        This is a simplified implementation - real rules might have complex conditions.
        """
        # Check for condition fields in rule
        condition_field = rule.get("condition_field")
        condition_value = rule.get("condition_value")
        
        if condition_field and condition_value is not None:
            actual_value = project_data.get(condition_field)
            # Simple equality check
            if str(actual_value) == str(condition_value):
                return True
        
        # If no specific condition, check for pattern matching
        # E.g., "shell_only=true AND fitout_required=true"
        condition_text = rule.get("condition") or rule.get("trigger_condition")
        if condition_text:
            # Very simple AND condition parser
            if "AND" in str(condition_text):
                conditions = str(condition_text).split("AND")
                all_met = True
                for cond in conditions:
                    cond = cond.strip()
                    if "=" in cond:
                        field, value = cond.split("=", 1)
                        field = field.strip()
                        value = value.strip()
                        actual = project_data.get(field)
                        if str(actual).lower() != value.lower():
                            all_met = False
                            break
                return all_met
            elif "=" in str(condition_text):
                # Simple field=value condition
                field, value = str(condition_text).split("=", 1)
                field = field.strip()
                value = value.strip()
                actual = project_data.get(field)
                return str(actual).lower() == value.lower()
        
        # Default: rule doesn't match
        return False
