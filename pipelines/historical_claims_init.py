"""
Kubeflow Pipeline: Historical Claims Initialization

Initializes historical claims with OCR, embeddings, and realistic AI decisions
for similarity search in the claims processing workflow (default: 10 claims).

Author: Claims Demo Team
RHOAI Version: 3.2
"""

from kfp import dsl
from kfp import compiler
from kfp import kubernetes


@dsl.component(
    base_image='registry.access.redhat.com/ubi9/python-312:latest',
    packages_to_install=['reportlab==4.2.5', 'sqlalchemy==2.0.36', 'psycopg2-binary==2.9.10']
)
def generate_realistic_pdfs(
    workspace_path: str,
    num_claims: int,
    metrics: dsl.Output[dsl.Metrics]
):
    """
    Generate realistic PDFs from existing claims.

    Reads claims from PostgreSQL (num_claims parameter) and creates PDF files with ReportLab.
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
        claims = session.execute(query, {"limit": num_claims}).fetchall()

    logger.info(f"Found {len(claims)} claims to process")

    generated = 0
    failed = 0
    claims_metadata = []

    # Generate sample OCR text for each claim type
    sample_texts = {
        "auto": "Vehicle Damage Report\n\nDate of Incident: 2025-12-15\nLocation: Highway 101, Mile Marker 45\n\nDescription: Rear-end collision during heavy traffic. Front bumper damage, headlight broken. Airbags deployed. No injuries reported. Police report filed #2025-12345.",
        "home": "Property Damage Claim\n\nDate of Loss: 2025-11-20\nProperty Address: 123 Main Street\n\nDescription: Water damage from burst pipe in basement. Affected areas: laundry room, storage area. Damage to flooring, drywall, and personal property. Emergency plumber called. Estimated repair cost: $8,500.",
        "health": "Medical Services Claim\n\nPatient Name: John Doe\nDate of Service: 2025-10-05\nProvider: City Medical Center\n\nServices Rendered: Emergency room visit for chest pain. EKG performed, blood tests completed. Diagnosis: Acute gastritis. Treatment: Medication prescribed. Total charges: $2,450."
    }

    def create_pdf(pdf_path, claim_number, claim_type, claim_text):
        """Create PDF from claim data."""
        doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                               rightMargin=0.75*inch, leftMargin=0.75*inch,
                               topMargin=0.75*inch, bottomMargin=0.75*inch)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                    fontSize=16, alignment=1, spaceAfter=12)
        elements.append(Paragraph("INSURANCE CLAIM DOCUMENT", title_style))
        elements.append(Spacer(1, 0.2*inch))

        # Claim info table
        claim_data = [
            ['Claim Number:', claim_number],
            ['Claim Type:', claim_type.upper()],
            ['Date:', datetime.now().strftime('%Y-%m-%d')]
        ]
        claim_table = Table(claim_data, colWidths=[2*inch, 4*inch])
        claim_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('PADDING', (0,0), (-1,-1), 6)
        ]))
        elements.append(claim_table)
        elements.append(Spacer(1, 0.3*inch))

        # Content
        for line in claim_text.split('\n'):
            if line.strip():
                escaped = line.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
                elements.append(Paragraph(escaped, styles['Normal']))
            else:
                elements.append(Spacer(1, 0.1*inch))

        doc.build(elements)

    # Generate PDFs for each claim
    for claim in claims:
        claim_id = claim.claim_id
        claim_number = claim.claim_number
        claim_type = claim.claim_type or 'auto'

        # Use sample text for the claim type
        claim_text = sample_texts.get(claim_type, sample_texts['auto'])

        # Create PDF filename
        pdf_filename = f"{claim_number}.pdf"
        pdf_path = output_dir / pdf_filename

        try:
            create_pdf(str(pdf_path), claim_number, claim_type, claim_text)
            generated += 1

            # Save metadata for next steps
            claims_metadata.append({
                "claim_id": claim_id,
                "claim_number": claim_number,
                "claim_type": claim_type,
                "user_id": claim.user_id,
                "pdf_filename": pdf_filename
            })

            if generated % 10 == 0:
                logger.info(f"Progress: {generated}/{len(claims)} PDFs")

        except Exception as e:
            logger.error(f"Failed to generate PDF for {claim_number}: {e}")
            failed += 1

    # Save metadata
    with open(metadata_file, 'w') as f:
        json.dump(claims_metadata, f)

    logger.info(f"Generated {generated}/{len(claims)} PDFs")
    logger.info(f"Failed: {failed}/{len(claims)} PDFs")
    logger.info(f"Metadata saved to {metadata_file}")

    engine.dispose()

    # Log metrics
    metrics.log_metric("total_claims", len(claims))
    metrics.log_metric("pdfs_generated", generated)
    metrics.log_metric("pdfs_failed", failed)

    if failed > 0:
        raise RuntimeError(f"{failed} PDFs failed to generate")


@dsl.component(
    base_image='registry.access.redhat.com/ubi9/python-312:latest',
    packages_to_install=['docling==2.18.0', 'sqlalchemy==2.0.36', 'psycopg2-binary==2.9.10']
)
def docling_parse_pdfs(
    workspace_path: str,
    metrics: dsl.Output[dsl.Metrics]
):
    """
    Parse PDFs using Docling and create claim_documents.

    Uses IBM's Docling for advanced document parsing.
    Creates claim_documents entries with raw_ocr_text.
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

    pdf_dir = Path(workspace_path) / "pdfs"
    metadata_file = Path(workspace_path) / "claims_metadata.json"

    logger.info(f"Parsing PDFs from {pdf_dir}")

    if not pdf_dir.exists():
        logger.error(f"PDF directory not found: {pdf_dir}")
        raise RuntimeError(f"PDF directory not found: {pdf_dir}")

    # Load metadata
    with open(metadata_file, 'r') as f:
        claims_metadata = json.load(f)

    logger.info(f"Found {len(claims_metadata)} PDFs to parse")

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)

    converter = DocumentConverter()
    parsed = 0
    failed = 0

    for claim_meta in claims_metadata:
        claim_id = claim_meta['claim_id']
        pdf_filename = claim_meta['pdf_filename']
        pdf_file = pdf_dir / pdf_filename

        if not pdf_file.exists():
            logger.error(f"PDF not found: {pdf_file}")
            failed += 1
            continue

        logger.info(f"Parsing {claim_meta['claim_number']}...")

        try:
            # Parse PDF with Docling
            result = converter.convert(str(pdf_file))
            extracted_text = result.document.export_to_text().strip()

            # Create claim_document entry
            with SessionLocal() as session:
                insert_query = text("""
                    INSERT INTO claim_documents (
                        claim_id,
                        document_type,
                        file_path,
                        raw_ocr_text,
                        ocr_confidence,
                        ocr_processed_at
                    ) VALUES (
                        CAST(:claim_id AS UUID),
                        'application/pdf',
                        :file_path,
                        :ocr_text,
                        0.95,
                        NOW()
                    )
                    ON CONFLICT (claim_id) DO UPDATE
                    SET raw_ocr_text = EXCLUDED.raw_ocr_text,
                        ocr_processed_at = EXCLUDED.ocr_processed_at
                """)
                session.execute(insert_query, {
                    "claim_id": claim_id,
                    "file_path": f"/claim_documents/{pdf_filename}",
                    "ocr_text": extracted_text
                })
                session.commit()

            parsed += 1
            logger.info(f"  Parsed ({parsed}/{len(claims_metadata)})")

            if parsed % 10 == 0:
                logger.info(f"Progress: {parsed}/{len(claims_metadata)}")

        except Exception as e:
            logger.error(f"  Failed to parse {claim_meta['claim_number']}: {e}")
            failed += 1

    logger.info(f"Parsed: {parsed}/{len(claims_metadata)}")
    logger.info(f"Failed: {failed}/{len(claims_metadata)}")
    engine.dispose()

    # Log metrics
    metrics.log_metric("total_documents", len(claims_metadata))
    metrics.log_metric("documents_parsed", parsed)
    metrics.log_metric("documents_failed", failed)

    if failed > 0:
        raise RuntimeError(f"{failed} documents failed to parse")


@dsl.component(
    base_image='registry.access.redhat.com/ubi9/python-312:latest',
    packages_to_install=['httpx==0.27.2', 'sqlalchemy==2.0.36', 'psycopg2-binary==2.9.10', 'pgvector==0.3.6']
)
def generate_embeddings(
    workspace_path: str,
    llamastack_endpoint: str,
    embedding_model: str,
    batch_size: int,
    max_retries: int,
    metrics: dsl.Output[dsl.Metrics]
):
    """
    Generate embeddings for claim documents using LlamaStack.

    Creates 768D embeddings via LlamaStack API and updates PostgreSQL with pgvector format.
    """
    import asyncio
    import logging
    import os
    import json
    from pathlib import Path
    from typing import List, Optional

    import httpx
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

    metadata_file = Path(workspace_path) / "claims_metadata.json"

    async def wait_for_llamastack():
        """Wait for LlamaStack to be ready."""
        logger.info(f"Waiting for LlamaStack at {llamastack_endpoint}...")
        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{llamastack_endpoint}/v1/health")
                    if response.status_code == 200:
                        logger.info("LlamaStack is ready")
                        return True
            except Exception as e:
                logger.debug(f"Attempt {attempt}/{max_retries}: {e}")
            if attempt < max_retries:
                await asyncio.sleep(10)
        logger.error("LlamaStack not ready")
        return False

    async def create_embedding(text: str, client: httpx.AsyncClient) -> Optional[List[float]]:
        """Create embedding via LlamaStack."""
        try:
            response = await client.post(
                f"{llamastack_endpoint}/v1/embeddings",
                json={"model": embedding_model, "input": text},
                timeout=60.0
            )
            if response.status_code == 200:
                data = response.json()
                # LlamaStack returns: {"data": [{"embedding": [...]}]}
                if 'data' in data and len(data['data']) > 0:
                    return data['data'][0]['embedding']
                return None
            else:
                logger.error(f"API error {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error: {e}")
            return None

    def format_embedding(embedding: List[float]) -> str:
        """Format for pgvector."""
        return '[' + ','.join(str(x) for x in embedding) + ']'

    async def process():
        if not await wait_for_llamastack():
            raise RuntimeError("LlamaStack not available")

        logger.info("Connecting to PostgreSQL...")
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=engine)

        # Load metadata
        with open(metadata_file, 'r') as f:
            claims_metadata = json.load(f)

        # Get claim_documents that need embeddings
        with SessionLocal() as session:
            query = text("""
                SELECT CAST(cd.id AS text) as doc_id, cd.raw_ocr_text, c.claim_number
                FROM claim_documents cd
                JOIN claims c ON cd.claim_id = c.id
                WHERE cd.embedding IS NULL
                  AND cd.raw_ocr_text IS NOT NULL
                  AND c.claim_number = ANY(:claim_numbers)
                ORDER BY c.claim_number
            """)
            claim_numbers = [cm['claim_number'] for cm in claims_metadata]
            documents = session.execute(query, {"claim_numbers": claim_numbers}).fetchall()

        if not documents:
            logger.info("No documents need embeddings")
            return {"processed": 0, "failed": 0, "total": 0}

        logger.info(f"Found {len(documents)} documents")
        processed = 0
        failed = 0

        async with httpx.AsyncClient() as client:
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(documents) + batch_size - 1) // batch_size
                logger.info(f"Batch {batch_num}/{total_batches} ({len(batch)} docs)")

                for row in batch:
                    ocr_text = row.raw_ocr_text[:2000] if len(row.raw_ocr_text) > 2000 else row.raw_ocr_text
                    logger.info(f"  Embedding {row.claim_number}...")

                    embedding = await create_embedding(ocr_text, client)
                    if embedding:
                        try:
                            with SessionLocal() as session:
                                update_query = text("""
                                    UPDATE claim_documents
                                    SET embedding = CAST(:embedding AS vector)
                                    WHERE CAST(id AS text) = :doc_id
                                """)
                                session.execute(update_query, {
                                    "embedding": format_embedding(embedding),
                                    "doc_id": row.doc_id
                                })
                                session.commit()
                            processed += 1
                            logger.info(f"    Done ({processed}/{len(documents)})")
                        except Exception as e:
                            logger.error(f"    DB error: {e}")
                            failed += 1
                    else:
                        logger.error("    Embedding failed")
                        failed += 1

                if i + batch_size < len(documents):
                    await asyncio.sleep(2)

        logger.info(f"Processed: {processed}/{len(documents)}")
        logger.info(f"Failed: {failed}/{len(documents)}")
        engine.dispose()

        if failed > 0:
            raise RuntimeError(f"{failed} embeddings failed")

        logger.info("All embeddings generated!")
        return {"processed": processed, "failed": failed, "total": len(documents)}

    # Run async function
    result = asyncio.run(process())

    # Log metrics
    metrics.log_metric("total_documents", result["total"])
    metrics.log_metric("embeddings_processed", result["processed"])
    metrics.log_metric("embeddings_failed", result["failed"])


@dsl.component(
    base_image='registry.access.redhat.com/ubi9/python-312:latest',
    packages_to_install=['httpx==0.27.2', 'sqlalchemy==2.0.36', 'psycopg2-binary==2.9.10']
)
def generate_decisions(
    workspace_path: str,
    llamastack_endpoint: str,
    llm_model: str,
    metrics: dsl.Output[dsl.Metrics]
):
    """
    Generate realistic AI decisions for historical claims.

    Calls LlamaStack to analyze each claim and create a decision with reasoning.
    Updates claims status and creates claim_decisions entries.
    """
    import asyncio
    import logging
    import os
    import json
    from pathlib import Path
    from datetime import datetime, timezone

    import httpx
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

    metadata_file = Path(workspace_path) / "claims_metadata.json"

    async def generate_decision(claim_data: dict, client: httpx.AsyncClient) -> dict:
        """Generate decision for a claim using LlamaStack."""
        prompt = f"""Analyze this insurance claim and make a decision.

Claim Number: {claim_data['claim_number']}
Claim Type: {claim_data['claim_type']}
Document Text: {claim_data['ocr_text'][:1000]}

Based on the information provided, decide whether to APPROVE or DENY this claim.
Provide clear reasoning for your decision.

Format your response as:
DECISION: [APPROVE or DENY]
CONFIDENCE: [0.0 to 1.0]
REASONING: [Your detailed reasoning]
"""

        try:
            response = await client.post(
                f"{llamastack_endpoint}/v1/chat/completions",
                json={
                    "model": llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=60.0
            )

            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']

                # Parse response
                decision = "manual_review"
                confidence = 0.5
                reasoning = content

                if "APPROVE" in content.upper():
                    decision = "approve"
                elif "DENY" in content.upper():
                    decision = "deny"

                # Extract confidence if present
                for line in content.split('\n'):
                    if "CONFIDENCE:" in line.upper():
                        try:
                            confidence = float(line.split(':')[1].strip())
                        except:
                            pass

                return {
                    "decision": decision,
                    "confidence": confidence,
                    "reasoning": content
                }
            else:
                logger.error(f"LLM API error {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return None

    async def process():
        logger.info("Generating decisions...")
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=engine)

        # Load metadata
        with open(metadata_file, 'r') as f:
            claims_metadata = json.load(f)

        # Get claims with embeddings but no decisions
        with SessionLocal() as session:
            query = text("""
                SELECT
                    CAST(c.id AS text) as claim_id,
                    c.claim_number,
                    c.claim_type,
                    cd.raw_ocr_text
                FROM claims c
                JOIN claim_documents cd ON cd.claim_id = c.id
                LEFT JOIN claim_decisions cdec ON cdec.claim_id = c.id
                WHERE cd.embedding IS NOT NULL
                  AND cdec.id IS NULL
                  AND c.claim_number = ANY(:claim_numbers)
                ORDER BY c.claim_number
            """)
            claim_numbers = [cm['claim_number'] for cm in claims_metadata]
            claims = session.execute(query, {"claim_numbers": claim_numbers}).fetchall()

        if not claims:
            logger.info("No claims need decisions")
            return {"processed": 0, "failed": 0, "total": 0}

        logger.info(f"Found {len(claims)} claims to process")
        processed = 0
        failed = 0

        async with httpx.AsyncClient() as client:
            for claim in claims:
                claim_id = claim.claim_id
                claim_number = claim.claim_number

                logger.info(f"Generating decision for {claim_number}...")

                claim_data = {
                    "claim_id": claim_id,
                    "claim_number": claim_number,
                    "claim_type": claim.claim_type,
                    "ocr_text": claim.raw_ocr_text
                }

                decision_result = await generate_decision(claim_data, client)

                if decision_result:
                    try:
                        with SessionLocal() as session:
                            # Insert decision
                            insert_decision = text("""
                                INSERT INTO claim_decisions (
                                    claim_id,
                                    initial_decision,
                                    initial_confidence,
                                    initial_reasoning,
                                    initial_decided_at,
                                    decision,
                                    confidence,
                                    reasoning,
                                    llm_model,
                                    requires_manual_review
                                ) VALUES (
                                    CAST(:claim_id AS UUID),
                                    :decision,
                                    :confidence,
                                    :reasoning,
                                    NOW(),
                                    :decision,
                                    :confidence,
                                    :reasoning,
                                    :llm_model,
                                    :requires_review
                                )
                            """)
                            session.execute(insert_decision, {
                                "claim_id": claim_id,
                                "decision": decision_result["decision"],
                                "confidence": decision_result["confidence"],
                                "reasoning": decision_result["reasoning"],
                                "llm_model": llm_model,
                                "requires_review": decision_result["decision"] == "manual_review"
                            })

                            # Update claim status - all historical claims are completed
                            # (regardless of approve/deny decision - they're historical data for RAG)
                            status_map = {
                                "approve": "completed",
                                "deny": "completed",  # Historical claims marked completed even if denied
                                "manual_review": "completed"
                            }

                            update_claim = text("""
                                UPDATE claims
                                SET status = :status,
                                    processed_at = NOW(),
                                    total_processing_time_ms = 5000
                                WHERE CAST(id AS text) = :claim_id
                            """)
                            session.execute(update_claim, {
                                "status": status_map[decision_result["decision"]],
                                "claim_id": claim_id
                            })

                            session.commit()

                        processed += 1
                        logger.info(f"  Decision: {decision_result['decision']} ({processed}/{len(claims)})")

                    except Exception as e:
                        logger.error(f"  DB error: {e}")
                        failed += 1
                else:
                    logger.error("  Decision generation failed")
                    failed += 1

                # Small delay between requests
                await asyncio.sleep(1)

        logger.info(f"Processed: {processed}/{len(claims)}")
        logger.info(f"Failed: {failed}/{len(claims)}")
        engine.dispose()

        if failed > 0:
            raise RuntimeError(f"{failed} decisions failed")

        logger.info("All decisions generated!")
        return {"processed": processed, "failed": failed, "total": len(claims)}

    # Run async function
    result = asyncio.run(process())

    # Log metrics
    metrics.log_metric("total_claims", result["total"])
    metrics.log_metric("decisions_processed", result["processed"])
    metrics.log_metric("decisions_failed", result["failed"])


@dsl.pipeline(
    name='Historical Claims Initialization',
    description="""
    Initialize historical claims data for RAG similarity search.

    This pipeline demonstrates RHOAI Data Science Pipelines:
    1. Generate realistic PDFs from existing claims
    2. Parse PDFs with Docling (IBM advanced parsing)
    3. Generate embeddings with LlamaStack (768D vectors)
    4. Generate AI decisions with LlamaStack (realistic reasoning)

    Complements real-time claim processing via MCP Servers.

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
def historical_claims_pipeline(
    num_claims: int = 10,
    llamastack_endpoint: str = 'http://llamastack-rhoai-service.claims-demo.svc.cluster.local:8321',
    embedding_model: str = 'vllm-embedding/embeddinggemma-300m',
    llm_model: str = 'vllm-inference/llama-3-3-70b-instruct-quantized-w8a8',
    batch_size: int = 5,
    max_retries: int = 30
):
    """
    Historical claims initialization pipeline.

    Args:
        num_claims: Number of claims to process (default: 10)
        llamastack_endpoint: LlamaStack API endpoint
        embedding_model: Embedding model name
        llm_model: LLM model for decisions
        batch_size: Documents per batch
        max_retries: Max retries for LlamaStack health check
    """

    # Task 1: Generate PDFs
    generate_task = generate_realistic_pdfs(
        workspace_path=dsl.WORKSPACE_PATH_PLACEHOLDER,
        num_claims=num_claims
    )
    generate_task.set_display_name('Generate Realistic PDFs')
    generate_task.set_cpu_limit('1')
    generate_task.set_memory_limit('2Gi')

    # Inject PostgreSQL credentials from Kubernetes secret
    kubernetes.use_secret_as_env(
        generate_task,
        secret_name='postgresql-secret',
        secret_key_to_env={
            'POSTGRES_USER': 'POSTGRES_USER',
            'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
            'POSTGRES_DATABASE': 'POSTGRES_DATABASE'
        }
    )

    # Task 2: Parse with Docling
    parse_task = docling_parse_pdfs(
        workspace_path=dsl.WORKSPACE_PATH_PLACEHOLDER
    )
    parse_task.set_display_name('Docling Parse PDFs')
    parse_task.set_cpu_limit('2')
    parse_task.set_memory_limit('8Gi')
    parse_task.after(generate_task)

    # Inject PostgreSQL credentials
    kubernetes.use_secret_as_env(
        parse_task,
        secret_name='postgresql-secret',
        secret_key_to_env={
            'POSTGRES_USER': 'POSTGRES_USER',
            'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
            'POSTGRES_DATABASE': 'POSTGRES_DATABASE'
        }
    )

    # Task 3: Generate Embeddings
    embeddings_task = generate_embeddings(
        workspace_path=dsl.WORKSPACE_PATH_PLACEHOLDER,
        llamastack_endpoint=llamastack_endpoint,
        embedding_model=embedding_model,
        batch_size=batch_size,
        max_retries=max_retries
    )
    embeddings_task.set_display_name('Generate Embeddings')
    embeddings_task.set_cpu_limit('1')
    embeddings_task.set_memory_limit('2Gi')
    embeddings_task.after(parse_task)

    # Inject PostgreSQL credentials
    kubernetes.use_secret_as_env(
        embeddings_task,
        secret_name='postgresql-secret',
        secret_key_to_env={
            'POSTGRES_USER': 'POSTGRES_USER',
            'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
            'POSTGRES_DATABASE': 'POSTGRES_DATABASE'
        }
    )

    # Task 4: Generate AI Decisions
    decisions_task = generate_decisions(
        workspace_path=dsl.WORKSPACE_PATH_PLACEHOLDER,
        llamastack_endpoint=llamastack_endpoint,
        llm_model=llm_model
    )
    decisions_task.set_display_name('Generate AI Decisions')
    decisions_task.set_cpu_limit('1')
    decisions_task.set_memory_limit('2Gi')
    decisions_task.after(embeddings_task)

    # Inject PostgreSQL credentials
    kubernetes.use_secret_as_env(
        decisions_task,
        secret_name='postgresql-secret',
        secret_key_to_env={
            'POSTGRES_USER': 'POSTGRES_USER',
            'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
            'POSTGRES_DATABASE': 'POSTGRES_DATABASE'
        }
    )


if __name__ == '__main__':
    # Compile pipeline to YAML
    compiler.Compiler().compile(
        pipeline_func=historical_claims_pipeline,
        package_path='historical_claims_init_pipeline.yaml'
    )
    print("[OK] Pipeline compiled to historical_claims_init_pipeline.yaml")
    print("[INFO] Upload this file to RHOAI Data Science Pipelines dashboard")
