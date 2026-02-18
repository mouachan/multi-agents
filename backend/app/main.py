"""
Main FastAPI application for Multi-Agent AI Platform.

Features:
- Agent Registry for dynamic agent management
- Orchestrator for chat-based interactions
- Claims and Tenders specialized agents
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_engine, check_database_connection, dispose_engine, Base

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def register_agents():
    """Register all agents in the registry at startup."""
    from app.services.agents.registry import AgentRegistry, AgentDefinition
    from app.services.claim_service import ClaimService, CLAIM_TOOLS
    from app.services.tender_service import TenderService, TENDER_TOOLS
    from app.llamastack.prompts import (
        CLAIMS_PROCESSING_AGENT_INSTRUCTIONS,
        USER_MESSAGE_FULL_WORKFLOW_TEMPLATE,
    )
    from app.llamastack.ao_prompts import (
        AO_PROCESSING_AGENT_INSTRUCTIONS,
        AO_USER_MESSAGE_TEMPLATE,
    )

    AgentRegistry.register(AgentDefinition(
        id="claims",
        name="Insurance Claims Processing",
        description="Automated insurance claims analysis with OCR, RAG, and decision-making",
        entity_type="claim",
        service_class=ClaimService,
        instructions=CLAIMS_PROCESSING_AGENT_INSTRUCTIONS,
        user_message_template=USER_MESSAGE_FULL_WORKFLOW_TEMPLATE,
        tools=CLAIM_TOOLS,
        color="blue",
        icon="document",
        api_prefix="/api/v1/claims",
        decision_values=["approve", "deny", "manual_review"],
    ))

    AgentRegistry.register(AgentDefinition(
        id="tenders",
        name="Analyse Appels d'Offres",
        description="Analyse automatisee d'appels d'offres BTP avec references, historique et capacites",
        entity_type="tender",
        service_class=TenderService,
        instructions=AO_PROCESSING_AGENT_INSTRUCTIONS,
        user_message_template=AO_USER_MESSAGE_TEMPLATE,
        tools=TENDER_TOOLS,
        color="amber",
        icon="building",
        api_prefix="/api/v1/tenders",
        decision_values=["go", "no_go", "a_approfondir"],
    ))

    logger.info(f"Registered {len(AgentRegistry.list_agents())} agents")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"LlamaStack endpoint: {settings.llamastack_endpoint}")
    logger.info(f"Database: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_database}")

    # Register agents
    register_agents()

    # Check database connection
    if not await check_database_connection():
        logger.error("Failed to connect to database on startup")
    else:
        logger.info("Database connection verified")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await dispose_engine()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-Agent AI Platform with LlamaStack, MCP Servers & OpenShift AI",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# =============================================================================
# Health Check Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "healthy",
    }


@app.get("/health/live")
async def liveness():
    """Liveness probe for Kubernetes."""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe for Kubernetes."""
    try:
        async with async_engine.connect() as conn:
            await conn.execute(select(1))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)},
        )


@app.get(f"{settings.api_v1_prefix}/agents")
async def list_agents():
    """List available AI agents (dynamic via AgentRegistry)."""
    from app.services.agents.registry import AgentRegistry
    return AgentRegistry.to_api_list()


# =============================================================================
# Import and Include API Routers
# =============================================================================

from app.api import claims, documents, hitl, admin, tenders, orchestrator, a2a

app.include_router(
    claims.router,
    prefix=f"{settings.api_v1_prefix}/claims",
    tags=["claims"]
)
app.include_router(
    documents.router,
    prefix=f"{settings.api_v1_prefix}/documents",
    tags=["documents"]
)
app.include_router(
    hitl.router,
    prefix=f"{settings.api_v1_prefix}/review",
    tags=["review"]
)
app.include_router(
    admin.router,
    prefix=f"{settings.api_v1_prefix}",
    tags=["admin"]
)
app.include_router(
    tenders.router,
    prefix=f"{settings.api_v1_prefix}/tenders",
    tags=["tenders"]
)
app.include_router(
    orchestrator.router,
    prefix=f"{settings.api_v1_prefix}/orchestrator",
    tags=["orchestrator"]
)
app.include_router(
    a2a.router,
    prefix=f"{settings.api_v1_prefix}/a2a",
    tags=["a2a"]
)


# =============================================================================
# Exception Handlers
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc) if settings.debug else None}
    )


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
