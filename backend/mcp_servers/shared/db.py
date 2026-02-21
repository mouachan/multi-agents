"""
Shared database utilities for MCP servers.

Provides PostgreSQL connection management and async query helpers
used by all MCP servers (claims, tenders, RAG).
"""

import asyncio
import logging
import os
from typing import Any, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Configuration from environment
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgresql")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DATABASE", "claims_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "claims_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "claims_pass")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(bind=engine)


def check_database_connection(check_pgvector: bool = False, max_retries: int = 10, retry_delay: float = 3.0) -> bool:
    """Verify database connectivity on startup, with retries."""
    import time
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                if check_pgvector:
                    has_pgvector = conn.execute(
                        text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
                    ).scalar()
                    if not has_pgvector:
                        logger.warning("pgvector extension not found - vector search may fail")
            logger.info("Database connection successful")
            return True
        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"Database connection attempt {attempt}/{max_retries} failed: {e}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Database connection failed after {max_retries} attempts: {e}")
                raise


async def run_db_query(query, params: dict) -> List[Any]:
    """Execute a read query in a thread pool and return all rows."""
    def _execute():
        with SessionLocal() as session:
            try:
                return session.execute(query, params).fetchall()
            except Exception:
                session.rollback()
                raise

    return await asyncio.to_thread(_execute)


async def run_db_query_one(query, params: dict) -> Optional[Any]:
    """Execute a read query in a thread pool and return one row."""
    def _execute():
        with SessionLocal() as session:
            try:
                return session.execute(query, params).fetchone()
            except Exception:
                session.rollback()
                raise

    return await asyncio.to_thread(_execute)


async def run_db_execute(query, params: dict) -> int:
    """Execute a write query (INSERT/UPDATE/DELETE) and return rows affected."""
    def _execute():
        with SessionLocal() as session:
            try:
                result = session.execute(query, params)
                session.commit()
                return result.rowcount
            except Exception:
                session.rollback()
                raise

    return await asyncio.to_thread(_execute)
