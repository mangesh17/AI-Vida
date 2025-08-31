"""
Core configuration settings for the Data Ingestion Service
"""

import os
from typing import List
from datetime import datetime
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "AI-Vida Data Ingestion Service"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Database
    database_url: str = Field(default="postgresql://localhost:5432/aivida", env="DATABASE_URL")
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production")
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )
    
    # AI Services
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4")
    
    # File Processing
    max_file_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    allowed_file_types: List[str] = Field(
        default=["pdf", "txt", "json"]
    )
    upload_directory: str = Field(default="/tmp/uploads")
    
    # FHIR Settings
    fhir_base_url: str = Field(default="")
    fhir_auth_token: str = Field(default="")
    
    # HL7 Settings
    hl7_endpoint: str = Field(default="", env="HL7_ENDPOINT")
    hl7_auth_token: str = Field(default="", env="HL7_AUTH_TOKEN")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # HIPAA Compliance
    audit_logging: bool = Field(default=True, env="AUDIT_LOGGING")
    data_retention_days: int = Field(default=2555, env="DATA_RETENTION_DAYS")  # ~7 years
    encryption_key: str = Field(default="dev-encryption-key-change-in-production", env="ENCRYPTION_KEY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"
    
    def current_timestamp(self) -> str:
        return datetime.utcnow().isoformat() + "Z"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()
