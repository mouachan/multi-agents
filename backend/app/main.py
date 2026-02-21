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
        color="emerald",
        icon="document",
        api_prefix="/api/v1/claims",
        decision_values=["approve", "deny", "manual_review"],
        routing_keywords=[
            "claim", "claims", "clm-", "sinistre", "sinistres",
            "assurance", "dommage", "remboursement",
            "indemnisation", "police d'assurance", "contrat d'assurance",
        ],
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
        routing_keywords=[
            "appel d'offres", "appels d'offres", "appel d offres",
            "ao", "tender", "tenders",
            "marche public", "marches publics", "soumission",
            "btp", "construction", "go/no-go", "go no go",
            "offre", "offres",
        ],
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


# Default tool display configuration (used when ConfigMap not mounted)
_DEFAULT_TOOL_DISPLAY = {
    "tools": {
        "ocr_document": {"label": {"fr": "OCR Document", "en": "OCR Document"}, "short": "OCR", "category": "extraction"},
        "ocr_extract_claim_info": {"label": {"fr": "OCR Extraction", "en": "OCR Extract"}, "short": "OCR", "category": "extraction"},
        "retrieve_user_info": {"label": {"fr": "Infos Utilisateur", "en": "User Info"}, "short": "USR", "category": "rag"},
        "retrieve_similar_claims": {"label": {"fr": "Sinistres Similaires", "en": "Similar Claims"}, "short": "SIM", "category": "rag"},
        "search_knowledge_base": {"label": {"fr": "Base de Connaissances", "en": "Knowledge Base"}, "short": "RAG", "category": "rag"},
        "retrieve_similar_references": {"label": {"fr": "References Similaires", "en": "Similar References"}, "short": "REF", "category": "rag"},
        "retrieve_historical_tenders": {"label": {"fr": "Historique AO", "en": "Historical Tenders"}, "short": "HIS", "category": "rag"},
        "retrieve_capabilities": {"label": {"fr": "Capacites", "en": "Capabilities"}, "short": "CAP", "category": "rag"},
        "list_claims": {"label": {"fr": "Liste Sinistres", "en": "List Claims"}, "short": "LST", "category": "crud"},
        "get_claim": {"label": {"fr": "Detail Sinistre", "en": "Get Claim"}, "short": "GET", "category": "crud"},
        "get_claim_documents": {"label": {"fr": "Documents Sinistre", "en": "Claim Documents"}, "short": "DOC", "category": "crud"},
        "get_claim_statistics": {"label": {"fr": "Statistiques Sinistres", "en": "Claim Statistics"}, "short": "STA", "category": "crud"},
        "analyze_claim": {"label": {"fr": "Analyser Sinistre", "en": "Analyze Claim"}, "short": "ANL", "category": "crud"},
        "list_tenders": {"label": {"fr": "Liste AO", "en": "List Tenders"}, "short": "LST", "category": "crud"},
        "get_tender": {"label": {"fr": "Detail AO", "en": "Get Tender"}, "short": "GET", "category": "crud"},
        "get_tender_documents": {"label": {"fr": "Documents AO", "en": "Tender Documents"}, "short": "DOC", "category": "crud"},
        "get_tender_statistics": {"label": {"fr": "Statistiques AO", "en": "Tender Statistics"}, "short": "STA", "category": "crud"},
        "analyze_tender": {"label": {"fr": "Analyser AO", "en": "Analyze Tender"}, "short": "ANL", "category": "crud"},
        "save_claim_decision": {"label": {"fr": "Sauvegarder Decision", "en": "Save Decision"}, "short": "SAV", "category": "crud"},
        "save_tender_decision": {"label": {"fr": "Sauvegarder Decision AO", "en": "Save Tender Decision"}, "short": "SAV", "category": "crud"},
        "generate_document_embedding": {"label": {"fr": "Generer Embedding", "en": "Generate Embedding"}, "short": "EMB", "category": "rag"},
    },
    "servers": {
        "ocr-server": {"label": "OCR", "color": "blue"},
        "rag-server": {"label": "RAG", "color": "purple"},
        "claims-server": {"label": "Claims", "color": "emerald"},
        "tenders-server": {"label": "Tenders", "color": "amber"},
    },
    "categories": {
        "extraction": {"label": {"fr": "OCR", "en": "OCR"}, "icon": "scan"},
        "rag": {"label": {"fr": "RAG", "en": "RAG"}, "icon": "search"},
        "crud": {"label": {"fr": "Database", "en": "Database"}, "icon": "database"},
    },
}


@app.get(f"{settings.api_v1_prefix}/config/tool-display")
async def get_tool_display_config():
    """Return tool display configuration (labels, abbreviations, categories, servers)."""
    from app.llamastack.orchestrator_prompts import ORCHESTRATOR_CONFIG

    config = ORCHESTRATOR_CONFIG.get("tool_display", {})
    # Merge: config overrides defaults per top-level key
    merged = {}
    for key in ("tools", "servers", "categories"):
        default_section = _DEFAULT_TOOL_DISPLAY.get(key, {})
        config_section = config.get(key, {})
        merged[key] = {**default_section, **config_section}
    return merged


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
