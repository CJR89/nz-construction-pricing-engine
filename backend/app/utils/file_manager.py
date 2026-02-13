"""
File Management Utilities
Handles Excel file uploads and storage.
"""

import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
from app.core.config import settings
from app.models.database import SessionLocal, UploadedFile
import logging

logger = logging.getLogger(__name__)


class FileManager:
    """Manages Excel file uploads and storage"""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_upload(self, file: UploadFile, file_type: str) -> dict:
        """Save uploaded file and track in database"""
        try:
            # Determine expected filename
            expected_names = {
                "master": settings.master_workbook_name,
                "bcm2": settings.bcm2_workbook_name,
                "elem": settings.elem_workbook_name,
                "cpr": settings.cpr_workbook_name,
                "det": settings.det_workbook_name
            }
            
            if file_type not in expected_names:
                return {
                    "status": "error",
                    "message": f"Invalid file type: {file_type}"
                }
            
            # Save file
            stored_filename = expected_names[file_type]
            file_path = self.upload_dir / stored_filename
            
            # Write file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            file_size = file_path.stat().st_size
            
            # Track in database
            db = SessionLocal()
            try:
                # Mark previous files of this type as inactive
                db.query(UploadedFile).filter(
                    UploadedFile.file_type == file_type
                ).update({"is_active": False})
                
                # Add new file record
                db_file = UploadedFile(
                    file_type=file_type,
                    original_filename=file.filename,
                    stored_filename=stored_filename,
                    file_size=file_size,
                    is_active=True
                )
                db.add(db_file)
                db.commit()
            finally:
                db.close()
            
            logger.info(f"Saved {file_type} file: {stored_filename} ({file_size} bytes)")
            
            return {
                "status": "success",
                "message": f"File uploaded successfully",
                "filename": stored_filename,
                "size": file_size
            }
        
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_file_path(self, file_type: str) -> Optional[Path]:
        """Get path to active uploaded file"""
        expected_names = {
            "master": settings.master_workbook_name,
            "bcm2": settings.bcm2_workbook_name,
            "elem": settings.elem_workbook_name,
            "cpr": settings.cpr_workbook_name,
            "det": settings.det_workbook_name
        }
        
        if file_type not in expected_names:
            return None
        
        file_path = self.upload_dir / expected_names[file_type]
        
        if file_path.exists():
            return file_path
        
        return None
    
    def check_required_files(self) -> dict:
        """Check if all required files are uploaded"""
        required_types = ["master", "bcm2", "elem", "cpr", "det"]
        status = {}
        
        for file_type in required_types:
            file_path = self.get_file_path(file_type)
            status[file_type] = {
                "uploaded": file_path is not None,
                "path": str(file_path) if file_path else None
            }
        
        all_present = all(s["uploaded"] for s in status.values())
        
        return {
            "all_present": all_present,
            "files": status
        }
