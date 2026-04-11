"""
Application configuration module.
Handles all application settings using Pydantic Settings.
"""

import os
import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import EmailStr, Field, field_validator

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings  # type: ignore[no-redef]


def _get_env_file() -> str:
    """Get the appropriate .env file based on environment"""
    # Check for CI environment first
    if os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true":
        if os.path.exists(".env.ci"):
            return ".env.ci"
    # Check for testing environment
    elif os.getenv("TESTING") == "true":
        if os.path.exists(".env.test"):
            return ".env.test"
    # Default to .env
    return ".env"


class Settings(BaseSettings):
    """Application settings configuration."""

    # Application Configuration
    APP_NAME: str = "考勤管理系统"
    PROJECT_NAME: str = "考勤管理系统"  # Added for compatibility
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    TESTING: bool = False

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False

    # Database Configuration
    DATABASE_URL: str = Field(
        default="", description="Database URL for async operations"
    )
    DATABASE_URL_SYNC: str = Field(
        default="", description="Database URL for sync operations"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str]) -> str:
        # If explicitly set in environment variables, always use it
        if isinstance(v, str) and v:
            return v

        # Check for explicit DATABASE_URL environment variable first
        explicit_db_url = os.getenv("DATABASE_URL")
        if explicit_db_url:
            return explicit_db_url

        # PostgreSQL-only configuration based on environment
        if os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true":
            # CI environment - PostgreSQL service
            return "postgresql+asyncpg://postgres:postgres@localhost:5432/test_attendence"
        elif os.getenv("TESTING") == "true":
            # Testing environment - local PostgreSQL
            test_host = os.getenv("TEST_DB_HOST", "localhost")
            test_user = os.getenv("TEST_DB_USER", "kwok")
            test_password = os.getenv("TEST_DB_PASSWORD", "Onjuju1084")
            test_database = os.getenv("TEST_DB_NAME", "attendence_dev")
            return f"postgresql+asyncpg://{test_user}:{test_password}@{test_host}:5432/{test_database}"

        # Fallback to development PostgreSQL if no environment variable is set
        return "postgresql+asyncpg://kwok:Onjuju1084@192.168.31.124:5432/attendence_dev"

    @field_validator("DATABASE_URL_SYNC", mode="before")
    @classmethod
    def assemble_db_connection_sync(cls, v: Optional[str]) -> str:
        # If explicitly set in environment variables, always use it
        if isinstance(v, str) and v:
            return v

        # Check for explicit DATABASE_URL_SYNC environment variable first
        explicit_db_url = os.getenv("DATABASE_URL_SYNC")
        if explicit_db_url:
            return explicit_db_url

        # PostgreSQL-only sync configuration based on environment
        if os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true":
            # CI environment - PostgreSQL service (sync)
            return "postgresql://postgres:postgres@localhost:5432/test_attendence"
        elif os.getenv("TESTING") == "true":
            # Testing environment - local PostgreSQL (sync)
            test_host = os.getenv("TEST_DB_HOST", "localhost")
            test_user = os.getenv("TEST_DB_USER", "kwok")
            test_password = os.getenv("TEST_DB_PASSWORD", "Onjuju1084")
            test_database = os.getenv("TEST_DB_NAME", "attendence_dev")
            return f"postgresql://{test_user}:{test_password}@{test_host}:5432/{test_database}"

        # Default fallback for sync database URL
        return "postgresql://kwok:Onjuju1084@192.168.31.124:5432/attendence_dev"

    # Authentication Configuration
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="JWT signing secret key",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    AUTH_APP_USER_READ_FIRST: bool = False
    AUTH_APP_USER_READ_PERCENT: int = 0
    AUTH_LOGOUT_ALL_DEVICES_DEFAULT: bool = True
    AUTH_LOGOUT_REQUIRE_DEVICE_ID_WHEN_SINGLE: bool = True
    API_RESPONSE_CAMELCASE_ALIAS_ENABLED: bool = False

    # Password Configuration
    PWD_CONTEXT_SCHEMES: List[str] = ["bcrypt"]
    PWD_CONTEXT_DEPRECATED: Optional[str] = None

    # Encryption Configuration (AES-256-GCM)
    ENCRYPTION_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="32-byte encryption key for AES-256-GCM",
    )
    SALT: str = Field(
        default_factory=lambda: secrets.token_urlsafe(16),
        description="Salt for key derivation",
    )

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Redis Configuration (Optional)
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    # Celery Configuration (Optional)
    CELERY_BROKER_URL: Optional[str] = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: Optional[str] = "redis://localhost:6379/2"

    # File Upload Configuration
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".xlsx", ".xls", ".csv"]
    UPLOAD_DIR: str = "uploads"

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Email Configuration (Optional)
    MAIL_SERVER: Optional[str] = None
    MAIL_PORT: Optional[int] = None
    MAIL_USE_TLS: bool = True
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM: Optional[EmailStr] = None

    # Monitoring Configuration (Optional)
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_PORT: Optional[int] = 9090

    # Security Headers
    SECURITY_HEADERS_ENABLED: bool = True
    CSP_POLICY: str = "default-src 'self'"

    # Pagination Configuration
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Task Configuration
    DEFAULT_ONLINE_TASK_MINUTES: int = 40
    DEFAULT_OFFLINE_TASK_MINUTES: int = 100
    RUSH_TASK_BONUS_MINUTES: int = 15
    POSITIVE_REVIEW_BONUS_MINUTES: int = 30
    LATE_RESPONSE_PENALTY_MINUTES: int = 30
    LATE_COMPLETION_PENALTY_MINUTES: int = 30
    NEGATIVE_REVIEW_PENALTY_MINUTES: int = 60

    # Business Rules Configuration
    RESPONSE_TIMEOUT_HOURS: int = 24
    COMPLETION_TIMEOUT_HOURS: int = 48
    MIN_RATING_FOR_POSITIVE: int = 4
    MAX_RATING_FOR_NEGATIVE: int = 2

    model_config = {
        "env_file": _get_env_file(),
        "case_sensitive": True,
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Global settings instance
settings = Settings()


# Computed properties for convenience
def get_database_url() -> str:
    """Get the async database URL."""
    return settings.DATABASE_URL


def get_database_url_sync() -> str:
    """Get the sync database URL."""
    return settings.DATABASE_URL_SYNC


def is_development() -> bool:
    """Check if the application is running in development mode."""
    return settings.DEBUG or settings.TESTING


def is_production() -> bool:
    """Check if the application is running in production mode."""
    return not (settings.DEBUG or settings.TESTING)


def get_cors_origins() -> List[str]:
    """Get CORS origins as string list."""
    return settings.CORS_ORIGINS


def get_upload_path() -> str:
    """Get the upload directory path."""
    import os

    upload_dir = settings.UPLOAD_DIR
    if not os.path.isabs(upload_dir):
        upload_dir = os.path.abspath(upload_dir)
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def get_log_config() -> Dict[str, Any]:
    """Get logging configuration."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": settings.LOG_FORMAT,
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["default"],
        },
        "loggers": {
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
