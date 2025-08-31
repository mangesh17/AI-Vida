# Source Code

This directory contains all source code for the AI-Vida HIPAA-compliant healthcare platform.

## Structure

- **`backend/`**: Microservices backend (Python/FastAPI)
  - `api-gateway/`: Main API gateway service
  - `auth-service/`: Authentication and authorization
  - `ingestion-service/`: Healthcare data ingestion
  - `normalization-service/`: Data normalization and standardization
  - `generation-service/`: AI-powered report generation
  - `chat-service/`: Patient-clinician chat functionality
  - `audit-service/`: HIPAA audit logging

- **`frontend/`**: Client applications
  - `patient-portal/`: React/TypeScript patient interface
  - `clinician-portal/`: React/TypeScript clinician interface
  - `admin-portal/`: React/TypeScript admin interface
  - `mobile-app/`: React Native mobile application

- **`shared/`**: Shared libraries and components
  - `models/`: Data models and schemas
  - `utils/`: Common utilities
  - `types/`: TypeScript type definitions

## Getting Started

1. Ensure you have the required development environment set up
2. Follow the setup instructions in each service's README
3. Use the scripts in `/scripts/setup/` for environment initialization

## Security

All code must comply with HIPAA security requirements. See `/docs/compliance/` for detailed guidelines.
