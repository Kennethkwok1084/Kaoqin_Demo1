"""
FastAPI application entry point.
Main application factory and configuration.
"""

import logging
import logging.config
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import attendance, auth
from app.api.v1 import import_api as import_router
from app.api.v1 import members, statistics, tasks
from app.core.cache import cleanup_cache, init_cache
from app.core.config import get_cors_origins, get_log_config, settings
from app.core.database import check_database_health, close_database, init_database
from app.core.exceptions import BaseCustomException
from app.core.security import get_security_headers

# Configure logging
logging.config.dictConfig(get_log_config())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    logger.info("Starting up application...")

    # Skip all external connections in testing mode
    if settings.TESTING:
        logger.info("Running in testing mode - skipping external service connections")
    else:
        # Initialize database if in development mode
        if settings.DEBUG:
            await init_database()
            logger.info("Database initialized")

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


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="考勤管理系统 - Attendance Management System for University Network Maintenance Teams",
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)


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
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"],
    )


# Exception handlers
@app.exception_handler(BaseCustomException)
async def custom_exception_handler(
    request: Request, exc: BaseCustomException
) -> JSONResponse:
    """Handle custom exceptions."""
    logger.error(f"Custom exception: {exc.message}", exc_info=exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "details": exc.details,
            "type": exc.__class__.__name__,
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "details": {},
            "type": "HTTPException",
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")

    # Format validation errors
    errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body'
        errors[field] = error["msg"]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": "Validation failed",
            "details": {"field_errors": errors},
            "type": "ValidationError",
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=exc)

    if settings.DEBUG:
        # In debug mode, return detailed error info
        import traceback

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "message": str(exc),
                "details": {"traceback": traceback.format_exc()},
                "type": exc.__class__.__name__,
            },
        )
    else:
        # In production, return generic error
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "message": "Internal server error",
                "details": {},
                "type": "InternalServerError",
            },
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
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(attendance.router, prefix="/api/v1/attendance", tags=["Attendance"])
app.include_router(statistics.router, prefix="/api/v1/statistics", tags=["Statistics"])
app.include_router(import_router.router, prefix="/api/v1/import", tags=["Import"])


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
