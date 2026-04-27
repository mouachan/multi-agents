"""
Postal domain API endpoints (Courrier & Colis).

Endpoints:
- GET    /                              - List reclamations with pagination
- GET    /statistics/overview           - Get reclamation statistics
- GET    /{reclamation_id}              - Get a specific reclamation
- POST   /                             - Create a new reclamation
- POST   /{reclamation_id}/process     - Process a reclamation with LlamaStack agent
- GET    /{reclamation_id}/status      - Get reclamation processing status
- GET    /{reclamation_id}/decision    - Get reclamation decision
- GET    /{reclamation_id}/logs        - Get processing logs
- GET    /{reclamation_id}/tracking    - Get tracking events
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.api.postal import schemas
from app.api.shared.schemas import ProcessingStepLog
from app.core.config import settings
from app.core.database import get_db
from app.models import reclamation as models
from app.llamastack.courrier_prompts import (
    COURRIER_RECLAMATION_INSTRUCTIONS,
    COURRIER_RECLAMATION_USER_TEMPLATE,
)
from app.services.document_storage import get_document
from app.services.reclamation_service import ReclamationService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service
reclamation_service = ReclamationService()


# =============================================================================
# GET / - List Reclamations
# =============================================================================

@router.get("/", response_model=schemas.ReclamationListResponse)
async def list_reclamations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    include_archived: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    """List reclamations with pagination and optional filtering."""
    try:
        query = select(models.Reclamation)

        # Filter out archived reclamations by default
        if not include_archived:
            query = query.where(models.Reclamation.is_archived == False)

        if status:
            query = query.where(models.Reclamation.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = (
            query
            .order_by(models.Reclamation.submitted_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await db.execute(query)
        reclamations = result.scalars().all()

        reclamation_responses = [
            schemas.ReclamationResponse.model_validate(r) for r in reclamations
        ]

        return schemas.ReclamationListResponse(
            items=reclamation_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Error listing reclamations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /statistics/overview - Get Reclamation Statistics
# =============================================================================

@router.get("/statistics/overview", response_model=schemas.ReclamationStatisticsResponse)
async def get_reclamation_statistics(db: AsyncSession = Depends(get_db)):
    """Get overall reclamation statistics by status and type."""
    try:
        # Count by status
        by_status: dict[str, int] = {}
        for status_value in models.ReclamationStatus:
            query = select(func.count()).where(
                models.Reclamation.status == status_value.value
            )
            result = await db.execute(query)
            count = result.scalar() or 0
            if count > 0:
                by_status[status_value.value] = count

        # Count by type
        by_type: dict[str, int] = {}
        for type_value in models.ReclamationType:
            query = select(func.count()).where(
                models.Reclamation.reclamation_type == type_value.value
            )
            result = await db.execute(query)
            count = result.scalar() or 0
            if count > 0:
                by_type[type_value.value] = count

        # Average processing time
        avg_query = select(func.avg(models.Reclamation.total_processing_time_ms)).where(
            models.Reclamation.total_processing_time_ms.isnot(None)
        )
        avg_result = await db.execute(avg_query)
        avg_processing_time = avg_result.scalar()

        total = sum(by_status.values())

        return schemas.ReclamationStatisticsResponse(
            total=total,
            by_status=by_status,
            by_type=by_type,
            avg_processing_time_ms=avg_processing_time,
        )

    except Exception as e:
        logger.error(f"Error getting reclamation statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /{reclamation_id} - Get Reclamation
# =============================================================================

@router.get("/{reclamation_id}", response_model=schemas.ReclamationResponse)
async def get_reclamation(
    reclamation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific reclamation by ID."""
    try:
        query = select(models.Reclamation).where(models.Reclamation.id == reclamation_id)
        result = await db.execute(query)
        reclamation = result.scalar_one_or_none()

        if not reclamation:
            raise HTTPException(status_code=404, detail="Reclamation not found")

        return schemas.ReclamationResponse.model_validate(reclamation)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting reclamation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# POST / - Create Reclamation
# =============================================================================

@router.post("/", response_model=schemas.ReclamationResponse, status_code=201)
async def create_reclamation(
    reclamation_data: schemas.ReclamationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new reclamation. Auto-generates reclamation_number if not provided or empty."""
    try:
        data = reclamation_data.model_dump()

        # Auto-generate reclamation_number as RECL-YYYY-NNNN
        if not data.get("reclamation_number"):
            year = datetime.now(timezone.utc).year
            # Get current max sequence for this year
            like_pattern = f"RECL-{year}-%"
            max_query = select(func.count()).where(
                models.Reclamation.reclamation_number.like(like_pattern)
            )
            max_result = await db.execute(max_query)
            current_count = max_result.scalar() or 0
            data["reclamation_number"] = f"RECL-{year}-{current_count + 1:04d}"

        new_reclamation = models.Reclamation(**data)
        db.add(new_reclamation)
        await db.commit()
        await db.refresh(new_reclamation)

        logger.info(f"Created new reclamation: {new_reclamation.id}")
        return schemas.ReclamationResponse.model_validate(new_reclamation)

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating reclamation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# POST /{reclamation_id}/process - Process Reclamation with LlamaStack Agent
# =============================================================================

@router.post("/{reclamation_id}/process", response_model=schemas.ProcessReclamationResponse)
async def process_reclamation(
    reclamation_id: UUID,
    process_request: schemas.ProcessReclamationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Process a reclamation using LlamaStack agent.

    The agent will:
    1. Extract document info via OCR
    2. Retrieve tracking history
    3. Find similar historical reclamations
    4. Make a decision (rembourser/reexpedier/rejeter/escalader)
    """
    try:
        # Get and validate reclamation
        reclamation = await reclamation_service.get_reclamation_by_id(db, str(reclamation_id))
        if not reclamation:
            raise HTTPException(status_code=404, detail="Reclamation not found")

        # If reclamation is already being processed, return 202 Accepted
        if reclamation.status == models.ReclamationStatus.processing:
            return Response(
                status_code=202,
                content=json.dumps({
                    "reclamation_id": str(reclamation_id),
                    "status": "processing",
                    "message": "Reclamation is already being processed. Please wait for completion.",
                    "processing_started_at": reclamation.updated_at.isoformat() if reclamation.updated_at else None,
                }),
                media_type="application/json",
            )

        agent_config = {
            "model": settings.llamastack_default_model,
            "instructions": COURRIER_RECLAMATION_INSTRUCTIONS,
        }

        # Process reclamation with agent service
        result = await reclamation_service.process_reclamation_with_agent(
            db=db,
            reclamation_id=str(reclamation_id),
            agent_config=agent_config,
        )

        # Save decision
        await reclamation_service.save_decision(
            db=db,
            reclamation_id=str(reclamation_id),
            decision_data=result["decision"],
        )

        recommendation = result["decision"].get("recommendation", "escalader")

        return schemas.ProcessReclamationResponse(
            reclamation_id=reclamation_id,
            status=result["reclamation_status"],
            message=f"Processing completed: {recommendation}",
            processing_started_at=reclamation.submitted_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing reclamation {reclamation_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /{reclamation_id}/status - Get Reclamation Status
# =============================================================================

@router.get("/{reclamation_id}/status", response_model=schemas.ReclamationStatusResponse)
async def get_reclamation_status(
    reclamation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get the current processing status of a reclamation."""
    try:
        query = select(models.Reclamation).where(models.Reclamation.id == reclamation_id)
        result = await db.execute(query)
        reclamation = result.scalar_one_or_none()

        if not reclamation:
            raise HTTPException(status_code=404, detail="Reclamation not found")

        # Read processing steps from reclamation metadata
        processing_steps = []
        current_step = None
        progress = 0.0

        if reclamation.reclamation_metadata and "processing_steps" in reclamation.reclamation_metadata:
            saved_steps = reclamation.reclamation_metadata["processing_steps"]
            for step in saved_steps:
                processing_steps.append(ProcessingStepLog(
                    step_name=step.get("step_name", "unknown"),
                    agent_name=step.get("agent_name", "unknown"),
                    status=step.get("status", "completed"),
                    duration_ms=step.get("duration_ms"),
                    started_at=None,
                    completed_at=None,
                    output_data=step.get("output_data"),
                    error_message=step.get("error_message"),
                ))

        # Determine progress
        terminal_statuses = [
            models.ReclamationStatus.completed,
            models.ReclamationStatus.rejected,
            models.ReclamationStatus.manual_review,
            models.ReclamationStatus.escalated,
        ]
        if reclamation.status in terminal_statuses:
            progress = 100.0
        elif processing_steps:
            current_step = processing_steps[-1].step_name
            step_progress = {
                "ocr_document": 25,
                "get_tracking": 40,
                "retrieve_similar_reclamations": 60,
                "search_courrier_knowledge": 75,
                "save_reclamation_decision": 100,
            }
            progress = step_progress.get(current_step, 50)
        else:
            progress = 0.0

        return schemas.ReclamationStatusResponse(
            reclamation_id=reclamation_id,
            status=reclamation.status,
            current_step=current_step,
            progress_percentage=progress,
            processing_steps=processing_steps,
            estimated_completion_time=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting reclamation status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /{reclamation_id}/decision - Get Reclamation Decision
# =============================================================================

@router.get("/{reclamation_id}/decision", response_model=schemas.ReclamationDecisionResponse)
async def get_reclamation_decision(
    reclamation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get the decision details for a processed reclamation."""
    try:
        query = (
            select(models.ReclamationDecision)
            .where(models.ReclamationDecision.reclamation_id == reclamation_id)
            .order_by(models.ReclamationDecision.created_at.desc())
        )
        result = await db.execute(query)
        decision = result.scalar_one_or_none()

        if not decision:
            raise HTTPException(status_code=404, detail="No decision found for this reclamation")

        return schemas.ReclamationDecisionResponse(
            id=decision.id,
            reclamation_id=decision.reclamation_id,
            decision=decision.decision.value,
            confidence=decision.confidence,
            reasoning=decision.reasoning,
            initial_decision=decision.initial_decision.value if decision.initial_decision else None,
            initial_confidence=decision.initial_confidence,
            initial_reasoning=decision.initial_reasoning,
            llm_model=decision.llm_model,
            requires_manual_review=decision.requires_manual_review,
            decided_at=decision.decided_at,
            metadata=decision.decision_metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting reclamation decision: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /{reclamation_id}/logs - Get Reclamation Logs
# =============================================================================

@router.get("/{reclamation_id}/logs", response_model=schemas.ReclamationLogsResponse)
async def get_reclamation_logs(
    reclamation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get processing logs for a reclamation."""
    try:
        query = select(models.Reclamation).where(models.Reclamation.id == reclamation_id)
        result = await db.execute(query)
        reclamation = result.scalar_one_or_none()

        if not reclamation:
            raise HTTPException(status_code=404, detail="Reclamation not found")

        processing_logs = []

        # Read processing steps from reclamation metadata
        if reclamation.reclamation_metadata and "processing_steps" in reclamation.reclamation_metadata:
            saved_steps = reclamation.reclamation_metadata["processing_steps"]
            for step in saved_steps:
                processing_logs.append(ProcessingStepLog(
                    step_name=step.get("step_name", "unknown"),
                    agent_name=step.get("agent_name", "unknown"),
                    status=step.get("status", "completed"),
                    duration_ms=step.get("duration_ms"),
                    started_at=None,
                    completed_at=None,
                    output_data=step.get("output_data"),
                    error_message=step.get("error_message"),
                ))

        return schemas.ReclamationLogsResponse(
            reclamation_id=reclamation_id,
            logs=processing_logs,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting reclamation logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /{reclamation_id}/tracking - Get Tracking Events
# =============================================================================

@router.get("/{reclamation_id}/tracking", response_model=list[schemas.TrackingEventResponse])
async def get_reclamation_tracking(
    reclamation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get tracking events for a reclamation's numero_suivi."""
    try:
        # Get the reclamation to find the numero_suivi
        reclamation_query = select(models.Reclamation).where(
            models.Reclamation.id == reclamation_id
        )
        reclamation_result = await db.execute(reclamation_query)
        reclamation = reclamation_result.scalar_one_or_none()

        if not reclamation:
            raise HTTPException(status_code=404, detail="Reclamation not found")

        # Get tracking events by numero_suivi
        tracking_query = (
            select(models.TrackingEvent)
            .where(models.TrackingEvent.numero_suivi == reclamation.numero_suivi)
            .order_by(models.TrackingEvent.event_date.desc())
        )
        result = await db.execute(tracking_query)
        events = result.scalars().all()

        return [schemas.TrackingEventResponse.model_validate(e) for e in events]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tracking events: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /{reclamation_id}/document/view - View reclamation document
# =============================================================================

@router.get("/{reclamation_id}/document/view")
async def view_reclamation_document(
    reclamation_id: str,
    lang: str = Query("fr", regex="^(fr|en)$"),
    db: AsyncSession = Depends(get_db),
):
    """View reclamation document PDF. Serves FR or EN version based on lang param."""
    try:
        # Look up reclamation by UUID or reclamation_number
        try:
            rec_uuid = UUID(reclamation_id)
            result = await db.execute(
                select(models.Reclamation).where(models.Reclamation.id == rec_uuid)
            )
        except ValueError:
            result = await db.execute(
                select(models.Reclamation).where(
                    models.Reclamation.reclamation_number == reclamation_id
                )
            )
        reclamation = result.scalar_one_or_none()

        if not reclamation:
            raise HTTPException(status_code=404, detail="Reclamation not found")

        # Determine which document path to use based on language
        metadata = reclamation.reclamation_metadata or {}
        if lang == "en" and metadata.get("document_path_en"):
            doc_path = metadata["document_path_en"]
        elif reclamation.document_path:
            doc_path = reclamation.document_path
        else:
            raise HTTPException(
                status_code=404, detail="No document associated with this reclamation"
            )

        # Fetch document from LlamaStack or local filesystem
        doc = get_document(
            reclamation.reclamation_number, fallback_path=doc_path
        )
        if not doc:
            logger.error(f"Document not found for reclamation {reclamation_id}")
            raise HTTPException(status_code=404, detail="Document file not found")

        data, filename = doc

        max_size = settings.max_upload_size_mb * 1024 * 1024
        if len(data) > max_size:
            raise HTTPException(status_code=413, detail="Document file too large")

        return Response(
            content=data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{filename}"'
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error viewing document for reclamation {reclamation_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error")
