"""Run long business processing jobs outside the HTTP request.

Agent processing (OCR, RAG, decision) can take minutes: the /process endpoints mark the
entity as processing, start the job here and return at once; the UI polls the entity
status. Cloud load balancers close requests idle for ~60 s.
"""
import asyncio
import logging
from typing import Any, Awaitable, Callable, Set

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

_tasks: Set[asyncio.Task] = set()  # keep references so running jobs are not garbage collected


def run_in_background(name: str, job: Callable[..., Awaitable[Any]], *args: Any) -> None:
    """Run job(db, *args) with its own DB session; failures are logged (jobs mark the entity failed)."""
    async def runner() -> None:
        async with AsyncSessionLocal() as db:
            try:
                await job(db, *args)
            except Exception as e:
                logger.error("Background job %s failed: %s", name, e, exc_info=True)

    task = asyncio.create_task(runner(), name=name)
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
