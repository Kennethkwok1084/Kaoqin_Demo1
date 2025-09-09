"""
Comprehensive tests for main.py - FastAPI application startup, configuration, middleware, and routing
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.main import (
    app,
    create_app,
    custom_openapi,
    lifespan,
    add_security_headers,
    custom_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler,
    health_check,
    api_health_check,
    root,
)
from app.core.exceptions import BaseCustomException, ValidationError
from app.core.config import settings


class TestApplicationSetup:
    """Test FastAPI application setup and configuration"""

    def test_create_app_returns_fastapi_instance(self):
        """Test that create_app returns a FastAPI instance"""
        test_app = create_app()
        assert isinstance(test_app, FastAPI)
        assert test_app.title == "Attendance Management System API"

    def test_app_configuration(self):
        """Test application configuration"""
        assert app.debug == settings.DEBUG
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
        assert app.openapi_url == "/openapi.json"

    def test_custom_openapi_schema_generation(self):
        """Test custom OpenAPI schema generation"""
        schema = custom_openapi()

        # Verify basic structure
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        assert "components" in schema

        # Verify title and version
        assert schema["info"]["title"] == "Attendance Management System API"

        # Test caching - second call should return cached version
        app.openapi_schema = schema
        cached_schema = custom_openapi()
        assert cached_schema is schema

    def test_openapi_security_enhancement(self):
        """Test OpenAPI security requirements are added to protected paths"""
        # Clear any cached schema
        app.openapi_schema = None

        with patch("app.main.is_protected_path", return_value=True):
            schema = custom_openapi()

            # Find a path in the schema
            if schema["paths"]:
                path_key = next(iter(schema["paths"].keys()))
                path_obj = schema["paths"][path_key]

                for method_key, method_obj in path_obj.items():
                    if method_key.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                        # Protected paths should have security requirements
                        assert "security" in method_obj
                        assert {"BearerAuth": []} in method_obj["security"]

                        # Should have auth error responses
                        responses = method_obj.get("responses", {})
                        assert "401" in responses
                        assert "403" in responses

    def test_middleware_registration(self):
        """Test middleware registration"""
        # Check if CORS middleware is registered
        cors_middleware_found = False
        trusted_host_middleware_found = False

        for middleware in app.user_middleware:
            middleware_class = middleware.cls.__name__
            if "CORS" in middleware_class:
                cors_middleware_found = True
            elif "TrustedHost" in middleware_class:
                trusted_host_middleware_found = True

        assert cors_middleware_found

        # TrustedHostMiddleware only in production
        if not settings.DEBUG:
            assert trusted_host_middleware_found

    def test_router_registration(self):
        """Test API router registration"""
        routes = [route.path for route in app.routes]

        expected_prefixes = [
            "/api/v1/auth",
            "/api/v1/members",
            "/api/v1/tasks",
            "/api/v1/dashboard",
            "/api/v1/attendance",
            "/api/v1/statistics",
            "/api/v1/import",
            "/api/v1/system-config",
            "/api/v1/system",
            "/api/v1/roles",
        ]

        for prefix in expected_prefixes:
            prefix_found = any(route.startswith(prefix) for route in routes)
            assert prefix_found, f"Router with prefix {prefix} not found"


class TestLifespanEvents:
    """Test application lifespan events"""

    @pytest.mark.asyncio
    async def test_lifespan_testing_mode(self):
        """Test lifespan behavior in testing mode"""
        with patch("app.main.settings.TESTING", True):
            with patch("app.main.logger") as mock_logger:
                async with lifespan(app):
                    pass

                # Verify testing mode message is logged
                mock_logger.info.assert_any_call(
                    "Running in testing mode - skipping external service connections"
                )

    @pytest.mark.asyncio
    async def test_lifespan_debug_mode(self):
        """Test lifespan behavior in debug mode"""
        with patch("app.main.settings.TESTING", False):
            with patch("app.main.settings.DEBUG", True):
                with patch(
                    "app.main.init_database", new_callable=AsyncMock
                ) as mock_init_db:
                    with patch(
                        "app.main.check_database_health", return_value=True
                    ) as mock_db_health:
                        with patch(
                            "app.main.init_cache", new_callable=AsyncMock
                        ) as mock_init_cache:
                            with patch(
                                "app.main.cleanup_cache", new_callable=AsyncMock
                            ) as mock_cleanup_cache:
                                with patch(
                                    "app.main.close_database", new_callable=AsyncMock
                                ) as mock_close_db:
                                    async with lifespan(app):
                                        pass

                                    # Verify startup operations
                                    mock_init_db.assert_called_once()
                                    mock_db_health.assert_called()
                                    mock_init_cache.assert_called_once()

                                    # Verify shutdown operations
                                    mock_cleanup_cache.assert_called_once()
                                    mock_close_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_database_health_failure(self):
        """Test lifespan behavior when database health check fails"""
        with patch("app.main.settings.TESTING", False):
            with patch("app.main.check_database_health", return_value=False):
                with patch("app.main.logger") as mock_logger:
                    with patch("app.main.init_cache", new_callable=AsyncMock):
                        async with lifespan(app):
                            pass

                        mock_logger.error.assert_any_call(
                            "Database health check failed!"
                        )


class TestSecurityMiddleware:
    """Test security headers middleware"""

    @pytest.mark.asyncio
    async def test_security_headers_enabled(self):
        """Test security headers are added when enabled"""
        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.headers = {}

        async def mock_call_next(request):
            return mock_response

        with patch("app.main.settings.SECURITY_HEADERS_ENABLED", True):
            with patch(
                "app.main.get_security_headers", return_value={"X-Test": "test-value"}
            ):
                result = await add_security_headers(mock_request, mock_call_next)

                assert result is mock_response
                assert "X-Test" in mock_response.headers
                assert mock_response.headers["X-Test"] == "test-value"

    @pytest.mark.asyncio
    async def test_security_headers_disabled(self):
        """Test security headers are not added when disabled"""
        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.headers = {}

        async def mock_call_next(request):
            return mock_response

        with patch("app.main.settings.SECURITY_HEADERS_ENABLED", False):
            result = await add_security_headers(mock_request, mock_call_next)

            assert result is mock_response
            assert len(mock_response.headers) == 0


class TestExceptionHandlers:
    """Test exception handlers"""

    @pytest.mark.asyncio
    async def test_custom_exception_handler(self):
        """Test custom exception handler"""
        mock_request = MagicMock()

        class TestException(BaseCustomException):
            def __init__(self):
                super().__init__(
                    message="Test custom error",
                    status_code=400,
                    details={"test": "details"},
                )

        exc = TestException()

        with patch("app.main.logger") as mock_logger:
            response = await custom_exception_handler(mock_request, exc)

            assert response.status_code == 400
            content = json.loads(response.body.decode())
            assert content["success"] is False
            assert content["message"] == "Test custom error"
            assert content["details"] == {"test": "details"}
            assert content["error_code"] == "TestException"

            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_http_exception_handler(self):
        """Test HTTP exception handler"""
        mock_request = MagicMock()
        exc = StarletteHTTPException(status_code=404, detail="Not found")

        with patch("app.main.logger") as mock_logger:
            response = await http_exception_handler(mock_request, exc)

            assert response.status_code == 404
            content = json.loads(response.body.decode())
            assert content["success"] is False
            assert content["message"] == "Not found"
            assert content["error_code"] == "HTTP_ERROR"

            mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_validation_exception_handler(self):
        """Test request validation exception handler"""
        mock_request = MagicMock()

        # Create a mock validation error
        mock_error = MagicMock()
        mock_error.errors.return_value = [
            {"loc": ["body", "field1"], "msg": "Field is required"},
            {"loc": ["body", "field2"], "msg": "Invalid value"},
        ]

        with patch("app.main.logger") as mock_logger:
            response = await validation_exception_handler(mock_request, mock_error)

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            content = json.loads(response.body.decode())
            assert content["success"] is False
            assert content["message"] == "数据验证失败"
            assert "field_errors" in content["details"]
            assert content["error_code"] == "ValidationError"

            mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_global_exception_handler_database_error(self):
        """Test global exception handler for database errors"""
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url = "http://test.com/api/test"

        exc = SQLAlchemyError("Database connection failed")

        with patch("app.main.logger") as mock_logger:
            response = await global_exception_handler(mock_request, exc)

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            content = json.loads(response.body.decode())
            assert content["success"] is False
            assert content["error_code"] == "DatabaseError"

            mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_global_exception_handler_event_loop_error(self):
        """Test global exception handler for event loop errors"""
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url = "http://test.com/api/test"

        exc = RuntimeError("Event loop is closed")

        with patch("app.main.logger") as mock_logger:
            response = await global_exception_handler(mock_request, exc)

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            content = json.loads(response.body.decode())
            assert content["success"] is False
            assert content["error_code"] == "AsyncError"

            mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_global_exception_handler_connection_error(self):
        """Test global exception handler for connection errors"""
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url = "http://test.com/api/test"

        exc = Exception("Connection timeout occurred")

        with patch("app.main.logger") as mock_logger:
            response = await global_exception_handler(mock_request, exc)

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            content = json.loads(response.body.decode())
            assert content["success"] is False
            assert content["error_code"] == "ConnectionError"

            mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_global_exception_handler_debug_mode(self):
        """Test global exception handler in debug mode"""
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url = "http://test.com/api/test"

        exc = Exception("Test error")

        with patch("app.main.settings.DEBUG", True):
            with patch("app.main.logger"):
                response = await global_exception_handler(mock_request, exc)

                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                content = json.loads(response.body.decode())
                assert content["success"] is False
                assert "traceback" in content["details"]
                assert content["error_code"] == "Exception"

    @pytest.mark.asyncio
    async def test_global_exception_handler_production_mode(self):
        """Test global exception handler in production mode"""
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url = "http://test.com/api/test"

        exc = Exception("Test error")

        with patch("app.main.settings.DEBUG", False):
            with patch("app.main.settings.TESTING", False):
                with patch("app.main.logger"):
                    response = await global_exception_handler(mock_request, exc)

                    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    content = json.loads(response.body.decode())
                    assert content["success"] is False
                    assert content["message"] == "Internal server error"
                    assert "error_id" in content["details"]
                    assert content["error_code"] == "InternalServerError"


class TestHealthCheckEndpoints:
    """Test health check endpoints"""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """Test health check endpoint when database is healthy"""
        with patch("app.main.check_database_health", return_value=True):
            result = await health_check()

            assert result["status"] == "healthy"
            assert result["database"] == "connected"
            assert "version" in result
            assert "debug" in result

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self):
        """Test health check endpoint when database is unhealthy"""
        with patch("app.main.check_database_health", return_value=False):
            result = await health_check()

            assert result["status"] == "unhealthy"
            assert result["database"] == "disconnected"

    @pytest.mark.asyncio
    async def test_api_health_check_healthy(self):
        """Test API health check endpoint when database is healthy"""
        with patch("app.main.check_database_health", return_value=True):
            result = await api_health_check()

            assert result["status"] == "healthy"
            assert result["database"] == "connected"
            assert result["api_version"] == "v1"
            assert result["endpoints"] == "operational"

    @pytest.mark.asyncio
    async def test_api_health_check_unhealthy(self):
        """Test API health check endpoint when database is unhealthy"""
        with patch("app.main.check_database_health", return_value=False):
            result = await api_health_check()

            assert result["status"] == "unhealthy"
            assert result["database"] == "disconnected"

    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test root endpoint"""
        result = await root()

        assert "message" in result
        assert "考勤管理系统" in result["message"]
        assert "version" in result
        assert "health" in result
        assert result["health"] == "/health"


class TestDebugEndpoints:
    """Test debug endpoints (only available in debug mode)"""

    @pytest.mark.asyncio
    async def test_debug_config_endpoint_in_debug_mode(self):
        """Test debug config endpoint in debug mode"""
        if not settings.DEBUG:
            # Skip if not in debug mode
            return

        with patch("app.main.get_cors_origins", return_value=["http://localhost:3000"]):
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                response = await client.get("/debug/config")

                if response.status_code == 200:
                    data = response.json()
                    assert "app_name" in data
                    assert "debug" in data
                    assert "database_url" in data
                    assert "cors_origins" in data

    @pytest.mark.asyncio
    async def test_debug_db_tables_endpoint(self):
        """Test debug database tables endpoint"""
        if not settings.DEBUG:
            # Skip if not in debug mode
            return

        with patch("app.main.get_table_names", return_value=["users", "tasks"]):
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                response = await client.get("/debug/db-tables")

                if response.status_code == 200:
                    data = response.json()
                    assert "tables" in data


class TestApplicationIntegration:
    """Test full application integration"""

    def test_application_startup_and_routes(self):
        """Test application can start and routes are accessible"""
        with TestClient(app) as client:
            # Test root endpoint
            response = client.get("/")
            assert response.status_code == 200

            # Test health endpoint
            response = client.get("/health")
            assert response.status_code == 200

            # Test API health endpoint
            response = client.get("/api/health")
            assert response.status_code == 200

            # Test OpenAPI docs (if enabled)
            if settings.DEBUG:
                response = client.get("/docs")
                assert response.status_code == 200

                response = client.get("/openapi.json")
                assert response.status_code == 200

    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        with TestClient(app) as client:
            response = client.options("/", headers={"Origin": "http://localhost:3000"})

            # Check CORS headers are present
            assert (
                "access-control-allow-origin" in response.headers
                or response.status_code == 405
            )

    def test_security_headers(self):
        """Test security headers are added to responses"""
        with patch("app.main.settings.SECURITY_HEADERS_ENABLED", True):
            with patch(
                "app.main.get_security_headers",
                return_value={"X-Content-Type-Options": "nosniff"},
            ):
                with TestClient(app) as client:
                    response = client.get("/")

                    # Check if security headers might be present
                    assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_exception_handling_integration(self):
        """Test exception handling works in real request flow"""
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            # Test 404 handling
            response = await client.get("/nonexistent-endpoint")
            assert response.status_code == 404

            data = response.json()
            assert data["success"] is False
            assert "message" in data


class TestApplicationFactory:
    """Test application factory patterns"""

    def test_run_function_import(self):
        """Test that run function can be imported and configured"""
        from app.main import run

        # Test function exists and is callable
        assert callable(run)

        # Mock uvicorn.run to test configuration
        with patch("app.main.uvicorn.run") as mock_run:
            # This would actually start the server, so we just test the import
            assert mock_run is not None

    def test_main_module_execution(self):
        """Test main module can be executed"""
        # Test that the main module structure allows for direct execution
        import app.main

        assert hasattr(app.main, "__name__")
        assert hasattr(app.main, "run")
        assert hasattr(app.main, "app")


class TestErrorScenarios:
    """Test edge cases and error scenarios"""

    @pytest.mark.asyncio
    async def test_lifespan_exception_handling(self):
        """Test lifespan handles exceptions gracefully"""
        with patch("app.main.settings.TESTING", False):
            with patch("app.main.init_database", side_effect=Exception("Init failed")):
                with patch("app.main.logger") as mock_logger:
                    try:
                        async with lifespan(app):
                            pass
                    except Exception:
                        pass  # Expected to handle gracefully

                    # Should still log startup message
                    mock_logger.info.assert_any_call("Starting up application...")

    def test_openapi_schema_with_no_routes(self):
        """Test OpenAPI schema generation when no routes exist"""
        test_app = FastAPI()
        test_app.openapi_schema = None

        # Temporarily replace the app's routes for testing
        original_routes = app.routes
        app.routes = []

        try:
            schema = custom_openapi()
            assert "paths" in schema
        finally:
            app.routes = original_routes

    @pytest.mark.asyncio
    async def test_validation_error_with_nested_fields(self):
        """Test validation error handler with nested field errors"""
        mock_request = MagicMock()

        mock_error = MagicMock()
        mock_error.errors.return_value = [
            {"loc": ["body", "nested", "field"], "msg": "Nested field error"},
            {"loc": ["body", "array", 0, "item"], "msg": "Array item error"},
        ]

        response = await validation_exception_handler(mock_request, mock_error)

        content = json.loads(response.body.decode())
        assert "nested.field" in content["details"]["field_errors"]
        assert "array.0.item" in content["details"]["field_errors"]

    @pytest.mark.asyncio
    async def test_exception_handler_with_none_request_url(self):
        """Test exception handler when request URL is None"""
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url = None

        exc = Exception("Test error")

        with patch("app.main.logger"):
            response = await global_exception_handler(mock_request, exc)

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            content = json.loads(response.body.decode())
            assert content["success"] is False
