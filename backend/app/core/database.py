"""
Database connection and session management.

FIXES APPLIED:
- Updated to SQLAlchemy 2.0 DeclarativeBase
- Added pool_pre_ping and pool_recycle
- Added connection health check function
"""

import logging
from typing import AsyncGenerator

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)


# SQLAlchemy 2.0 style base class
class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Sync engine for migrations
engine = create_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=settings.database_pool_pre_ping,
    pool_recycle=settings.database_pool_recycle,
    echo=settings.debug,
)

# Async engine for application
async_engine = create_async_engine(
    settings.async_database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=settings.database_pool_pre_ping,
    pool_recycle=settings.database_pool_recycle,
    echo=settings.debug,
)

# Async session factory (SQLAlchemy 2.0 style)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync session factory (for migrations)
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
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


async def check_database_connection() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection check: OK")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


async def dispose_engine() -> None:
    """
    Dispose of the async engine connections.
    Call this on application shutdown.
    """
    await async_engine.dispose()
    logger.info("Database engine disposed")
