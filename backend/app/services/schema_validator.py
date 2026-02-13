"""
Schema Validator Module
Validates project inputs against the schema loaded from master workbook.
"""

from typing import Dict, Any, List, Tuple
from app.services.config_loader import get_config_loader
import logging

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates project data against schema definitions"""
    
    def __init__(self):
        self.config_loader = get_config_loader()
    
    def validate_project_input(self, project_data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate project input data against schema.
        
        Returns:
            Tuple of (is_valid, errors, missing_required)
        """
        if not self.config_loader:
            logger.error("Config loader not initialized")
            return False, ["Configuration not loaded"], []
        
        errors = []
        missing_required = []
        
        # Get schema for Project_Input entity
        schema_fields = self.config_loader.get_schema_for_entity("Project_Input")
        
        if not schema_fields:
            logger.warning("No schema fields found for Project_Input")
            return True, [], []  # No schema to validate against
        
        project_stage = project_data.get("project_stage", "Concept")
        
        # Validate each field
        for field_def in schema_fields:
            field_name = field_def.get("field_name")
            if not field_name:
                continue
            
            field_value = project_data.get(field_name)
            
            # Check if required
            is_required = self._is_field_required(field_def, project_stage)
            
            if is_required and (field_value is None or field_value == ""):
                missing_required.append(field_name)
                continue
            
            # Skip validation if field is not provided and not required
            if field_value is None or field_value == "":
                continue
            
            # Validate type
            field_type = field_def.get("field_type", "").lower()
            type_valid, type_error = self._validate_type(field_name, field_value, field_type)
            if not type_valid:
                errors.append(type_error)
            
            # Validate allowed values
            allowed_values = field_def.get("allowed_values")
            if allowed_values:
                allowed_list = [v.strip() for v in str(allowed_values).split(",")]
                if str(field_value) not in allowed_list:
                    errors.append(f"{field_name}: value '{field_value}' not in allowed values: {allowed_list}")
        
        is_valid = len(errors) == 0 and len(missing_required) == 0
        return is_valid, errors, missing_required
    
    def _is_field_required(self, field_def: Dict[str, Any], project_stage: str) -> bool:
        """Check if field is required for given stage"""
        required = field_def.get("required", "").lower()
        
        if required in ["yes", "true", "1"]:
            # Check if applies to current stage
            applies_stage = field_def.get("applies_stage", "")
            if applies_stage:
                applicable_stages = [s.strip() for s in str(applies_stage).split(",")]
                if project_stage not in applicable_stages and "All" not in applicable_stages:
                    return False
            return True
        
        return False
    
    def _validate_type(self, field_name: str, value: Any, field_type: str) -> Tuple[bool, str]:
        """Validate field type"""
        try:
            if field_type in ["number", "float", "decimal"]:
                float(value)
            elif field_type in ["integer", "int"]:
                int(value)
            elif field_type in ["boolean", "bool"]:
                if not isinstance(value, bool):
                    if str(value).lower() not in ["true", "false", "yes", "no", "1", "0"]:
                        return False, f"{field_name}: invalid boolean value '{value}'"
            elif field_type in ["string", "text"]:
                str(value)
            # Add more type validations as needed
            
            return True, ""
        except (ValueError, TypeError) as e:
            return False, f"{field_name}: invalid {field_type} value '{value}'"
    
    def get_required_fields_for_stage(self, project_stage: str) -> List[str]:
        """Get list of required field names for a given stage"""
        if not self.config_loader:
            return []
        
        schema_fields = self.config_loader.get_schema_for_entity("Project_Input")
        required_fields = []
        
        for field_def in schema_fields:
            if self._is_field_required(field_def, project_stage):
                field_name = field_def.get("field_name")
                if field_name:
                    required_fields.append(field_name)
        
        return required_fields
