"""The business API of every domain, generated from its DomainSpec (app/domains).

    GET  /api/v1/<domain>/                     the cases
    GET  /api/v1/<domain>/statistics           number of cases by status, average processing time
    GET  /api/v1/<domain>/<id>                 one case, with the steps of its last processing
    POST /api/v1/<domain>/<id>/process         the domain's agent processes the case (in the background)
    GET  /api/v1/<domain>/<id>/decision        its current decision: the agent's, then the reviewer's
    GET  /api/v1/<domain>/<id>/document?lang=  its PDF (French, or the English version when there is one)

plus the routes of a single domain, at the end of this file (claims: personal data found in the claim;
postal: tracking timeline of the parcel). Access: the user's profile must give the domain's agent
(dependency added in app/main.py).
"""
import logging
from typing import Callable, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains import DomainSpec
from app.models.claim import GuardrailsDetection
from app.models.reclamation import TrackingEvent
from app.services import decisions
from app.services.background import is_running, run_in_background
from app.services.cases import case_number, case_to_api
from app.services.documents import read_document
from app.services.processing import job_name, process_case

logger = logging.getLogger(__name__)


async def load_case(db: AsyncSession, spec: DomainSpec, case_id: UUID):
    case = await db.get(spec.model, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"{spec.label} not found")
    return case


def domain_router(spec: DomainSpec) -> APIRouter:
    router = APIRouter()
    model = spec.model

    @router.get("/")
    async def list_cases(db: AsyncSession = Depends(get_db)):
        cases = (await db.execute(
            select(model).where(model.is_archived.is_(False)).order_by(model.submitted_at.desc())
        )).scalars().all()
        return {"items": [case_to_api(spec, case) for case in cases], "total": len(cases)}

    @router.get("/statistics")
    async def statistics(db: AsyncSession = Depends(get_db)):
        rows = (await db.execute(select(model.status, func.count()).group_by(model.status))).all()
        by_status = {getattr(status, "value", status): count for status, count in rows}
        average = (await db.execute(select(func.avg(model.total_processing_time_ms)))).scalar()
        return {"total": sum(by_status.values()), "by_status": by_status,
                "average_processing_time_ms": float(average) if average is not None else None}

    @router.get("/{case_id}")
    async def get_case(case_id: UUID, db: AsyncSession = Depends(get_db)):
        return case_to_api(spec, await load_case(db, spec, case_id))

    @router.post("/{case_id}/process")
    async def process(case_id: UUID, db: AsyncSession = Depends(get_db)):
        case = await load_case(db, spec, case_id)
        name = job_name(spec, case.id)
        if is_running(name):
            return JSONResponse(status_code=202, content={"id": str(case.id), "status": "processing",
                                                          "message": "Already being processed"})
        case.status = "processing"
        await db.commit()
        run_in_background(name, process_case, spec, case.id)
        return {"id": str(case.id), "status": "processing", "message": "Processing started"}

    @router.get("/{case_id}/decision")
    async def get_decision(case_id: UUID, db: AsyncSession = Depends(get_db)):
        await load_case(db, spec, case_id)
        decision = await decisions.latest_decision(db, spec, case_id)
        if decision is None:
            raise HTTPException(status_code=404, detail=f"No decision for this {spec.label.lower()} yet")
        return decisions.decision_to_api(decision)

    @router.get("/{case_id}/document")
    async def document(case_id: UUID, lang: str = Query("fr", pattern="^(fr|en)$"),
                       db: AsyncSession = Depends(get_db)):
        case = await load_case(db, spec, case_id)
        meta = case.meta or {}
        english = meta.get("document_file_id_en") or meta.get("document_path_en")
        stored = english if lang == "en" and english else case.document_path
        content = await read_document(stored) if stored else None
        if content is None:
            raise HTTPException(status_code=404, detail="Document not found")
        filename = f"{case_number(spec, case)}{'-en' if stored == english else ''}.pdf"
        return Response(content=content, media_type="application/pdf",
                        headers={"Content-Disposition": f'inline; filename="{filename}"'})

    EXTRA_ROUTES.get(spec.name, lambda _router: None)(router)
    return router


# ---------------------------------------------------------------------------- domain-specific routes

def _claims_routes(router: APIRouter) -> None:
    @router.get("/{case_id}/personal-data")
    async def personal_data(case_id: UUID, db: AsyncSession = Depends(get_db)):
        """Types of personal data found in the claim (app/services/pii_report.py)."""
        rows = (await db.execute(
            select(GuardrailsDetection).where(GuardrailsDetection.claim_id == case_id)
            .order_by(GuardrailsDetection.detected_at.desc())
        )).scalars().all()
        return [{"id": str(row.id), "detected_at": row.detected_at, **(row.record_metadata or {})} for row in rows]


def _postal_routes(router: APIRouter) -> None:
    from app.domains import get_domain

    @router.get("/{case_id}/tracking")
    async def tracking(case_id: UUID, db: AsyncSession = Depends(get_db)):
        """Tracking timeline of the complaint's parcel, most recent event first."""
        complaint = await load_case(db, get_domain("postal"), case_id)
        events = (await db.execute(
            select(TrackingEvent).where(TrackingEvent.numero_suivi == complaint.numero_suivi)
            .order_by(TrackingEvent.event_date.desc())
        )).scalars().all()
        return [{"id": str(e.id), "event_type": getattr(e.event_type, "value", e.event_type),
                 "event_date": e.event_date, "location": e.location, "detail": e.detail,
                 "code_postal": e.code_postal, "is_final": e.is_final, "metadata": e.event_metadata}
                for e in events]


EXTRA_ROUTES: Dict[str, Callable[[APIRouter], None]] = {"claims": _claims_routes, "postal": _postal_routes}
