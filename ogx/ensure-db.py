"""Create the OGX database (with pgvector) before OGX starts.

Run by the ogx service of docker-compose.yml. Idempotent, so it also works on an
existing postgres_data volume, where the initdb scripts no longer run.
"""
import asyncio
import os

import asyncpg


async def main() -> None:
    params = {
        "host": os.environ["POSTGRES_HOST"],
        "port": int(os.environ.get("POSTGRES_PORT", "5432")),
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
    }
    db = os.environ["POSTGRES_DB"]

    conn = await asyncpg.connect(database="postgres", **params)
    try:
        if not await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db):
            await conn.execute(f'CREATE DATABASE "{db}"')
            print(f"Created database {db}")
    finally:
        await conn.close()

    conn = await asyncpg.connect(database=db, **params)
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    finally:
        await conn.close()


asyncio.run(main())
