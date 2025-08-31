"""
Router initialization
"""

from .upload import router as upload_router
from .fhir import router as fhir_router  
from .hl7 import router as hl7_router

__all__ = ['upload_router', 'fhir_router', 'hl7_router']
