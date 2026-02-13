from sqlalchemy import create_engine, Column, String, JSON, DateTime, Integer, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Project(Base):
    """Project model for storing construction projects"""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Project data stored as JSON
    data = Column(JSON, nullable=False)
    
    # Cached evaluation results
    last_evaluation = Column(JSON, nullable=True)
    last_evaluation_at = Column(DateTime, nullable=True)


class UploadedFile(Base):
    """Track uploaded Excel files"""
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_type = Column(String, nullable=False)  # master, bcm2, elem, cpr, det
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
