-- Initialize AI-Vida Database with HIPAA-compliant settings

-- Create application database
CREATE DATABASE aivida_main;
CREATE DATABASE aivida_audit;
CREATE DATABASE aivida_test;

-- Create application user
CREATE USER aivida_app WITH PASSWORD 'development_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE aivida_main TO aivida_app;
GRANT ALL PRIVILEGES ON DATABASE aivida_audit TO aivida_app;
GRANT ALL PRIVILEGES ON DATABASE aivida_test TO aivida_app;

-- Enable required extensions
\c aivida_main;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

\c aivida_audit;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

\c aivida_test;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Configure logging for HIPAA compliance
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_lock_waits = on;

-- Reload configuration
SELECT pg_reload_conf();
