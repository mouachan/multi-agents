"""Backend of the multi-agent platform: business APIs, human review, chat, administration.

    app/domains/     the business domains (claims, tenders, postal): what differs between them
    app/agents.py    the agent profiles of the chat, and their A2A agents
    app/api/         the HTTP API (one module per area, listed in ROUTERS below)
    app/services/    the logic: processing by the agents, decisions, review, chat, demo reset...
    app/models/      the database tables (SQLAlchemy)
    app/core/        settings, database, authentication, MLflow tracing, prompt files

Every API route needs an authenticated user (OpenShift token, app/core/auth.py); a domain's routes
need access to its agent, the administration the admin profile.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api import admin, auth, chat, review, sandbox
from app.api.domains import domain_router
from app.core import tracing
from app.core.auth import current_user, require_admin, require_domain
from app.core.config import settings
from app.core.database import async_engine, dispose_engine
from app.domains import all_domains

logging.basicConfig(level=getattr(logging, settings.log_level.upper()),
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s %s (database %s:%s/%s)", settings.app_name, settings.app_version,
                settings.postgres_host, settings.postgres_port, settings.postgres_database)
    tracing.init_mlflow()
    yield
    tracing.shutdown_tracing()
    await dispose_engine()


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan,
              docs_url="/docs" if settings.debug else None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/health/live")
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error("Readiness check failed: %s", e)
        return JSONResponse(status_code=503, content={"status": "not_ready", "error": str(e)})


authenticated = [Depends(current_user)]
ROUTERS = [
    # (router, URL prefix under /api/v1, access)
    (auth.router, "/auth", authenticated),
    *[(domain_router(spec), f"/{spec.name}", [Depends(require_domain(spec.name))]) for spec in all_domains()],
    (review.router, "/review", authenticated),
    (chat.router, "/chat", authenticated),
    (sandbox.router, "/sandbox", authenticated),
    (admin.router, "/admin", [Depends(require_admin)]),
]
for router, prefix, dependencies in ROUTERS:
    app.include_router(router, prefix=f"{settings.api_v1_prefix}{prefix}", dependencies=dependencies,
                       tags=[prefix.strip("/")])


@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    logger.error("Unexpected error on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
