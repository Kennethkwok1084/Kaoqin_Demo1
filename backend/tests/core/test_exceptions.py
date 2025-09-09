"""
Comprehensive tests for exceptions.py - Custom exception handling and error response formatting
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, OperationalError
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import (
    # Base exceptions
    BaseCustomException,
    # Authentication exceptions
    AuthenticationError,
    AuthorizationError,
    InvalidTokenError,
    TokenExpiredError,
    InvalidCredentialsError,
    # Validation exceptions
    ValidationError,
    DuplicateResourceError,
    ResourceNotFoundError,
    # Business logic exceptions
    BusinessLogicError,
    TaskProcessingError,
    WorkHourCalculationError,
    AttendanceCalculationError,
    InvalidTaskStatusError,
    InvalidDateRangeError,
    # File processing exceptions
    FileProcessingError,
    InvalidFileFormatError,
    FileSizeExceededError,
    ExcelImportError,
    DataMatchingError,
    # Database exceptions
    DatabaseError,
    DatabaseConnectionError,
    DatabaseIntegrityError,
    # Rate limiting exceptions
    RateLimitExceededError,
    # Configuration exceptions
    ConfigurationError,
    MissingConfigurationError,
    # External service exceptions
    ExternalServiceError,
    EmailServiceError,
    RedisServiceError,
    # Permission exceptions
    PermissionDeniedError,
    # Data consistency exceptions
    DataConsistencyError,
    ServiceIntegrationError,
    # Concurrency exceptions
    ConcurrencyConflictError,
    ResourceLockError,
    # Bulk operation exceptions
    BulkOperationError,
    BatchSizeExceededError,
    # Performance exceptions
    PerformanceDegradationError,
    TimeoutError,
    OperationTimeoutError,
    # Utility functions
    create_http_exception,
    handle_database_error,
    handle_validation_error,
    get_error_response,
    is_client_error,
    is_server_error,
)


class TestBaseCustomException:
    """Test the base custom exception class"""

    def test_base_exception_with_message(self):
        """Test base exception with direct message"""
        exc = BaseCustomException(
            message="Test error", status_code=400, details={"key": "value"}
        )

        assert exc.message == "Test error"
        assert exc.status_code == 400
        assert exc.details == {"key": "value"}
        assert exc.message_key is None
        assert str(exc) == "Test error"

    def test_base_exception_with_message_key(self):
        """Test base exception with message key"""
        with patch("app.core.exceptions.get_message", return_value="Localized message"):
            exc = BaseCustomException(
                message_key="TEST_KEY", status_code=500, test_param="value"
            )

            assert exc.message == "Localized message"
            assert exc.message_key == "TEST_KEY"
            assert exc.status_code == 500

    def test_base_exception_defaults(self):
        """Test base exception with default values"""
        with patch("app.core.exceptions.Messages.GENERAL_ERROR", "General error"):
            exc = BaseCustomException()

            assert exc.message == "General error"
            assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert exc.details == {}
            assert exc.message_key is None

    def test_base_exception_message_priority(self):
        """Test that message_key takes priority over direct message"""
        with patch("app.core.exceptions.get_message", return_value="Key message"):
            exc = BaseCustomException(message="Direct message", message_key="TEST_KEY")

            assert exc.message == "Key message"


class TestAuthenticationExceptions:
    """Test authentication-related exceptions"""

    def test_authentication_error_defaults(self):
        """Test AuthenticationError with defaults"""
        with patch("app.core.exceptions.get_message", return_value="Auth error"):
            exc = AuthenticationError()

            assert exc.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc.message_key == "AUTH_ERROR_CREDENTIALS_VALIDATION"
            assert exc.message == "Auth error"

    def test_authentication_error_custom_message(self):
        """Test AuthenticationError with custom message"""
        exc = AuthenticationError(message="Custom auth error")

        assert exc.message == "Custom auth error"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authorization_error(self):
        """Test AuthorizationError"""
        with patch("app.core.exceptions.get_message", return_value="Admin required"):
            exc = AuthorizationError()

            assert exc.status_code == status.HTTP_403_FORBIDDEN
            assert exc.message_key == "AUTH_ERROR_ADMIN_REQUIRED"
            assert exc.message == "Admin required"

    def test_invalid_token_error(self):
        """Test InvalidTokenError"""
        with patch("app.core.exceptions.get_message", return_value="Invalid token"):
            exc = InvalidTokenError()

            assert exc.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc.message_key == "AUTH_ERROR_INVALID_TOKEN"
            assert exc.message == "Invalid token"
            assert isinstance(exc, AuthenticationError)

    def test_token_expired_error(self):
        """Test TokenExpiredError"""
        with patch("app.core.exceptions.get_message", return_value="Token expired"):
            exc = TokenExpiredError()

            assert exc.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc.message_key == "AUTH_ERROR_EXPIRED_TOKEN"
            assert exc.message == "Token expired"
            assert isinstance(exc, AuthenticationError)

    def test_invalid_credentials_error(self):
        """Test InvalidCredentialsError"""
        with patch(
            "app.core.exceptions.get_message", return_value="Invalid credentials"
        ):
            exc = InvalidCredentialsError()

            assert exc.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc.message_key == "AUTH_ERROR_INVALID_CREDENTIALS"
            assert exc.message == "Invalid credentials"
            assert isinstance(exc, AuthenticationError)


class TestValidationExceptions:
    """Test validation-related exceptions"""

    def test_validation_error_with_field_errors(self):
        """Test ValidationError with field errors"""
        field_errors = {"field1": "Error 1", "field2": "Error 2"}
        with patch("app.core.exceptions.get_message", return_value="Validation failed"):
            exc = ValidationError(field_errors=field_errors)

            assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert exc.details["field_errors"] == field_errors
            assert exc.message_key == "VALIDATION_ERROR_GENERAL"

    def test_validation_error_without_field_errors(self):
        """Test ValidationError without field errors"""
        with patch("app.core.exceptions.get_message", return_value="Validation failed"):
            exc = ValidationError(message="Custom validation error")

            assert exc.message == "Custom validation error"
            assert exc.details["field_errors"] == {}

    def test_duplicate_resource_error(self):
        """Test DuplicateResourceError"""
        with patch(
            "app.core.exceptions.get_message", return_value="Duplicate resource"
        ):
            exc = DuplicateResourceError()

            assert exc.status_code == status.HTTP_409_CONFLICT
            assert exc.message_key == "VALIDATION_ERROR_DUPLICATE_RESOURCE"

    def test_resource_not_found_error(self):
        """Test ResourceNotFoundError"""
        with patch(
            "app.core.exceptions.get_message", return_value="Resource not found"
        ):
            exc = ResourceNotFoundError()

            assert exc.status_code == status.HTTP_404_NOT_FOUND
            assert exc.message_key == "VALIDATION_ERROR_RESOURCE_NOT_FOUND"


class TestBusinessLogicExceptions:
    """Test business logic-related exceptions"""

    def test_business_logic_error(self):
        """Test BusinessLogicError"""
        with patch(
            "app.core.exceptions.get_message", return_value="Business logic error"
        ):
            exc = BusinessLogicError()

            assert exc.status_code == status.HTTP_400_BAD_REQUEST
            assert exc.message_key == "VALIDATION_ERROR_BUSINESS_LOGIC"

    def test_task_processing_error(self):
        """Test TaskProcessingError"""
        with patch(
            "app.core.exceptions.get_message", return_value="Task processing failed"
        ):
            exc = TaskProcessingError()

            assert exc.status_code == status.HTTP_400_BAD_REQUEST
            assert exc.message_key == "TASK_ERROR_PROCESSING_FAILED"
            assert isinstance(exc, BusinessLogicError)

    def test_work_hour_calculation_error(self):
        """Test WorkHourCalculationError"""
        with patch(
            "app.core.exceptions.get_message",
            return_value="Work hour calculation failed",
        ):
            exc = WorkHourCalculationError()

            assert exc.message_key == "ATTENDANCE_ERROR_WORK_HOURS_CALCULATION"
            assert isinstance(exc, BusinessLogicError)

    def test_attendance_calculation_error(self):
        """Test AttendanceCalculationError"""
        with patch(
            "app.core.exceptions.get_message",
            return_value="Attendance calculation failed",
        ):
            exc = AttendanceCalculationError()

            assert exc.message_key == "ATTENDANCE_ERROR_CALCULATION_FAILED"
            assert isinstance(exc, BusinessLogicError)

    def test_invalid_task_status_error(self):
        """Test InvalidTaskStatusError"""
        with patch(
            "app.core.exceptions.get_message", return_value="Invalid status transition"
        ):
            exc = InvalidTaskStatusError()

            assert exc.message_key == "VALIDATION_ERROR_INVALID_STATUS_TRANSITION"
            assert isinstance(exc, BusinessLogicError)

    def test_invalid_date_range_error(self):
        """Test InvalidDateRangeError"""
        with patch(
            "app.core.exceptions.get_message", return_value="Invalid date range"
        ):
            exc = InvalidDateRangeError()

            assert exc.message_key == "VALIDATION_ERROR_INVALID_DATE_RANGE"
            assert isinstance(exc, BusinessLogicError)


class TestFileProcessingExceptions:
    """Test file processing-related exceptions"""

    def test_file_processing_error(self):
        """Test FileProcessingError"""
        exc = FileProcessingError()

        assert exc.message == "File processing error"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_file_processing_error_custom_message(self):
        """Test FileProcessingError with custom message"""
        exc = FileProcessingError("Custom file error")

        assert exc.message == "Custom file error"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_file_format_error(self):
        """Test InvalidFileFormatError"""
        exc = InvalidFileFormatError()

        assert exc.message == "Invalid file format"
        assert isinstance(exc, FileProcessingError)

    def test_file_size_exceeded_error(self):
        """Test FileSizeExceededError"""
        exc = FileSizeExceededError()

        assert exc.message == "File size exceeds limit"
        assert isinstance(exc, FileProcessingError)

    def test_excel_import_error(self):
        """Test ExcelImportError"""
        exc = ExcelImportError()

        assert exc.message == "Excel import failed"
        assert isinstance(exc, FileProcessingError)

    def test_data_matching_error(self):
        """Test DataMatchingError"""
        exc = DataMatchingError()

        assert exc.message == "Data matching failed"
        assert isinstance(exc, FileProcessingError)


class TestDatabaseExceptions:
    """Test database-related exceptions"""

    def test_database_error(self):
        """Test DatabaseError"""
        exc = DatabaseError()

        assert exc.message == "Database error"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_database_connection_error(self):
        """Test DatabaseConnectionError"""
        exc = DatabaseConnectionError()

        assert exc.message == "Database connection failed"
        assert isinstance(exc, DatabaseError)

    def test_database_integrity_error(self):
        """Test DatabaseIntegrityError"""
        exc = DatabaseIntegrityError()

        assert exc.message == "Database integrity constraint violation"
        assert exc.status_code == status.HTTP_409_CONFLICT
        assert isinstance(exc, DatabaseError)


class TestOtherExceptions:
    """Test other exception categories"""

    def test_rate_limit_exceeded_error(self):
        """Test RateLimitExceededError"""
        exc = RateLimitExceededError()

        assert exc.message == "Rate limit exceeded"
        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_configuration_error(self):
        """Test ConfigurationError"""
        exc = ConfigurationError()

        assert exc.message == "Configuration error"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_missing_configuration_error(self):
        """Test MissingConfigurationError"""
        exc = MissingConfigurationError()

        assert exc.message == "Missing required configuration"
        assert isinstance(exc, ConfigurationError)

    def test_external_service_error(self):
        """Test ExternalServiceError"""
        exc = ExternalServiceError()

        assert exc.message == "External service error"
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY

    def test_email_service_error(self):
        """Test EmailServiceError"""
        exc = EmailServiceError()

        assert exc.message == "Email service error"
        assert isinstance(exc, ExternalServiceError)

    def test_redis_service_error(self):
        """Test RedisServiceError"""
        exc = RedisServiceError()

        assert exc.message == "Redis service error"
        assert isinstance(exc, ExternalServiceError)

    def test_permission_denied_error(self):
        """Test PermissionDeniedError"""
        with patch("app.core.exceptions.get_message", return_value="Permission denied"):
            exc = PermissionDeniedError()

            assert exc.status_code == status.HTTP_403_FORBIDDEN
            assert exc.message_key == "AUTH_ERROR_PERMISSION_DENIED"

    def test_data_consistency_error(self):
        """Test DataConsistencyError"""
        with patch("app.core.exceptions.get_message", return_value="Consistency error"):
            exc = DataConsistencyError()

            assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert exc.message_key == "DATA_ERROR_CONSISTENCY_CHECK"

    def test_service_integration_error(self):
        """Test ServiceIntegrationError"""
        with patch(
            "app.core.exceptions.get_message", return_value="Integration failed"
        ):
            exc = ServiceIntegrationError()

            assert exc.status_code == status.HTTP_502_BAD_GATEWAY
            assert exc.message_key == "SERVICE_ERROR_INTEGRATION_FAILED"


class TestConcurrencyExceptions:
    """Test concurrency-related exceptions"""

    def test_concurrency_conflict_error(self):
        """Test ConcurrencyConflictError"""
        with patch(
            "app.core.exceptions.get_message", return_value="Concurrency conflict"
        ):
            exc = ConcurrencyConflictError()

            assert exc.status_code == status.HTTP_409_CONFLICT
            assert exc.message_key == "CONCURRENCY_ERROR_CONFLICT"

    def test_resource_lock_error(self):
        """Test ResourceLockError"""
        with patch("app.core.exceptions.get_message", return_value="Lock failed"):
            exc = ResourceLockError()

            assert exc.status_code == status.HTTP_423_LOCKED
            assert exc.message_key == "RESOURCE_ERROR_LOCK_FAILED"


class TestBulkOperationExceptions:
    """Test bulk operation-related exceptions"""

    def test_bulk_operation_error(self):
        """Test BulkOperationError"""
        with patch(
            "app.core.exceptions.get_message", return_value="Bulk operation failed"
        ):
            exc = BulkOperationError()

            assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert exc.message_key == "BULK_ERROR_OPERATION_FAILED"

    def test_batch_size_exceeded_error(self):
        """Test BatchSizeExceededError"""
        with patch(
            "app.core.exceptions.get_message", return_value="Batch size exceeded"
        ):
            exc = BatchSizeExceededError()

            assert exc.message_key == "BULK_ERROR_BATCH_SIZE_EXCEEDED"
            assert isinstance(exc, BulkOperationError)


class TestPerformanceExceptions:
    """Test performance-related exceptions"""

    def test_performance_degradation_error(self):
        """Test PerformanceDegradationError"""
        with patch(
            "app.core.exceptions.get_message", return_value="Performance degraded"
        ):
            exc = PerformanceDegradationError()

            assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert exc.message_key == "PERFORMANCE_ERROR_DEGRADATION"

    def test_timeout_error(self):
        """Test TimeoutError"""
        with patch("app.core.exceptions.get_message", return_value="Operation timeout"):
            exc = TimeoutError()

            assert exc.status_code == status.HTTP_408_REQUEST_TIMEOUT
            assert exc.message_key == "OPERATION_ERROR_TIMEOUT"

    def test_operation_timeout_error(self):
        """Test OperationTimeoutError"""
        with patch("app.core.exceptions.get_message", return_value="Operation timeout"):
            exc = OperationTimeoutError()

            assert exc.status_code == status.HTTP_408_REQUEST_TIMEOUT
            assert exc.message_key == "OPERATION_ERROR_TIMEOUT"
            assert isinstance(exc, TimeoutError)


class TestExceptionHandlers:
    """Test exception handler functions"""

    def test_create_http_exception(self):
        """Test create_http_exception function"""
        custom_exc = BaseCustomException(
            message="Test error", status_code=400, details={"key": "value"}
        )

        http_exc = create_http_exception(custom_exc)

        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 400
        assert http_exc.detail["message"] == "Test error"
        assert http_exc.detail["details"] == {"key": "value"}
        assert http_exc.detail["type"] == "BaseCustomException"

    def test_handle_database_error_integrity_duplicate(self):
        """Test handle_database_error with duplicate key error"""
        mock_error = IntegrityError("duplicate key value", None, None)

        result = handle_database_error(mock_error)

        assert isinstance(result, DuplicateResourceError)
        assert result.message == "Resource already exists"

    def test_handle_database_error_integrity_foreign_key(self):
        """Test handle_database_error with foreign key error"""
        mock_error = IntegrityError("foreign key constraint", None, None)

        result = handle_database_error(mock_error)

        assert isinstance(result, ValidationError)
        assert result.message == "Referenced resource does not exist"

    def test_handle_database_error_integrity_other(self):
        """Test handle_database_error with other integrity error"""
        mock_error = IntegrityError("check constraint", None, None)

        result = handle_database_error(mock_error)

        assert isinstance(result, DatabaseIntegrityError)
        assert result.message == "Database integrity constraint violation"

    def test_handle_database_error_operational(self):
        """Test handle_database_error with operational error"""
        mock_error = OperationalError("connection failed", None, None)

        result = handle_database_error(mock_error)

        assert isinstance(result, DatabaseConnectionError)
        assert result.message == "Database connection failed"

    def test_handle_database_error_other(self):
        """Test handle_database_error with other error"""
        mock_error = Exception("generic database error")

        result = handle_database_error(mock_error)

        assert isinstance(result, DatabaseError)
        assert "generic database error" in result.message

    def test_handle_validation_error_pydantic(self):
        """Test handle_validation_error with PydanticValidationError"""
        # Create a mock PydanticValidationError
        mock_error = MagicMock(spec=PydanticValidationError)
        mock_error.errors.return_value = [
            {"loc": ("field1",), "msg": "Field is required"},
            {"loc": ("nested", "field2"), "msg": "Invalid value"},
        ]

        with patch(
            "app.core.exceptions.Messages.VALIDATION_ERROR_GENERAL", "Validation failed"
        ):
            result = handle_validation_error(mock_error)

            assert isinstance(result, ValidationError)
            assert result.message == "Validation failed"
            assert "field1" in result.details["field_errors"]
            assert "nested.field2" in result.details["field_errors"]

    def test_handle_validation_error_other(self):
        """Test handle_validation_error with other error"""
        mock_error = Exception("validation failed")

        result = handle_validation_error(mock_error)

        assert isinstance(result, ValidationError)
        assert result.message == "validation failed"


class TestUtilityFunctions:
    """Test utility functions"""

    def test_get_error_response(self):
        """Test get_error_response function"""
        exc = BaseCustomException(message="Test error", details={"key": "value"})

        response = get_error_response(exc)

        assert response["error"] is True
        assert response["message"] == "Test error"
        assert response["details"] == {"key": "value"}
        assert response["type"] == "BaseCustomException"

    def test_is_client_error(self):
        """Test is_client_error function"""
        assert is_client_error(400) is True
        assert is_client_error(404) is True
        assert is_client_error(499) is True
        assert is_client_error(500) is False
        assert is_client_error(399) is False

    def test_is_server_error(self):
        """Test is_server_error function"""
        assert is_server_error(500) is True
        assert is_server_error(503) is True
        assert is_server_error(599) is True
        assert is_server_error(400) is False
        assert is_server_error(499) is False


class TestExceptionInheritance:
    """Test exception inheritance hierarchy"""

    def test_authentication_exception_inheritance(self):
        """Test authentication exception inheritance"""
        exc = InvalidTokenError()

        assert isinstance(exc, InvalidTokenError)
        assert isinstance(exc, AuthenticationError)
        assert isinstance(exc, BaseCustomException)
        assert isinstance(exc, Exception)

    def test_business_logic_exception_inheritance(self):
        """Test business logic exception inheritance"""
        exc = TaskProcessingError()

        assert isinstance(exc, TaskProcessingError)
        assert isinstance(exc, BusinessLogicError)
        assert isinstance(exc, BaseCustomException)
        assert isinstance(exc, Exception)

    def test_file_processing_exception_inheritance(self):
        """Test file processing exception inheritance"""
        exc = ExcelImportError()

        assert isinstance(exc, ExcelImportError)
        assert isinstance(exc, FileProcessingError)
        assert isinstance(exc, BaseCustomException)
        assert isinstance(exc, Exception)

    def test_database_exception_inheritance(self):
        """Test database exception inheritance"""
        exc = DatabaseIntegrityError()

        assert isinstance(exc, DatabaseIntegrityError)
        assert isinstance(exc, DatabaseError)
        assert isinstance(exc, BaseCustomException)
        assert isinstance(exc, Exception)

    def test_external_service_exception_inheritance(self):
        """Test external service exception inheritance"""
        exc = EmailServiceError()

        assert isinstance(exc, EmailServiceError)
        assert isinstance(exc, ExternalServiceError)
        assert isinstance(exc, BaseCustomException)
        assert isinstance(exc, Exception)


class TestExceptionMessageHandling:
    """Test exception message handling with various scenarios"""

    def test_message_with_kwargs(self):
        """Test message handling with keyword arguments"""
        with patch("app.core.exceptions.get_message") as mock_get_message:
            mock_get_message.return_value = "User test_user not found"

            exc = ResourceNotFoundError(
                message_key="USER_NOT_FOUND", username="test_user"
            )

            mock_get_message.assert_called_once_with(
                "USER_NOT_FOUND", username="test_user"
            )
            assert exc.message == "User test_user not found"

    def test_details_parameter_handling(self):
        """Test details parameter handling in exceptions"""
        details = {"resource_id": 123, "operation": "delete"}
        exc = ResourceNotFoundError(details=details)

        assert exc.details == details

    def test_exception_with_none_details(self):
        """Test exception handling when details is None"""
        exc = BaseCustomException(message="Test", details=None)

        assert exc.details == {}


class TestExceptionEdgeCases:
    """Test edge cases and error scenarios"""

    def test_exception_with_empty_message(self):
        """Test exception with empty message"""
        with patch("app.core.exceptions.Messages.GENERAL_ERROR", "Default error"):
            exc = BaseCustomException(message="")

            assert exc.message == ""
            assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_exception_with_zero_status_code(self):
        """Test exception with invalid status code"""
        exc = BaseCustomException(message="Test", status_code=0)

        assert exc.status_code == 0  # Should accept any integer

    def test_nested_exception_handling(self):
        """Test nested exception scenarios"""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            custom_exc = BaseCustomException(
                message=f"Wrapped error: {str(e)}", details={"original_error": str(e)}
            )

            assert "Original error" in custom_exc.message
            assert custom_exc.details["original_error"] == "Original error"

    def test_exception_str_representation(self):
        """Test string representation of exceptions"""
        exc = ValidationError(
            message="Validation failed", field_errors={"field": "error"}
        )

        assert str(exc) == "Validation failed"
        assert repr(exc)  # Should not raise an error

    def test_exception_with_complex_details(self):
        """Test exception with complex details structure"""
        complex_details = {
            "errors": [
                {"field": "email", "message": "Invalid format"},
                {"field": "password", "message": "Too short"},
            ],
            "metadata": {"request_id": "12345", "timestamp": "2024-01-01T00:00:00Z"},
        }

        exc = ValidationError(details=complex_details)

        assert exc.details == complex_details
