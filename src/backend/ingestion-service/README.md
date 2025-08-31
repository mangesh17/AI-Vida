# AI-Vida Data Ingestion Service

The Data Ingestion Service is a FastAPI-based microservice responsible for processing medical documents, specifically discharge summaries, and extracting structured data from them.

## Features

- **Multi-format Support**: PDF, JSON, FHIR, HL7 messages
- **PDF Processing**: Advanced text extraction with quality scoring and OCR fallback
- **Medical Text Processing**: Normalization of medical abbreviations and terms
- **Data Validation**: Pydantic models for structured data validation
- **Async Operations**: High-performance async/await architecture
- **HIPAA Compliance**: Secure logging and data handling
- **Authentication**: JWT-based security

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Redis 6+

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp ../.env.example .env
# Edit .env with your configuration
```

3. Start the service:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## API Endpoints

### Health Check
- `GET /health` - Service health status

### File Upload
- `POST /upload/` - Upload medical documents (PDF, TXT, JSON)
- `GET /upload/status/{file_id}` - Check processing status

### FHIR Processing
- `POST /fhir/bundle` - Process FHIR bundles
- `POST /fhir/patient` - Process FHIR patient resources

### HL7 Processing
- `POST /hl7/message` - Process HL7 messages
- `POST /hl7/batch` - Process multiple HL7 messages

## Data Models

### Discharge Summary
- Patient information
- Admission details
- Medical history
- Medications
- Follow-up appointments

### Medication
- Name (brand/generic)
- Dosage and frequency
- Duration and instructions
- Drug codes (RxNorm, NDC)

### Appointment
- Provider and department
- Date and location
- Instructions and preparation

## Configuration

Key environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT signing secret
- `OPENAI_API_KEY`: For AI processing (future)
- `MAX_FILE_SIZE_MB`: Maximum upload size
- `ALLOWED_FILE_TYPES`: Supported file formats

## Testing

Run the test suite:
```bash
python tests/test_ingestion_service.py
```

## Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   API Gateway   │───▶│   Ingestion  │───▶│   PostgreSQL    │
│                 │    │   Service    │    │                 │
└─────────────────┘    └──────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │    Redis     │
                       │   (Cache)    │
                       └──────────────┘
```

## Security

- JWT authentication for all endpoints
- HIPAA-compliant logging (PHI redaction)
- Encrypted data storage
- Audit trail for all operations
- Rate limiting and request validation

## Development

### Code Style
- Black for formatting
- isort for import sorting
- flake8 for linting
- Type hints throughout

### Pre-commit Hooks
```bash
pre-commit install
```

## Production Deployment

- Use environment-specific configuration
- Set up proper database migrations
- Configure log aggregation
- Set up monitoring and alerting
- Use HTTPS with proper certificates

## Support

For issues and questions, refer to the main AI-Vida documentation or open an issue in the project repository.
