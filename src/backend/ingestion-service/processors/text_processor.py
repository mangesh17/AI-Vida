"""
Text processing and normalization utilities
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional
import asyncio

logger = logging.getLogger(__name__)


class TextProcessor:
    """Text processing and normalization for clinical documents"""
    
    def __init__(self):
        self.medical_abbreviations = {
            'pt': 'patient',
            'dx': 'diagnosis',
            'tx': 'treatment',
            'rx': 'prescription',
            'hx': 'history',
            'sx': 'symptoms',
            'f/u': 'follow-up',
            'w/': 'with',
            'w/o': 'without',
            'c/o': 'complains of',
            'r/o': 'rule out',
            's/p': 'status post',
            'bid': 'twice daily',
            'tid': 'three times daily',
            'qid': 'four times daily',
            'prn': 'as needed',
            'po': 'by mouth',
            'iv': 'intravenous',
            'im': 'intramuscular',
            'sc': 'subcutaneous'
        }
    
    async def process_json(self, json_content: bytes) -> str:
        """Process structured JSON content"""
        try:
            data = json.loads(json_content.decode('utf-8'))
            
            # Convert structured data to text format
            if isinstance(data, dict):
                return await self._dict_to_text(data)
            elif isinstance(data, list):
                return await self._list_to_text(data)
            else:
                return str(data)
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON content: {e}")
            raise ValueError("Invalid JSON format")
    
    async def _dict_to_text(self, data: Dict[str, Any]) -> str:
        """Convert dictionary to readable text"""
        text_parts = []
        
        # Handle common document sections
        section_order = [
            'patient_info', 'admission_info', 'chief_complaint',
            'history_present_illness', 'past_medical_history',
            'medications', 'allergies', 'social_history',
            'physical_exam', 'assessment', 'plan',
            'discharge_medications', 'follow_up', 'instructions'
        ]
        
        # Process known sections first
        processed_keys = set()
        for section in section_order:
            if section in data:
                text_parts.append(await self._format_section(section, data[section]))
                processed_keys.add(section)
        
        # Process remaining keys
        for key, value in data.items():
            if key not in processed_keys:
                text_parts.append(await self._format_section(key, value))
        
        return '\n\n'.join(text_parts)
    
    async def _list_to_text(self, data: List[Any]) -> str:
        """Convert list to readable text"""
        text_parts = []
        
        for i, item in enumerate(data):
            if isinstance(item, dict):
                text_parts.append(f"Item {i + 1}:")
                text_parts.append(await self._dict_to_text(item))
            else:
                text_parts.append(f"Item {i + 1}: {str(item)}")
        
        return '\n'.join(text_parts)
    
    async def _format_section(self, section_name: str, content: Any) -> str:
        """Format a section with appropriate heading"""
        # Clean up section name
        clean_name = section_name.replace('_', ' ').title()
        
        if isinstance(content, dict):
            content_text = await self._dict_to_text(content)
        elif isinstance(content, list):
            content_text = await self._list_to_text(content)
        else:
            content_text = str(content)
        
        return f"{clean_name}:\n{content_text}"
    
    async def normalize_text(self, text: str) -> str:
        """Normalize clinical text"""
        if not text:
            return ""
        
        # Basic text cleaning
        text = await self._clean_text(text)
        
        # Expand medical abbreviations
        text = await self._expand_abbreviations(text)
        
        # Normalize formatting
        text = await self._normalize_formatting(text)
        
        return text
    
    async def _clean_text(self, text: str) -> str:
        """Basic text cleaning"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common OCR artifacts
        text = re.sub(r'[^\w\s\.,!?;:()\-\/]', '', text)
        
        # Fix common formatting issues
        text = re.sub(r'\.+', '.', text)  # Multiple periods
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)  # Space before punctuation
        
        return text.strip()
    
    async def _expand_abbreviations(self, text: str) -> str:
        """Expand medical abbreviations"""
        words = text.split()
        expanded_words = []
        
        for word in words:
            clean_word = word.lower().strip('.,!?;:')
            if clean_word in self.medical_abbreviations:
                replacement = self.medical_abbreviations[clean_word]
                # Preserve original capitalization pattern
                if word.isupper():
                    replacement = replacement.upper()
                elif word.istitle():
                    replacement = replacement.title()
                expanded_words.append(word.replace(clean_word, replacement))
            else:
                expanded_words.append(word)
        
        return ' '.join(expanded_words)
    
    async def _normalize_formatting(self, text: str) -> str:
        """Normalize text formatting"""
        # Ensure proper sentence spacing
        text = re.sub(r'\.(\w)', r'. \1', text)
        
        # Normalize line breaks
        text = re.sub(r'\n+', '\n', text)
        
        # Ensure proper paragraph breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    async def extract_sections(self, text: str) -> Dict[str, str]:
        """Extract common sections from discharge summary text"""
        sections = {}
        
        # Common section headers
        section_patterns = {
            'chief_complaint': r'(?i)chief\s+complaint:?\s*(.*?)(?=\n\w+:|$)',
            'history_present_illness': r'(?i)history\s+of\s+present\s+illness:?\s*(.*?)(?=\n\w+:|$)',
            'past_medical_history': r'(?i)past\s+medical\s+history:?\s*(.*?)(?=\n\w+:|$)',
            'medications': r'(?i)(?:discharge\s+)?medications?:?\s*(.*?)(?=\n\w+:|$)',
            'allergies': r'(?i)allergies:?\s*(.*?)(?=\n\w+:|$)',
            'physical_exam': r'(?i)physical\s+exam(?:ination)?:?\s*(.*?)(?=\n\w+:|$)',
            'assessment': r'(?i)assessment:?\s*(.*?)(?=\n\w+:|$)',
            'plan': r'(?i)plan:?\s*(.*?)(?=\n\w+:|$)',
            'follow_up': r'(?i)follow[-\s]?up:?\s*(.*?)(?=\n\w+:|$)',
            'instructions': r'(?i)(?:discharge\s+)?instructions:?\s*(.*?)(?=\n\w+:|$)'
        }
        
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            if match:
                section_content = match.group(1).strip()
                if section_content:
                    sections[section_name] = section_content
        
        return sections
    
    async def identify_medication_list(self, text: str) -> List[str]:
        """Extract medication list from text"""
        medications = []
        
        # Look for medication patterns
        med_patterns = [
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?([A-Za-z][A-Za-z\s\-]+)\s+(?:\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?))',
            r'(?i)(?:^|\n)\s*[-*•]\s*([A-Za-z][A-Za-z\s\-]+)\s+(?:\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?))'
        ]
        
        for pattern in med_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                med_name = match.strip()
                if len(med_name) > 2 and med_name not in medications:
                    medications.append(med_name)
        
        return medications
    
    async def identify_appointments(self, text: str) -> List[Dict[str, str]]:
        """Extract appointment information from text"""
        appointments = []
        
        # Look for appointment patterns
        apt_patterns = [
            r'(?i)follow[-\s]?up\s+(?:with\s+)?([^.]+?)(?:on\s+|in\s+)?(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\w+\s+\d{1,2})',
            r'(?i)appointment\s+(?:with\s+)?([^.]+?)(?:on\s+|in\s+)?(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\w+\s+\d{1,2})',
            r'(?i)see\s+([^.]+?)(?:on\s+|in\s+)?(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\w+\s+\d{1,2})'
        ]
        
        for pattern in apt_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for provider, date in matches:
                appointments.append({
                    'provider': provider.strip(),
                    'date': date.strip()
                })
        
        return appointments
