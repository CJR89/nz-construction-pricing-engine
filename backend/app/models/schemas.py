from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ProjectStage(str, Enum):
    CONCEPT = "Concept"
    PRELIMINARY = "Preliminary"
    DEVELOPED = "Developed"
    DETAILED = "Detailed"


class RateLibrary(str, Enum):
    BCM2 = "BCM2"
    ELEM = "ELEM"
    CPR = "CPR"
    DET = "DET"


class ProjectInput(BaseModel):
    """Project input data model"""
    project_id: str
    project_stage: str
    building_type: Optional[str] = None
    location_city: Optional[str] = None
    gfa_m2: Optional[float] = None
    shell_only: Optional[bool] = None
    fitout_required: Optional[bool] = None
    # Add other fields as needed based on schema
    
    class Config:
        use_enum_values = True


class AuditLogEntry(BaseModel):
    """Single audit log entry"""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    action: str
    decision: str
    reason: str
    rule_id: Optional[str] = None
    source: Optional[str] = None


class EngineOutput(BaseModel):
    """Engine evaluation output"""
    project_id: str
    project_stage: str
    selected_primary_library: Optional[str] = None
    selected_secondary_library: Optional[str] = None
    blocked_reason: Optional[str] = None
    required_missing_inputs: List[str] = []
    next_action: str
    audit_log: List[AuditLogEntry] = []


class RateSearchRequest(BaseModel):
    """Rate library search request"""
    rate_library: RateLibrary
    sheet: Optional[str] = None
    search_text: str


class CityValues(BaseModel):
    """City-specific rate values"""
    low: Optional[float] = None
    high: Optional[float] = None


class RateRow(BaseModel):
    """Normalized rate row"""
    description: str
    unit: Optional[str] = None
    city_values: Dict[str, CityValues] = {}
    hours: Optional[str] = None
    source_file: str  # Required: name of Excel file
    source_sheet: str
    source_row_index: int


class RateSearchResponse(BaseModel):
    """Rate search response"""
    results: List[RateRow]
    total_count: int


class ConceptEstimateLineItem(BaseModel):
    """Line item in concept estimate"""
    description: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    rate: Optional[float] = None
    amount: Optional[float] = None
    source_file: Optional[str] = None  # Required for traced line items
    source_sheet: Optional[str] = None
    source_row_index: Optional[int] = None  # Standardized field name
    note: Optional[str] = None


class ConceptEstimate(BaseModel):
    """Concept stage estimate breakdown"""
    project_id: str
    base_build_cost: Optional[float] = None
    fitout_cost: Optional[float] = None
    subtotal: Optional[float] = None
    line_items: List[ConceptEstimateLineItem] = []
    disclaimer: str
    audit_log: List[AuditLogEntry] = []


class FileUploadResponse(BaseModel):
    """File upload response"""
    file_type: str
    filename: str
    status: str
    message: str


class ConfigSummary(BaseModel):
    """Configuration summary"""
    modules: List[str]
    stages: List[str]
    libraries: List[str]
    schema_fields_count: int
    rules_count: int
    pricing_flow_count: int
