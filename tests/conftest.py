# Test Configuration
"""
Configuration and fixtures for AI-Vida tests
"""

import pytest
import os
from pathlib import Path

# Set test environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "postgresql://aivida_app:development_password@localhost:5432/aivida_main"

# Test data directory
TEST_DATA_DIR = Path(__file__).parent.parent / "test_data"

@pytest.fixture(scope="session")
def test_data_dir():
    """Fixture providing path to test data directory"""
    return TEST_DATA_DIR

@pytest.fixture(scope="session")
def service_base_url():
    """Fixture providing the base URL for the service"""
    return "http://127.0.0.1:8001"

@pytest.fixture(scope="session")
def test_auth_token():
    """Fixture providing test authentication token"""
    return "Bearer test-token-123"

@pytest.fixture
def sample_discharge_text(test_data_dir):
    """Fixture providing sample discharge summary text"""
    with open(test_data_dir / "sample_discharge_summary.txt", "r") as f:
        return f.read()

@pytest.fixture
def structured_discharge_json(test_data_dir):
    """Fixture providing structured discharge JSON"""
    import json
    with open(test_data_dir / "structured_discharge.json", "r") as f:
        return json.load(f)

@pytest.fixture
def fhir_bundle_data(test_data_dir):
    """Fixture providing FHIR bundle data"""
    import json
    with open(test_data_dir / "fhir_bundle.json", "r") as f:
        return json.load(f)

@pytest.fixture
def hl7_adt_message(test_data_dir):
    """Fixture providing HL7 ADT message"""
    with open(test_data_dir / "sample_hl7_adt.txt", "r") as f:
        return f.read()
