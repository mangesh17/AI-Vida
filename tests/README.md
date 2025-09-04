# AI-Vida Tests

This directory contains all testing suites for the AI-Vida platform, ensuring code quality, security, and HIPAA compliance.

## Structure

- **`unit/`**: Unit tests for individual components and functions
- **`integration/`**: Integration tests for service interactions
  - **`test_data_ingestion_api.py`**: API integration tests for Data Ingestion Service
- **`e2e/`**: End-to-end tests for complete user workflows
- **`security/`**: Security penetration and vulnerability tests

## Current Integration Tests

### Data Ingestion Service API Tests

Located in `integration/test_data_ingestion_api.py`, these tests validate:

✅ **Service Health**: Database connectivity and service status  
✅ **File Upload**: Text and JSON document processing  
✅ **FHIR Processing**: Bundle parsing and resource extraction  
✅ **HL7 Processing**: Message parsing and segment extraction  
✅ **Document Management**: Listing and status tracking  

### Running Integration Tests

#### Prerequisites

1. Ensure the Data Ingestion Service is running:
   ```bash
   cd src/backend/ingestion-service
   uvicorn main:app --host 127.0.0.1 --port 8001 --reload
   ```

2. Ensure the database containers are running:
   ```bash
   docker-compose up -d
   ```

#### Run Tests

```bash
# From project root - run all tests
pytest tests/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run specific API tests
pytest tests/integration/test_data_ingestion_api.py -v

# Run as standalone script (backward compatibility)
python tests/integration/test_data_ingestion_api.py
```

### Test Data

Integration tests use real medical data samples from the `test_data/` directory:

- `sample_discharge_summary.txt` - STEMI patient discharge summary
- `structured_discharge.json` - Structured surgical discharge data
- `fhir_bundle.json` - FHIR bundle with medications and appointments
- `sample_hl7_adt.txt` - HL7 ADT discharge message
- **`compliance/`**: HIPAA compliance validation tests

## Testing Strategy

### Unit Tests
- Test individual functions and classes
- Mock external dependencies
- Achieve >90% code coverage

### Integration Tests
- Test service-to-service communication
- Database integration testing
- API contract testing

### End-to-End Tests
- Complete user journey testing
- Cross-browser compatibility
- Mobile application testing

### Security Tests
- Penetration testing
- Vulnerability scanning
- Authentication/authorization testing
- Data encryption validation

### Compliance Tests
- HIPAA Security Rule validation
- Audit trail verification
- Access control testing
- Data retention policy validation

## Running Tests

```bash
# Run all tests
npm test

# Run specific test suites
npm run test:unit
npm run test:integration
npm run test:e2e
npm run test:security
npm run test:compliance
```

## Continuous Integration

All tests are automatically executed in the CI/CD pipeline before deployment.
