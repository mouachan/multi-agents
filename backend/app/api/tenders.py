"""
Tenders (Appels d'Offres) API endpoints.

Endpoints:
- GET    /                        - List tenders with pagination
- GET    /{tender_id}             - Get a specific tender
- POST   /                        - Create a new tender
- POST   /{tender_id}/process     - Process a tender with AO agent
- GET    /{tender_id}/status      - Get tender processing status
- GET    /{tender_id}/decision    - Get Go/No-Go decision
- GET    /{tender_id}/logs        - Get processing logs
- GET    /statistics/overview     - Get tender statistics
- GET    /documents/{tender_id}/view - View tender document
"""

import json
import logging
import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import ao_schemas as schemas
from app.core.config import settings
from app.core.database import get_db
from app.models import tender as models
from app.llamastack.ao_prompts import AO_PROCESSING_AGENT_INSTRUCTIONS
from app.services.tender_service import TenderService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service
tender_service = TenderService()


# =============================================================================
# GET / - List Tenders
# =============================================================================

@router.get("/", response_model=schemas.TenderListResponse)
async def list_tenders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    entity_id: Optional[str] = Query(default=None),
    include_archived: bool = Query(default=False),
    db: AsyncSession = Depends(get_db)
):
    """List tenders with pagination and optional filtering."""
    try:
        query = select(models.Tender)

        # Filter out archived tenders by default
        if not include_archived:
            query = query.where(models.Tender.is_archived == False)

        if status:
            query = query.where(models.Tender.status == status)
        if entity_id:
            query = query.where(models.Tender.entity_id == entity_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = (
            query
            .order_by(models.Tender.submitted_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await db.execute(query)
        tenders = result.scalars().all()

        return schemas.TenderListResponse(
            tenders=[schemas.TenderResponse.model_validate(t) for t in tenders],
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Error listing tenders: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /{tender_id} - Get Tender
# =============================================================================

@router.get("/{tender_id}", response_model=schemas.TenderResponse)
async def get_tender(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific tender by ID."""
    try:
        query = select(models.Tender).where(models.Tender.id == tender_id)
        result = await db.execute(query)
        tender = result.scalar_one_or_none()

        if not tender:
            raise HTTPException(status_code=404, detail="Tender not found")

        return schemas.TenderResponse.model_validate(tender)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tender: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# POST / - Create Tender
# =============================================================================

@router.post("/", response_model=schemas.TenderResponse, status_code=201)
async def create_tender(
    tender_data: schemas.TenderCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new tender."""
    try:
        new_tender = models.Tender(**tender_data.model_dump())
        db.add(new_tender)
        await db.commit()
        await db.refresh(new_tender)

        logger.info(f"Created new tender: {new_tender.id}")
        return schemas.TenderResponse.model_validate(new_tender)

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating tender: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# POST /{tender_id}/process - Process Tender with AO Agent
# =============================================================================

@router.post("/{tender_id}/process", response_model=schemas.ProcessTenderResponse)
async def process_tender(
    tender_id: UUID,
    process_request: schemas.ProcessTenderRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Process a tender using LlamaStack ReActAgent.

    The agent will:
    1. Extract document info via OCR
    2. Retrieve similar past project references
    3. Retrieve historical tender win/loss data
    4. Retrieve internal capabilities (certifications, equipment, teams)
    5. Make a Go/No-Go decision
    """
    try:
        # Get and validate tender
        tender = await tender_service.get_tender_by_id(db, str(tender_id))
        if not tender:
            raise HTTPException(status_code=404, detail="Tender not found")

        # If tender is already being processed, return 202 Accepted instead of 409 error
        if tender.status == models.TenderStatus.processing:
            return Response(
                status_code=202,
                content=json.dumps({
                    "tender_id": str(tender_id),
                    "status": "processing",
                    "message": "Tender is already being processed. Please wait for completion.",
                    "processing_started_at": tender.updated_at.isoformat() if tender.updated_at else None
                }),
                media_type="application/json"
            )

        # Build tool list for Responses API
        tools = []
        if not process_request.skip_ocr:
            tools.append("ocr_document")
        if process_request.enable_rag:
            tools.extend([
                "retrieve_similar_references",
                "retrieve_historical_tenders",
                "retrieve_capabilities"
            ])

        agent_config = {
            "model": settings.llamastack_default_model,
            "instructions": AO_PROCESSING_AGENT_INSTRUCTIONS,
        }

        # Process tender with agent service
        result = await tender_service.process_tender_with_agent(
            db=db,
            tender_id=str(tender_id),
            agent_config=agent_config,
            tools=tools
        )

        # Save decision
        await tender_service.save_decision(
            db=db,
            tender_id=str(tender_id),
            decision_data=result["decision"]
        )

        recommendation = result["decision"].get("recommendation", "a_approfondir")

        return schemas.ProcessTenderResponse(
            tender_id=tender_id,
            status=result["tender_status"],
            message=f"Processing completed: {recommendation}",
            processing_started_at=tender.submitted_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing tender {tender_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /{tender_id}/status - Get Tender Status
# =============================================================================

@router.get("/{tender_id}/status", response_model=schemas.TenderStatusResponse)
async def get_tender_status(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get the current processing status of a tender."""
    try:
        tender_query = select(models.Tender).where(models.Tender.id == tender_id)
        tender_result = await db.execute(tender_query)
        tender = tender_result.scalar_one_or_none()

        if not tender:
            raise HTTPException(status_code=404, detail="Tender not found")

        # Read processing steps from tender metadata (saved during processing)
        processing_steps = []
        current_step = None
        progress = 0.0

        if tender.tender_metadata and 'processing_steps' in tender.tender_metadata:
            # Read processing steps from tender metadata
            saved_steps = tender.tender_metadata['processing_steps']
            for step in saved_steps:
                processing_steps.append(schemas.ProcessingStepLog(
                    step_name=step.get('step_name', 'unknown'),
                    agent_name=step.get('agent_name', 'unknown'),
                    status=step.get('status', 'completed'),
                    duration_ms=step.get('duration_ms'),
                    started_at=None,
                    completed_at=None,
                    output_data=step.get('output_data'),
                    error_message=step.get('error_message')
                ))

        # Determine progress - Check tender status first
        if tender.status in [models.TenderStatus.completed, models.TenderStatus.failed, models.TenderStatus.manual_review]:
            progress = 100.0
        elif processing_steps:
            current_step = processing_steps[-1].step_name
            # Map actual tool names to progress percentages
            step_progress = {
                "ocr_document": 20,
                "retrieve_similar_references": 40,
                "retrieve_historical_tenders": 60,
                "retrieve_capabilities": 80,
                "ocr": 20,
                "rag_retrieval": 60,
                "llm_decision": 100
            }
            progress = step_progress.get(current_step, 50)
        else:
            progress = 0.0

        return schemas.TenderStatusResponse(
            tender_id=tender_id,
            status=tender.status,
            current_step=current_step,
            progress_percentage=progress,
            processing_steps=processing_steps,
            estimated_completion_time=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tender status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /{tender_id}/decision - Get Go/No-Go Decision
# =============================================================================

@router.get("/{tender_id}/decision", response_model=schemas.TenderDecisionResponse)
async def get_tender_decision(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get the Go/No-Go decision details for a processed tender."""
    try:
        query = (
            select(models.TenderDecision)
            .where(models.TenderDecision.tender_id == tender_id)
            .order_by(models.TenderDecision.created_at.desc())
        )
        result = await db.execute(query)
        decision = result.scalar_one_or_none()

        if not decision:
            raise HTTPException(status_code=404, detail="No decision found for this tender")

        return schemas.TenderDecisionResponse(
            id=decision.id,
            tender_id=decision.tender_id,
            # Initial system decision
            initial_decision=decision.initial_decision.value,
            initial_confidence=decision.initial_confidence,
            initial_reasoning=decision.initial_reasoning,
            initial_decided_at=decision.initial_decided_at,
            # Final reviewer decision
            final_decision=decision.final_decision.value if decision.final_decision else None,
            final_decision_by=decision.final_decision_by,
            final_decision_by_name=decision.final_decision_by_name,
            final_decision_at=decision.final_decision_at,
            final_decision_notes=decision.final_decision_notes,
            # Legacy fields for backwards compatibility
            decision=decision.decision.value,
            confidence=decision.confidence,
            reasoning=decision.reasoning,
            # Supporting analysis
            risk_analysis=decision.risk_analysis,
            similar_references=decision.similar_references,
            historical_ao_analysis=decision.historical_ao_analysis,
            internal_capabilities=decision.internal_capabilities,
            llm_model=decision.llm_model,
            requires_manual_review=decision.requires_manual_review,
            decided_at=decision.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tender decision: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /{tender_id}/logs - Get Tender Logs
# =============================================================================

@router.get("/{tender_id}/logs", response_model=schemas.TenderLogsResponse)
async def get_tender_logs(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get processing logs for a tender from LlamaStack session history."""
    try:
        # Get tender to check metadata
        tender_query = select(models.Tender).where(models.Tender.id == tender_id)
        tender_result = await db.execute(tender_query)
        tender = tender_result.scalar_one_or_none()

        if not tender:
            raise HTTPException(status_code=404, detail="Tender not found")

        processing_logs = []

        # Read processing steps from tender metadata (saved during processing)
        if tender.tender_metadata and 'processing_steps' in tender.tender_metadata:
            saved_steps = tender.tender_metadata['processing_steps']
            for step in saved_steps:
                processing_logs.append(schemas.ProcessingStepLog(
                    step_name=step.get('step_name', 'unknown'),
                    agent_name=step.get('agent_name', 'unknown'),
                    status=step.get('status', 'completed'),
                    duration_ms=step.get('duration_ms'),
                    started_at=None,
                    completed_at=None,
                    output_data=step.get('output_data'),
                    error_message=step.get('error_message')
                ))

        return schemas.TenderLogsResponse(
            tender_id=tender_id,
            logs=processing_logs
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tender logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /statistics/overview - Get Tender Statistics
# =============================================================================

@router.get("/statistics/overview", response_model=schemas.TenderStatistics)
async def get_tender_statistics(db: AsyncSession = Depends(get_db)):
    """Get overall tender statistics."""
    try:
        status_counts = {}
        status_values = ["pending", "processing", "completed", "failed", "manual_review", "pending_info"]

        for status_value in status_values:
            query = select(func.count()).where(models.Tender.status == status_value)
            result = await db.execute(query)
            status_counts[status_value] = result.scalar() or 0

        avg_query = select(func.avg(models.Tender.total_processing_time_ms)).where(
            models.Tender.total_processing_time_ms.isnot(None)
        )
        avg_result = await db.execute(avg_query)
        avg_processing_time = avg_result.scalar()

        return schemas.TenderStatistics(
            total_tenders=sum(status_counts.values()),
            pending_tenders=status_counts.get("pending", 0),
            processing_tenders=status_counts.get("processing", 0),
            completed_tenders=status_counts.get("completed", 0),
            failed_tenders=status_counts.get("failed", 0),
            manual_review_tenders=status_counts.get("manual_review", 0),
            pending_info_tenders=status_counts.get("pending_info", 0),
            average_processing_time_ms=avg_processing_time
        )

    except Exception as e:
        logger.error(f"Error getting tender statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /documents/{tender_id}/view - View Tender Document
# =============================================================================

@router.get("/documents/{tender_id}/view")
async def view_tender_document(
    tender_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """View tender document PDF."""
    try:
        result = await db.execute(
            select(models.Tender).where(models.Tender.id == tender_id)
        )
        tender = result.scalar_one_or_none()

        if not tender:
            raise HTTPException(status_code=404, detail="Tender not found")

        if not tender.document_path:
            raise HTTPException(status_code=404, detail="No document associated with this tender")

        if not os.path.exists(tender.document_path):
            raise HTTPException(status_code=404, detail="Document file not found")

        return FileResponse(
            tender.document_path,
            media_type="application/pdf",
            filename=os.path.basename(tender.document_path)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing tender document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
