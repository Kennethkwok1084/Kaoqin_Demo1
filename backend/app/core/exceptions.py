"""
统一异常处理类
提供不同业务场景的具体异常类型，使用统一消息管理
"""

from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from .messages import Messages, get_message


class BaseCustomException(Exception):
    """自定义异常基类"""

    def __init__(
        self,
        message: str = None,
        message_key: str = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        **message_kwargs
    ):
        # 优先使用message_key从统一消息库获取消息
        if message_key:
            self.message = get_message(message_key, **message_kwargs)
        elif message:
            self.message = message
        else:
            self.message = Messages.GENERAL_ERROR
            
        self.message_key = message_key
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


# 认证和授权相关异常
class AuthenticationError(BaseCustomException):
    """认证失败时抛出的异常"""

    def __init__(self, message: str = None, message_key: str = "AUTH_ERROR_CREDENTIALS_VALIDATION", **kwargs):
        super().__init__(message=message, message_key=message_key, status_code=status.HTTP_401_UNAUTHORIZED, **kwargs)


class AuthorizationError(BaseCustomException):
    """授权失败时抛出的异常"""

    def __init__(self, message: str = None, message_key: str = "AUTH_ERROR_ADMIN_REQUIRED", **kwargs):
        super().__init__(message=message, message_key=message_key, status_code=status.HTTP_403_FORBIDDEN, **kwargs)


class InvalidTokenError(AuthenticationError):
    """JWT令牌无效时抛出的异常"""

    def __init__(self, message: str = None, message_key: str = "AUTH_ERROR_INVALID_TOKEN", **kwargs):
        super().__init__(message=message, message_key=message_key, **kwargs)


class TokenExpiredError(AuthenticationError):
    """JWT令牌过期时抛出的异常"""

    def __init__(self, message: str = None, message_key: str = "AUTH_ERROR_EXPIRED_TOKEN", **kwargs):
        super().__init__(message=message, message_key=message_key, **kwargs)


class InvalidCredentialsError(AuthenticationError):
    """登录凭证无效时抛出的异常"""

    def __init__(self, message: str = None, message_key: str = "AUTH_ERROR_INVALID_CREDENTIALS", **kwargs):
        super().__init__(message=message, message_key=message_key, **kwargs)


# 数据验证相关异常
class ValidationError(BaseCustomException):
    """数据验证失败时抛出的异常"""

    def __init__(
        self,
        message: str = None,
        message_key: str = "VALIDATION_ERROR_GENERAL",
        field_errors: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            message_key=message_key,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field_errors": field_errors or {}},
            **kwargs
        )


class DuplicateResourceError(BaseCustomException):
    """尝试创建重复资源时抛出的异常"""

    def __init__(self, message: str = None, message_key: str = "VALIDATION_ERROR_DUPLICATE_RESOURCE", **kwargs):
        super().__init__(message=message, message_key=message_key, status_code=status.HTTP_409_CONFLICT, **kwargs)


class ResourceNotFoundError(BaseCustomException):
    """请求的资源不存在时抛出的异常"""

    def __init__(self, message: str = None, message_key: str = "VALIDATION_ERROR_RESOURCE_NOT_FOUND", **kwargs):
        super().__init__(message=message, message_key=message_key, status_code=status.HTTP_404_NOT_FOUND, **kwargs)


# 业务逻辑相关异常
class BusinessLogicError(BaseCustomException):
    """业务逻辑验证失败时抛出的异常"""

    def __init__(self, message: str = None, message_key: str = "VALIDATION_ERROR_BUSINESS_LOGIC", **kwargs):
        super().__init__(message=message, message_key=message_key, status_code=status.HTTP_400_BAD_REQUEST, **kwargs)


class TaskProcessingError(BusinessLogicError):
    """任务处理失败时抛出的异常"""

    def __init__(self, message: str = None, message_key: str = "TASK_ERROR_PROCESSING_FAILED", **kwargs):
        super().__init__(message=message, message_key=message_key, **kwargs)


class WorkHourCalculationError(BusinessLogicError):
    """工时计算失败时抛出的异常"""

    def __init__(self, message: str = None, message_key: str = "ATTENDANCE_ERROR_WORK_HOURS_CALCULATION", **kwargs):
        super().__init__(message=message, message_key=message_key, **kwargs)


class AttendanceCalculationError(BusinessLogicError):
    """考勤计算失败时抛出的异常"""

    def __init__(self, message: str = None, message_key: str = "ATTENDANCE_ERROR_CALCULATION_FAILED", **kwargs):
        super().__init__(message=message, message_key=message_key, **kwargs)


class InvalidTaskStatusError(BusinessLogicError):
    """无效任务状态转换时抛出的异常"""

    def __init__(self, message: str = None, message_key: str = "VALIDATION_ERROR_INVALID_STATUS_TRANSITION", **kwargs):
        super().__init__(message=message, message_key=message_key, **kwargs)


class InvalidDateRangeError(BusinessLogicError):
    """无效日期范围时抛出的异常"""

    def __init__(self, message: str = None, message_key: str = "VALIDATION_ERROR_INVALID_DATE_RANGE", **kwargs):
        super().__init__(message=message, message_key=message_key, **kwargs)


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
        super().__init__(message)
        self.status_code = status.HTTP_409_CONFLICT


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
            "type": exc.__class__.__name__,
        },
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

        return ValidationError("Validation failed", field_errors=field_errors)

    return ValidationError(str(error))


# Utility functions
def get_error_response(exc: BaseCustomException) -> Dict[str, Any]:
    """Get error response dictionary."""
    return {
        "error": True,
        "message": exc.message,
        "details": exc.details,
        "type": exc.__class__.__name__,
    }


def is_client_error(status_code: int) -> bool:
    """Check if status code is a client error (4xx)."""
    return 400 <= status_code < 500


def is_server_error(status_code: int) -> bool:
    """Check if status code is a server error (5xx)."""
    return 500 <= status_code < 600
