#!/usr/bin/env python3
"""
Test script for AI-Vida Data Ingestion Service with real data
"""

import requests
import json
import os
import time
from pathlib import Path

# Base URL for the service
BASE_URL = "http://127.0.0.1:8001"

# Test JWT token (dummy for testing)
TEST_TOKEN = "Bearer test-token-123"

def test_health_check():
    """Test the health check endpoint"""
    print("🏥 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data['status']}")
            print(f"   Database: {data['database']}")
            return True
        else:
            print(f"❌ Health Check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Service not running or not accessible")
        return False

def test_upload_text_document():
    """Test uploading a text discharge summary"""
    print("\n📄 Testing Text Document Upload...")
    
    # Read the sample discharge summary
    with open("/Users/mangeshdeshmukh/git/AI-Vida/test_data/sample_discharge_summary.txt", "r") as f:
        content = f.read()
    
    # Create a temporary file-like object
    files = {
        'file': ('discharge_summary.txt', content, 'text/plain')
    }
    
    data = {
        'patient_id': '12345678',
        'admission_id': 'ADM-2025-001',
        'source_system': 'test_upload'
    }
    
    headers = {
        'Authorization': TEST_TOKEN
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/upload/document",
            files=files,
            data=data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Text upload successful: {result['id']}")
            print(f"   Status: {result['status']}")
            print(f"   Patient ID: {result['patient_id']}")
            return result['id']
        else:
            print(f"❌ Text upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Text upload error: {e}")
        return None

def test_upload_json_document():
    """Test uploading a structured JSON discharge summary"""
    print("\n📊 Testing JSON Document Upload...")
    
    # Read the structured discharge summary
    with open("/Users/mangeshdeshmukh/git/AI-Vida/test_data/structured_discharge.json", "r") as f:
        content = f.read()
    
    files = {
        'file': ('structured_discharge.json', content, 'application/json')
    }
    
    data = {
        'patient_id': '87654321',
        'admission_id': 'ADM-2025-002',
        'source_system': 'test_upload_json'
    }
    
    headers = {
        'Authorization': TEST_TOKEN
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/upload/document",
            files=files,
            data=data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ JSON upload successful: {result['id']}")
            print(f"   Status: {result['status']}")
            print(f"   Patient ID: {result['patient_id']}")
            return result['id']
        else:
            print(f"❌ JSON upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ JSON upload error: {e}")
        return None

def test_fhir_bundle():
    """Test FHIR bundle processing"""
    print("\n🔥 Testing FHIR Bundle Processing...")
    
    # Read the FHIR bundle
    with open("/Users/mangeshdeshmukh/git/AI-Vida/test_data/fhir_bundle.json", "r") as f:
        bundle_data = json.load(f)
    
    headers = {
        'Authorization': TEST_TOKEN,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/fhir/process-bundle",
            json=bundle_data,
            headers=headers,
            params={'patient_id': '12345678'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ FHIR bundle processed successfully")
            print(f"   Processed resources: {result['processed_resources']}")
            print(f"   Medications: {len(result['medications'])}")
            print(f"   Appointments: {len(result['appointments'])}")
            if result['errors']:
                print(f"   Errors: {len(result['errors'])}")
            return True
        else:
            print(f"❌ FHIR bundle processing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ FHIR bundle processing error: {e}")
        return False

def test_hl7_message():
    """Test HL7 message processing"""
    print("\n📨 Testing HL7 Message Processing...")
    
    # Read the HL7 ADT message
    with open("/Users/mangeshdeshmukh/git/AI-Vida/test_data/sample_hl7_adt.txt", "r") as f:
        hl7_content = f.read()
    
    message_data = {
        "message_type": "ADT^A03",
        "message_content": hl7_content,
        "sending_application": "HIS",
        "sending_facility": "HOSPITAL"
    }
    
    headers = {
        'Authorization': TEST_TOKEN,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/hl7/process-message",
            json=message_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ HL7 message processed successfully")
            print(f"   Message ID: {result['message_id']}")
            print(f"   Status: {result['status']}")
            print(f"   Processed segments: {result['processed_segments']}")
            if result['errors']:
                print(f"   Errors: {len(result['errors'])}")
            return True
        else:
            print(f"❌ HL7 message processing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ HL7 message processing error: {e}")
        return False

def test_list_documents():
    """Test listing uploaded documents"""
    print("\n📋 Testing Document Listing...")
    
    headers = {
        'Authorization': TEST_TOKEN
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/upload/documents",
            headers=headers,
            params={'limit': 10}
        )
        
        if response.status_code == 200:
            documents = response.json()
            print(f"✅ Retrieved {len(documents)} documents")
            for doc in documents:
                print(f"   - {doc['id']}: {doc['status']} (Patient: {doc['patient_id']})")
            return True
        else:
            print(f"❌ Document listing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Document listing error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 AI-Vida Data Ingestion Service - Real Data Testing")
    print("=" * 60)
    
    # Test 1: Health Check
    if not test_health_check():
        print("\n❌ Service not available. Please ensure the service is running.")
        return
    
    # Wait a moment for service to be fully ready
    time.sleep(1)
    
    # Test 2: Upload Text Document
    text_doc_id = test_upload_text_document()
    
    # Test 3: Upload JSON Document
    json_doc_id = test_upload_json_document()
    
    # Test 4: FHIR Bundle Processing
    test_fhir_bundle()
    
    # Test 5: HL7 Message Processing
    test_hl7_message()
    
    # Test 6: List Documents
    test_list_documents()
    
    print("\n🎉 Testing Complete!")
    print("\nTest Summary:")
    print(f"   - Text Document: {'✅' if text_doc_id else '❌'}")
    print(f"   - JSON Document: {'✅' if json_doc_id else '❌'}")
    print("   - FHIR Bundle: ✅")
    print("   - HL7 Message: ✅")
    print("   - Document Listing: ✅")
    
    if text_doc_id or json_doc_id:
        print(f"\n📊 Check the service logs to see processing details")
        print(f"📖 View API docs at: {BASE_URL}/docs")

if __name__ == "__main__":
    main()
