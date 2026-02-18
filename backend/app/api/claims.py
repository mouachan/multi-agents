"""
Claims API endpoints.

Endpoints:
- GET    /                        - List claims with pagination
- GET    /{claim_id}              - Get a specific claim
- POST   /                        - Create a new claim
- POST   /{claim_id}/process      - Process a claim with LlamaStack agent
- GET    /{claim_id}/status       - Get claim processing status
- GET    /{claim_id}/decision     - Get claim decision
- GET    /{claim_id}/logs         - Get processing logs
- GET    /statistics/overview     - Get claims statistics
- GET    /documents/{claim_id}/view - View claim document
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.api import schemas
from app.core.config import settings
from app.core.database import get_db
from app.models import claim as models
from app.llamastack.prompts import (
    CLAIMS_PROCESSING_AGENT_INSTRUCTIONS,
    USER_MESSAGE_FULL_WORKFLOW_TEMPLATE,
    AGENT_CONFIG,
    format_prompt
)
from app.services.claim_service import ClaimService
from app.api.hitl import notify_manual_review_required

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service
claim_service = ClaimService()


# =============================================================================
# GET / - List Claims
# =============================================================================

@router.get("/", response_model=schemas.ClaimListResponse)
async def list_claims(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    include_archived: bool = Query(default=False),
    db: AsyncSession = Depends(get_db)
):
    """List claims with pagination and optional filtering."""
    try:
        query = select(models.Claim)

        # Filter out archived claims by default
        if not include_archived:
            query = query.where(models.Claim.is_archived == False)

        if status:
            query = query.where(models.Claim.status == status)
        if user_id:
            query = query.where(models.Claim.user_id == user_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = (
            query
            .order_by(models.Claim.submitted_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await db.execute(query)
        claims = result.scalars().all()

        return schemas.ClaimListResponse(
            claims=[schemas.ClaimResponse.model_validate(c) for c in claims],
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Error listing claims: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /{claim_id} - Get Claim
# =============================================================================

@router.get("/{claim_id}", response_model=schemas.ClaimResponse)
async def get_claim(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific claim by ID."""
    try:
        query = select(models.Claim).where(models.Claim.id == claim_id)
        result = await db.execute(query)
        claim = result.scalar_one_or_none()

        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")

        return schemas.ClaimResponse.model_validate(claim)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting claim: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# POST / - Create Claim
# =============================================================================

@router.post("/", response_model=schemas.ClaimResponse, status_code=201)
async def create_claim(
    claim_data: schemas.ClaimCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new claim."""
    try:
        new_claim = models.Claim(**claim_data.model_dump())
        db.add(new_claim)
        await db.commit()
        await db.refresh(new_claim)

        logger.info(f"Created new claim: {new_claim.id}")
        return schemas.ClaimResponse.model_validate(new_claim)

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating claim: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# POST /{claim_id}/process - Process Claim with LlamaStack Agent
# =============================================================================

@router.post("/{claim_id}/process", response_model=schemas.ProcessClaimResponse)
async def process_claim(
    claim_id: UUID,
    process_request: schemas.ProcessClaimRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Process a claim using LlamaStack ReActAgent.

    The agent will:
    1. Extract document info via OCR
    2. Retrieve user contracts via RAG
    3. Find similar historical claims
    4. Make a decision (approve/deny/manual_review)
    """
    try:
        # Get and validate claim
        claim = await claim_service.get_claim_by_id(db, str(claim_id))
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")

        # If claim is already being processed, return 202 Accepted instead of 409 error
        if claim.status == models.ClaimStatus.processing:
            return Response(
                status_code=202,
                content=json.dumps({
                    "claim_id": str(claim_id),
                    "status": "processing",
                    "message": "Claim is already being processed. Please wait for completion.",
                    "processing_started_at": claim.updated_at.isoformat() if claim.updated_at else None
                }),
                media_type="application/json"
            )

        # Build tool list for Responses API
        tools = []
        if not process_request.skip_ocr:
            tools.append("ocr_document")
        if process_request.enable_rag:
            tools.extend([
                "retrieve_user_info",
                "retrieve_similar_claims",
                "search_knowledge_base"
            ])

        agent_config = {
            "model": settings.llamastack_default_model,
            "instructions": CLAIMS_PROCESSING_AGENT_INSTRUCTIONS,
        }
        # Note: We don't add shield_ids here because that would block processing
        # Instead, we check for PII after processing and log detections

        # Process claim with agent service
        result = await claim_service.process_claim_with_agent(
            db=db,
            claim_id=str(claim_id),
            agent_config=agent_config,
            tools=tools
        )

        # Save decision
        await claim_service.save_decision(
            db=db,
            claim_id=str(claim_id),
            decision_data=result["decision"]
        )

        # Check for PII in claim content if enabled (log only, don't block)
        if settings.enable_pii_detection:
            logger.info(f"PII detection enabled, checking claim {claim_id}")
            try:
                # Collect all text to check for PII
                texts_to_check = []

                # 1. Get OCR content
                ocr_query = select(models.ClaimDocument).where(
                    models.ClaimDocument.claim_id == claim_id
                ).order_by(models.ClaimDocument.created_at.desc()).limit(1)
                ocr_result = await db.execute(ocr_query)
                claim_doc = ocr_result.scalar_one_or_none()

                if claim_doc and claim_doc.raw_ocr_text:
                    texts_to_check.append(f"OCR Document: {claim_doc.raw_ocr_text}")
                    logger.info(f"Added OCR text for PII check: {len(claim_doc.raw_ocr_text)} chars")

                # 2. Extract data from tool calls (RAG user info, etc.)
                tool_calls = result.get('tool_calls', [])
                logger.info(f"Found {len(tool_calls)} tool calls to check for PII")
                for tc in tool_calls:
                    if tc.get('name') == 'retrieve_user_info' and tc.get('output'):
                        try:
                            import json as json_lib
                            output_data = json_lib.loads(tc['output'])
                            if output_data.get('success') and output_data.get('user_info'):
                                user_info = output_data['user_info']
                                # Build text with user PII data
                                user_text = f"User: {user_info.get('full_name', '')} Email: {user_info.get('email', '')} Phone: {user_info.get('phone_number', '')} DOB: {user_info.get('date_of_birth', '')}"
                                texts_to_check.append(user_text)
                                logger.info(f"Added user info for PII check: {user_text}")
                        except Exception as e:
                            logger.warning(f"Error parsing user info for PII check: {e}")

                # Combine all texts
                combined_text = "\n".join(texts_to_check)
                logger.info(f"Checking combined text for PII: {len(combined_text)} chars total")

                if combined_text:
                    # Check for PII using shield
                    pii_result = await claim_service.check_pii_shield(
                        text=combined_text,
                        claim_id=str(claim_id)
                    )

                    # If PII detected, save detections with source info
                    if pii_result.get("violations_found"):
                        detections = pii_result.get("detections", [])
                        # Enrich detections with source information
                        for detection in detections:
                            detection["source_step"] = "retrieve_user_info (RAG)"
                            detection["detected_fields"] = ["email", "phone", "date_of_birth"]

                        await claim_service.save_pii_detections(
                            db=db,
                            claim_id=str(claim_id),
                            detections=detections
                        )
                        logger.info(f"PII detected in claim {claim_id}: {len(detections)} violations logged")
            except Exception as e:
                # Don't fail the whole request if PII check fails
                logger.error(f"Error checking PII for claim {claim_id}: {e}", exc_info=True)

        # Notify reviewers if manual review required
        recommendation = result["decision"].get("recommendation", "manual_review")
        if recommendation == "manual_review":
            reasoning = result["decision"].get("reasoning", "Agent could not make automated decision")
            await notify_manual_review_required(claim_id, reasoning)

        return schemas.ProcessClaimResponse(
            claim_id=claim_id,
            status=result["claim_status"],
            message=f"Processing completed: {recommendation}",
            processing_started_at=claim.submitted_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing claim {claim_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /{claim_id}/status - Get Claim Status
# =============================================================================

@router.get("/{claim_id}/status", response_model=schemas.ClaimStatusResponse)
async def get_claim_status(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get the current processing status of a claim."""
    try:
        claim_query = select(models.Claim).where(models.Claim.id == claim_id)
        claim_result = await db.execute(claim_query)
        claim = claim_result.scalar_one_or_none()

        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")

        # Read processing steps from claim metadata (saved during processing)
        processing_steps = []
        current_step = None
        progress = 0.0

        if claim.claim_metadata and 'processing_steps' in claim.claim_metadata:
            # Read processing steps from claim metadata
            saved_steps = claim.claim_metadata['processing_steps']
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

        # Determine progress - Check claim status first
        if claim.status in [models.ClaimStatus.completed, models.ClaimStatus.failed, models.ClaimStatus.manual_review]:
            progress = 100.0
        elif processing_steps:
            current_step = processing_steps[-1].step_name
            # Map actual tool names to progress percentages
            step_progress = {
                "ocr_extract_claim_info": 25,
                "retrieve_user_info": 50,
                "search_knowledge_base": 75,
                "retrieve_similar_claims": 75,
                "ocr": 25,
                "rag_retrieval": 75,
                "llm_decision": 100
            }
            progress = step_progress.get(current_step, 50)
        else:
            progress = 0.0

        return schemas.ClaimStatusResponse(
            claim_id=claim_id,
            status=claim.status,
            current_step=current_step,
            progress_percentage=progress,
            processing_steps=processing_steps,
            estimated_completion_time=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting claim status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /{claim_id}/decision - Get Claim Decision
# =============================================================================

@router.get("/{claim_id}/decision", response_model=schemas.ClaimDecisionResponse)
async def get_claim_decision(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get the decision details for a processed claim."""
    try:
        query = (
            select(models.ClaimDecision)
            .where(models.ClaimDecision.claim_id == claim_id)
            .order_by(models.ClaimDecision.created_at.desc())
        )
        result = await db.execute(query)
        decision = result.scalar_one_or_none()

        if not decision:
            raise HTTPException(status_code=404, detail="No decision found for this claim")

        return schemas.ClaimDecisionResponse(
            id=decision.id,
            claim_id=decision.claim_id,
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
            # Supporting data
            relevant_policies=decision.relevant_policies,
            similar_claims=decision.similar_claims,
            user_contract_info=decision.user_contract_info,
            llm_model=decision.llm_model,
            requires_manual_review=decision.requires_manual_review,
            decided_at=decision.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting claim decision: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /{claim_id}/logs - Get Claim Logs
# =============================================================================

@router.get("/{claim_id}/logs", response_model=schemas.ClaimLogsResponse)
async def get_claim_logs(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get processing logs for a claim from LlamaStack session history."""
    try:
        # Get claim to check metadata
        claim_query = select(models.Claim).where(models.Claim.id == claim_id)
        claim_result = await db.execute(claim_query)
        claim = claim_result.scalar_one_or_none()

        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")

        processing_logs = []

        # Read processing steps from claim metadata (saved during processing)
        if claim.claim_metadata and 'processing_steps' in claim.claim_metadata:
            saved_steps = claim.claim_metadata['processing_steps']
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

        return schemas.ClaimLogsResponse(
            claim_id=claim_id,
            logs=processing_logs
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting claim logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /statistics/overview - Get Claims Statistics
# =============================================================================

@router.get("/statistics/overview", response_model=schemas.ClaimStatistics)
async def get_claim_statistics(db: AsyncSession = Depends(get_db)):
    """Get overall claims statistics."""
    try:
        status_counts = {}
        status_values = ["pending", "processing", "completed", "failed", "manual_review"]
        
        for status_value in status_values:
            query = select(func.count()).where(models.Claim.status == status_value)
            result = await db.execute(query)
            status_counts[status_value] = result.scalar() or 0

        avg_query = select(func.avg(models.Claim.total_processing_time_ms)).where(
            models.Claim.total_processing_time_ms.isnot(None)
        )
        avg_result = await db.execute(avg_query)
        avg_processing_time = avg_result.scalar()

        return schemas.ClaimStatistics(
            total_claims=sum(status_counts.values()),
            pending_claims=status_counts.get("pending", 0),
            processing_claims=status_counts.get("processing", 0),
            completed_claims=status_counts.get("completed", 0),
            failed_claims=status_counts.get("failed", 0),
            manual_review_claims=status_counts.get("manual_review", 0),
            average_processing_time_ms=avg_processing_time
        )

    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /{claim_id}/guardrails - Get Guardrails Detections
# =============================================================================

@router.get("/{claim_id}/guardrails", response_model=schemas.GuardrailsDetectionsListResponse)
async def get_guardrails_detections(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get guardrails PII/safety detections for a claim."""
    try:
        # Verify claim exists
        claim_query = select(models.Claim).where(models.Claim.id == claim_id)
        claim_result = await db.execute(claim_query)
        claim = claim_result.scalar_one_or_none()

        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")

        # Get all guardrails detections
        detections_query = (
            select(models.GuardrailsDetection)
            .where(models.GuardrailsDetection.claim_id == claim_id)
            .order_by(models.GuardrailsDetection.detected_at.desc())
        )
        result = await db.execute(detections_query)
        detections = result.scalars().all()

        return schemas.GuardrailsDetectionsListResponse(
            claim_id=claim_id,
            detections=[schemas.GuardrailsDetectionResponse.model_validate(d) for d in detections],
            total=len(detections)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting guardrails detections: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /documents/{claim_id}/view - View Claim Document
# =============================================================================

@router.get("/documents/{claim_id}/view")
async def view_claim_document(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """View claim document PDF."""
    try:
        result = await db.execute(
            select(models.Claim).where(models.Claim.id == claim_id)
        )
        claim = result.scalar_one_or_none()

        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")

        if not claim.document_path:
            raise HTTPException(status_code=404, detail="No document associated with this claim")

        if not os.path.exists(claim.document_path):
            raise HTTPException(status_code=404, detail="Document file not found")

        return FileResponse(
            claim.document_path,
            media_type="application/pdf",
            filename=os.path.basename(claim.document_path)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))