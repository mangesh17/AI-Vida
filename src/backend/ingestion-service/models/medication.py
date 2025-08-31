"""
Medication data models
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid


class MedicationRoute(str, Enum):
    """Medication administration routes"""
    ORAL = "oral"
    IV = "intravenous"
    IM = "intramuscular"
    SC = "subcutaneous"
    TOPICAL = "topical"
    INHALED = "inhaled"
    SUBLINGUAL = "sublingual"
    RECTAL = "rectal"
    OPHTHALMIC = "ophthalmic"
    OTIC = "otic"
    NASAL = "nasal"


class MedicationFrequency(str, Enum):
    """Common medication frequencies"""
    ONCE_DAILY = "once_daily"
    TWICE_DAILY = "twice_daily"
    THREE_TIMES_DAILY = "three_times_daily"
    FOUR_TIMES_DAILY = "four_times_daily"
    EVERY_4_HOURS = "every_4_hours"
    EVERY_6_HOURS = "every_6_hours"
    EVERY_8_HOURS = "every_8_hours"
    EVERY_12_HOURS = "every_12_hours"
    AS_NEEDED = "as_needed"
    BEDTIME = "bedtime"
    MORNING = "morning"
    WITH_MEALS = "with_meals"
    BEFORE_MEALS = "before_meals"
    AFTER_MEALS = "after_meals"


class MedicationBase(BaseModel):
    """Base medication model"""
    medication_name: str = Field(..., description="Brand or generic medication name")
    generic_name: Optional[str] = Field(None, description="Generic name if brand provided")
    dosage: str = Field(..., description="Dosage amount and units")
    frequency: str = Field(..., description="How often to take medication")
    duration: Optional[str] = Field(None, description="How long to take medication")
    instructions: Optional[str] = Field(None, description="Special instructions")
    route: Optional[MedicationRoute] = Field(MedicationRoute.ORAL, description="Administration route")
    
    @validator('medication_name')
    def validate_medication_name(cls, v):
        """Validate medication name is not empty"""
        if not v or not v.strip():
            raise ValueError("Medication name cannot be empty")
        return v.strip()
    
    @validator('dosage')
    def validate_dosage(cls, v):
        """Validate dosage format"""
        if not v or not v.strip():
            raise ValueError("Dosage cannot be empty")
        return v.strip()


class MedicationCreate(MedicationBase):
    """Model for creating medications"""
    discharge_summary_id: uuid.UUID = Field(..., description="Associated discharge summary ID")


class MedicationUpdate(BaseModel):
    """Model for updating medications"""
    medication_name: Optional[str] = None
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None
    route: Optional[MedicationRoute] = None
    rxnorm_code: Optional[str] = None
    ndc_code: Optional[str] = None


class Medication(MedicationBase):
    """Complete medication model"""
    id: uuid.UUID = Field(..., description="Unique identifier")
    discharge_summary_id: uuid.UUID = Field(..., description="Associated discharge summary ID")
    rxnorm_code: Optional[str] = Field(None, description="RxNorm concept code")
    ndc_code: Optional[str] = Field(None, description="National Drug Code")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z",
            uuid.UUID: str
        }


class MedicationSchedule(BaseModel):
    """Medication schedule for patient display"""
    medication_id: uuid.UUID
    medication_name: str
    dosage: str
    times: List[str] = Field(..., description="List of times to take medication (e.g., ['8:00 AM', '8:00 PM'])")
    instructions: Optional[str] = None
    route: str = "oral"
    
    class Config:
        json_encoders = {
            uuid.UUID: str
        }


class MedicationSummary(BaseModel):
    """Simplified medication summary for patient view"""
    name: str = Field(..., description="Medication name (brand + generic if available)")
    dosage: str = Field(..., description="How much to take")
    frequency: str = Field(..., description="How often to take (patient-friendly)")
    instructions: Optional[str] = Field(None, description="Special instructions")
    duration: Optional[str] = Field(None, description="How long to take")
    important_notes: Optional[str] = Field(None, description="Important safety information")


class MedicationList(BaseModel):
    """List of medications with summary information"""
    medications: List[MedicationSummary] = Field(..., description="List of medications")
    total_count: int = Field(..., description="Total number of medications")
    daily_schedule: List[MedicationSchedule] = Field(..., description="Daily medication schedule")
    important_reminders: List[str] = Field(default_factory=list, description="Important reminders")
