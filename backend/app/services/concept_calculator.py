"""
Concept Calculator Module
Implements basic Concept Feasibility Estimate calculation.
STRICT BLOCKING: If required input missing, block and list missing fields - no guessing.
"""

from typing import Dict, Any, List, Optional, Tuple
from app.services.config_loader import get_config_loader
from app.services.rate_parsers import get_parser
from app.models.schemas import ConceptEstimate, ConceptEstimateLineItem, AuditLogEntry
from app.core.config import settings
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConceptCalculator:
    """Calculates concept stage estimates using BCM2 rates"""
    
    def __init__(self):
        self.config_loader = get_config_loader()
    
    def calculate(self, project_data: Dict[str, Any]) -> ConceptEstimate:
        """
        Calculate concept estimate.
        STRICT: Block if required inputs missing - no guessing values.
        """
        project_id = project_data.get("project_id", "unknown")
        audit_log = []
        line_items = []
        
        # Strict validation: check required inputs
        missing_inputs = self._validate_required_inputs(project_data)
        
        if missing_inputs:
            # BLOCK: Required inputs missing
            audit_log.append(AuditLogEntry(
                action="concept_calculation",
                decision="BLOCKED",
                reason=f"Missing required inputs: {', '.join(missing_inputs)}",
                source="concept_calculator"
            ))
            
            return ConceptEstimate(
                project_id=project_id,
                base_build_cost=None,
                fitout_cost=None,
                subtotal=None,
                line_items=[],
                disclaimer=f"BLOCKED: Cannot calculate estimate. Missing required inputs: {', '.join(missing_inputs)}",
                audit_log=audit_log
            )
        
        # Get required inputs
        building_type = project_data.get("building_type")
        location_city = project_data.get("location_city")
        gfa_m2 = float(project_data.get("gfa_m2"))
        shell_only = project_data.get("shell_only", False)
        fitout_required = project_data.get("fitout_required", False)
        
        audit_log.append(AuditLogEntry(
            action="concept_calculation",
            decision="Proceeding with calculation",
            reason=f"All required inputs present: building_type={building_type}, location={location_city}, gfa={gfa_m2}m2",
            source="concept_calculator"
        ))
        
        # Get BCM2 rate
        base_rate, rate_source = self._get_bcm2_rate(building_type, location_city)
        
        if base_rate is None:
            # Rate not found - BLOCK
            audit_log.append(AuditLogEntry(
                action="rate_lookup",
                decision="BLOCKED",
                reason=f"Rate not found for building_type='{building_type}', location='{location_city}'",
                source="concept_calculator"
            ))
            
            return ConceptEstimate(
                project_id=project_id,
                base_build_cost=None,
                fitout_cost=None,
                subtotal=None,
                line_items=[],
                disclaimer=f"BLOCKED: Rate not found for building type '{building_type}' in {location_city}. Please verify inputs or provide rate manually.",
                audit_log=audit_log
            )
        
        # Calculate base build cost
        base_build_cost = base_rate * gfa_m2
        
        line_items.append(ConceptEstimateLineItem(
            description=f"Base build - {building_type}",
            quantity=gfa_m2,
            unit="m2",
            rate=base_rate,
            amount=base_build_cost,
            source_file=rate_source.get("source_file"),
            source_sheet=rate_source.get("source_sheet"),
            source_row_index=rate_source.get("source_row_index"),  # Standardized field name
            note=f"Rate for {location_city}"
        ))
        
        audit_log.append(AuditLogEntry(
            action="rate_application",
            decision=f"Applied BCM2 rate ${base_rate}/m2",
            reason=f"Matched building_type '{building_type}' in {location_city}",
            source=f"{rate_source.get('source_file')} - {rate_source.get('source_sheet')} row {rate_source.get('source_row_index')}"
        ))
        
        # Handle fitout if required
        fitout_cost = None
        if shell_only and fitout_required:
            # Check if fitout allowance is provided
            fitout_allowance = project_data.get("fitout_allowance_per_m2")
            
            if fitout_allowance is None:
                # BLOCK: Fitout required but no allowance provided
                audit_log.append(AuditLogEntry(
                    action="fitout_calculation",
                    decision="BLOCKED",
                    reason="shell_only=true AND fitout_required=true, but fitout_allowance_per_m2 not provided",
                    source="concept_calculator"
                ))
                
                return ConceptEstimate(
                    project_id=project_id,
                    base_build_cost=base_build_cost,
                    fitout_cost=None,
                    subtotal=None,
                    line_items=line_items,
                    disclaimer="BLOCKED: Fitout required but fitout_allowance_per_m2 not provided. Please specify fitout allowance.",
                    audit_log=audit_log
                )
            
            # Calculate fitout cost
            fitout_cost = float(fitout_allowance) * gfa_m2
            
            line_items.append(ConceptEstimateLineItem(
                description="Fitout allowance",
                quantity=gfa_m2,
                unit="m2",
                rate=float(fitout_allowance),
                amount=fitout_cost,
                note="User-provided fitout allowance"
            ))
            
            audit_log.append(AuditLogEntry(
                action="fitout_calculation",
                decision=f"Applied fitout allowance ${fitout_allowance}/m2",
                reason="shell_only=true AND fitout_required=true",
                source="User input"
            ))
        
        # Calculate subtotal
        subtotal = base_build_cost
        if fitout_cost:
            subtotal += fitout_cost
        
        # Add placeholder items for excluded costs
        line_items.append(ConceptEstimateLineItem(
            description="Demolition (if required)",
            note="Not priced - provide if required"
        ))
        
        line_items.append(ConceptEstimateLineItem(
            description="External works & services connections",
            note="Not priced - site-specific, provide if required"
        ))
        
        line_items.append(ConceptEstimateLineItem(
            description="Professional fees",
            note="Not priced - typically 8-15% of construction cost"
        ))
        
        line_items.append(ConceptEstimateLineItem(
            description="GST (15%)",
            amount=subtotal * 0.15 if subtotal else None,
            note="Calculated on subtotal"
        ))
        
        disclaimer = (
            "FEASIBILITY ESTIMATE ONLY - Concept Stage. "
            "This estimate is based on building costs per m2 and is indicative only. "
            "Excludes: demolition, site works, services connections, fees unless specifically noted. "
            "For preliminary design stage, elemental costing is recommended."
        )
        
        return ConceptEstimate(
            project_id=project_id,
            base_build_cost=base_build_cost,
            fitout_cost=fitout_cost,
            subtotal=subtotal,
            line_items=line_items,
            disclaimer=disclaimer,
            audit_log=audit_log
        )
    
    def _validate_required_inputs(self, project_data: Dict[str, Any]) -> List[str]:
        """
        Validate required inputs for concept calculation.
        Returns list of missing required fields.
        """
        required_fields = ["building_type", "location_city", "gfa_m2"]
        missing = []
        
        for field in required_fields:
            value = project_data.get(field)
            if value is None or value == "":
                missing.append(field)
        
        # If shell_only=true AND fitout_required=true, need fitout_allowance
        if project_data.get("shell_only") and project_data.get("fitout_required"):
            if project_data.get("fitout_allowance_per_m2") is None:
                missing.append("fitout_allowance_per_m2")
        
        return missing
    
    def _get_bcm2_rate(self, building_type: str, location_city: str) -> Tuple[Optional[float], Dict[str, Any]]:
        """
        Get BCM2 rate for building type and location.
        Returns (rate, source_info) or (None, {}) if not found.
        """
        try:
            # Get BCM2 file path
            bcm2_path = Path(settings.upload_dir) / settings.bcm2_workbook_name
            
            if not bcm2_path.exists():
                logger.error(f"BCM2 workbook not found: {bcm2_path}")
                return None, {}
            
            # Get parser and search for building type
            parser = get_parser("BCM2", str(bcm2_path))
            results = parser.search_rates(building_type)
            
            if not results:
                logger.warning(f"No BCM2 rates found for building_type '{building_type}'")
                return None, {}
            
            # Get first matching result
            rate_row = results[0]
            
            # Extract city value
            city_values = rate_row.get("city_values", {})
            city_data = city_values.get(location_city)
            
            if not city_data:
                logger.warning(f"No rate found for city '{location_city}' in BCM2 results")
                return None, {}
            
            # Use low value, or average of low/high if range
            rate = city_data.get("low")
            if rate is None:
                return None, {}
            
            # If high value exists, use midpoint
            high = city_data.get("high")
            if high:
                rate = (rate + high) / 2
            
            source_info = {
                "source_file": rate_row.get("source_file"),
                "source_sheet": rate_row.get("source_sheet"),
                "source_row_index": rate_row.get("source_row_index")
            }
            
            return rate, source_info
        
        except Exception as e:
            logger.error(f"Error getting BCM2 rate: {e}")
            return None, {}
