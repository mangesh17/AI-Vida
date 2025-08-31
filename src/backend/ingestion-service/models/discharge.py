"""
Discharge summary data models
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid


class DocumentStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEWED = "reviewed"
    PUBLISHED = "published"


class DocumentType(str, Enum):
    """Supported document types"""
    DISCHARGE_SUMMARY = "discharge_summary"
    PROGRESS_NOTE = "progress_note"
    CONSULTATION = "consultation"
    PROCEDURE_NOTE = "procedure_note"


class DischargeSummaryBase(BaseModel):
    """Base discharge summary model"""
    patient_id: Optional[str] = Field(None, description="Patient identifier")
    admission_id: Optional[str] = Field(None, description="Admission identifier")
    document_type: DocumentType = DocumentType.DISCHARGE_SUMMARY
    original_content: str = Field(..., description="Original document content")
    source_system: Optional[str] = Field(None, description="Source system identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DischargeSummaryCreate(DischargeSummaryBase):
    """Model for creating discharge summaries"""
    pass


class DischargeSummaryUpdate(BaseModel):
    """Model for updating discharge summaries"""
    processed_content: Optional[Dict[str, Any]] = None
    status: Optional[DocumentStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class DischargeSummary(DischargeSummaryBase):
    """Complete discharge summary model"""
    id: uuid.UUID = Field(..., description="Unique identifier")
    processed_content: Optional[Dict[str, Any]] = Field(None, description="Processed content")
    file_hash: Optional[str] = Field(None, description="File content hash")
    status: DocumentStatus = DocumentStatus.PENDING
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing completion timestamp")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z",
            uuid.UUID: str
        }


class ProcessedContent(BaseModel):
    """Structured processed content"""
    summary: Optional[str] = Field(None, description="Patient-friendly summary")
    medications: List[Dict[str, Any]] = Field(default_factory=list, description="Medication list")
    appointments: List[Dict[str, Any]] = Field(default_factory=list, description="Appointment list")
    diet_activity: Optional[Dict[str, Any]] = Field(None, description="Diet and activity instructions")
    warning_signs: Optional[Dict[str, Any]] = Field(None, description="Warning signs to watch for")
    emergency_contacts: List[Dict[str, Any]] = Field(default_factory=list, description="Emergency contacts")
    
    @validator('medications')
    def validate_medications(cls, v):
        """Validate medication structure"""
        required_fields = ['name', 'dosage', 'frequency']
        for med in v:
            for field in required_fields:
                if field not in med:
                    raise ValueError(f"Medication missing required field: {field}")
        return v
    
    @validator('appointments')
    def validate_appointments(cls, v):
        """Validate appointment structure"""
        required_fields = ['type', 'date', 'provider']
        for apt in v:
            for field in required_fields:
                if field not in apt:
                    raise ValueError(f"Appointment missing required field: {field}")
        return v


class DischargeSummaryResponse(BaseModel):
    """API response model for discharge summaries"""
    id: uuid.UUID
    status: DocumentStatus
    patient_id: Optional[str]
    admission_id: Optional[str]
    document_type: DocumentType
    created_at: datetime
    processed_at: Optional[datetime]
    processed_content: Optional[ProcessedContent]
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z",
            uuid.UUID: str
        }
