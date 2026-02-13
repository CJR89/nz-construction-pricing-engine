from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    app_name: str = "NZ Construction Pricing Engine"
    env: str = "development"
    
    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    api_prefix: str = "/api"
    
    # Database
    database_url: str = "sqlite:///./nz_pricing_engine.db"
    
    # File Upload
    upload_dir: str = "./uploads"
    max_upload_size: int = 52428800  # 50MB
    
    # Required Excel Files
    master_workbook_name: str = "Construction_Knowledge_Base_FINALIZED_WITH_SCHEMA.xlsm"
    bcm2_workbook_name: str = "Building Costs m2 NZ.xlsm"
    elem_workbook_name: str = "Elemental Costs of Building NZ.xlsm"
    cpr_workbook_name: str = "CostPlan NZ Rates.xlsx"
    det_workbook_name: str = "Detailed Rates NZ.xlsm"
    
    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
