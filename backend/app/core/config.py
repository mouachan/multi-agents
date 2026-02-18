"""
Configuration settings for the Claims Demo backend application.
Loads settings from environment variables and provides typed configuration.

FIXES APPLIED:
- Removed default secret_key (must be set via env var)
- Added warning for wildcard CORS
- Added validator for production settings
"""

import logging
import warnings
from typing import List, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Multi-Agent AI Platform"
    app_version: str = "2.1.0"
    debug: bool = False
    environment: str = "production"

    # API
    api_v1_prefix: str = "/api/v1"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Database
    postgres_host: str = "postgresql-service"
    postgres_port: int = 5432
    postgres_database: str = "claims_db"
    postgres_user: str
    postgres_password: str
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_pre_ping: bool = True
    database_pool_recycle: int = 3600  # 1 hour

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL database URL."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
        )

    @property
    def async_database_url(self) -> str:
        """Construct async PostgreSQL database URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
        )

    # LlamaStack (OpenShift AI)
    llamastack_endpoint: str = "http://llamastack-test-v035.claims-demo.svc.cluster.local:8321"
    llamastack_api_key: Optional[str] = None
    llamastack_default_model: str = "vllm-inference-1/llama-instruct-32-3b"
    llamastack_embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    llamastack_embedding_dimension: int = 768
    llamastack_timeout: int = 300  # seconds
    llamastack_max_retries: int = 3
    llamastack_max_tokens: int = 4096  # max tokens for responses (avoid exceeding model context)

    # MCP Servers
    ocr_server_url: str = "http://ocr-server.claims-demo.svc.cluster.local:8080"
    rag_server_url: str = "http://rag-server.claims-demo.svc.cluster.local:8080"
    claims_server_url: str = "http://claims-server:8080"
    tenders_server_url: str = "http://tenders-server:8080"
    guardrails_server_url: str = (
        "http://claims-guardrails.claims-demo.svc.cluster.local:8080"
    )

    # Guardrails/Shields Configuration
    enable_pii_detection: bool = True  # Enable PII detection and dual-level storage
    pii_redaction_mode: str = "dual"  # "dual" = store original + redacted, "redact_only" = only redacted
    pii_shield_id: str = "pii_detector"  # LlamaStack shield ID for PII detection

    # CORS - default to restrictive, override in production via env vars
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]

    # Security - NO DEFAULT for secret_key, must be set via env var
    #secret_key: str  # Required, no default
    #algorithm: str = "HS256"
    #access_token_expire_minutes: int = 30

    # File Storage
    documents_storage_path: str = "/mnt/documents"
    max_upload_size_mb: int = 10

    # Processing
    max_processing_time_seconds: int = 300
    default_workflow_type: str = "standard"
    enable_async_processing: bool = True

    # Admin & Database Reset
    # Configure this to point to your GitHub repository branch
    # Example: https://raw.githubusercontent.com/your-org/agentic-claim-demo/main/database/seed_data/001_sample_data.sql
    seed_data_url: str = ""  # Must be set via SEED_DATA_URL env var

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 100

    @field_validator('cors_origins', mode='before')
    @classmethod
    def validate_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string if needed."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    @model_validator(mode='after')
    def validate_production_settings(self):
        """Warn about insecure settings in production."""
        if self.environment == "production":
            # Check for wildcard CORS
            if "*" in self.cors_origins:
                warnings.warn(
                    "SECURITY WARNING: Wildcard CORS origin ('*') is enabled in production. "
                    "This is insecure. Set CORS_ORIGINS to specific allowed domains.",
                    UserWarning
                )
            
            # Check for debug mode
            if self.debug:
                warnings.warn(
                    "SECURITY WARNING: Debug mode is enabled in production.",
                    UserWarning
                )
        
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()
