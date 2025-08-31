"""
Logging configuration for the Data Ingestion Service
"""

import logging
import logging.handlers
import sys
from typing import Dict, Any
import json
from datetime import datetime

from .config import get_settings

settings = get_settings()


class HIPAAFormatter(logging.Formatter):
    """Custom formatter that ensures HIPAA compliance in logs"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S UTC'
        )
    
    def format(self, record: logging.LogRecord) -> str:
        # Ensure no PHI is logged
        if hasattr(record, 'msg'):
            # Simple check for common PHI patterns
            sensitive_patterns = [
                'ssn', 'social security', 'patient_name', 'dob', 'date_of_birth',
                'phone', 'address', 'email', 'mrn', 'medical record number'
            ]
            
            msg_lower = str(record.msg).lower()
            for pattern in sensitive_patterns:
                if pattern in msg_lower:
                    record.msg = "[REDACTED - POTENTIAL PHI]"
                    break
        
        return super().format(record)


class AuditLogger:
    """Separate audit logger for HIPAA compliance"""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        # Create audit log handler
        if settings.is_production:
            handler = logging.handlers.RotatingFileHandler(
                '/var/log/aivida/audit.log',
                maxBytes=100*1024*1024,  # 100MB
                backupCount=10
            )
        else:
            handler = logging.StreamHandler(sys.stdout)
        
        handler.setFormatter(HIPAAFormatter())
        self.logger.addHandler(handler)
    
    def log_access(self, user_id: str, resource: str, action: str, 
                   ip_address: str = None, metadata: Dict[str, Any] = None):
        """Log access events for audit trail"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "access",
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "ip_address": ip_address,
            "metadata": metadata or {}
        }
        
        self.logger.info(json.dumps(audit_entry))
    
    def log_data_processing(self, user_id: str, document_id: str, 
                          operation: str, status: str, 
                          metadata: Dict[str, Any] = None):
        """Log data processing events"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "data_processing",
            "user_id": user_id,
            "document_id": document_id,
            "operation": operation,
            "status": status,
            "metadata": metadata or {}
        }
        
        self.logger.info(json.dumps(audit_entry))


def setup_logging():
    """Setup application logging"""
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(HIPAAFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler for production
    if settings.is_production:
        file_handler = logging.handlers.RotatingFileHandler(
            '/var/log/aivida/application.log',
            maxBytes=50*1024*1024,  # 50MB
            backupCount=5
        )
        file_handler.setFormatter(HIPAAFormatter())
        root_logger.addHandler(file_handler)
    
    # Set library log levels
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('fastapi').setLevel(logging.INFO)
    logging.getLogger('asyncpg').setLevel(logging.WARNING)
    
    logging.info("Logging configured successfully")


# Global audit logger instance
audit_logger = AuditLogger()
