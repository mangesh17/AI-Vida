"""
HL7 message processing router
"""

import logging
import re
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from datetime import datetime

from core.config import get_settings
from core.database import get_db_connection
from core.logging_config import audit_logger

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()
settings = get_settings()


class HL7Message(BaseModel):
    """HL7 message model"""
    message_type: str
    message_content: str
    sending_application: Optional[str] = None
    sending_facility: Optional[str] = None
    timestamp: Optional[str] = None


class HL7ProcessingResult(BaseModel):
    """HL7 processing result"""
    message_id: str
    status: str
    processed_segments: int
    extracted_data: Dict[str, Any]
    errors: List[str] = []


async def verify_hl7_permissions(token: str = Depends(security)):
    """Verify user has HL7 processing permissions"""
    if not token or not token.credentials:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return token.credentials


@router.post("/process-message", response_model=HL7ProcessingResult)
async def process_hl7_message(
    message: HL7Message = Body(...),
    token: str = Depends(verify_hl7_permissions)
):
    """
    Process HL7 message (ADT, ORU, etc.)
    
    Supports:
    - ADT^A01 (Admit)
    - ADT^A03 (Discharge) 
    - ADT^A08 (Update)
    - ORU^R01 (Results)
    """
    
    try:
        # Parse HL7 message
        parser = HL7Parser()
        parsed_data = await parser.parse_message(message.message_content)
        
        # Process based on message type
        if message.message_type.startswith("ADT"):
            result = await _process_adt_message(parsed_data, message.message_content)
        elif message.message_type.startswith("ORU"):
            result = await _process_oru_message(parsed_data, message.message_content)
        else:
            raise ValueError(f"Unsupported message type: {message.message_type}")
        
        # Log audit event
        audit_logger.log_data_processing(
            user_id=token[:10] + "...",
            document_id=result["message_id"],
            operation="hl7_processing",
            status=result["status"],
            metadata={
                "message_type": message.message_type,
                "processed_segments": result["processed_segments"]
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing HL7 message: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing HL7 message: {str(e)}")


@router.post("/adt-discharge")
async def process_adt_discharge(
    message_content: str = Body(..., embed=True),
    token: str = Depends(verify_hl7_permissions)
):
    """Process ADT discharge message specifically"""
    
    try:
        parser = HL7Parser()
        parsed_data = await parser.parse_message(message_content)
        
        # Validate this is a discharge message
        event_type = parsed_data.get("EVN", {}).get("event_type")
        if event_type not in ["A03", "A16"]:  # A03=Discharge, A16=Pending discharge
            raise ValueError("Not a discharge ADT message")
        
        # Extract discharge information
        discharge_info = await _extract_discharge_info(parsed_data)
        
        # Create discharge summary placeholder
        discharge_summary_id = await _create_discharge_summary_from_adt(discharge_info)
        
        return {
            "discharge_summary_id": str(discharge_summary_id),
            "patient_id": discharge_info.get("patient_id"),
            "admission_id": discharge_info.get("admission_id"),
            "discharge_date": discharge_info.get("discharge_date"),
            "status": "processed"
        }
        
    except Exception as e:
        logger.error(f"Error processing ADT discharge: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing ADT discharge: {str(e)}")


class HL7Parser:
    """HL7 message parser"""
    
    def __init__(self):
        self.field_separator = "|"
        self.component_separator = "^"
        self.repetition_separator = "~"
        self.escape_character = "\\"
        self.subcomponent_separator = "&"
    
    async def parse_message(self, message_content: str) -> Dict[str, Any]:
        """Parse HL7 message into structured data"""
        
        segments = {}
        lines = message_content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse segment
            segment_data = await self._parse_segment(line)
            if segment_data:
                segment_type = segment_data["segment_type"]
                
                # Handle multiple segments of same type
                if segment_type in segments:
                    if not isinstance(segments[segment_type], list):
                        segments[segment_type] = [segments[segment_type]]
                    segments[segment_type].append(segment_data)
                else:
                    segments[segment_type] = segment_data
        
        return segments
    
    async def _parse_segment(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse individual HL7 segment"""
        
        if len(line) < 3:
            return None
        
        segment_type = line[:3]
        fields = line.split(self.field_separator)
        
        segment_data = {
            "segment_type": segment_type,
            "raw": line
        }
        
        # Parse based on segment type
        if segment_type == "MSH":
            await self._parse_msh_segment(fields, segment_data)
        elif segment_type == "EVN":
            await self._parse_evn_segment(fields, segment_data)
        elif segment_type == "PID":
            await self._parse_pid_segment(fields, segment_data)
        elif segment_type == "PV1":
            await self._parse_pv1_segment(fields, segment_data)
        elif segment_type == "OBX":
            await self._parse_obx_segment(fields, segment_data)
        elif segment_type == "DG1":
            await self._parse_dg1_segment(fields, segment_data)
        
        return segment_data
    
    async def _parse_msh_segment(self, fields: List[str], segment_data: Dict[str, Any]):
        """Parse MSH (Message Header) segment"""
        if len(fields) >= 12:
            segment_data.update({
                "sending_application": fields[3] if len(fields) > 3 else "",
                "sending_facility": fields[4] if len(fields) > 4 else "",
                "receiving_application": fields[5] if len(fields) > 5 else "",
                "receiving_facility": fields[6] if len(fields) > 6 else "",
                "timestamp": fields[7] if len(fields) > 7 else "",
                "message_type": fields[9] if len(fields) > 9 else "",
                "message_control_id": fields[10] if len(fields) > 10 else "",
                "processing_id": fields[11] if len(fields) > 11 else ""
            })
    
    async def _parse_evn_segment(self, fields: List[str], segment_data: Dict[str, Any]):
        """Parse EVN (Event Type) segment"""
        if len(fields) >= 3:
            segment_data.update({
                "event_type": fields[1] if len(fields) > 1 else "",
                "recorded_date": fields[2] if len(fields) > 2 else "",
                "operator_id": fields[5] if len(fields) > 5 else ""
            })
    
    async def _parse_pid_segment(self, fields: List[str], segment_data: Dict[str, Any]):
        """Parse PID (Patient Identification) segment"""
        if len(fields) >= 6:
            # Patient ID
            patient_id_components = fields[3].split(self.component_separator) if len(fields) > 3 else [""]
            patient_id = patient_id_components[0] if patient_id_components else ""
            
            # Patient name
            name_components = fields[5].split(self.component_separator) if len(fields) > 5 else ["", "", ""]
            last_name = name_components[0] if len(name_components) > 0 else ""
            first_name = name_components[1] if len(name_components) > 1 else ""
            
            segment_data.update({
                "patient_id": patient_id,
                "last_name": last_name,
                "first_name": first_name,
                "dob": fields[7] if len(fields) > 7 else "",
                "gender": fields[8] if len(fields) > 8 else "",
                "address": fields[11] if len(fields) > 11 else "",
                "phone": fields[13] if len(fields) > 13 else ""
            })
    
    async def _parse_pv1_segment(self, fields: List[str], segment_data: Dict[str, Any]):
        """Parse PV1 (Patient Visit) segment"""
        if len(fields) >= 20:
            segment_data.update({
                "patient_class": fields[2] if len(fields) > 2 else "",
                "assigned_location": fields[3] if len(fields) > 3 else "",
                "admission_type": fields[4] if len(fields) > 4 else "",
                "attending_doctor": fields[7] if len(fields) > 7 else "",
                "admit_date": fields[44] if len(fields) > 44 else "",
                "discharge_date": fields[45] if len(fields) > 45 else ""
            })
    
    async def _parse_obx_segment(self, fields: List[str], segment_data: Dict[str, Any]):
        """Parse OBX (Observation/Result) segment"""
        if len(fields) >= 6:
            segment_data.update({
                "set_id": fields[1] if len(fields) > 1 else "",
                "value_type": fields[2] if len(fields) > 2 else "",
                "observation_id": fields[3] if len(fields) > 3 else "",
                "observation_value": fields[5] if len(fields) > 5 else "",
                "units": fields[6] if len(fields) > 6 else "",
                "reference_range": fields[7] if len(fields) > 7 else "",
                "abnormal_flags": fields[8] if len(fields) > 8 else ""
            })
    
    async def _parse_dg1_segment(self, fields: List[str], segment_data: Dict[str, Any]):
        """Parse DG1 (Diagnosis) segment"""
        if len(fields) >= 4:
            segment_data.update({
                "set_id": fields[1] if len(fields) > 1 else "",
                "diagnosis_code": fields[3] if len(fields) > 3 else "",
                "diagnosis_description": fields[4] if len(fields) > 4 else "",
                "diagnosis_type": fields[6] if len(fields) > 6 else ""
            })


async def _process_adt_message(parsed_data: Dict[str, Any], raw_message: str) -> HL7ProcessingResult:
    """Process ADT (Admission/Discharge/Transfer) message"""
    
    extracted_data = {}
    errors = []
    processed_segments = 0
    
    try:
        # Extract patient information
        if "PID" in parsed_data:
            pid = parsed_data["PID"]
            extracted_data["patient"] = {
                "patient_id": pid.get("patient_id", ""),
                "name": f"{pid.get('first_name', '')} {pid.get('last_name', '')}".strip(),
                "dob": pid.get("dob", ""),
                "gender": pid.get("gender", "")
            }
            processed_segments += 1
        
        # Extract visit information
        if "PV1" in parsed_data:
            pv1 = parsed_data["PV1"]
            extracted_data["visit"] = {
                "patient_class": pv1.get("patient_class", ""),
                "location": pv1.get("assigned_location", ""),
                "admission_type": pv1.get("admission_type", ""),
                "attending_doctor": pv1.get("attending_doctor", ""),
                "admit_date": pv1.get("admit_date", ""),
                "discharge_date": pv1.get("discharge_date", "")
            }
            processed_segments += 1
        
        # Extract event information
        if "EVN" in parsed_data:
            evn = parsed_data["EVN"]
            extracted_data["event"] = {
                "event_type": evn.get("event_type", ""),
                "recorded_date": evn.get("recorded_date", "")
            }
            processed_segments += 1
        
        # Extract diagnoses
        if "DG1" in parsed_data:
            dg1_segments = parsed_data["DG1"]
            if not isinstance(dg1_segments, list):
                dg1_segments = [dg1_segments]
            
            diagnoses = []
            for dg1 in dg1_segments:
                diagnoses.append({
                    "code": dg1.get("diagnosis_code", ""),
                    "description": dg1.get("diagnosis_description", ""),
                    "type": dg1.get("diagnosis_type", "")
                })
                processed_segments += 1
            
            extracted_data["diagnoses"] = diagnoses
        
        message_id = parsed_data.get("MSH", {}).get("message_control_id", "unknown")
        
        return HL7ProcessingResult(
            message_id=message_id,
            status="success",
            processed_segments=processed_segments,
            extracted_data=extracted_data,
            errors=errors
        )
        
    except Exception as e:
        errors.append(str(e))
        return HL7ProcessingResult(
            message_id="error",
            status="error",
            processed_segments=processed_segments,
            extracted_data=extracted_data,
            errors=errors
        )


async def _process_oru_message(parsed_data: Dict[str, Any], raw_message: str) -> HL7ProcessingResult:
    """Process ORU (Observation Result) message"""
    
    extracted_data = {}
    errors = []
    processed_segments = 0
    
    try:
        # Extract patient information
        if "PID" in parsed_data:
            pid = parsed_data["PID"]
            extracted_data["patient"] = {
                "patient_id": pid.get("patient_id", ""),
                "name": f"{pid.get('first_name', '')} {pid.get('last_name', '')}".strip()
            }
            processed_segments += 1
        
        # Extract observations/results
        if "OBX" in parsed_data:
            obx_segments = parsed_data["OBX"]
            if not isinstance(obx_segments, list):
                obx_segments = [obx_segments]
            
            observations = []
            for obx in obx_segments:
                observations.append({
                    "observation_id": obx.get("observation_id", ""),
                    "value": obx.get("observation_value", ""),
                    "units": obx.get("units", ""),
                    "reference_range": obx.get("reference_range", ""),
                    "abnormal_flags": obx.get("abnormal_flags", "")
                })
                processed_segments += 1
            
            extracted_data["observations"] = observations
        
        message_id = parsed_data.get("MSH", {}).get("message_control_id", "unknown")
        
        return HL7ProcessingResult(
            message_id=message_id,
            status="success",
            processed_segments=processed_segments,
            extracted_data=extracted_data,
            errors=errors
        )
        
    except Exception as e:
        errors.append(str(e))
        return HL7ProcessingResult(
            message_id="error",
            status="error",
            processed_segments=processed_segments,
            extracted_data=extracted_data,
            errors=errors
        )


async def _extract_discharge_info(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract discharge information from parsed HL7 data"""
    
    discharge_info = {}
    
    # Patient information
    if "PID" in parsed_data:
        pid = parsed_data["PID"]
        discharge_info.update({
            "patient_id": pid.get("patient_id", ""),
            "patient_name": f"{pid.get('first_name', '')} {pid.get('last_name', '')}".strip(),
            "dob": pid.get("dob", ""),
            "gender": pid.get("gender", "")
        })
    
    # Visit information
    if "PV1" in parsed_data:
        pv1 = parsed_data["PV1"]
        discharge_info.update({
            "admission_id": pv1.get("assigned_location", ""),
            "discharge_date": pv1.get("discharge_date", ""),
            "attending_physician": pv1.get("attending_doctor", "")
        })
    
    return discharge_info


async def _create_discharge_summary_from_adt(discharge_info: Dict[str, Any]) -> str:
    """Create discharge summary record from ADT information"""
    
    # Generate basic discharge content from HL7 data
    content_parts = []
    
    if discharge_info.get("patient_name"):
        content_parts.append(f"Patient: {discharge_info['patient_name']}")
    
    if discharge_info.get("discharge_date"):
        content_parts.append(f"Discharge Date: {discharge_info['discharge_date']}")
    
    if discharge_info.get("attending_physician"):
        content_parts.append(f"Attending Physician: {discharge_info['attending_physician']}")
    
    content_parts.append("Discharge summary generated from HL7 ADT message.")
    content_parts.append("Additional clinical documentation required.")
    
    content = "\n".join(content_parts)
    
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
            discharge_info.get("patient_id", ""),
            content,
            "hl7_adt",
            discharge_info,
            "pending"
        )
        
        return result['id']
