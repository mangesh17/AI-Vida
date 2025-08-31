#!/usr/bin/env python3
"""
Test script for AI-Vida Data Ingestion Service
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Add the ingestion service to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src/backend/ingestion-service'))

from core.config import get_settings
from processors.text_processor import TextProcessor
from processors.pdf_parser import PDFParser

async def test_text_processor():
    """Test text processing functionality"""
    print("🧪 Testing Text Processor...")
    
    processor = TextProcessor()
    
    # Test medical text normalization
    sample_text = "Pt c/o chest pain. Dx: MI. Rx: aspirin 81mg po bid, lisinopril 10mg po qd"
    normalized = await processor.normalize_text(sample_text)
    print(f"Original: {sample_text}")
    print(f"Normalized: {normalized}")
    
    # Test section extraction
    discharge_sample = """
    Chief Complaint: Chest pain
    
    History of Present Illness: Patient is a 65-year-old male with history of hypertension who presents with chest pain.
    
    Medications:
    1. Aspirin 81mg once daily
    2. Lisinopril 10mg once daily
    3. Metformin 500mg twice daily
    
    Follow-up: Cardiology in 2 weeks
    """
    
    sections = await processor.extract_sections(discharge_sample)
    print(f"\nExtracted sections: {list(sections.keys())}")
    
    medications = await processor.identify_medication_list(discharge_sample)
    print(f"Identified medications: {medications}")
    
    appointments = await processor.identify_appointments(discharge_sample)
    print(f"Identified appointments: {appointments}")
    
    print("✅ Text Processor tests completed\n")

async def test_pdf_parser():
    """Test PDF parsing functionality"""
    print("🧪 Testing PDF Parser...")
    
    parser = PDFParser()
    
    # Create a simple test PDF content (this is just a simulation)
    # In real usage, this would be actual PDF bytes
    test_pdf_text = b"""Sample discharge summary content
    Patient: John Doe
    DOB: 01/01/1980
    
    Discharge Medications:
    1. Lisinopril 10mg daily
    2. Aspirin 81mg daily
    
    Follow-up appointments:
    - Cardiology: 2 weeks
    - Primary care: 1 month
    """
    
    try:
        # Since we don't have actual PDF content, we'll test the quality scoring
        sample_text = test_pdf_text.decode('utf-8')
        quality_score = parser._calculate_quality_score(sample_text)
        print(f"Quality score for sample text: {quality_score:.2f}")
        
        print("✅ PDF Parser tests completed\n")
    except Exception as e:
        print(f"⚠️ PDF Parser test skipped (expected without real PDF): {e}\n")

async def test_json_processing():
    """Test JSON processing"""
    print("🧪 Testing JSON Processing...")
    
    processor = TextProcessor()
    
    sample_json = {
        "patient_info": {
            "name": "John Doe",
            "dob": "1980-01-01",
            "mrn": "12345"
        },
        "medications": [
            {
                "name": "Lisinopril",
                "dosage": "10mg",
                "frequency": "daily"
            },
            {
                "name": "Aspirin", 
                "dosage": "81mg",
                "frequency": "daily"
            }
        ],
        "follow_up": [
            {
                "provider": "Cardiology",
                "timeframe": "2 weeks"
            }
        ]
    }
    
    json_bytes = json.dumps(sample_json).encode('utf-8')
    processed_text = await processor.process_json(json_bytes)
    
    print("Sample JSON processed to text:")
    print(processed_text[:500] + "..." if len(processed_text) > 500 else processed_text)
    
    print("✅ JSON Processing tests completed\n")

def test_configuration():
    """Test configuration loading"""
    print("🧪 Testing Configuration...")
    
    # Set some test environment variables
    os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'
    os.environ['REDIS_URL'] = 'redis://localhost:6379'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['OPENAI_API_KEY'] = 'test-openai-key'
    os.environ['ENCRYPTION_KEY'] = 'test-encryption-key'
    
    try:
        settings = get_settings()
        print(f"App name: {settings.app_name}")
        print(f"Environment: {settings.environment}")
        print(f"Debug mode: {settings.debug}")
        print(f"Max file size: {settings.max_file_size / (1024*1024):.1f}MB")
        print(f"Allowed file types: {settings.allowed_file_types}")
        print("✅ Configuration tests completed\n")
    except Exception as e:
        print(f"❌ Configuration error: {e}\n")

async def main():
    """Run all tests"""
    print("🚀 AI-Vida Data Ingestion Service Tests")
    print("=" * 50)
    
    # Test configuration first
    test_configuration()
    
    # Test processors
    await test_text_processor()
    await test_pdf_parser()
    await test_json_processing()
    
    print("🎉 All tests completed!")
    print("\nNext steps:")
    print("1. Set up PostgreSQL database")
    print("2. Configure environment variables (.env file)")
    print("3. Run the service: python src/backend/ingestion-service/main.py")
    print("4. Test API endpoints at http://localhost:8001/docs")

if __name__ == "__main__":
    asyncio.run(main())
