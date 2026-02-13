"""
NZ Construction Pricing Engine - FastAPI Application
Excel is READ-ONLY: openpyxl with data_only=True, no formula execution.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.models.database import init_db
from app.api.routes import router
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Production-ready construction pricing engine using Excel rate libraries",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix=settings.api_prefix)


@app.on_event("startup")
async def startup_event():
    """Initialize database and load config on startup"""
    logger.info(f"Starting {settings.app_name}")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Try to load config if master workbook exists
    from app.utils.file_manager import FileManager
    from app.services.config_loader import initialize_config
    
    file_manager = FileManager()
    master_path = file_manager.get_file_path("master")
    
    if master_path:
        try:
            initialize_config(str(master_path))
            logger.info(f"Configuration loaded from {master_path}")
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
            logger.warning("Upload master workbook via /api/upload to enable configuration")
    else:
        logger.warning("Master workbook not found. Upload via /api/upload to enable configuration")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "api_docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from app.utils.file_manager import FileManager
    
    file_manager = FileManager()
    files_status = file_manager.check_required_files()
    
    return {
        "status": "healthy",
        "files_uploaded": files_status["all_present"],
        "config_loaded": settings is not None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.env == "development"
    )
