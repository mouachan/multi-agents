"""
Pytest configuration and fixtures for testing.

Provides database fixtures, mocks, and test data.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.models.claim import Base, Claim, ClaimDocument, ClaimDecision, ClaimStatus, DecisionType


# Enable foreign keys for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign keys for SQLite."""
    if 'sqlite' in str(dbapi_conn):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=NullPool,
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for each test."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_claim_data():
    """Sample claim data for testing."""
    return {
        "user_id": "USR001",
        "claim_number": "CLM-TEST-001",
        "claim_type": "medical",
        "document_path": "/test/claim_001.pdf",
        "status": ClaimStatus.pending
    }


@pytest.fixture
async def test_claim(db_session: AsyncSession, sample_claim_data):
    """Create a test claim in database."""
    claim = Claim(**sample_claim_data)
    db_session.add(claim)
    await db_session.commit()
    await db_session.refresh(claim)
    return claim


@pytest.fixture
async def test_claim_with_document(db_session: AsyncSession, test_claim: Claim):
    """Create test claim with OCR document."""
    document = ClaimDocument(
        claim_id=test_claim.id,
        document_type="medical_bill",
        file_path="/test/claim_001.pdf",
        raw_ocr_text="Patient: John Doe\nDiagnosis: Flu treatment\nAmount: $150.00",
        structured_data={
            "patient_name": "John Doe",
            "diagnosis": "Flu treatment",
            "amount": "150.00"
        },
        ocr_confidence=0.95
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)

    return test_claim, document


@pytest.fixture
async def test_claim_with_decision(db_session: AsyncSession, test_claim: Claim):
    """Create test claim with initial decision."""
    decision = ClaimDecision(
        claim_id=test_claim.id,
        initial_decision=DecisionType.approve,
        initial_confidence=0.85,
        initial_reasoning="Claim is valid and within coverage",
        decision=DecisionType.approve,
        confidence=0.85,
        reasoning="Claim is valid and within coverage",
        requires_manual_review=False
    )
    db_session.add(decision)
    await db_session.commit()
    await db_session.refresh(decision)

    return test_claim, decision


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_llamastack_response():
    """Mock LlamaStack API response."""
    return {
        "agent_id": "test-agent-123",
        "session_id": "test-session-456",
        "turn_id": "test-turn-789",
        "response": {
            "content": """
            Based on the claim analysis:

            **Recommendation**: approve
            **Confidence**: 85%
            **Reasoning**: The claim is for flu treatment which is covered under the user's health insurance.
            The amount of $150 is within reasonable limits for outpatient care.
            """,
            "role": "assistant"
        },
        "usage": {
            "prompt_tokens": 250,
            "completion_tokens": 100,
            "total_tokens": 350
        }
    }


@pytest.fixture
def mock_agent_config():
    """Mock agent configuration."""
    return {
        "model": "test-model",
        "instructions": "You are a helpful claims processing assistant.",
        "enable_session_persistence": True,
        "sampling_params": {
            "temperature": 0.0,
            "top_p": 0.9
        }
    }


# ============================================================================
# Logging Fixtures
# ============================================================================

@pytest.fixture
def capture_logs(caplog):
    """Capture logs for verification."""
    import logging
    caplog.set_level(logging.INFO)
    return caplog


# ============================================================================
# Helper Functions
# ============================================================================

@pytest.fixture
def assert_logged():
    """Helper to assert log messages."""
    def _assert_logged(caplog, level: str, message: str):
        """Check if a log message was recorded."""
        for record in caplog.records:
            if record.levelname == level and message in record.message:
                return True
        return False
    return _assert_logged
