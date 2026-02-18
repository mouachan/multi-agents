#!/usr/bin/env python3
"""
Generate embeddings for knowledge_base and claim_documents.
Strategy:
- KB: All 15 entries
- Claims: 90 new claim_documents
  - 80 with full OCR (~300-500 chars)
  - 10 with short OCR (<50 chars) for MANUAL_REVIEW
"""
import asyncio
import logging
import os
import sys
from typing import List, Optional
import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgresql.claims-demo.svc.cluster.local")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DATABASE", "claims_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "claims_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
LLAMASTACK_ENDPOINT = os.getenv("LLAMASTACK_ENDPOINT", "http://llamastack-rhoai-service.claims-demo.svc.cluster.local:8321")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemma-300m")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# OCR templates
OCR_TEMPLATES = {
    "Auto": [
        "Vehicle damage claim. Accident date: 2025-11-15. Driver: {name}. Vehicle: 2020 Toyota Camry. Damage: Front bumper and hood. Estimated repair: $4,500. Police report #: 2025-11-15-0042. Witness: Available. Photos: Attached.",
        "Auto insurance claim for collision. Date of incident: 2025-10-20. Insured: {name}. Vehicle make/model: Honda Accord 2019. Location: Intersection of Main St and 5th Ave. Other party involved: Yes. Damage assessment: $6,200.",
        "Car accident claim filed 2025-12-01. Policyholder: {name}. Vehicle: Ford F-150 2021. Type of damage: Rear-end collision. Est. repair cost: $3,800. Towing required: Yes. Rental car needed during repair.",
    ],
    "Home": [
        "Home insurance claim for water damage. Property owner: {name}. Address: 123 Oak Street. Date of loss: 2025-11-10. Cause: Burst pipe in basement. Affected areas: Basement, first floor. Estimated damages: $12,000. Emergency repairs completed.",
        "Property damage claim. Homeowner: {name}. Incident date: 2025-10-25. Type: Wind damage to roof. Shingles blown off, water intrusion. Contractor estimate: $8,500. Temporary repairs: Completed. Photos: Available.",
        "Residential claim submitted 2025-12-05. Owner: {name}. Property location: 456 Elm Ave. Damage type: Fire in kitchen. Extent: Kitchen cabinets, appliances, smoke damage throughout. Loss estimate: $25,000.",
    ],
    "Medical": [
        "Medical insurance claim. Patient: {name}. Date of service: 2025-11-20. Provider: City General Hospital. Diagnosis: Appendectomy. Total charges: $18,500. Pre-authorization: Obtained. Hospital stay: 2 days.",
        "Healthcare claim submission. Insured: {name}. Service date: 2025-10-15. Treatment: MRI scan and specialist consultation. Facility: Metro Medical Center. Billed amount: $3,200. Physician referral: Yes.",
        "Health insurance claim for emergency room visit. Patient name: {name}. ER admission: 2025-12-01 11:30 PM. Chief complaint: Severe abdominal pain. Treatment provided: CT scan, pain management. Charges: $5,600.",
    ]
}

# Short OCR for MANUAL_REVIEW (insufficient information)
SHORT_OCR_TEMPLATE = "Claim document for {name}. Date: {date}. Damage noted."

async def create_embedding(text: str, client: httpx.AsyncClient) -> Optional[List[float]]:
    """Create embedding using LlamaStack API."""
    try:
        response = await client.post(
            f"{LLAMASTACK_ENDPOINT}/v1/embeddings",
            json={"model": EMBEDDING_MODEL, "input": text.strip()},
            timeout=60.0
        )
        response.raise_for_status()
        result = response.json()

        if "data" not in result or len(result["data"]) == 0:
            logger.error(f"Invalid embedding response: {result}")
            return None

        embedding = result["data"][0].get("embedding")
        if not embedding:
            return None

        logger.debug(f"Created embedding with dimension: {len(embedding)}")
        return embedding
    except Exception as e:
        logger.error(f"Error creating embedding: {e}")
        return None

def format_embedding(embedding: List[float]) -> str:
    """Format embedding for PostgreSQL pgvector."""
    return '[' + ','.join(str(x) for x in embedding) + ']'

async def generate_kb_embeddings(session_maker):
    """Generate embeddings for knowledge_base."""
    logger.info("=== Generating Knowledge Base Embeddings ===")

    with session_maker() as session:
        query = text("SELECT CAST(id AS text) as id, title, content FROM knowledge_base WHERE embedding IS NULL")
        result = session.execute(query).fetchall()
        kb_entries = [(row.id, row.title, row.content) for row in result]

    if not kb_entries:
        logger.info("No knowledge base entries need embeddings")
        return 0

    logger.info(f"Found {len(kb_entries)} KB entries without embeddings")

    async with httpx.AsyncClient() as client:
        generated = 0
        for kb_id, title, content in kb_entries:
            text_to_embed = f"{title}\n\n{content}"[:2000]
            logger.info(f"  Generating embedding for: {title}")

            embedding = await create_embedding(text_to_embed, client)
            if embedding:
                with session_maker() as session:
                    update_query = text("""
                        UPDATE knowledge_base
                        SET embedding = CAST(:embedding AS vector)
                        WHERE CAST(id AS text) = :kb_id
                    """)
                    session.execute(update_query, {
                        "embedding": format_embedding(embedding),
                        "kb_id": kb_id
                    })
                    session.commit()
                    generated += 1
                    logger.info(f"    ✅ Updated ({generated}/{len(kb_entries)})")
            else:
                logger.error(f"    ❌ Failed to generate embedding")

            await asyncio.sleep(0.5)

    logger.info(f"✅ KB Embeddings: {generated}/{len(kb_entries)} generated")
    return generated

async def generate_claim_documents(session_maker):
    """Create claim_documents with OCR and embeddings."""
    logger.info("=== Generating Claim Documents ===")

    # Get claims without documents
    with session_maker() as session:
        query = text("""
            SELECT
                CAST(c.id AS text) as claim_id,
                c.claim_number,
                c.claim_type,
                c.document_path,
                u.full_name
            FROM claims c
            LEFT JOIN claim_documents cd ON c.id = cd.claim_id
            JOIN users u ON c.user_id = u.user_id
            WHERE cd.id IS NULL
            ORDER BY c.claim_number
        """)
        result = session.execute(query).fetchall()
        claims = [(row.claim_id, row.claim_number, row.claim_type, row.document_path, row.full_name) for row in result]

    if not claims:
        logger.info("No claims need documents")
        return 0, 0

    logger.info(f"Found {len(claims)} claims without documents")

    # Identify claims for short OCR (MANUAL_REVIEW scenario)
    short_ocr_claims = [
        "CLM-2024-0020", "CLM-2024-0044", "CLM-2024-0057",
        "CLM-2024-0074", "CLM-2024-0075", "CLM-2024-0076",
        "CLM-2024-0088", "CLM-2024-0089", "CLM-2024-0096",
        "CLM-2024-0098"
    ]

    async with httpx.AsyncClient() as client:
        full_ocr_count = 0
        short_ocr_count = 0

        for idx, (claim_id, claim_number, claim_type, doc_path, full_name) in enumerate(claims):
            is_short = claim_number in short_ocr_claims

            # Generate OCR text
            if is_short:
                ocr_text = SHORT_OCR_TEMPLATE.format(name=full_name, date="2025-12")
                short_ocr_count += 1
                logger.info(f"  [{idx+1}/{len(claims)}] {claim_number} - SHORT OCR for MANUAL_REVIEW")
            else:
                import random
                template = random.choice(OCR_TEMPLATES.get(claim_type, OCR_TEMPLATES["Auto"]))
                ocr_text = template.format(name=full_name)
                full_ocr_count += 1
                logger.info(f"  [{idx+1}/{len(claims)}] {claim_number} - FULL OCR")

            # Generate embedding
            embedding = await create_embedding(ocr_text, client)
            if not embedding:
                logger.error(f"    ❌ Failed to generate embedding for {claim_number}")
                continue

            # Insert claim_document
            with session_maker() as session:
                insert_query = text("""
                    INSERT INTO claim_documents (
                        claim_id, document_type, file_path,
                        raw_ocr_text, ocr_confidence, embedding,
                        created_at, updated_at
                    ) VALUES (
                        CAST(:claim_id AS uuid), :doc_type, :file_path,
                        :ocr_text, :confidence, CAST(:embedding AS vector),
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """)
                session.execute(insert_query, {
                    "claim_id": claim_id,
                    "doc_type": claim_type,
                    "file_path": doc_path,
                    "ocr_text": ocr_text,
                    "confidence": 0.95 if not is_short else 0.60,
                    "embedding": format_embedding(embedding)
                })
                session.commit()
                logger.info(f"    ✅ Document created with embedding")

            await asyncio.sleep(0.3)

    logger.info(f"✅ Claim Documents: {len(claims)} total ({full_ocr_count} full, {short_ocr_count} short)")
    return full_ocr_count, short_ocr_count

async def main():
    logger.info("Starting embedding generation...")
    logger.info(f"LlamaStack: {LLAMASTACK_ENDPOINT}")
    logger.info(f"Model: {EMBEDDING_MODEL}")
    logger.info(f"Database: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)

    try:
        # Step 1: KB embeddings
        kb_count = await generate_kb_embeddings(SessionLocal)

        # Step 2: Claim documents + embeddings
        full_count, short_count = await generate_claim_documents(SessionLocal)

        logger.info("\n" + "="*60)
        logger.info("SUMMARY")
        logger.info("="*60)
        logger.info(f"✅ Knowledge Base embeddings: {kb_count}")
        logger.info(f"✅ Claim documents (full OCR): {full_count}")
        logger.info(f"⚠️  Claim documents (short OCR): {short_count}")
        logger.info(f"✅ Total embeddings generated: {kb_count + full_count + short_count}")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
