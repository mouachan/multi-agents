"""
Admin API endpoints for database management and demo utilities.
"""
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/reset-database")
async def reset_database(db: AsyncSession = Depends(get_db)):
    """
    Reset database to initial state.

    WARNING: This will delete ALL data and reload seed data.
    For demo purposes only.
    """
    try:
        logger.warning("⚠️  DATABASE RESET REQUESTED")

        # Step 1: Truncate all tables (cascade to handle foreign keys)
        truncate_queries = [
            "TRUNCATE TABLE guardrails_detections CASCADE",
            "TRUNCATE TABLE claim_decisions CASCADE",
            "TRUNCATE TABLE claim_documents CASCADE",
            "TRUNCATE TABLE processing_logs CASCADE",
            "TRUNCATE TABLE claims CASCADE",
            "TRUNCATE TABLE user_contracts CASCADE",
            "TRUNCATE TABLE users CASCADE",
            "TRUNCATE TABLE knowledge_base CASCADE"
        ]

        for query in truncate_queries:
            await db.execute(text(query))

        await db.commit()
        logger.info("✅ All tables truncated")

        # Step 2: Reload seed data from GitHub URL
        logger.info(f"📥 Fetching seed data from: {settings.seed_data_url}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(settings.seed_data_url)
                response.raise_for_status()
                seed_sql = response.text
                logger.info(f"✅ Seed data fetched successfully ({len(seed_sql)} chars)")
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch seed data from {settings.seed_data_url}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch seed data from URL: {str(e)}"
            )

        # Execute seed SQL (split by statement)
        # Remove comments and empty lines
        statements = []
        current_statement = []

        for line in seed_sql.split('\n'):
            # Skip comments and empty lines
            stripped = line.strip()
            if not stripped or stripped.startswith('--'):
                continue

            current_statement.append(line)

            # If line ends with semicolon, it's end of statement
            if stripped.endswith(';'):
                statement = '\n'.join(current_statement)
                if statement.strip():
                    statements.append(statement)
                current_statement = []

        # Execute each statement
        for i, statement in enumerate(statements):
            try:
                await db.execute(text(statement))
                logger.debug(f"Executed statement {i+1}/{len(statements)}")
            except Exception as e:
                logger.error(f"Error executing statement {i+1}: {e}")
                logger.error(f"Statement: {statement[:200]}...")
                # Continue with next statement

        await db.commit()
        logger.info(f"✅ Seed data loaded ({len(statements)} statements)")

        # Step 3: Verify data
        result = await db.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()

        result = await db.execute(text("SELECT COUNT(*) FROM user_contracts"))
        contract_count = result.scalar()

        result = await db.execute(text("SELECT COUNT(*) FROM claims"))
        claim_count = result.scalar()

        result = await db.execute(text("SELECT COUNT(*) FROM knowledge_base"))
        kb_count = result.scalar()

        logger.info(f"✅ Database reset complete:")
        logger.info(f"   - Users: {user_count}")
        logger.info(f"   - Contracts: {contract_count}")
        logger.info(f"   - Claims: {claim_count}")
        logger.info(f"   - Knowledge Base: {kb_count}")

        return {
            "success": True,
            "message": "Database reset successfully",
            "data": {
                "users": user_count,
                "contracts": contract_count,
                "claims": claim_count,
                "knowledge_base": kb_count
            }
        }

    except Exception as e:
        logger.error(f"❌ Database reset failed: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database reset failed: {str(e)}"
        )


@router.get("/database-stats")
async def get_database_stats(db: AsyncSession = Depends(get_db)):
    """Get current database statistics."""
    try:
        stats = {}

        # Users
        result = await db.execute(text("SELECT COUNT(*) FROM users"))
        stats['users'] = result.scalar()

        # Contracts
        result = await db.execute(text("SELECT COUNT(*) FROM user_contracts"))
        stats['contracts'] = result.scalar()

        # Claims by status
        result = await db.execute(text("""
            SELECT status, COUNT(*)
            FROM claims
            GROUP BY status
        """))
        stats['claims_by_status'] = {row[0]: row[1] for row in result.fetchall()}

        # Total claims
        stats['claims_total'] = sum(stats['claims_by_status'].values())

        # Knowledge base
        result = await db.execute(text("SELECT COUNT(*) FROM knowledge_base"))
        stats['knowledge_base'] = result.scalar()

        # Embeddings
        result = await db.execute(text("""
            SELECT COUNT(*), COUNT(embedding)
            FROM knowledge_base
        """))
        kb_total, kb_with_emb = result.fetchone()
        stats['knowledge_base_embeddings'] = f"{kb_with_emb}/{kb_total}"

        result = await db.execute(text("""
            SELECT COUNT(*), COUNT(embedding)
            FROM claim_documents
        """))
        cd_total, cd_with_emb = result.fetchone()
        stats['claim_documents_embeddings'] = f"{cd_with_emb}/{cd_total}"

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get database stats: {str(e)}"
        )
