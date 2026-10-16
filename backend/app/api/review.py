"""Human review API (app/services/review.py).

    GET  /api/v1/review/inbox                             the cases waiting for a reviewer
    GET  /api/v1/review/<domain>/<id>                     the brief of a case
    POST /api/v1/review/<domain>/<id>/questions           ask the agent   {question, language}
    POST /api/v1/review/<domain>/<id>/decision            decide          {decision, justification}

A reviewer only sees and decides the cases of the domains their profile gives access to.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import User, current_user, require_tools
from app.core.database import get_db
from app.domains import DOMAINS, DomainSpec
from app.services import review

router = APIRouter()


class Question(BaseModel):
    question: str
    language: str = "fr"


class Decision(BaseModel):
    decision: str
    justification: str = ""


def _domain(domain: str, user: User) -> DomainSpec:
    spec = DOMAINS.get(domain)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"Unknown domain {domain}")
    if domain not in user.domains:
        raise HTTPException(status_code=403, detail=f"Your profile has no access to the {domain} agent")
    return spec


async def _case(db: AsyncSession, spec: DomainSpec, case_id: UUID):
    case = await db.get(spec.model, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"{spec.label} not found")
    return case


@router.get("/inbox")
async def inbox(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    return await review.inbox(db, [spec for name, spec in DOMAINS.items() if name in user.domains])


@router.get("/{domain}/{case_id}")
async def brief(domain: str, case_id: UUID, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    spec = _domain(domain, user)
    try:
        return await review.brief(db, spec, await _case(db, spec, case_id))
    except review.ReviewError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{domain}/{case_id}/questions")
async def ask(domain: str, case_id: UUID, body: Question,
              user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    spec = _domain(domain, user)
    require_tools(user, spec.processing_tools, "to answer a question about the case")
    try:
        return await review.ask_agent(db, spec, await _case(db, spec, case_id), body.question, body.language, user)
    except review.ReviewError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{domain}/{case_id}/decision")
async def decide(domain: str, case_id: UUID, body: Decision,
                 user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    spec = _domain(domain, user)
    try:
        return await review.decide(db, spec, await _case(db, spec, case_id), body.decision, body.justification, user)
    except review.ReviewError as e:
        raise HTTPException(status_code=409, detail=str(e))
