"""
Database configuration and connection management.
Handles SQLAlchemy async and sync database connections.
OPTIMIZED VERSION FOR CI/CD PERFORMANCE
"""

import logging
import os
import time
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional

from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_database_url, get_database_url_sync, settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base Model
Base = declarative_base()

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
Base.metadata = MetaData(naming_convention=convention)


def _is_ci_environment() -> bool:
    """Check if running in CI/CD environment."""
    return os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"


def _is_testing_environment() -> bool:
    """Check if running in testing environment."""
    return os.getenv("TESTING") == "true" or settings.TESTING


def _get_optimized_pool_config() -> Dict[str, Any]:
    """Get optimized pool configuration based on environment."""
    if _is_ci_environment():
        # CI environment: lightweight, fast connections
        return {
            "pool_size": 2,  # Reduced pool size for CI resources
            "max_overflow": 3,  # Limited overflow for CI
            "pool_recycle": 300,  # 5 minutes - frequent recycle in CI
            "pool_timeout": 10,  # Fast timeout for CI
            "pool_pre_ping": True,
        }
    elif _is_testing_environment():
        # Testing environment: minimal overhead
        return {
            "pool_size": 1,
            "max_overflow": 2,
            "pool_recycle": 600,  # 10 minutes
            "pool_timeout": 5,
            "pool_pre_ping": True,
        }
    else:
        # Production environment: robust configuration
        return {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_recycle": 1800,  # 30 minutes
            "pool_timeout": 30,
            "pool_pre_ping": True,
        }


def _get_optimized_connect_args() -> Dict[str, Any]:
    """Get optimized connection arguments based on environment."""
    base_args: Dict[str, Any] = {
        "server_settings": {
            "application_name": f"kaoqin_backend_{os.getenv('ENVIRONMENT', 'dev')}",
        },
    }

    if _is_ci_environment():
        # CI environment: aggressive timeouts (using only valid asyncpg parameters)
        base_args.update(
            {
                "command_timeout": 30,  # 30 seconds for CI
            }
        )
    elif _is_testing_environment():
        # Testing environment: moderate timeouts
        base_args.update(
            {
                "command_timeout": 60,  # 1 minute for tests
            }
        )
    else:
        # Production environment: generous timeouts
        base_args.update(
            {
                "command_timeout": 300,  # 5 minutes for large data operations
            }
        )

    return base_args


# Async Database Engine
def _get_async_engine_args() -> Dict[str, Any]:
    """Get engine arguments based on database type and environment."""
    db_url = get_database_url()

    # Base arguments for all environments
    base_args = {
        "echo": settings.DEBUG and not _is_ci_environment(),  # Disable echo in CI
        "future": True,
        "pool_pre_ping": True,
        "execution_options": {"compiled_cache": {}},
    }

    if "sqlite" in db_url:
        # SQLite-specific configuration
        from sqlalchemy.pool import StaticPool

        base_args.update(
            {
                "poolclass": StaticPool,
                "connect_args": {"check_same_thread": False},
            }
        )
    else:
        # PostgreSQL-specific configuration with optimizations
        pool_config = _get_optimized_pool_config()
        connect_args = _get_optimized_connect_args()

        base_args.update(
            {
                **pool_config,
                "connect_args": connect_args,
            }
        )

    return base_args


async_engine = create_async_engine(get_database_url(), **_get_async_engine_args())

# Async Session Factory with optimized settings
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Sync Database Engine (for Alembic migrations)
def _get_sync_engine_args() -> Dict[str, Any]:
    """Get sync engine arguments based on database type and environment."""
    db_url = get_database_url_sync()

    base_args: Dict[str, Any] = {
        "echo": settings.DEBUG and not _is_ci_environment(),  # Disable echo in CI
        "future": True,
        "pool_pre_ping": True,
    }

    if "sqlite" in db_url:
        # SQLite-specific configuration
        from sqlalchemy.pool import StaticPool

        base_args.update(
            {
                "poolclass": StaticPool,
                "connect_args": {"check_same_thread": False},
            }
        )
    else:
        # PostgreSQL-specific configuration with optimizations
        pool_config = _get_optimized_pool_config()

        # Remove async-specific options for sync engine
        sync_pool_config = {
            k: v for k, v in pool_config.items() if k != "pool_pre_ping"
        }
        base_args.update(sync_pool_config)

    return base_args


sync_engine = create_engine(get_database_url_sync(), **_get_sync_engine_args())

# Sync Session Factory
SessionLocal = sessionmaker(
    sync_engine,
    autocommit=False,
    autoflush=False,
)


# Async Database Dependency with improved error handling
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create async database session.
    Used as a dependency in FastAPI endpoints.
    Optimized for CI/CD environments.
    """
    session = None
    try:
        session = AsyncSessionLocal()
        yield session
    except Exception as e:
        if session:
            try:
                await session.rollback()
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")
        logger.error(f"Database session error: {e}")
        raise
    finally:
        if session:
            try:
                await session.close()
            except Exception as close_error:
                logger.error(f"Session close failed: {close_error}")


# Sync Database Dependency with improved error handling
def get_sync_session() -> Generator[Session, None, None]:
    """
    Create sync database session.
    Used for migrations and sync operations.
    Optimized for CI/CD environments.
    """
    session = None
    try:
        session = SessionLocal()
        yield session
    except Exception as e:
        if session:
            try:
                session.rollback()
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")
        logger.error(f"Sync database session error: {e}")
        raise
    finally:
        if session:
            try:
                session.close()
            except Exception as close_error:
                logger.error(f"Session close failed: {close_error}")


# Database Health Check with timeout
async def check_database_health(timeout_seconds: int = 5) -> bool:
    """
    Check if database connection is healthy.
    Used in health check endpoints.
    Optimized with configurable timeout.
    """
    import asyncio

    from sqlalchemy import text

    try:
        # Create a new session for health check
        async with AsyncSessionLocal() as session:
            # Use asyncio.wait_for to enforce timeout
            await asyncio.wait_for(
                session.execute(text("SELECT 1")), timeout=timeout_seconds
            )
            return True
    except asyncio.TimeoutError:
        logger.error(f"Database health check timed out after {timeout_seconds}s")
        return False
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# Database Initialization
async def init_database() -> None:
    """
    Initialize database tables.
    Only use in development or testing.
    """
    logger.warning("init_database is deprecated; use Alembic migrations instead")


# Database Cleanup with improved error handling
async def close_database() -> None:
    """
    Close database connections.
    Used during application shutdown.
    Optimized for CI/CD environments.
    """
    try:
        await async_engine.dispose()
        logger.info("Async database engine disposed")
    except Exception as e:
        logger.error(f"Error disposing async engine: {e}")

    try:
        sync_engine.dispose()
        logger.info("Sync database engine disposed")
    except Exception as e:
        logger.error(f"Error disposing sync engine: {e}")

    logger.info("Database connections closed")


# Transaction Helper with timeout support
class DatabaseTransaction:
    """Context manager for database transactions with timeout support."""

    def __init__(self, session: AsyncSession, timeout_seconds: Optional[int] = None):
        self.session = session
        self.timeout_seconds = timeout_seconds or (10 if _is_ci_environment() else 30)

    async def __aenter__(self) -> AsyncSession:
        return self.session

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[Any],
    ) -> None:
        import asyncio

        try:
            if exc_type is not None:
                await asyncio.wait_for(
                    self.session.rollback(), timeout=self.timeout_seconds
                )
                logger.error(f"Transaction rolled back due to: {exc_val}")
            else:
                await asyncio.wait_for(
                    self.session.commit(), timeout=self.timeout_seconds
                )
        except asyncio.TimeoutError:
            logger.error(
                f"Transaction operation timed out after {self.timeout_seconds}s"
            )
            try:
                await self.session.rollback()
            except Exception:
                pass  # Best effort rollback
            raise
        except Exception as e:
            logger.error(f"Transaction error: {e}")
            try:
                await self.session.rollback()
            except Exception:
                pass  # Best effort rollback
            raise


# Bulk Operations Helper with optimizations
class BulkOperations:
    """Helper class for bulk database operations optimized for CI/CD."""

    @staticmethod
    async def bulk_insert(
        session: AsyncSession, instances: List[Any], batch_size: Optional[int] = None
    ) -> None:
        """Bulk insert instances with optimized batch size."""
        if not instances:
            return

        # Optimize batch size for environment
        if batch_size is None:
            batch_size = 100 if _is_ci_environment() else 500

        for i in range(0, len(instances), batch_size):
            batch = instances[i : i + batch_size]
            session.add_all(batch)
            await session.flush()

    @staticmethod
    async def bulk_update(
        session: AsyncSession, mappings: List[Any], batch_size: Optional[int] = None
    ) -> None:
        """Bulk update instances with optimized batch size."""
        if not mappings:
            return

        # Optimize batch size for environment
        if batch_size is None:
            batch_size = 50 if _is_ci_environment() else 200

        for i in range(0, len(mappings), batch_size):
            batch = mappings[i : i + batch_size]
            for mapping in batch:
                await session.merge(mapping)
            await session.flush()


# Database Utilities
def get_table_names() -> List[str]:
    """Get all table names from metadata."""
    return list(Base.metadata.tables.keys())


def get_model_by_tablename(tablename: str) -> Optional[Any]:
    """Get model class by table name."""
    for mapper in Base.registry.mappers:
        model = mapper.class_
        if hasattr(model, "__tablename__") and model.__tablename__ == tablename:
            return model
    return None


# Connection Pool Monitoring with error handling
async def get_pool_status() -> Dict[str, Any]:
    """Get connection pool status for monitoring."""
    try:
        pool = async_engine.pool
        return {
            "pool_size": getattr(pool, "size", lambda: 0)(),
            "checked_in": getattr(pool, "checkedin", lambda: 0)(),
            "checked_out": getattr(pool, "checkedout", lambda: 0)(),
            "overflow": getattr(pool, "overflow", lambda: 0)(),
            "invalid": getattr(pool, "invalid", lambda: 0)(),
            "environment": (
                "ci"
                if _is_ci_environment()
                else "testing" if _is_testing_environment() else "production"
            ),
        }
    except Exception as e:
        logger.error(f"Failed to get pool status: {e}")
        return {"error": str(e)}


# Database Event Listeners (optimized for CI/CD)
if not _is_ci_environment():  # Skip event listeners in CI to reduce overhead

    @event.listens_for(async_engine.sync_engine, "before_cursor_execute")
    def receive_before_cursor_execute(
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        """Log slow queries in debug mode."""
        if settings.DEBUG:
            context._query_start_time = time.time()

    @event.listens_for(async_engine.sync_engine, "after_cursor_execute")
    def receive_after_cursor_execute(
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        """Log query execution time in debug mode."""
        if settings.DEBUG and hasattr(context, "_query_start_time"):
            total = time.time() - context._query_start_time
            # Lower threshold for CI environments
            threshold = 0.05 if _is_ci_environment() else 0.1
            if total > threshold:
                logger.warning(f"Slow query ({total:.3f}s): {statement[:100]}...")


# CI/CD specific utilities
def get_environment_info() -> Dict[str, Any]:
    """Get current environment information for debugging."""
    return {
        "is_ci": _is_ci_environment(),
        "is_testing": _is_testing_environment(),
        "database_url": (
            get_database_url().split("@")[-1] if "@" in get_database_url() else "sqlite"
        ),
        "pool_config": _get_optimized_pool_config(),
        "debug_mode": settings.DEBUG,
    }
