"""The business database (PostgreSQL + pgvector), the same tables as the backend.

Queries are plain SQL with named parameters (:name). Rows come back as dicts of JSON-ready values
(dates as ISO text, decimals as float, ids as text), so a tool can return them as they are.
The driver is synchronous (psycopg2): each query runs in a worker thread.
"""
import asyncio
import logging
import os
import time
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}".format(
    user=os.getenv("POSTGRES_USER", "multi_agent_user"),
    password=os.getenv("POSTGRES_PASSWORD", ""),
    host=os.getenv("POSTGRES_HOST", "postgresql"),
    port=os.getenv("POSTGRES_PORT", "5432"),
    name=os.getenv("POSTGRES_DATABASE", "multi_agent_db"),
)
engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10, pool_pre_ping=True, pool_recycle=3600)

Row = Dict[str, Any]


def plain(value: Any) -> Any:
    """A database value as JSON accepts it."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    return value


def _run(sql: str, params: Dict[str, Any], commit: bool = False):
    with engine.connect() as connection:
        result = connection.execute(text(sql), params)
        if commit:
            connection.commit()
            return result.rowcount
        return [{key: plain(value) for key, value in row._mapping.items()} for row in result]


async def fetch_all(sql: str, **params) -> List[Row]:
    return await asyncio.to_thread(_run, sql, params)


async def fetch_one(sql: str, **params) -> Optional[Row]:
    rows = await fetch_all(sql, **params)
    return rows[0] if rows else None


async def execute(sql: str, **params) -> int:
    """A write (INSERT, UPDATE, DELETE), committed; returns the number of rows changed."""
    return await asyncio.to_thread(_run, sql, params, True)


def wait_for_database(attempts: int = 10, delay: float = 3.0) -> None:
    """At startup: the database may still be starting (same pod start order as the backend)."""
    for attempt in range(1, attempts + 1):
        try:
            _run("SELECT 1", {})
            return
        except Exception as e:
            if attempt == attempts:
                raise
            logger.warning("Database not reachable (%d/%d): %s", attempt, attempts, e)
            time.sleep(delay)
