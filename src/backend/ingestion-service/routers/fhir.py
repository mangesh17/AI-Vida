"""
FHIR resource processing router
"""

import json
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from core.config import get_settings
from core.database import get_db_connection
from core.logging_config import audit_logger
from models import DischargeSummaryCreate, MedicationCreate, AppointmentCreate

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()
settings = get_settings()


class FHIRResource(BaseModel):
    """Base FHIR resource model"""
    resourceType: str
    id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class FHIRBundle(BaseModel):
    """FHIR Bundle resource"""
    resourceType: str = "Bundle"
    id: Optional[str] = None
    type: str
    entry: List[Dict[str, Any]] = []


async def verify_fhir_permissions(token: str = Depends(security)):
    """Verify user has FHIR processing permissions"""
    # TODO: Implement proper JWT validation
    if not token or not token.credentials:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return token.credentials


@router.post("/process-bundle")
async def process_fhir_bundle(
    bundle: FHIRBundle = Body(...),
    patient_id: Optional[str] = None,
    token: str = Depends(verify_fhir_permissions)
):
    """
    Process a FHIR Bundle containing discharge-related resources
    
    Supports:
    - Patient resources
    - Encounter resources  
    - MedicationStatement resources
    - Appointment resources
    - DocumentReference resources
    """
    
    try:
        # Initialize processing results
        results = {
            "processed_resources": 0,
            "discharge_summaries": [],
            "medications": [],
            "appointments": [],
            "errors": []
        }
        
        # Process bundle entries
        for entry in bundle.entry:
            try:
                resource = entry.get("resource", {})
                resource_type = resource.get("resourceType")
                
                if resource_type == "DocumentReference":
                    # Process discharge summary document
                    discharge_id = await _process_document_reference(resource, patient_id)
                    if discharge_id:
                        results["discharge_summaries"].append(str(discharge_id))
                
                elif resource_type == "MedicationStatement":
                    # Process medication
                    medication_id = await _process_medication_statement(resource, patient_id)
                    if medication_id:
                        results["medications"].append(str(medication_id))
                
                elif resource_type == "Appointment":
                    # Process appointment
                    appointment_id = await _process_appointment(resource, patient_id)
                    if appointment_id:
                        results["appointments"].append(str(appointment_id))
                
                elif resource_type == "Patient":
                    # Extract patient information
                    patient_id = _extract_patient_id(resource)
                
                elif resource_type == "Encounter":
                    # Process encounter information
                    await _process_encounter(resource, patient_id)
                
                results["processed_resources"] += 1
                
            except Exception as e:
                logger.error(f"Error processing FHIR resource: {e}")
                results["errors"].append({
                    "resource_type": resource.get("resourceType", "unknown"),
                    "error": str(e)
                })
        
        # Log audit event
        audit_logger.log_data_processing(
            user_id=token[:10] + "...",
            document_id=bundle.id or "bundle",
            operation="fhir_bundle_processing",
            status="success" if not results["errors"] else "partial_success",
            metadata={
                "processed_resources": results["processed_resources"],
                "errors_count": len(results["errors"])
            }
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing FHIR bundle: {e}")
        raise HTTPException(status_code=500, detail="Error processing FHIR bundle")


@router.post("/medication-statement")
async def process_medication_statement(
    medication_statement: Dict[str, Any] = Body(...),
    patient_id: Optional[str] = None,
    discharge_summary_id: Optional[str] = None,
    token: str = Depends(verify_fhir_permissions)
):
    """Process individual FHIR MedicationStatement resource"""
    
    try:
        medication_id = await _process_medication_statement(
            medication_statement, 
            patient_id, 
            discharge_summary_id
        )
        
        return {
            "medication_id": str(medication_id),
            "status": "processed"
        }
        
    except Exception as e:
        logger.error(f"Error processing MedicationStatement: {e}")
        raise HTTPException(status_code=500, detail="Error processing medication statement")


@router.post("/appointment")
async def process_appointment_resource(
    appointment: Dict[str, Any] = Body(...),
    patient_id: Optional[str] = None,
    discharge_summary_id: Optional[str] = None,
    token: str = Depends(verify_fhir_permissions)
):
    """Process individual FHIR Appointment resource"""
    
    try:
        appointment_id = await _process_appointment(
            appointment, 
            patient_id, 
            discharge_summary_id
        )
        
        return {
            "appointment_id": str(appointment_id),
            "status": "processed"
        }
        
    except Exception as e:
        logger.error(f"Error processing Appointment: {e}")
        raise HTTPException(status_code=500, detail="Error processing appointment")


# Helper functions

async def _process_document_reference(resource: Dict[str, Any], patient_id: Optional[str] = None):
    """Process FHIR DocumentReference"""
    
    # Extract document content
    content = resource.get("content", [])
    if not content:
        raise ValueError("DocumentReference has no content")
    
    # Get the document text (simplified - in real implementation would fetch from URL)
    attachment = content[0].get("attachment", {})
    document_text = attachment.get("data", "")  # Base64 encoded content
    
    if not document_text:
        # In real implementation, fetch from contentType URL
        url = attachment.get("url", "")
        if url:
            # TODO: Fetch document from URL
            raise ValueError("Document URL fetching not implemented")
        else:
            raise ValueError("No document content or URL provided")
    
    # Decode base64 content if present
    import base64
    try:
        document_text = base64.b64decode(document_text).decode('utf-8')
    except Exception:
        pass  # Content might already be plain text
    
    # Create discharge summary
    discharge_data = DischargeSummaryCreate(
        patient_id=patient_id or _extract_patient_reference(resource.get("subject")),
        original_content=document_text,
        source_system="fhir",
        metadata={
            "fhir_resource_id": resource.get("id"),
            "document_type": resource.get("type", {}).get("coding", [{}])[0].get("display", "discharge_summary"),
            "creation_date": resource.get("date")
        }
    )
    
    # Save to database
    async with get_db_connection() as conn:
        query = """
        INSERT INTO discharge_summaries 
        (patient_id, original_content, source_system, metadata, status)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """
        
        result = await conn.fetchrow(
            query,
            discharge_data.patient_id,
            discharge_data.original_content,
            discharge_data.source_system,
            discharge_data.metadata,
            "pending"
        )
        
        return result['id']


async def _process_medication_statement(resource: Dict[str, Any], 
                                      patient_id: Optional[str] = None,
                                      discharge_summary_id: Optional[str] = None):
    """Process FHIR MedicationStatement"""
    
    # Extract medication information
    medication = resource.get("medicationCodeableConcept") or resource.get("medicationReference", {})
    
    if "coding" in medication:
        # CodeableConcept
        coding = medication["coding"][0] if medication["coding"] else {}
        medication_name = coding.get("display", "Unknown medication")
        rxnorm_code = coding.get("code") if coding.get("system") == "http://www.nlm.nih.gov/research/umls/rxnorm" else None
    else:
        # Reference to Medication resource
        medication_name = "Unknown medication"  # Would need to resolve reference
        rxnorm_code = None
    
    # Extract dosage
    dosage_info = resource.get("dosage", [{}])[0] if resource.get("dosage") else {}
    dose_quantity = dosage_info.get("doseAndRate", [{}])[0].get("doseQuantity", {}) if dosage_info.get("doseAndRate") else {}
    
    dosage = f"{dose_quantity.get('value', '')} {dose_quantity.get('unit', '')}" if dose_quantity else ""
    
    # Extract frequency
    timing = dosage_info.get("timing", {})
    frequency = _extract_frequency_from_timing(timing)
    
    # Create medication record (need discharge_summary_id)
    if not discharge_summary_id:
        # Find most recent discharge summary for this patient
        async with get_db_connection() as conn:
            result = await conn.fetchrow(
                "SELECT id FROM discharge_summaries WHERE patient_id = $1 ORDER BY created_at DESC LIMIT 1",
                patient_id
            )
            if result:
                discharge_summary_id = result['id']
            else:
                # Create a placeholder discharge summary
                placeholder_result = await conn.fetchrow(
                    """
                    INSERT INTO discharge_summaries (patient_id, original_content, source_system, status)
                    VALUES ($1, 'FHIR medication data', 'fhir', 'pending')
                    RETURNING id
                    """,
                    patient_id
                )
                discharge_summary_id = placeholder_result['id']
    
    # Create medication
    async with get_db_connection() as conn:
        query = """
        INSERT INTO medications 
        (discharge_summary_id, medication_name, dosage, frequency, rxnorm_code)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """
        
        result = await conn.fetchrow(
            query,
            discharge_summary_id,
            medication_name,
            dosage,
            frequency,
            rxnorm_code
        )
        
        return result['id']


async def _process_appointment(resource: Dict[str, Any], 
                             patient_id: Optional[str] = None,
                             discharge_summary_id: Optional[str] = None):
    """Process FHIR Appointment"""
    
    # Extract appointment information
    appointment_type = "follow_up"  # Default
    if resource.get("appointmentType"):
        appointment_type = resource["appointmentType"].get("coding", [{}])[0].get("display", "follow_up")
    
    # Extract participants (providers)
    participants = resource.get("participant", [])
    provider_name = "Unknown provider"
    for participant in participants:
        actor = participant.get("actor", {})
        if actor.get("reference", "").startswith("Practitioner/"):
            provider_name = actor.get("display", "Unknown provider")
            break
    
    # Extract date/time
    start_time = resource.get("start")
    if start_time:
        from datetime import datetime
        appointment_date = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    else:
        appointment_date = None
    
    # Find discharge summary if not provided
    if not discharge_summary_id and patient_id:
        async with get_db_connection() as conn:
            result = await conn.fetchrow(
                "SELECT id FROM discharge_summaries WHERE patient_id = $1 ORDER BY created_at DESC LIMIT 1",
                patient_id
            )
            if result:
                discharge_summary_id = result['id']
    
    if not discharge_summary_id:
        raise ValueError("No discharge summary found for appointment")
    
    # Create appointment
    async with get_db_connection() as conn:
        query = """
        INSERT INTO appointments 
        (discharge_summary_id, appointment_type, provider_name, appointment_date)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """
        
        result = await conn.fetchrow(
            query,
            discharge_summary_id,
            appointment_type,
            provider_name,
            appointment_date
        )
        
        return result['id']


async def _process_encounter(resource: Dict[str, Any], patient_id: Optional[str] = None):
    """Process FHIR Encounter for context"""
    # Extract encounter information for context
    # This could be used to link other resources
    pass


def _extract_patient_id(resource: Dict[str, Any]) -> str:
    """Extract patient ID from Patient resource"""
    return resource.get("id", "")


def _extract_patient_reference(subject: Dict[str, Any]) -> str:
    """Extract patient ID from subject reference"""
    if not subject:
        return ""
    
    reference = subject.get("reference", "")
    if reference.startswith("Patient/"):
        return reference.replace("Patient/", "")
    
    return ""


def _extract_frequency_from_timing(timing: Dict[str, Any]) -> str:
    """Extract frequency from FHIR Timing"""
    if not timing:
        return "as directed"
    
    repeat = timing.get("repeat", {})
    frequency = repeat.get("frequency", 1)
    period = repeat.get("period", 1)
    period_unit = repeat.get("periodUnit", "d")
    
    # Convert to readable format
    if period_unit == "d" and period == 1:
        if frequency == 1:
            return "once daily"
        elif frequency == 2:
            return "twice daily"
        elif frequency == 3:
            return "three times daily"
        elif frequency == 4:
            return "four times daily"
    
    return f"{frequency} times per {period} {period_unit}"
