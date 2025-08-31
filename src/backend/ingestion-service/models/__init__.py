"""
Data models initialization
"""

from .discharge import (
    DischargeSummary,
    DischargeSummaryCreate,
    DischargeSummaryUpdate,
    DischargeSummaryResponse,
    ProcessedContent,
    DocumentStatus,
    DocumentType
)

from .medication import (
    Medication,
    MedicationCreate,
    MedicationUpdate,
    MedicationSummary,
    MedicationList,
    MedicationSchedule,
    MedicationRoute,
    MedicationFrequency
)

from .appointment import (
    Appointment,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentSummary,
    AppointmentList,
    AppointmentCalendarEvent,
    AppointmentReminder,
    AppointmentType,
    AppointmentStatus
)

__all__ = [
    # Discharge models
    'DischargeSummary',
    'DischargeSummaryCreate',
    'DischargeSummaryUpdate',
    'DischargeSummaryResponse',
    'ProcessedContent',
    'DocumentStatus',
    'DocumentType',
    
    # Medication models
    'Medication',
    'MedicationCreate',
    'MedicationUpdate',
    'MedicationSummary',
    'MedicationList',
    'MedicationSchedule',
    'MedicationRoute',
    'MedicationFrequency',
    
    # Appointment models
    'Appointment',
    'AppointmentCreate',
    'AppointmentUpdate',
    'AppointmentSummary',
    'AppointmentList',
    'AppointmentCalendarEvent',
    'AppointmentReminder',
    'AppointmentType',
    'AppointmentStatus'
]
