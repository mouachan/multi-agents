"""
Kubeflow Pipeline: Complete Data Initialization

Initializes ALL data needed for the claims demo:
1. Knowledge Base embeddings (15 entries)
2. Historical claims with OCR, embeddings, and AI decisions (60 claims)
3. Test claims with realistic scenarios APPROVE/DENY/MANUAL_REVIEW (40 claims)

Author: Claims Demo Team
RHOAI Version: 3.2
"""

from kfp import dsl
from kfp import compiler
from kfp import kubernetes


@dsl.component(
    base_image='registry.access.redhat.com/ubi9/python-312:latest',
    packages_to_install=['httpx==0.27.0', 'sqlalchemy==2.0.36', 'psycopg2-binary==2.9.10']
)
def generate_kb_embeddings(
    workspace_path: str,
    llamastack_endpoint: str,
    embedding_model: str,
    metrics: dsl.Output[dsl.Metrics]
):
    """
    Step 1: Generate Knowledge Base embeddings.

    Reads knowledge_base entries from PostgreSQL and generates 768D embeddings
    for RAG similarity search.

    workspace_path is needed to trigger PVC creation (even if not used).
    """
    import logging
    import os
    import asyncio
    from typing import List, Optional
    import httpx
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Database connection from environment variables (injected from secret)
    postgres_host = os.getenv('POSTGRES_HOST', 'postgresql.claims-demo.svc.cluster.local')
    postgres_port = os.getenv('POSTGRES_PORT', '5432')
    postgres_db = os.getenv('POSTGRES_DATABASE')
    postgres_user = os.getenv('POSTGRES_USER')
    postgres_password = os.getenv('POSTGRES_PASSWORD')

    DATABASE_URL = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

    async def create_embedding(text: str, client: httpx.AsyncClient) -> Optional[List[float]]:
        try:
            response = await client.post(
                f"{llamastack_endpoint}/v1/embeddings",
                json={"model": embedding_model, "input": text.strip()},
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            if "data" in result and len(result["data"]) > 0:
                return result["data"][0].get("embedding")
            return None
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return None

    def format_embedding(embedding: List[float]) -> str:
        return '[' + ','.join(str(x) for x in embedding) + ']'

    async def process():
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=engine)
        kb_count = 0

        async with httpx.AsyncClient() as client:
            logger.info("=== Generating Knowledge Base Embeddings ===")

            with SessionLocal() as session:
                query = text("SELECT CAST(id AS text) as id, title, content FROM knowledge_base WHERE embedding IS NULL")
                kb_entries = [(r.id, r.title, r.content) for r in session.execute(query).fetchall()]

            logger.info(f"Found {len(kb_entries)} KB entries to process")

            for kb_id, title, content in kb_entries:
                text_to_embed = f"{title}\n\n{content}"[:2000]
                logger.info(f"  KB: {title}")

                embedding = await create_embedding(text_to_embed, client)
                if embedding:
                    with SessionLocal() as session:
                        session.execute(
                            text("UPDATE knowledge_base SET embedding = CAST(:emb AS vector) WHERE CAST(id AS text) = :id"),
                            {"emb": format_embedding(embedding), "id": kb_id}
                        )
                        session.commit()
                        kb_count += 1

                await asyncio.sleep(0.5)

        engine.dispose()
        logger.info(f"✅ Knowledge Base embeddings: {kb_count}/{len(kb_entries)}")
        metrics.log_metric("kb_embeddings", kb_count)

    asyncio.run(process())


@dsl.component(
    base_image='registry.access.redhat.com/ubi9/python-312:latest',
    packages_to_install=['reportlab==4.2.5', 'sqlalchemy==2.0.36', 'psycopg2-binary==2.9.10']
)
def generate_realistic_pdfs(
    workspace_path: str,
    num_historical_claims: int,
    metrics: dsl.Output[dsl.Metrics]
):
    """
    Step 2: Generate realistic PDFs from existing claims.

    Reads claims from PostgreSQL and creates PDF files with ReportLab.
    PDFs are saved to the workspace for the next step.
    """
    import logging
    import os
    from datetime import datetime
    from pathlib import Path
    import json

    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Database connection from environment variables (injected from secret)
    postgres_host = os.getenv('POSTGRES_HOST', 'postgresql.claims-demo.svc.cluster.local')
    postgres_port = os.getenv('POSTGRES_PORT', '5432')
    postgres_db = os.getenv('POSTGRES_DATABASE')
    postgres_user = os.getenv('POSTGRES_USER')
    postgres_password = os.getenv('POSTGRES_PASSWORD')

    DATABASE_URL = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

    # Output directory in workspace
    output_dir = Path(workspace_path) / "pdfs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Metadata file for next steps
    metadata_file = Path(workspace_path) / "claims_metadata.json"

    logger.info(f"Generating PDFs to {output_dir}")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)

    # Query to get claims (not claim_documents - those don't exist yet!)
    with SessionLocal() as session:
        query = text("""
            SELECT
                c.id::text as claim_id,
                c.claim_number,
                c.claim_type,
                c.user_id,
                c.document_path
            FROM claims c
            WHERE c.status = 'pending'
            ORDER BY c.submitted_at DESC
            LIMIT :limit
        """)
        claims = session.execute(query, {"limit": num_historical_claims}).fetchall()

    logger.info(f"Found {len(claims)} claims to process")

    generated = 0
    failed = 0
    claims_metadata = []

    # Generate sample OCR text for each claim type
    sample_texts = {
        "Auto": "Vehicle Damage Report\n\nDate of Incident: 2025-12-15\nLocation: Highway 101, Mile Marker 45\n\nDescription: Rear-end collision during heavy traffic. Front bumper damage, headlight broken. Airbags deployed. No injuries reported. Police report filed #2025-12345.",
        "Home": "Property Damage Claim\n\nDate of Loss: 2025-11-20\nProperty Address: 123 Main Street\n\nDescription: Water damage from burst pipe in basement. Affected areas: laundry room, storage area. Damage to flooring, drywall, and personal property. Emergency plumber called. Estimated repair cost: $8,500.",
        "Medical": "Medical Services Claim\n\nPatient Name: John Doe\nDate of Service: 2025-10-05\nProvider: City Medical Center\n\nServices Rendered: Emergency room visit for chest pain. EKG performed, blood tests completed. Diagnosis: Acute gastritis. Treatment: Medication prescribed. Total charges: $2,450.",
        "Life": "Life Insurance Claim\n\nPolicyhold: Jane Smith\nDate of Event: 2025-09-01\n\nDescription: Beneficiary claim for accidental death benefit. Documentation includes death certificate, police report, and medical examiner report. Total benefit amount: $250,000."
    }

    def create_pdf(pdf_path, claim_number, claim_type, claim_text):
        """Create PDF from claim data."""
        doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                               rightMargin=0.75*inch, leftMargin=0.75*inch,
                               topMargin=0.75*inch, bottomMargin=0.75*inch)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=12)

        story = []
        story.append(Paragraph(f"Insurance Claim: {claim_number}", title_style))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"<b>Claim Type:</b> {claim_type}", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("<b>Claim Details:</b>", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(claim_text, styles['Normal']))

        doc.build(story)

    # Process each claim
    for claim in claims:
        claim_id, claim_number, claim_type, user_id, document_path = claim
        pdf_filename = f"{claim_number}.pdf"
        pdf_path = output_dir / pdf_filename

        # Get appropriate sample text
        claim_text = sample_texts.get(claim_type, sample_texts["Auto"])

        try:
            create_pdf(pdf_path, claim_number, claim_type, claim_text)
            generated += 1
            claims_metadata.append({
                "claim_id": claim_id,
                "claim_number": claim_number,
                "claim_type": claim_type,
                "pdf_path": str(pdf_path)
            })
            logger.info(f"Generated PDF {generated}/{len(claims)}: {pdf_filename}")
        except Exception as e:
            logger.error(f"Failed to generate {pdf_filename}: {e}")
            failed += 1

    # Save metadata
    with open(metadata_file, 'w') as f:
        json.dump(claims_metadata, f, indent=2)

    logger.info(f"Successfully generated {generated} PDFs, {failed} failed")
    metrics.log_metric("pdfs_generated", generated)
    metrics.log_metric("pdfs_failed", failed)

    engine.dispose()


@dsl.component(
    base_image='registry.access.redhat.com/ubi9/python-312:latest',
    packages_to_install=['docling==2.18.0', 'sqlalchemy==2.0.36', 'psycopg2-binary==2.9.10']
)
def parse_with_docling(
    workspace_path: str,
    batch_size: int,
    metrics: dsl.Output[dsl.Metrics]
):
    """
    Step 3: Parse PDFs with Docling.

    Uses IBM Docling for advanced PDF parsing and OCR.
    Stores results in claim_documents table.
    """
    import logging
    import os
    import json
    from pathlib import Path

    from docling.document_converter import DocumentConverter
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Database connection from environment variables
    postgres_host = os.getenv('POSTGRES_HOST', 'postgresql.claims-demo.svc.cluster.local')
    postgres_port = os.getenv('POSTGRES_PORT', '5432')
    postgres_db = os.getenv('POSTGRES_DATABASE')
    postgres_user = os.getenv('POSTGRES_USER')
    postgres_password = os.getenv('POSTGRES_PASSWORD')

    DATABASE_URL = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

    # Read metadata
    metadata_file = Path(workspace_path) / "claims_metadata.json"
    with open(metadata_file) as f:
        claims_metadata = json.load(f)

    logger.info(f"Parsing {len(claims_metadata)} PDFs with Docling")

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)
    converter = DocumentConverter()

    parsed = 0
    failed = 0

    for claim_meta in claims_metadata:
        claim_id = claim_meta['claim_id']
        claim_number = claim_meta['claim_number']
        claim_type = claim_meta['claim_type']
        pdf_path = claim_meta['pdf_path']

        if not Path(pdf_path).exists():
            logger.error(f"PDF not found: {pdf_path}")
            failed += 1
            continue

        try:
            # Parse with Docling
            result = converter.convert(pdf_path)
            ocr_text = result.document.export_to_markdown()
            confidence = 0.95

            # Store in claim_documents
            with SessionLocal() as session:
                session.execute(text("""
                    INSERT INTO claim_documents
                    (claim_id, document_type, file_path, raw_ocr_text, ocr_confidence, ocr_processed_at)
                    VALUES (CAST(:claim_id AS uuid), :doc_type, :file_path, :ocr_text, :confidence, NOW())
                """), {
                    "claim_id": claim_id,
                    "doc_type": claim_type,
                    "file_path": pdf_path,
                    "ocr_text": ocr_text,
                    "confidence": confidence
                })
                session.commit()

            parsed += 1
            logger.info(f"Parsed {parsed}/{len(claims_metadata)}: {claim_number}")

        except Exception as e:
            logger.error(f"Failed to parse {claim_number}: {e}")
            failed += 1

    logger.info(f"Successfully parsed {parsed} PDFs, {failed} failed")
    metrics.log_metric("pdfs_parsed", parsed)
    metrics.log_metric("pdfs_parse_failed", failed)

    engine.dispose()


@dsl.component(
    base_image='registry.access.redhat.com/ubi9/python-312:latest',
    packages_to_install=['httpx==0.27.0', 'sqlalchemy==2.0.36', 'psycopg2-binary==2.9.10']
)
def generate_embeddings(
    workspace_path: str,
    llamastack_endpoint: str,
    embedding_model: str,
    batch_size: int,
    metrics: dsl.Output[dsl.Metrics]
):
    """
    Step 4: Generate embeddings for claim_documents.

    Generates 768D embeddings for similarity search.
    """
    import logging
    import os
    import json
    import asyncio
    from pathlib import Path
    from typing import List, Optional
    import httpx
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Database connection
    postgres_host = os.getenv('POSTGRES_HOST', 'postgresql.claims-demo.svc.cluster.local')
    postgres_port = os.getenv('POSTGRES_PORT', '5432')
    postgres_db = os.getenv('POSTGRES_DATABASE')
    postgres_user = os.getenv('POSTGRES_USER')
    postgres_password = os.getenv('POSTGRES_PASSWORD')

    DATABASE_URL = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

    async def create_embedding(text: str, client: httpx.AsyncClient) -> Optional[List[float]]:
        try:
            response = await client.post(
                f"{llamastack_endpoint}/v1/embeddings",
                json={"model": embedding_model, "input": text.strip()},
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            if "data" in result and len(result["data"]) > 0:
                return result["data"][0].get("embedding")
            return None
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return None

    def format_embedding(embedding: List[float]) -> str:
        return '[' + ','.join(str(x) for x in embedding) + ']'

    async def process():
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=engine)
        embeddings_generated = 0

        async with httpx.AsyncClient() as client:
            logger.info("=== Generating Historical Claim Embeddings ===")

            with SessionLocal() as session:
                query = text("""
                    SELECT CAST(cd.id AS text) as doc_id, cd.raw_ocr_text, c.claim_number
                    FROM claim_documents cd
                    JOIN claims c ON cd.claim_id = c.id
                    WHERE cd.embedding IS NULL
                      AND cd.raw_ocr_text IS NOT NULL
                    ORDER BY c.claim_number
                """)
                docs = [(r.doc_id, r.raw_ocr_text, r.claim_number) for r in session.execute(query).fetchall()]

            logger.info(f"Found {len(docs)} claim documents to embed")

            for doc_id, ocr_text, claim_num in docs:
                logger.info(f"  Claim: {claim_num}")

                embedding = await create_embedding(ocr_text[:2000], client)
                if embedding:
                    with SessionLocal() as session:
                        session.execute(
                            text("UPDATE claim_documents SET embedding = CAST(:emb AS vector) WHERE CAST(id AS text) = :id"),
                            {"emb": format_embedding(embedding), "id": doc_id}
                        )
                        session.commit()
                        embeddings_generated += 1

                await asyncio.sleep(0.3)

        engine.dispose()
        logger.info(f"✅ Historical embeddings: {embeddings_generated}/{len(docs)}")
        metrics.log_metric("embeddings_generated", embeddings_generated)

    asyncio.run(process())


@dsl.component(
    base_image='registry.access.redhat.com/ubi9/python-312:latest',
    packages_to_install=['httpx==0.27.0', 'sqlalchemy==2.0.36', 'psycopg2-binary==2.9.10']
)
def generate_decisions(
    workspace_path: str,
    llamastack_endpoint: str,
    llm_model: str,
    batch_size: int,
    metrics: dsl.Output[dsl.Metrics]
):
    """
    Step 5: Generate AI decisions for historical claims.

    Marks claims as 'completed' with realistic AI decisions.
    """
    import logging
    import os
    import json
    import asyncio
    from pathlib import Path
    from typing import Dict, Any
    import httpx
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Database connection
    postgres_host = os.getenv('POSTGRES_HOST', 'postgresql.claims-demo.svc.cluster.local')
    postgres_port = os.getenv('POSTGRES_PORT', '5432')
    postgres_db = os.getenv('POSTGRES_DATABASE')
    postgres_user = os.getenv('POSTGRES_USER')
    postgres_password = os.getenv('POSTGRES_PASSWORD')

    DATABASE_URL = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

    # Read metadata
    metadata_file = Path(workspace_path) / "claims_metadata.json"
    with open(metadata_file) as f:
        claims_metadata = json.load(f)

    async def generate_decision(claim_data: Dict[str, Any], client: httpx.AsyncClient) -> Dict[str, Any]:
        prompt = f"""Analyze this insurance claim and provide a decision.

Claim: {claim_data['claim_number']}
Type: {claim_data['claim_type']}

Provide decision as JSON:
{{"decision": "approve/deny", "reasoning": "brief explanation", "confidence": 0.0-1.0}}"""

        try:
            response = await client.post(
                f"{llamastack_endpoint}/v1/chat/completions",
                json={"model": llm_model, "messages": [{"role": "user", "content": prompt}]},
                timeout=120.0
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Parse JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            decision = json.loads(content)
            return decision
        except Exception as e:
            logger.error(f"Decision error: {e}")
            return {"decision": "approve", "reasoning": "Default approval", "confidence": 0.5}

    async def process():
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=engine)
        processed = 0
        failed = 0

        async with httpx.AsyncClient() as client:
            logger.info("=== Generating Historical Decisions ===")

            for claim_meta in claims_metadata:
                claim_id = claim_meta['claim_id']
                claim_number = claim_meta['claim_number']
                claim_type = claim_meta['claim_type']

                logger.info(f"  Processing: {claim_number}")

                decision_result = await generate_decision({
                    "claim_number": claim_number,
                    "claim_type": claim_type
                }, client)

                if decision_result:
                    try:
                        with SessionLocal() as session:
                            # Update claim status to completed
                            session.execute(text("""
                                UPDATE claims
                                SET status = 'completed', decision = :decision, processing_completed_at = NOW()
                                WHERE CAST(id AS text) = :claim_id
                            """), {"decision": decision_result["decision"], "claim_id": claim_id})

                            # Insert decision record
                            session.execute(text("""
                                INSERT INTO claim_decisions
                                (claim_id, decision_type, decision, reasoning, confidence_score, decided_by)
                                VALUES (CAST(:claim_id AS uuid), 'system', :decision, :reasoning, :confidence, 'AI-Historical')
                            """), {
                                "claim_id": claim_id,
                                "decision": decision_result["decision"],
                                "reasoning": decision_result.get("reasoning", ""),
                                "confidence": decision_result.get("confidence", 0.8)
                            })

                            session.commit()

                        processed += 1
                        logger.info(f"  Decision: {decision_result['decision']} ({processed}/{len(claims_metadata)})")

                    except Exception as e:
                        logger.error(f"  DB error: {e}")
                        failed += 1
                else:
                    logger.error("  Decision generation failed")
                    failed += 1

                # Small delay between requests
                await asyncio.sleep(1)

        logger.info(f"Processed: {processed}/{len(claims_metadata)}")
        logger.info(f"Failed: {failed}/{len(claims_metadata)}")
        engine.dispose()

        if failed > 0:
            raise RuntimeError(f"{failed} decisions failed")

        logger.info("All decisions generated!")
        metrics.log_metric("decisions_processed", processed)
        metrics.log_metric("decisions_failed", failed)

    asyncio.run(process())


@dsl.component(
    base_image='registry.access.redhat.com/ubi9/python-312:latest',
    packages_to_install=['httpx==0.27.0', 'sqlalchemy==2.0.36', 'psycopg2-binary==2.9.10']
)
def generate_test_claims(
    workspace_path: str,
    num_historical_claims: int,
    llamastack_endpoint: str,
    embedding_model: str,
    metrics: dsl.Output[dsl.Metrics]
):
    """
    Step 6: Generate test claims with realistic scenarios.

    Creates claim_documents for remaining pending claims with:
    - APPROVE scenarios (valid contracts, reasonable amounts)
    - DENY scenarios (expired contracts, excessive amounts)
    - MANUAL_REVIEW scenarios (short OCR, multiple contracts)

    workspace_path is needed for consistency (even if not used).
    """
    import logging
    import os
    import asyncio
    from typing import List, Optional
    import httpx
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Database connection
    postgres_host = os.getenv('POSTGRES_HOST', 'postgresql.claims-demo.svc.cluster.local')
    postgres_port = os.getenv('POSTGRES_PORT', '5432')
    postgres_db = os.getenv('POSTGRES_DATABASE')
    postgres_user = os.getenv('POSTGRES_USER')
    postgres_password = os.getenv('POSTGRES_PASSWORD')

    DATABASE_URL = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

    # Test scenarios - Claims to mark as MANUAL_REVIEW (short OCR)
    MANUAL_REVIEW_CLAIMS = [
        "CLM-2024-0061", "CLM-2024-0062", "CLM-2024-0063", "CLM-2024-0064", "CLM-2024-0065",
        "CLM-2024-0066", "CLM-2024-0067", "CLM-2024-0068", "CLM-2024-0069", "CLM-2024-0070"
    ]

    OCR_TEMPLATES = {
        "Auto": "Vehicle damage claim. Accident date: 2025-11-15. Driver: {name}. Vehicle: Toyota Camry. Damage: Front bumper. Estimated repair: ${amount}. Police report filed.",
        "Home": "Home insurance claim for water damage. Property owner: {name}. Date of loss: 2025-11-10. Cause: Burst pipe. Estimated damages: ${amount}.",
        "Medical": "Medical insurance claim. Patient: {name}. Service: Hospital visit. Total charges: ${amount}. Hospital stay: 2 days.",
        "Life": "Life insurance claim. Beneficiary: {name}. Claim amount: ${amount}. Documentation attached."
    }

    SHORT_OCR = "Claim document for {name}. Date: 2025-12. Insufficient data."

    async def create_embedding(text: str, client: httpx.AsyncClient) -> Optional[List[float]]:
        try:
            response = await client.post(
                f"{llamastack_endpoint}/v1/embeddings",
                json={"model": embedding_model, "input": text.strip()},
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            if "data" in result and len(result["data"]) > 0:
                return result["data"][0].get("embedding")
            return None
        except Exception as e:
            logger.error(f"Error: {e}")
            return None

    def format_embedding(embedding: List[float]) -> str:
        return '[' + ','.join(str(x) for x in embedding) + ']'

    async def process():
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=engine)

        approve_count = 0
        deny_count = 0
        manual_count = 0

        async with httpx.AsyncClient() as client:
            logger.info("=== Generating Test Claims ===")

            # Get pending claims (after historical ones)
            with SessionLocal() as session:
                query = text("""
                    SELECT CAST(c.id AS text) as id, c.claim_number, c.claim_type, c.amount,
                           c.user_id, u.first_name, u.last_name
                    FROM claims c
                    JOIN users u ON c.user_id = u.id
                    WHERE c.status = 'pending'
                    ORDER BY c.claim_number
                    OFFSET :offset
                """)
                claims = session.execute(query, {"offset": num_historical_claims}).fetchall()

            logger.info(f"Found {len(claims)} test claims to process")

            for claim_id, claim_num, claim_type, amount, user_id, first_name, last_name in claims:
                full_name = f"{first_name} {last_name}"
                is_manual = claim_num in MANUAL_REVIEW_CLAIMS

                # Generate OCR text
                if is_manual:
                    ocr_text = SHORT_OCR.format(name=full_name)
                    confidence = 0.60
                    manual_count += 1
                    scenario = "MANUAL_REVIEW"
                else:
                    template = OCR_TEMPLATES.get(claim_type, OCR_TEMPLATES["Auto"])
                    ocr_text = template.format(name=full_name, amount=float(amount))
                    confidence = 0.95
                    # Determine scenario based on amount
                    if float(amount) > 15000:
                        deny_count += 1
                        scenario = "DENY"
                    else:
                        approve_count += 1
                        scenario = "APPROVE"

                logger.info(f"  {claim_num}: {scenario}")

                # Generate embedding
                embedding = await create_embedding(ocr_text, client)
                if embedding:
                    with SessionLocal() as session:
                        session.execute(text("""
                            INSERT INTO claim_documents
                            (claim_id, document_type, file_path, raw_ocr_text, ocr_confidence, embedding)
                            VALUES (CAST(:claim_id AS uuid), :doc_type, :file_path, :ocr_text, :confidence, CAST(:emb AS vector))
                        """), {
                            "claim_id": claim_id,
                            "doc_type": claim_type,
                            "file_path": f"/claim_documents/{claim_num}.pdf",
                            "ocr_text": ocr_text,
                            "confidence": confidence,
                            "emb": format_embedding(embedding)
                        })
                        session.commit()

                await asyncio.sleep(0.3)

        engine.dispose()

        logger.info(f"\n{'='*60}")
        logger.info(f"TEST CLAIMS SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"✅ APPROVE: {approve_count}")
        logger.info(f"❌ DENY: {deny_count}")
        logger.info(f"⚠️  MANUAL_REVIEW: {manual_count}")
        logger.info(f"✅ Total: {approve_count + deny_count + manual_count}")
        logger.info(f"{'='*60}")

        metrics.log_metric("test_approve", approve_count)
        metrics.log_metric("test_deny", deny_count)
        metrics.log_metric("test_manual_review", manual_count)

    asyncio.run(process())


@dsl.pipeline(
    name='Complete Data Initialization',
    description="""
    Complete data initialization for the Claims Demo.

    This pipeline initializes ALL data needed:
    1. Knowledge Base embeddings (15 entries)
    2. Historical claims with OCR, embeddings, and AI decisions (60 claims)
    3. Test claims with realistic scenarios (40 claims)

    PostgreSQL credentials are injected from postgresql-secret via environment variables.
    """,
    pipeline_config=dsl.PipelineConfig(
        workspace=dsl.WorkspaceConfig(
            size='20Gi',
            kubernetes=dsl.KubernetesWorkspaceConfig(
                pvcSpecPatch={
                    'accessModes': ['ReadWriteOnce']
                }
            )
        ),
    ),
)
def complete_data_init_pipeline(
    num_historical_claims: int = 60,
    llamastack_endpoint: str = 'http://llamastack-rhoai-service.claims-demo.svc.cluster.local:8321',
    embedding_model: str = 'vllm-embedding/embeddinggemma-300m',
    llm_model: str = 'vllm-inference/llama-3-3-70b-instruct-quantized-w8a8',
    batch_size: int = 5,
    max_retries: int = 30
):
    """
    Complete data initialization pipeline.

    Args:
        num_historical_claims: Number of claims to process as historical (default: 60)
        llamastack_endpoint: LlamaStack API endpoint
        embedding_model: Embedding model name
        llm_model: LLM model for decisions
        batch_size: Documents per batch
        max_retries: Max retries for LlamaStack health check
    """

    # Task 1: Generate KB Embeddings
    kb_task = generate_kb_embeddings(
        workspace_path=dsl.WORKSPACE_PATH_PLACEHOLDER,
        llamastack_endpoint=llamastack_endpoint,
        embedding_model=embedding_model
    )
    kb_task.set_display_name('1. Generate KB Embeddings')
    kb_task.set_cpu_limit('1')
    kb_task.set_memory_limit('2Gi')

    kubernetes.use_secret_as_env(
        kb_task,
        secret_name='postgresql-secret',
        secret_key_to_env={
            'POSTGRES_USER': 'POSTGRES_USER',
            'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
            'POSTGRES_DATABASE': 'POSTGRES_DATABASE'
        }
    )

    # Task 2: Generate PDFs
    generate_task = generate_realistic_pdfs(
        workspace_path=dsl.WORKSPACE_PATH_PLACEHOLDER,
        num_historical_claims=num_historical_claims
    )
    generate_task.set_display_name('2. Generate Historical PDFs')
    generate_task.set_cpu_limit('1')
    generate_task.set_memory_limit('2Gi')
    generate_task.after(kb_task)

    kubernetes.use_secret_as_env(
        generate_task,
        secret_name='postgresql-secret',
        secret_key_to_env={
            'POSTGRES_USER': 'POSTGRES_USER',
            'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
            'POSTGRES_DATABASE': 'POSTGRES_DATABASE'
        }
    )

    # Task 3: Parse with Docling
    parse_task = parse_with_docling(
        workspace_path=dsl.WORKSPACE_PATH_PLACEHOLDER,
        batch_size=batch_size
    )
    parse_task.set_display_name('3. Parse PDFs with Docling')
    parse_task.set_cpu_limit('2')
    parse_task.set_memory_limit('8Gi')
    parse_task.after(generate_task)

    kubernetes.use_secret_as_env(
        parse_task,
        secret_name='postgresql-secret',
        secret_key_to_env={
            'POSTGRES_USER': 'POSTGRES_USER',
            'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
            'POSTGRES_DATABASE': 'POSTGRES_DATABASE'
        }
    )

    # Task 4: Generate Embeddings
    embeddings_task = generate_embeddings(
        workspace_path=dsl.WORKSPACE_PATH_PLACEHOLDER,
        llamastack_endpoint=llamastack_endpoint,
        embedding_model=embedding_model,
        batch_size=batch_size
    )
    embeddings_task.set_display_name('4. Generate Historical Embeddings')
    embeddings_task.set_cpu_limit('1')
    embeddings_task.set_memory_limit('2Gi')
    embeddings_task.after(parse_task)

    kubernetes.use_secret_as_env(
        embeddings_task,
        secret_name='postgresql-secret',
        secret_key_to_env={
            'POSTGRES_USER': 'POSTGRES_USER',
            'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
            'POSTGRES_DATABASE': 'POSTGRES_DATABASE'
        }
    )

    # Task 5: Generate Decisions
    decisions_task = generate_decisions(
        workspace_path=dsl.WORKSPACE_PATH_PLACEHOLDER,
        llamastack_endpoint=llamastack_endpoint,
        llm_model=llm_model,
        batch_size=batch_size
    )
    decisions_task.set_display_name('5. Generate Historical Decisions')
    decisions_task.set_cpu_limit('1')
    decisions_task.set_memory_limit('2Gi')
    decisions_task.after(embeddings_task)

    kubernetes.use_secret_as_env(
        decisions_task,
        secret_name='postgresql-secret',
        secret_key_to_env={
            'POSTGRES_USER': 'POSTGRES_USER',
            'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
            'POSTGRES_DATABASE': 'POSTGRES_DATABASE'
        }
    )

    # Task 6: Generate Test Claims
    test_task = generate_test_claims(
        workspace_path=dsl.WORKSPACE_PATH_PLACEHOLDER,
        num_historical_claims=num_historical_claims,
        llamastack_endpoint=llamastack_endpoint,
        embedding_model=embedding_model
    )
    test_task.set_display_name('6. Generate Test Claims')
    test_task.set_cpu_limit('1')
    test_task.set_memory_limit('2Gi')
    test_task.after(decisions_task)

    kubernetes.use_secret_as_env(
        test_task,
        secret_name='postgresql-secret',
        secret_key_to_env={
            'POSTGRES_USER': 'POSTGRES_USER',
            'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
            'POSTGRES_DATABASE': 'POSTGRES_DATABASE'
        }
    )


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=complete_data_init_pipeline,
        package_path="complete_data_init_v2_pipeline.yaml"
    )
    print("✅ Pipeline compiled: complete_data_init_v2_pipeline.yaml")
