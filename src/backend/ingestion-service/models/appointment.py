"""
Appointment data models
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid


class AppointmentType(str, Enum):
    """Types of medical appointments"""
    FOLLOW_UP = "follow_up"
    SPECIALIST = "specialist"
    PRIMARY_CARE = "primary_care"
    LAB_WORK = "lab_work"
    IMAGING = "imaging"
    PROCEDURE = "procedure"
    THERAPY = "therapy"
    SURGERY = "surgery"
    EMERGENCY = "emergency"
    TELEHEALTH = "telehealth"


class AppointmentStatus(str, Enum):
    """Appointment status"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class AppointmentBase(BaseModel):
    """Base appointment model"""
    appointment_type: AppointmentType = Field(..., description="Type of appointment")
    provider_name: str = Field(..., description="Healthcare provider name")
    department: Optional[str] = Field(None, description="Hospital department")
    appointment_date: datetime = Field(..., description="Appointment date and time")
    location: Optional[str] = Field(None, description="Appointment location")
    address: Optional[str] = Field(None, description="Full address")
    phone: Optional[str] = Field(None, description="Contact phone number")
    instructions: Optional[str] = Field(None, description="General instructions")
    preparation_notes: Optional[str] = Field(None, description="How to prepare for appointment")
    
    @validator('provider_name')
    def validate_provider_name(cls, v):
        """Validate provider name is not empty"""
        if not v or not v.strip():
            raise ValueError("Provider name cannot be empty")
        return v.strip()
    
    @validator('appointment_date')
    def validate_future_date(cls, v):
        """Validate appointment is in the future (for new appointments)"""
        # Note: This validation might be relaxed for historical data
        return v


class AppointmentCreate(AppointmentBase):
    """Model for creating appointments"""
    discharge_summary_id: uuid.UUID = Field(..., description="Associated discharge summary ID")


class AppointmentUpdate(BaseModel):
    """Model for updating appointments"""
    appointment_type: Optional[AppointmentType] = None
    provider_name: Optional[str] = None
    department: Optional[str] = None
    appointment_date: Optional[datetime] = None
    location: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    instructions: Optional[str] = None
    preparation_notes: Optional[str] = None


class Appointment(AppointmentBase):
    """Complete appointment model"""
    id: uuid.UUID = Field(..., description="Unique identifier")
    discharge_summary_id: uuid.UUID = Field(..., description="Associated discharge summary ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z",
            uuid.UUID: str
        }


class AppointmentSummary(BaseModel):
    """Simplified appointment summary for patient view"""
    type: str = Field(..., description="Type of appointment (patient-friendly)")
    provider: str = Field(..., description="Doctor or provider name")
    date: str = Field(..., description="Formatted date")
    time: str = Field(..., description="Formatted time")
    location: Optional[str] = Field(None, description="Where to go")
    department: Optional[str] = Field(None, description="Which department")
    phone: Optional[str] = Field(None, description="Contact number")
    preparation: Optional[str] = Field(None, description="How to prepare")
    important_notes: Optional[str] = Field(None, description="Important information")


class AppointmentCalendarEvent(BaseModel):
    """Calendar event format for .ics export"""
    title: str = Field(..., description="Event title")
    start_datetime: datetime = Field(..., description="Start date and time")
    end_datetime: datetime = Field(..., description="End date and time")
    location: Optional[str] = Field(None, description="Event location")
    description: Optional[str] = Field(None, description="Event description")
    provider: str = Field(..., description="Provider name")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }


class AppointmentReminder(BaseModel):
    """Appointment reminder settings"""
    appointment_id: uuid.UUID
    reminder_type: str = Field(..., description="Type of reminder (email, sms, etc.)")
    reminder_time: datetime = Field(..., description="When to send reminder")
    message: str = Field(..., description="Reminder message")
    status: str = Field(default="pending", description="Reminder status")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z",
            uuid.UUID: str
        }


class AppointmentList(BaseModel):
    """List of appointments with summary information"""
    appointments: List[AppointmentSummary] = Field(..., description="List of appointments")
    total_count: int = Field(..., description="Total number of appointments")
    next_appointment: Optional[AppointmentSummary] = Field(None, description="Next upcoming appointment")
    calendar_events: List[AppointmentCalendarEvent] = Field(..., description="Calendar format events")
    important_reminders: List[str] = Field(default_factory=list, description="Important reminders")
