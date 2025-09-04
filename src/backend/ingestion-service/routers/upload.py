"""
File upload router for discharge summaries and clinical documents
"""

import os
import hashlib
import asyncio
import json
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form, BackgroundTasks
from fastapi.security import HTTPBearer
import logging

from core.config import get_settings
from core.database import get_db_connection
from core.logging_config import audit_logger
from models import DischargeSummary, DischargeSummaryCreate, DischargeSummaryResponse, DocumentStatus
from processors.pdf_parser import PDFParser
from processors.text_processor import TextProcessor

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()
settings = get_settings()


async def verify_upload_permissions(token: str = Depends(security)):
    """Verify user has upload permissions"""
    # TODO: Implement proper JWT validation
    # For now, just validate token format
    if not token or not token.credentials:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return token.credentials


@router.post("/document", response_model=DischargeSummaryResponse)
async def upload_discharge_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    patient_id: Optional[str] = Form(None),
    admission_id: Optional[str] = Form(None),
    source_system: Optional[str] = Form(None),
    token: str = Depends(verify_upload_permissions)
):
    """
    Upload and process a discharge summary document
    
    Supports:
    - PDF files
    - Text files
    - JSON files (structured data)
    """
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in settings.allowed_file_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {settings.allowed_file_types}"
        )
    
    # Validate file size
    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size: {settings.max_file_size / (1024*1024):.1f}MB"
        )
    
    # Calculate file hash for deduplication
    file_hash = hashlib.sha256(content).hexdigest()
    
    try:
        # Check for duplicate files
        async with get_db_connection() as conn:
            existing = await conn.fetchrow(
                "SELECT id FROM discharge_summaries WHERE file_hash = $1",
                file_hash
            )
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="Document already exists in the system"
                )
        
        # Process file content based on type
        if file_extension == 'pdf':
            processor = PDFParser()
            text_content = await processor.extract_text(content)
        elif file_extension == 'txt':
            text_content = content.decode('utf-8')
        elif file_extension == 'json':
            # Handle structured JSON input
            processor = TextProcessor()
            text_content = await processor.process_json(content)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Create discharge summary record
        discharge_data = DischargeSummaryCreate(
            patient_id=patient_id,
            admission_id=admission_id,
            original_content=text_content,
            source_system=source_system or "file_upload",
            metadata={
                "filename": file.filename,
                "file_size": len(content),
                "file_type": file_extension,
                "upload_method": "api"
            }
        )
        
        # Save to database
        async with get_db_connection() as conn:
            query = """
            INSERT INTO discharge_summaries 
            (patient_id, admission_id, original_content, source_system, file_hash, metadata, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, created_at, updated_at
            """
            
            result = await conn.fetchrow(
                query,
                discharge_data.patient_id,
                discharge_data.admission_id,
                discharge_data.original_content,
                discharge_data.source_system,
                file_hash,
                json.dumps(discharge_data.metadata),  # Convert dict to JSON string
                DocumentStatus.PENDING.value
            )
            
            # Create discharge summary object
            discharge_summary = DischargeSummary(
                id=result['id'],
                patient_id=discharge_data.patient_id,
                admission_id=discharge_data.admission_id,
                document_type=discharge_data.document_type,
                original_content=discharge_data.original_content,
                source_system=discharge_data.source_system,
                file_hash=file_hash,
                status=DocumentStatus.PENDING,
                created_at=result['created_at'],
                updated_at=result['updated_at'],
                metadata=discharge_data.metadata
            )
        
        # Log audit event
        audit_logger.log_data_processing(
            user_id=token[:10] + "...",  # Log partial token for audit
            document_id=str(discharge_summary.id),
            operation="upload",
            status="success",
            metadata={
                "filename": file.filename,
                "file_size": len(content),
                "patient_id": patient_id
            }
        )
        
        # Queue background processing
        background_tasks.add_task(
            _process_document_background,
            discharge_summary.id,
            text_content
        )
        
        logger.info(f"Document uploaded successfully: {discharge_summary.id}")
        
        # Return response
        return DischargeSummaryResponse(
            id=discharge_summary.id,
            status=discharge_summary.status,
            patient_id=discharge_summary.patient_id,
            admission_id=discharge_summary.admission_id,
            document_type=discharge_summary.document_type,
            created_at=discharge_summary.created_at,
            processed_at=discharge_summary.processed_at,
            processed_content=None  # Will be populated after processing
        )
        
    except HTTPException as http_exc:
        # Re-raise HTTPExceptions (like 409 for duplicates) as-is
        logger.error(f"HTTP error uploading document: {http_exc.detail}")
        
        # Log audit event for HTTP errors
        audit_logger.log_data_processing(
            user_id=token[:10] + "...",
            document_id="unknown",
            operation="upload",
            status="error",
            metadata={
                "error": f"{http_exc.status_code}: {http_exc.detail}",
                "filename": file.filename if file.filename else "unknown"
            }
        )
        
        raise http_exc
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        
        # Log audit event for failure
        audit_logger.log_data_processing(
            user_id=token[:10] + "...",
            document_id="unknown",
            operation="upload",
            status="error",
            metadata={
                "error": str(e),
                "filename": file.filename if file.filename else "unknown"
            }
        )
        
        raise HTTPException(status_code=500, detail="Error processing upload")


@router.get("/documents", response_model=List[DischargeSummaryResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[DocumentStatus] = None,
    patient_id: Optional[str] = None,
    token: str = Depends(verify_upload_permissions)
):
    """List uploaded discharge documents with optional filtering"""
    
    try:
        async with get_db_connection() as conn:
            # Build query with filters
            where_clauses = []
            params = [skip, limit]
            param_count = 2
            
            if status:
                param_count += 1
                where_clauses.append(f"status = ${param_count}")
                params.append(status.value)
            
            if patient_id:
                param_count += 1
                where_clauses.append(f"patient_id = ${param_count}")
                params.append(patient_id)
            
            where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            query = f"""
            SELECT id, patient_id, admission_id, document_type, status, 
                   created_at, processed_at, processed_content
            FROM discharge_summaries 
            {where_clause}
            ORDER BY created_at DESC
            OFFSET $1 LIMIT $2
            """
            
            rows = await conn.fetch(query, *params)
            
            documents = []
            for row in rows:
                documents.append(DischargeSummaryResponse(
                    id=row['id'],
                    status=DocumentStatus(row['status']),
                    patient_id=row['patient_id'],
                    admission_id=row['admission_id'],
                    document_type=row['document_type'],
                    created_at=row['created_at'],
                    processed_at=row['processed_at'],
                    processed_content=row['processed_content']
                ))
            
            return documents
            
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving documents")


@router.get("/documents/{document_id}", response_model=DischargeSummaryResponse)
async def get_document(
    document_id: str,
    token: str = Depends(verify_upload_permissions)
):
    """Get a specific discharge document by ID"""
    
    try:
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, patient_id, admission_id, document_type, status,
                       created_at, processed_at, processed_content
                FROM discharge_summaries 
                WHERE id = $1
                """,
                document_id
            )
            
            if not row:
                raise HTTPException(status_code=404, detail="Document not found")
            
            return DischargeSummaryResponse(
                id=row['id'],
                status=DocumentStatus(row['status']),
                patient_id=row['patient_id'],
                admission_id=row['admission_id'],
                document_type=row['document_type'],
                created_at=row['created_at'],
                processed_at=row['processed_at'],
                processed_content=row['processed_content']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving document")


async def _process_document_background(document_id: str, content: str):
    """Background task to process uploaded document"""
    try:
        # Update status to processing
        async with get_db_connection() as conn:
            await conn.execute(
                "UPDATE discharge_summaries SET status = $1 WHERE id = $2",
                DocumentStatus.PROCESSING.value,
                document_id
            )
        
        # TODO: Integrate with AI processing service
        # For now, just mark as completed
        await asyncio.sleep(1)  # Simulate processing time
        
        async with get_db_connection() as conn:
            await conn.execute(
                """
                UPDATE discharge_summaries 
                SET status = $1, processed_at = NOW()
                WHERE id = $2
                """,
                DocumentStatus.COMPLETED.value,
                document_id
            )
        
        logger.info(f"Document processed successfully: {document_id}")
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        
        # Update status to failed
        async with get_db_connection() as conn:
            await conn.execute(
                "UPDATE discharge_summaries SET status = $1 WHERE id = $2",
                DocumentStatus.FAILED.value,
                document_id
            )
