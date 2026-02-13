"""
API Routes for NZ Construction Pricing Engine
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.database import get_db, Project
from app.models.schemas import (
    ProjectInput, EngineOutput, RateSearchRequest, RateSearchResponse,
    ConceptEstimate, FileUploadResponse, ConfigSummary
)
from app.services.config_loader import get_config_loader, initialize_config
from app.services.evaluation_engine import EvaluationEngine
from app.services.concept_calculator import ConceptCalculator
from app.services.rate_parsers import get_parser
from app.utils.file_manager import FileManager
from app.core.config import settings
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
file_manager = FileManager()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Form(...)
):
    """
    Upload Excel files (master, bcm2, elem, cpr, det).
    Files are stored in uploads directory (not committed to git).
    """
    result = await file_manager.save_upload(file, file_type)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    # If master workbook uploaded, reinitialize config
    if file_type == "master":
        try:
            master_path = file_manager.get_file_path("master")
            if master_path:
                initialize_config(str(master_path))
                logger.info("Config reloaded from new master workbook")
        except Exception as e:
            logger.error(f"Error loading config from master workbook: {e}")
            raise HTTPException(status_code=500, detail=f"Config load error: {str(e)}")
    
    return FileUploadResponse(
        file_type=file_type,
        filename=result["filename"],
        status=result["status"],
        message=result["message"]
    )


@router.get("/config/summary", response_model=ConfigSummary)
async def get_config_summary():
    """
    Get configuration summary from loaded master workbook.
    Returns modules, stages, libraries discovered.
    """
    config_loader = get_config_loader()
    
    if not config_loader:
        raise HTTPException(
            status_code=400,
            detail="Configuration not loaded. Please upload master workbook first."
        )
    
    config = config_loader.config
    
    # Extract unique stages from pricing flow
    stages = list(set([
        flow.get("project_stage")
        for flow in config.get("pricing_flow", [])
        if flow.get("project_stage")
    ]))
    
    # Extract libraries
    libraries = ["BCM2", "ELEM", "CPR", "DET"]
    
    # Modules from schema entities
    modules = list(set([
        field.get("entity")
        for field in config.get("schema", [])
        if field.get("entity")
    ]))
    
    return ConfigSummary(
        modules=modules,
        stages=stages,
        libraries=libraries,
        schema_fields_count=len(config.get("schema", [])),
        rules_count=len(config.get("rules", [])),
        pricing_flow_count=len(config.get("pricing_flow", []))
    )


@router.post("/projects", response_model=Dict[str, Any])
async def create_project(
    project: ProjectInput,
    db: Session = Depends(get_db)
):
    """
    Create new project with validation.
    Project data is validated against schema.
    """
    # Check if project_id already exists
    existing = db.query(Project).filter(Project.id == project.project_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Project ID already exists")
    
    # Create project
    db_project = Project(
        id=project.project_id,
        data=project.dict()
    )
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    logger.info(f"Created project: {project.project_id}")
    
    return {
        "project_id": db_project.id,
        "created_at": db_project.created_at.isoformat(),
        "data": db_project.data
    }


@router.get("/projects/{project_id}", response_model=Dict[str, Any])
async def get_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get project by ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "project_id": project.id,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
        "data": project.data,
        "last_evaluation": project.last_evaluation
    }


@router.post("/projects/{project_id}/evaluate", response_model=EngineOutput)
async def evaluate_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Evaluate project and determine pricing approach.
    Returns selected libraries, blocking status, and audit trail.
    STRICT: Blocks if required inputs missing or rules violated.
    """
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check config loaded
    if not get_config_loader():
        raise HTTPException(
            status_code=400,
            detail="Configuration not loaded. Please upload master workbook first."
        )
    
    # Evaluate
    engine = EvaluationEngine()
    result = engine.evaluate(project.data)
    
    # Cache evaluation result
    project.last_evaluation = result.dict()
    project.last_evaluation_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"Evaluated project {project_id}: blocked={result.blocked_reason is not None}")
    
    return result


@router.post("/rates/search", response_model=RateSearchResponse)
async def search_rates(request: RateSearchRequest):
    """
    Search rate library for matching rates.
    Returns normalized results with source traceability.
    """
    # Get file path for library
    library_files = {
        "BCM2": "bcm2",
        "ELEM": "elem",
        "CPR": "cpr",
        "DET": "det"
    }
    
    file_type = library_files.get(request.rate_library.value)
    if not file_type:
        raise HTTPException(status_code=400, detail="Invalid library")
    
    file_path = file_manager.get_file_path(file_type)
    if not file_path:
        raise HTTPException(
            status_code=400,
            detail=f"{request.rate_library.value} workbook not uploaded"
        )
    
    # Search rates
    try:
        parser = get_parser(request.rate_library.value, str(file_path))
        results = parser.search_rates(request.search_text, request.sheet)
        
        logger.info(f"Rate search: library={request.rate_library.value}, query='{request.search_text}', found={len(results)}")
        
        return RateSearchResponse(
            results=results,
            total_count=len(results)
        )
    
    except Exception as e:
        logger.error(f"Rate search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/estimate/concept", response_model=ConceptEstimate)
async def calculate_concept_estimate(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Calculate concept stage feasibility estimate.
    STRICT: Blocks if required inputs missing - no guessing.
    """
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check config loaded
    if not get_config_loader():
        raise HTTPException(
            status_code=400,
            detail="Configuration not loaded. Please upload master workbook first."
        )
    
    # Verify stage is Concept
    project_stage = project.data.get("project_stage", "")
    if project_stage != "Concept":
        raise HTTPException(
            status_code=400,
            detail=f"Concept estimate only available for Concept stage (current: {project_stage})"
        )
    
    # Calculate estimate
    calculator = ConceptCalculator()
    estimate = calculator.calculate(project.data)
    
    logger.info(f"Calculated concept estimate for {project_id}: subtotal=${estimate.subtotal}")
    
    return estimate
