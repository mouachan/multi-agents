#!/usr/bin/env python3
"""
Complete Data Initialization Pipeline
Initializes KB embeddings + historical claims + current test claims with test scenarios.
"""
from kfp import dsl, compiler
from kfp.dsl import component, Output, Metrics
from kfp import kubernetes


@component(
    base_image="registry.access.redhat.com/ubi9/python-312:latest",
    packages_to_install=["httpx==0.27.0", "sqlalchemy==2.0.25", "psycopg2-binary==2.9.9"]
)
def generate_kb_embeddings(
    postgres_host: str,
    postgres_port: str,
    llamastack_endpoint: str,
    embedding_model: str,
    metrics: Output[Metrics]
):
    """Step 1: Generate Knowledge Base embeddings."""
    import asyncio
    import logging
    import os
    from typing import List, Optional
    import httpx
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Get credentials from environment (injected from secret)
    postgres_user = os.getenv('POSTGRES_USER', 'claims_user')
    postgres_password = os.getenv('POSTGRES_PASSWORD')
    postgres_db = os.getenv('POSTGRES_DATABASE', 'claims_db')

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
            logger.error(f"Error creating embedding: {e}")
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
        logger.info(f"✅ Knowledge Base embeddings: {kb_count}/15")
        metrics.log_metric("kb_embeddings", kb_count)

    asyncio.run(process())


@component(
    base_image="registry.access.redhat.com/ubi9/python-312:latest",
    packages_to_install=["reportlab==4.2.5", "sqlalchemy==2.0.36", "psycopg2-binary==2.9.10"]
)
def generate_historical_pdfs(
    workspace_path: dsl.OutputPath(str),
    num_historical_claims: int,
    postgres_host: str,
    postgres_port: str
):
    """Step 2: Generate PDFs for historical claims (first N claims)."""
    import logging
    import os
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Get credentials from environment (injected from secret)
    postgres_user = os.getenv('POSTGRES_USER', 'claims_user')
    postgres_password = os.getenv('POSTGRES_PASSWORD')
    postgres_db = os.getenv('POSTGRES_DATABASE', 'claims_db')

    DATABASE_URL = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)

    # Get first N claims (these will be historical)
    with SessionLocal() as session:
        query = text("""
            SELECT claim_number, claim_type, amount, description, submitted_at
            FROM claims
            WHERE status = 'pending'
            ORDER BY claim_number
            LIMIT :limit
        """)
        claims = session.execute(query, {"limit": num_historical_claims}).fetchall()

    pdf_dir = os.path.join(workspace_path, "pdfs")
    os.makedirs(pdf_dir, exist_ok=True)

    logger.info(f"Generating {len(claims)} PDFs...")
    styles = getSampleStyleSheet()

    for claim in claims:
        claim_num, claim_type, amount, description, submitted_at = claim
        pdf_path = os.path.join(pdf_dir, f"{claim_num}.pdf")

        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        story = []

        story.append(Paragraph(f"<b>Insurance Claim: {claim_num}</b>", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Type:</b> {claim_type}", styles['Normal']))
        story.append(Paragraph(f"<b>Amount:</b> ${amount:,.2f}", styles['Normal']))
        story.append(Paragraph(f"<b>Date:</b> {submitted_at.strftime('%Y-%m-%d')}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Description:</b>", styles['Heading2']))
        story.append(Paragraph(description or "No description provided.", styles['Normal']))

        doc.build(story)
        logger.info(f"  Generated: {claim_num}.pdf")

    logger.info(f"✅ Generated {len(claims)} PDFs in {pdf_dir}")

    # Write path for next step
    with open(workspace_path, 'w') as f:
        f.write(pdf_dir)


@component(
    base_image="registry.access.redhat.com/ubi9/python-312:latest",
    packages_to_install=["docling==2.18.0", "sqlalchemy==2.0.36", "psycopg2-binary==2.9.10"]
)
def parse_historical_pdfs(
    workspace_path: dsl.InputPath(str),
    num_historical_claims: int,
    postgres_host: str,
    postgres_port: str,
    metrics: Output[Metrics]
):
    """Step 3: Parse PDFs with Docling for historical claims."""
    import logging
    import os
    from docling.document_converter import DocumentConverter
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Get credentials from environment (injected from secret)
    postgres_user = os.getenv('POSTGRES_USER', 'claims_user')
    postgres_password = os.getenv('POSTGRES_PASSWORD')
    postgres_db = os.getenv('POSTGRES_DATABASE', 'claims_db')

    DATABASE_URL = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

    with open(workspace_path, 'r') as f:
        pdf_dir = f.read().strip()

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)

    # Get historical claims
    with SessionLocal() as session:
        query = text("""
            SELECT CAST(id AS text) as id, claim_number, claim_type
            FROM claims
            WHERE status = 'pending'
            ORDER BY claim_number
            LIMIT :limit
        """)
        claims = session.execute(query, {"limit": num_historical_claims}).fetchall()

    converter = DocumentConverter()
    parsed = 0

    logger.info(f"Parsing {len(claims)} PDFs with Docling...")

    for claim_id, claim_num, claim_type in claims:
        pdf_path = os.path.join(pdf_dir, f"{claim_num}.pdf")

        if not os.path.exists(pdf_path):
            logger.warning(f"  PDF not found: {claim_num}")
            continue

        try:
            result = converter.convert(pdf_path)
            ocr_text = result.document.export_to_markdown()
            confidence = 0.95

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
            logger.info(f"  Parsed: {claim_num} ({parsed}/{len(claims)})")

        except Exception as e:
            logger.error(f"  Error parsing {claim_num}: {e}")

    engine.dispose()
    logger.info(f"✅ Parsed {parsed}/{len(claims)} PDFs")
    metrics.log_metric("pdfs_parsed", parsed)


@component(
    base_image="registry.access.redhat.com/ubi9/python-312:latest",
    packages_to_install=["httpx==0.27.0", "sqlalchemy==2.0.25", "psycopg2-binary==2.9.9"]
)
def generate_historical_embeddings(
    num_historical_claims: int,
    postgres_host: str,
    postgres_port: str,
    llamastack_endpoint: str,
    embedding_model: str,
    metrics: Output[Metrics]
):
    """Step 4: Generate embeddings for historical claim_documents."""
    import asyncio
    import logging
    import os
    from typing import List, Optional
    import httpx
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Get credentials from environment (injected from secret)
    postgres_user = os.getenv('POSTGRES_USER', 'claims_user')
    postgres_password = os.getenv('POSTGRES_PASSWORD')
    postgres_db = os.getenv('POSTGRES_DATABASE', 'claims_db')

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
            logger.error(f"Error: {e}")
            return None

    def format_embedding(embedding: List[float]) -> str:
        return '[' + ','.join(str(x) for x in embedding) + ']'

    async def process():
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=engine)
        emb_count = 0

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
                    LIMIT :limit
                """)
                docs = session.execute(query, {"limit": num_historical_claims}).fetchall()

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
                        emb_count += 1

                await asyncio.sleep(0.3)

        engine.dispose()
        logger.info(f"✅ Historical embeddings: {emb_count}/{num_historical_claims}")
        metrics.log_metric("historical_embeddings", emb_count)

    asyncio.run(process())


@component(
    base_image="registry.access.redhat.com/ubi9/python-312:latest",
    packages_to_install=["httpx==0.27.0", "sqlalchemy==2.0.25", "psycopg2-binary==2.9.9"]
)
def generate_historical_decisions(
    num_historical_claims: int,
    postgres_host: str,
    postgres_port: str,
    llamastack_endpoint: str,
    llm_model: str,
    metrics: Output[Metrics]
):
    """Step 5: Generate AI decisions and mark historical claims as completed."""
    import asyncio
    import logging
    import json
    import os
    import httpx
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Get credentials from environment (injected from secret)
    postgres_user = os.getenv('POSTGRES_USER', 'claims_user')
    postgres_password = os.getenv('POSTGRES_PASSWORD')
    postgres_db = os.getenv('POSTGRES_DATABASE', 'claims_db')

    DATABASE_URL = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

    async def generate_decision(claim_data: dict, client: httpx.AsyncClient) -> dict:
        prompt = f"""Analyze this insurance claim and provide a decision.

Claim: {claim_data['claim_number']}
Type: {claim_data['claim_type']}
Amount: ${claim_data['amount']}
Description: {claim_data['description']}

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

        async with httpx.AsyncClient() as client:
            logger.info("=== Generating Historical Decisions ===")

            with SessionLocal() as session:
                query = text("""
                    SELECT CAST(id AS text) as id, claim_number, claim_type, amount, description
                    FROM claims
                    WHERE status = 'pending'
                    ORDER BY claim_number
                    LIMIT :limit
                """)
                claims = session.execute(query, {"limit": num_historical_claims}).fetchall()

            for claim_id, claim_num, claim_type, amount, description in claims:
                logger.info(f"  Processing: {claim_num}")

                decision = await generate_decision({
                    "claim_number": claim_num,
                    "claim_type": claim_type,
                    "amount": float(amount),
                    "description": description
                }, client)

                with SessionLocal() as session:
                    # Update claim status to completed
                    session.execute(text("""
                        UPDATE claims
                        SET status = 'completed', decision = :decision, processing_completed_at = NOW()
                        WHERE CAST(id AS text) = :claim_id
                    """), {"decision": decision["decision"], "claim_id": claim_id})

                    # Insert decision record
                    session.execute(text("""
                        INSERT INTO claim_decisions
                        (claim_id, decision_type, decision, reasoning, confidence_score, decided_by)
                        VALUES (CAST(:claim_id AS uuid), 'system', :decision, :reasoning, :confidence, 'AI-Historical')
                    """), {
                        "claim_id": claim_id,
                        "decision": decision["decision"],
                        "reasoning": decision.get("reasoning", ""),
                        "confidence": decision.get("confidence", 0.8)
                    })
                    session.commit()

                processed += 1
                await asyncio.sleep(1)

        engine.dispose()
        logger.info(f"✅ Historical decisions: {processed}/{num_historical_claims}")
        metrics.log_metric("historical_decisions", processed)

    asyncio.run(process())


@component(
    base_image="registry.access.redhat.com/ubi9/python-312:latest",
    packages_to_install=["httpx==0.27.0", "sqlalchemy==2.0.25", "psycopg2-binary==2.9.9"]
)
def generate_test_claims(
    num_historical_claims: int,
    postgres_host: str,
    postgres_port: str,
    llamastack_endpoint: str,
    embedding_model: str,
    metrics: Output[Metrics]
):
    """Step 6: Generate claim_documents for test claims (APPROVE/DENY/MANUAL_REVIEW)."""
    import asyncio
    import logging
    import os
    from typing import List, Optional
    import httpx
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Get credentials from environment (injected from secret)
    postgres_user = os.getenv('POSTGRES_USER', 'claims_user')
    postgres_password = os.getenv('POSTGRES_PASSWORD')
    postgres_db = os.getenv('POSTGRES_DATABASE', 'claims_db')

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
                    # Determine scenario based on amount (simplified)
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
    name="complete-data-initialization",
    description="Complete data initialization: KB embeddings + historical claims + test scenarios"
)
def complete_data_init_pipeline(
    num_historical_claims: int = 60,
    postgres_host: str = "postgresql.claims-demo.svc.cluster.local",
    postgres_port: str = "5432",
    llamastack_endpoint: str = "http://llamastack-rhoai-service.claims-demo.svc.cluster.local:8321",
    embedding_model: str = "vllm-embedding/embeddinggemma-300m",
    llm_model: str = "vllm-inference/llama-3-3-70b-instruct-quantized-w8a8"
):
    """
    Complete data initialization pipeline.

    Steps:
    1. Generate Knowledge Base embeddings (15)
    2. Generate historical claims PDFs (60)
    3. Parse PDFs with Docling
    4. Generate embeddings for historical claims
    5. Generate AI decisions (mark as completed)
    6. Generate test claims with APPROVE/DENY/MANUAL_REVIEW scenarios (40)
    """

    # Step 1: KB Embeddings
    kb_task = generate_kb_embeddings(
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        llamastack_endpoint=llamastack_endpoint,
        embedding_model=embedding_model
    )
    kb_task.set_display_name('1. Generate KB Embeddings')
    kb_task.set_cpu_limit('1')
    kb_task.set_memory_limit('2Gi')

    # Inject PostgreSQL credentials from Kubernetes secret
    kubernetes.use_secret_as_env(
        kb_task,
        secret_name='postgresql-secret',
        secret_key_to_env={
            'POSTGRES_USER': 'POSTGRES_USER',
            'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
            'POSTGRES_DATABASE': 'POSTGRES_DATABASE'
        }
    )

    # Step 2: Generate Historical PDFs
    pdf_task = generate_historical_pdfs(
        num_historical_claims=num_historical_claims,
        postgres_host=postgres_host,
        postgres_port=postgres_port
    )
    pdf_task.set_display_name('2. Generate Historical PDFs')
    pdf_task.set_cpu_limit('1')
    pdf_task.set_memory_limit('2Gi')
    pdf_task.after(kb_task)

    # Inject PostgreSQL credentials from Kubernetes secret
    kubernetes.use_secret_as_env(
        pdf_task,
        secret_name='postgresql-secret',
        secret_key_to_env={
            'POSTGRES_USER': 'POSTGRES_USER',
            'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
            'POSTGRES_DATABASE': 'POSTGRES_DATABASE'
        }
    )

    # Step 3: Parse PDFs with Docling
    parse_task = parse_historical_pdfs(
        workspace_path=pdf_task.output,
        num_historical_claims=num_historical_claims,
        postgres_host=postgres_host,
        postgres_port=postgres_port
    )
    parse_task.set_display_name('3. Parse PDFs with Docling')
    parse_task.set_cpu_limit('2')
    parse_task.set_memory_limit('8Gi')

    # Inject PostgreSQL credentials from Kubernetes secret
    kubernetes.use_secret_as_env(
        parse_task,
        secret_name='postgresql-secret',
        secret_key_to_env={
            'POSTGRES_USER': 'POSTGRES_USER',
            'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
            'POSTGRES_DATABASE': 'POSTGRES_DATABASE'
        }
    )

    # Step 4: Generate Historical Embeddings
    hist_emb_task = generate_historical_embeddings(
        num_historical_claims=num_historical_claims,
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        llamastack_endpoint=llamastack_endpoint,
        embedding_model=embedding_model
    )
    hist_emb_task.set_display_name('4. Generate Historical Embeddings')
    hist_emb_task.set_cpu_limit('1')
    hist_emb_task.set_memory_limit('2Gi')
    hist_emb_task.after(parse_task)

    # Inject PostgreSQL credentials from Kubernetes secret
    kubernetes.use_secret_as_env(
        hist_emb_task,
        secret_name='postgresql-secret',
        secret_key_to_env={
            'POSTGRES_USER': 'POSTGRES_USER',
            'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
            'POSTGRES_DATABASE': 'POSTGRES_DATABASE'
        }
    )

    # Step 5: Generate Historical Decisions
    decisions_task = generate_historical_decisions(
        num_historical_claims=num_historical_claims,
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        llamastack_endpoint=llamastack_endpoint,
        llm_model=llm_model
    )
    decisions_task.set_display_name('5. Generate Historical Decisions')
    decisions_task.set_cpu_limit('1')
    decisions_task.set_memory_limit('2Gi')
    decisions_task.after(hist_emb_task)

    # Inject PostgreSQL credentials from Kubernetes secret
    kubernetes.use_secret_as_env(
        decisions_task,
        secret_name='postgresql-secret',
        secret_key_to_env={
            'POSTGRES_USER': 'POSTGRES_USER',
            'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
            'POSTGRES_DATABASE': 'POSTGRES_DATABASE'
        }
    )

    # Step 6: Generate Test Claims
    test_task = generate_test_claims(
        num_historical_claims=num_historical_claims,
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        llamastack_endpoint=llamastack_endpoint,
        embedding_model=embedding_model
    )
    test_task.set_display_name('6. Generate Test Claims')
    test_task.set_cpu_limit('1')
    test_task.set_memory_limit('2Gi')
    test_task.after(decisions_task)

    # Inject PostgreSQL credentials from Kubernetes secret
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
        package_path="complete_data_initialization_pipeline.yaml"
    )
    print("✅ Pipeline compiled: complete_data_initialization_pipeline.yaml")
