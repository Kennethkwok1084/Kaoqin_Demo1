"""FastAPI application entry point."""

import logging
import logging.config
import os
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from uuid import uuid4
from typing import Any, AsyncGenerator, Dict

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import attendance, auth, dashboard
from app.api.v1 import import_api as import_router
from app.api.v1 import campus_rooms, config_workhour, ops_stats, user_admin
from app.api.v1 import doc_compat
from app.api.v1 import assistance, coop, inspection_sampling, members, monitoring, repair, roles, statistics, system, system_config
from app.api.v1 import media, repair_orders, task_lifecycle
from app.api.deps import create_error_response
from app.core.cache import cleanup_cache, init_cache
from app.core.config import get_cors_origins, get_log_config, settings
from app.core.database import check_database_health, close_database, init_database
from app.core.exceptions import BaseCustomException
from app.core.request_context import get_request_id, reset_request_id, set_request_id
from app.core.startup import initialize_app
from app.core.openapi_config import (
    get_custom_openapi_schema,
    get_openapi_config,
    is_protected_path,
)
from app.core.security import get_security_headers
from app.core.runtime import APP_START_TIME

# Configure logging
logging.config.dictConfig(get_log_config())
logger = logging.getLogger(__name__)

# 应用启动时间在 app.core.runtime 中维护


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    logger.info("Starting up application...")

    # Skip all external connections in testing mode
    if settings.TESTING:
        logger.info("Running in testing mode - skipping external service connections")
        # Initialize minimal cache for testing
        await init_cache()
        logger.info("Cache initialized")
    else:
        # 执行应用程序初始化（包括数据库迁移和管理员用户创建）
        initialization_success = await initialize_app()
        if not initialization_success:
            logger.error("应用程序初始化失败，但继续启动...")

        # Initialize database if in development mode (deprecated in favor of startup logic)
        if settings.DEBUG and not initialization_success:
            await init_database()
            logger.info("Database initialized (fallback)")

        # Check database health
        db_healthy = await check_database_health()
        if not db_healthy:
            logger.error("Database health check failed!")
        else:
            logger.info("Database health check passed")

        # Initialize cache
        await init_cache()
        logger.info("Cache initialized")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    if not settings.TESTING:
        await cleanup_cache()
        await close_database()
    logger.info("Application shutdown complete")


# Get OpenAPI configuration
openapi_config = get_openapi_config()

# Create FastAPI application
app = FastAPI(
    **openapi_config,  # Use complete OpenAPI configuration
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",  # Always enable docs for development
    redoc_url="/redoc",  # Always enable redoc for development
    openapi_url="/openapi.json",
)


# Custom OpenAPI schema with enhanced security and response definitions
def custom_openapi() -> Dict[str, Any]:
    """Generate custom OpenAPI schema with enhanced configuration."""
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    # Generate base OpenAPI schema
    openapi_schema = get_openapi(
        title=openapi_config["title"],
        version=openapi_config["version"],
        description=openapi_config["description"],
        routes=app.routes,
        servers=openapi_config["servers"],
    )

    # Add custom enhancements
    custom_components = get_custom_openapi_schema()
    openapi_schema["components"].update(custom_components["components"])

    # Add security requirements to protected endpoints
    for path_key, path_obj in openapi_schema["paths"].items():
        for method_key, method_obj in path_obj.items():
            if method_key.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                # Add security requirement for protected paths
                if is_protected_path(path_key):
                    method_obj["security"] = [{"BearerAuth": []}]

                # Add common error responses
                if "responses" not in method_obj:
                    method_obj["responses"] = {}

                if is_protected_path(path_key):
                    method_obj["responses"]["401"] = {
                        "$ref": "#/components/responses/UnauthorizedError"
                    }
                    method_obj["responses"]["403"] = {
                        "$ref": "#/components/responses/ForbiddenError"
                    }

                if method_key.upper() in ["POST", "PUT", "PATCH"]:
                    method_obj["responses"]["422"] = {
                        "$ref": "#/components/responses/ValidationError"
                    }

    # Store and return enhanced schema
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Apply custom OpenAPI schema
app.openapi = custom_openapi  # type: ignore[method-assign]


@app.middleware("http")
async def add_request_id(request: Request, call_next: Any) -> Response:
    """Attach request_id to context and response headers for traceability."""
    incoming_request_id = request.headers.get("X-Request-ID")
    request_id = incoming_request_id or f"req_{uuid4().hex}"

    token = set_request_id(request_id)
    request.state.request_id = request_id
    try:
        response: Response = await call_next(request)
    finally:
        reset_request_id(token)

    response.headers["X-Request-ID"] = request_id
    return response


# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next: Any) -> Response:
    """Add security headers to all responses."""
    response: Response = await call_next(request)

    if settings.SECURITY_HEADERS_ENABLED:
        headers = get_security_headers()
        for header, value in headers.items():
            response.headers[header] = value

    return response


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add trusted host middleware for production
if not settings.DEBUG:
    trusted_hosts_env = os.getenv("TRUSTED_HOSTS", "")
    trusted_hosts = [x.strip() for x in trusted_hosts_env.split(",") if x.strip()]
    if not trusted_hosts:
        inferred_hosts: list[str] = []
        for origin in get_cors_origins():
            host = urlparse(origin).hostname
            if host:
                inferred_hosts.append(host)
        trusted_hosts = sorted(set(inferred_hosts))
    if not trusted_hosts:
        trusted_hosts = ["localhost", "127.0.0.1"]

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=trusted_hosts,
    )


# Exception handlers
@app.exception_handler(BaseCustomException)
async def custom_exception_handler(
    request: Request, exc: BaseCustomException
) -> JSONResponse:
    """Handle custom exceptions."""
    logger.error(f"[{get_request_id()}] Custom exception: {exc.message}", exc_info=exc)
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
            error_code=exc.__class__.__name__,
        ),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(f"[{get_request_id()}] HTTP exception: {exc.status_code} - {exc.detail}")
    message = exc.detail if isinstance(exc.detail, str) else "HTTP request failed"
    details = exc.detail if isinstance(exc.detail, dict) else {}
    error_code = "HTTP_ERROR"

    if isinstance(exc.detail, dict):
        detail_dict = exc.detail
        message = str(detail_dict.get("message", "HTTP request failed"))
        error_code = str(detail_dict.get("error_code", "HTTP_ERROR"))
        details = {
            key: value
            for key, value in detail_dict.items()
            if key not in {"message", "error_code"}
        }

    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            message=message,
            status_code=exc.status_code,
            details=details,
            error_code=error_code,
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    logger.warning(f"[{get_request_id()}] Validation error: {exc.errors()}")

    # Format validation errors and keep both structured details and a
    # backward-compatible field map for existing clients.
    error_items = []
    field_errors: Dict[str, str] = {}
    for error in exc.errors():
        loc = [str(loc) for loc in error.get("loc", ())]
        field_loc = loc[1:] if loc and loc[0] in {"body", "query", "path"} else loc
        field = ".".join(field_loc)
        message = error.get("msg", "数据校验失败")

        error_items.append(
            {
                "field": field or None,
                "loc": loc,
                "message": message,
                "msg": message,
                "code": "INVALID_PARAMETER",
            }
        )
        if field:
            field_errors[field] = message

    response_content = create_error_response(
        message="提交数据校验失败",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="ValidationError",
        errors=error_items,
        details={"field_errors": field_errors},
    )
    # Backward compatibility for tests/clients still reading legacy "detail" key.
    response_content["detail"] = [
        {"loc": item["loc"], "msg": item["msg"]} for item in error_items
    ]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_content,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with enhanced error categorization."""
    import traceback

    from sqlalchemy.exc import SQLAlchemyError

    # Log the error with full context
    logger.error(
        f"[{get_request_id()}] Unexpected error in {request.method} {request.url}: {str(exc)}",
        exc_info=exc,
    )

    # Enhanced error categorization for better debugging
    error_context = {
        "path": str(request.url),
        "method": request.method,
        "exception_type": exc.__class__.__name__,
        "exception_module": exc.__class__.__module__,
    }

    # Handle specific exception types
    if isinstance(exc, SQLAlchemyError):
        # Database-related errors
        logger.error(f"Database error: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=create_error_response(
                message=(
                    "Database service temporarily unavailable"
                    if not settings.DEBUG
                    else str(exc)
                ),
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                details=(
                    error_context if settings.DEBUG else {"error_type": "database"}
                ),
                error_code="DatabaseError",
            ),
        )
    elif "Event loop is closed" in str(exc) or "RuntimeError" in str(exc):
        # Event loop / async context errors (common in tests/CI)
        logger.error(f"Event loop error: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=create_error_response(
                message="Async operation failed" if not settings.DEBUG else str(exc),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details=error_context if settings.DEBUG else {"error_type": "async"},
                error_code="AsyncError",
            ),
        )
    elif "connection" in str(exc).lower() or "timeout" in str(exc).lower():
        # Connection/timeout related errors
        logger.error(f"Connection error: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=create_error_response(
                message=(
                    "Service temporarily unavailable"
                    if not settings.DEBUG
                    else str(exc)
                ),
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                details=(
                    error_context if settings.DEBUG else {"error_type": "connection"}
                ),
                error_code="ConnectionError",
            ),
        )

    # Generic exception handling
    if settings.DEBUG or settings.TESTING:
        # In debug/testing mode, return detailed error info
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=create_error_response(
                message=str(exc),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details={
                    **error_context,
                    "traceback": traceback.format_exc().split("\n")[-20:],
                },
                error_code=exc.__class__.__name__,
            ),
        )
    else:
        # In production, return generic error
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=create_error_response(
                message="Internal server error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details={"error_id": hash(str(exc)) % 1000000},
                error_code="InternalServerError",
            ),
        )


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    db_healthy = await check_database_health()

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "version": settings.APP_VERSION,
        "database": "connected" if db_healthy else "disconnected",
        "debug": settings.DEBUG,
    }


@app.get("/api/health", tags=["Health"])
async def api_health_check() -> Dict[str, Any]:
    """API health check endpoint."""
    db_healthy = await check_database_health()

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "api_version": "v1",
        "database": "connected" if db_healthy else "disconnected",
        "endpoints": "operational",
    }


@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """Root endpoint."""
    return {
        "message": "欢迎使用考勤管理系统 API",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "disabled",
        "health": "/health",
    }


# Include API routers

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(members.router, prefix="/api/v1/members", tags=["Members"])
app.include_router(repair.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(monitoring.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(assistance.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(coop.router, prefix="/api/v1", tags=["Coop Workflows"])
app.include_router(inspection_sampling.router, prefix="/api/v1", tags=["Inspection Sampling Workflows"])
app.include_router(task_lifecycle.router, prefix="/api/v1", tags=["Task Lifecycle"])
app.include_router(repair_orders.router, prefix="/api/v1", tags=["Repair Orders"])
app.include_router(media.router, prefix="/api/v1", tags=["Media"])
app.include_router(user_admin.router, prefix="/api/v1", tags=["User Admin"])
app.include_router(config_workhour.router, prefix="/api/v1", tags=["Config Workhour"])
app.include_router(campus_rooms.router, prefix="/api/v1", tags=["Campus Rooms"])
app.include_router(ops_stats.router, prefix="/api/v1", tags=["Ops Stats"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(attendance.router, prefix="/api/v1/attendance", tags=["Attendance"])
app.include_router(statistics.router, prefix="/api/v1/statistics", tags=["Statistics"])
app.include_router(import_router.router, prefix="/api/v1/import", tags=["Import"])
app.include_router(doc_compat.router, prefix="/api/v1", tags=["Doc Compatibility"])
app.include_router(
    system_config.router, prefix="/api/v1/system-config", tags=["System Config"]
)
app.include_router(system.router, prefix="/api/v1/system", tags=["System Settings"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["Roles & Permissions"])


# Development utilities
if settings.DEBUG:

    @app.get("/debug/config", tags=["Debug"])
    async def debug_config() -> Dict[str, Any]:
        """Debug endpoint to view configuration (development only)."""
        return {
            "app_name": settings.APP_NAME,
            "debug": settings.DEBUG,
            "database_url": (
                settings.DATABASE_URL.replace(
                    settings.DATABASE_URL.split("@")[0].split(":")[-1], "***"
                )
                if "@" in settings.DATABASE_URL
                else "***"
            ),
            "cors_origins": get_cors_origins(),
            "log_level": settings.LOG_LEVEL,
        }

    @app.get("/debug/db-tables", tags=["Debug"])
    async def debug_db_tables() -> Dict[str, Any]:
        """Debug endpoint to view database tables (development only)."""
        from app.core.database import get_table_names

        return {"tables": get_table_names()}


# Application factory function
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    return app


# Run function for development
def run() -> None:
    """Run the application with uvicorn (development only)."""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    run()
