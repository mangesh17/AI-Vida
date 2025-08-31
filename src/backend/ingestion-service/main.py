"""
AI-Vida Data Ingestion Service
Main FastAPI application for processing discharge summaries and clinical data
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import logging
from contextlib import asynccontextmanager

from routers.upload import router as upload_router
from routers.fhir import router as fhir_router
from routers.hl7 import router as hl7_router
from core.config import get_settings
from core.database import get_database_connection, init_database
from core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

security = HTTPBearer()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting AI-Vida Data Ingestion Service")
    
    # Initialize database
    await init_database()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI-Vida Data Ingestion Service")


# Create FastAPI application
app = FastAPI(
    title="AI-Vida Data Ingestion Service",
    description="HIPAA-compliant service for processing discharge summaries and clinical data",
    version="2.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_router, prefix="/api/v1/upload", tags=["Upload"])
app.include_router(fhir_router, prefix="/api/v1/fhir", tags=["FHIR"])
app.include_router(hl7_router, prefix="/api/v1/hl7", tags=["HL7"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "AI-Vida Data Ingestion Service",
        "version": "2.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check database connection
        db = await get_database_connection()
        await db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": settings.current_timestamp()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.environment == "development",
        log_level="info"
    )
