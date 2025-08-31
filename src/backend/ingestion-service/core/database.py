"""
Database connection and initialization
"""

import asyncpg
import logging
from typing import Optional
from contextlib import asynccontextmanager

from .config import get_settings

logger = logging.getLogger(__name__)

# Global connection pool
_connection_pool: Optional[asyncpg.Pool] = None


def get_settings_safe():
    """Get settings safely for database operations"""
    return get_settings()


async def init_database():
    """Initialize database connection pool"""
    global _connection_pool
    
    settings = get_settings_safe()
    
    try:
        _connection_pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=2,
            max_size=settings.database_pool_size,
            command_timeout=60
        )
        logger.info("Database connection pool initialized")
        
        # Run initial setup if needed
        await _create_tables()
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def get_database_connection():
    """Get database connection from pool"""
    if _connection_pool is None:
        raise RuntimeError("Database not initialized")
    
    return await _connection_pool.acquire()


@asynccontextmanager
async def get_db_connection():
    """Context manager for database connections"""
    conn = await get_database_connection()
    try:
        yield conn
    finally:
        await _connection_pool.release(conn)


async def _create_tables():
    """Create necessary database tables"""
    create_tables_sql = """
    -- Discharge summaries table
    CREATE TABLE IF NOT EXISTS discharge_summaries (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        patient_id VARCHAR(255),
        admission_id VARCHAR(255),
        document_type VARCHAR(50) DEFAULT 'discharge_summary',
        original_content TEXT NOT NULL,
        processed_content JSONB,
        file_hash VARCHAR(64) UNIQUE,
        source_system VARCHAR(100),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        processed_at TIMESTAMP WITH TIME ZONE,
        status VARCHAR(20) DEFAULT 'pending',
        metadata JSONB DEFAULT '{}'::jsonb
    );

    -- Medications table
    CREATE TABLE IF NOT EXISTS medications (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        discharge_summary_id UUID REFERENCES discharge_summaries(id),
        medication_name VARCHAR(500) NOT NULL,
        generic_name VARCHAR(500),
        dosage VARCHAR(200),
        frequency VARCHAR(200),
        duration VARCHAR(200),
        instructions TEXT,
        rxnorm_code VARCHAR(50),
        ndc_code VARCHAR(50),
        route VARCHAR(100),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Appointments table
    CREATE TABLE IF NOT EXISTS appointments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        discharge_summary_id UUID REFERENCES discharge_summaries(id),
        appointment_type VARCHAR(200),
        provider_name VARCHAR(300),
        department VARCHAR(200),
        appointment_date TIMESTAMP WITH TIME ZONE,
        location VARCHAR(500),
        address TEXT,
        phone VARCHAR(50),
        instructions TEXT,
        preparation_notes TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Processing logs for audit trail
    CREATE TABLE IF NOT EXISTS processing_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        discharge_summary_id UUID REFERENCES discharge_summaries(id),
        process_type VARCHAR(100) NOT NULL,
        status VARCHAR(50) NOT NULL,
        started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        completed_at TIMESTAMP WITH TIME ZONE,
        error_message TEXT,
        metadata JSONB DEFAULT '{}'::jsonb
    );

    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_discharge_summaries_patient_id ON discharge_summaries(patient_id);
    CREATE INDEX IF NOT EXISTS idx_discharge_summaries_status ON discharge_summaries(status);
    CREATE INDEX IF NOT EXISTS idx_discharge_summaries_created_at ON discharge_summaries(created_at);
    CREATE INDEX IF NOT EXISTS idx_medications_discharge_id ON medications(discharge_summary_id);
    CREATE INDEX IF NOT EXISTS idx_appointments_discharge_id ON appointments(discharge_summary_id);
    CREATE INDEX IF NOT EXISTS idx_processing_logs_discharge_id ON processing_logs(discharge_summary_id);
    """
    
    async with get_db_connection() as conn:
        await conn.execute(create_tables_sql)
        logger.info("Database tables created/verified")


async def close_database():
    """Close database connection pool"""
    global _connection_pool
    if _connection_pool:
        await _connection_pool.close()
        _connection_pool = None
        logger.info("Database connection pool closed")
