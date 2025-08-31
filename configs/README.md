# Configuration Files

This directory contains environment-specific configuration files for the AI-Vida platform.

## Structure

- **`database/`**: Database connection and configuration files
  - Connection strings for different environments
  - Database schema configurations
  - Migration settings

- **`logging/`**: Logging configuration and settings
  - Log levels for different environments
  - Audit logging configurations
  - HIPAA-compliant log retention policies

- **`monitoring/`**: Monitoring and alerting configurations
  - Prometheus configuration
  - Grafana dashboards
  - Alert manager settings

- **`security/`**: Security-related configurations
  - OAuth 2.0 provider settings
  - Encryption key management
  - CORS and security headers

## Environment Variables

Configuration files use environment variables for sensitive data:

- `DATABASE_URL`: Database connection string
- `JWT_SECRET`: JWT token signing secret
- `ENCRYPTION_KEY`: Data encryption key
- `OAUTH_CLIENT_ID`: OAuth client identifier
- `OAUTH_CLIENT_SECRET`: OAuth client secret

## Security Note

- Never commit sensitive configuration data to version control
- Use environment variables or secure key management systems
- All configurations must comply with HIPAA security requirements
- Encrypt configuration files containing sensitive data
