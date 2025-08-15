"""
Database configuration and connection management.
Handles SQLAlchemy async and sync database connections.
"""

import logging
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

# Async Database Engine
async_engine = create_async_engine(
    get_database_url(),
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=5,  # Reduced pool size for remote connection
    max_overflow=10,  # Reduced overflow
    pool_recycle=1800,  # Recycle connections every 30 minutes
    connect_args={
        "command_timeout": 60,
        "server_settings": {
            "application_name": "kaoqin_backend",
        },
    },
    execution_options={
        "compiled_cache": {},
    },
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync Database Engine (for Alembic migrations)
sync_engine = create_engine(
    get_database_url_sync(),
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
)

# Sync Session Factory
SessionLocal = sessionmaker(
    sync_engine,
    autocommit=False,
    autoflush=False,
)


# Async Database Dependency
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create async database session.
    Used as a dependency in FastAPI endpoints.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


# Sync Database Dependency
def get_sync_session() -> Generator[Session, None, None]:
    """
    Create sync database session.
    Used for migrations and sync operations.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Sync database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# Database Health Check
async def check_database_health() -> bool:
    """
    Check if database connection is healthy.
    Used in health check endpoints.
    """
    try:
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# Database Initialization
async def init_database() -> None:
    """
    Initialize database tables.
    Only use in development or testing.
    """
    if settings.DEBUG or settings.TESTING:
        async with async_engine.begin() as conn:
            # Import all models to ensure they are registered
            from app.models import attendance, member, task  # noqa

            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    else:
        logger.warning("Database initialization skipped in production mode")


# Database Cleanup
async def close_database() -> None:
    """
    Close database connections.
    Used during application shutdown.
    """
    await async_engine.dispose()
    sync_engine.dispose()
    logger.info("Database connections closed")


# Transaction Helper
class DatabaseTransaction:
    """Context manager for database transactions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def __aenter__(self) -> AsyncSession:
        return self.session

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[Any],
    ) -> None:
        if exc_type is not None:
            await self.session.rollback()
            logger.error(f"Transaction rolled back due to: {exc_val}")
        else:
            await self.session.commit()


# Bulk Operations Helper
class BulkOperations:
    """Helper class for bulk database operations."""

    @staticmethod
    async def bulk_insert(session: AsyncSession, instances: List[Any]) -> None:
        """Bulk insert instances."""
        session.add_all(instances)
        await session.flush()

    @staticmethod
    async def bulk_update(session: AsyncSession, mappings: List[Any]) -> None:
        """Bulk update instances."""
        for mapping in mappings:
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


# Connection Pool Monitoring
async def get_pool_status() -> Dict[str, Any]:
    """Get connection pool status for monitoring."""
    pool = async_engine.pool
    return {
        "pool_size": getattr(pool, "size", lambda: 0)(),
        "checked_in": getattr(pool, "checkedin", lambda: 0)(),
        "checked_out": getattr(pool, "checkedout", lambda: 0)(),
        "overflow": getattr(pool, "overflow", lambda: 0)(),
        "invalid": getattr(pool, "invalid", lambda: 0)(),
    }


# Database Event Listeners

# Note: SQLite-specific pragmas removed as we use PostgreSQL exclusively


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
        if total > 0.1:  # Log queries taking more than 100ms
            logger.warning(f"Slow query ({total:.3f}s): {statement[:100]}...")
