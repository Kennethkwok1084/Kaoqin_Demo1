"""
Custom exception classes for the application.
Provides specific error types for different business logic scenarios.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class BaseCustomException(Exception):
    """Base class for custom exceptions."""
    
    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


# Authentication and Authorization Exceptions
class AuthenticationError(BaseCustomException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(BaseCustomException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid."""
    
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message)


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token is expired."""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""
    
    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message)


# Data Validation Exceptions
class ValidationError(BaseCustomException):
    """Raised when data validation fails."""
    
    def __init__(
        self, 
        message: str = "Validation error", 
        field_errors: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            message, 
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {"field_errors": field_errors or {}}
        )


class DuplicateResourceError(BaseCustomException):
    """Raised when trying to create a duplicate resource."""
    
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, status.HTTP_409_CONFLICT)


class ResourceNotFoundError(BaseCustomException):
    """Raised when requested resource is not found."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


# Business Logic Exceptions
class BusinessLogicError(BaseCustomException):
    """Raised when business logic validation fails."""
    
    def __init__(self, message: str = "Business logic error"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class TaskProcessingError(BusinessLogicError):
    """Raised when task processing fails."""
    
    def __init__(self, message: str = "Task processing failed"):
        super().__init__(message)


class WorkHourCalculationError(BusinessLogicError):
    """Raised when work hour calculation fails."""
    
    def __init__(self, message: str = "Work hour calculation error"):
        super().__init__(message)


class AttendanceCalculationError(BusinessLogicError):
    """Raised when attendance calculation fails."""
    
    def __init__(self, message: str = "Attendance calculation error"):
        super().__init__(message)


class InvalidTaskStatusError(BusinessLogicError):
    """Raised when task status transition is invalid."""
    
    def __init__(self, message: str = "Invalid task status transition"):
        super().__init__(message)


class InvalidDateRangeError(BusinessLogicError):
    """Raised when date range is invalid."""
    
    def __init__(self, message: str = "Invalid date range"):
        super().__init__(message)


# File Processing Exceptions
class FileProcessingError(BaseCustomException):
    """Raised when file processing fails."""
    
    def __init__(self, message: str = "File processing error"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class InvalidFileFormatError(FileProcessingError):
    """Raised when file format is invalid."""
    
    def __init__(self, message: str = "Invalid file format"):
        super().__init__(message)


class FileSizeExceededError(FileProcessingError):
    """Raised when file size exceeds limit."""
    
    def __init__(self, message: str = "File size exceeds limit"):
        super().__init__(message)


class ExcelImportError(FileProcessingError):
    """Raised when Excel import fails."""
    
    def __init__(self, message: str = "Excel import failed"):
        super().__init__(message)


class DataMatchingError(FileProcessingError):
    """Raised when data matching fails."""
    
    def __init__(self, message: str = "Data matching failed"):
        super().__init__(message)


# Database Exceptions
class DatabaseError(BaseCustomException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str = "Database error"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    
    def __init__(self, message: str = "Database connection failed"):
        super().__init__(message)


class DatabaseIntegrityError(DatabaseError):
    """Raised when database integrity constraint is violated."""
    
    def __init__(self, message: str = "Database integrity constraint violation"):
        super().__init__(message, status.HTTP_409_CONFLICT)


# Rate Limiting Exceptions
class RateLimitExceededError(BaseCustomException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS)


# Configuration Exceptions
class ConfigurationError(BaseCustomException):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is missing."""
    
    def __init__(self, message: str = "Missing required configuration"):
        super().__init__(message)


# External Service Exceptions
class ExternalServiceError(BaseCustomException):
    """Raised when external service fails."""
    
    def __init__(self, message: str = "External service error"):
        super().__init__(message, status.HTTP_502_BAD_GATEWAY)


class EmailServiceError(ExternalServiceError):
    """Raised when email service fails."""
    
    def __init__(self, message: str = "Email service error"):
        super().__init__(message)


class RedisServiceError(ExternalServiceError):
    """Raised when Redis service fails."""
    
    def __init__(self, message: str = "Redis service error"):
        super().__init__(message)


# Exception Handlers
def create_http_exception(exc: BaseCustomException) -> HTTPException:
    """Convert custom exception to HTTPException."""
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "message": exc.message,
            "details": exc.details,
            "type": exc.__class__.__name__
        }
    )


def handle_database_error(error: Exception) -> BaseCustomException:
    """Handle SQLAlchemy database errors."""
    from sqlalchemy.exc import IntegrityError, OperationalError
    
    if isinstance(error, IntegrityError):
        if "duplicate key" in str(error).lower():
            return DuplicateResourceError("Resource already exists")
        elif "foreign key" in str(error).lower():
            return ValidationError("Referenced resource does not exist")
        else:
            return DatabaseIntegrityError("Database integrity constraint violation")
    
    elif isinstance(error, OperationalError):
        return DatabaseConnectionError("Database connection failed")
    
    else:
        return DatabaseError(f"Database error: {str(error)}")


def handle_validation_error(error: Exception) -> ValidationError:
    """Handle Pydantic validation errors."""
    from pydantic import ValidationError as PydanticValidationError
    
    if isinstance(error, PydanticValidationError):
        field_errors = {}
        for err in error.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            field_errors[field] = err["msg"]
        
        return ValidationError(
            "Validation failed",
            field_errors=field_errors
        )
    
    return ValidationError(str(error))


# Utility functions
def get_error_response(exc: BaseCustomException) -> Dict[str, Any]:
    """Get error response dictionary."""
    return {
        "error": True,
        "message": exc.message,
        "details": exc.details,
        "type": exc.__class__.__name__
    }


def is_client_error(status_code: int) -> bool:
    """Check if status code is a client error (4xx)."""
    return 400 <= status_code < 500


def is_server_error(status_code: int) -> bool:
    """Check if status code is a server error (5xx)."""
    return 500 <= status_code < 600