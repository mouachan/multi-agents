#!/usr/bin/env python3
"""
KFP Pipeline: Data Initialization
Generates embeddings for knowledge_base and claim_documents after database initialization.
"""
from kfp import dsl, compiler
from kfp.dsl import component, Output, Metrics


@component(
    base_image="registry.access.redhat.com/ubi9/python-312:latest",
    packages_to_install=["httpx==0.27.0", "sqlalchemy==2.0.25", "psycopg2-binary==2.9.9"]
)
def generate_embeddings(
    postgres_host: str,
    postgres_port: str,
    postgres_db: str,
    postgres_user: str,
    postgres_password: str,
    llamastack_endpoint: str,
    embedding_model: str,
    metrics: Output[Metrics]
):
    """Generate embeddings for knowledge_base and claim_documents."""
    import asyncio
    import logging
    from typing import List, Optional
    import httpx
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    DATABASE_URL = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

    # OCR templates for claims
    OCR_TEMPLATES = {
        "Auto": [
            "Vehicle damage claim. Accident date: 2025-11-15. Driver: {name}. Vehicle: 2020 Toyota Camry. Damage: Front bumper and hood. Estimated repair: $4,500. Police report #: 2025-11-15-0042.",
            "Auto insurance claim for collision. Date of incident: 2025-10-20. Insured: {name}. Vehicle: Honda Accord 2019. Damage assessment: $6,200.",
            "Car accident claim filed 2025-12-01. Policyholder: {name}. Vehicle: Ford F-150 2021. Est. repair cost: $3,800.",
        ],
        "Home": [
            "Home insurance claim for water damage. Property owner: {name}. Date of loss: 2025-11-10. Cause: Burst pipe. Estimated damages: $12,000.",
            "Property damage claim. Homeowner: {name}. Incident: Wind damage to roof. Estimate: $8,500.",
            "Residential claim. Owner: {name}. Damage: Fire in kitchen. Loss estimate: $25,000.",
        ],
        "Medical": [
            "Medical insurance claim. Patient: {name}. Service: Appendectomy. Total charges: $18,500. Hospital stay: 2 days.",
            "Healthcare claim. Insured: {name}. Treatment: MRI scan and consultation. Billed: $3,200.",
            "Health insurance claim for ER visit. Patient: {name}. Treatment: CT scan, pain management. Charges: $5,600.",
        ]
    }

    SHORT_OCR_TEMPLATE = "Claim document for {name}. Date: {date}. Damage noted."

    async def create_embedding(text: str, client: httpx.AsyncClient) -> Optional[List[float]]:
        """Create embedding using LlamaStack."""
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
        """Format for PostgreSQL pgvector."""
        return '[' + ','.join(str(x) for x in embedding) + ']'

    async def process():
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=engine)

        kb_count = 0
        claim_full = 0
        claim_short = 0

        # Short OCR claims for MANUAL_REVIEW
        short_claims = [
            "CLM-2024-0020", "CLM-2024-0044", "CLM-2024-0057",
            "CLM-2024-0074", "CLM-2024-0075", "CLM-2024-0076",
            "CLM-2024-0088", "CLM-2024-0089", "CLM-2024-0096",
            "CLM-2024-0098"
        ]

        async with httpx.AsyncClient() as client:
            # 1. Knowledge Base embeddings
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

            # 2. Claim Documents
            logger.info("=== Generating Claim Documents ===")
            with SessionLocal() as session:
                query = text("""
                    SELECT CAST(c.id AS text) as claim_id, c.claim_number, c.claim_type,
                           c.document_path, u.full_name
                    FROM claims c
                    LEFT JOIN claim_documents cd ON c.id = cd.claim_id
                    JOIN users u ON c.user_id = u.user_id
                    WHERE cd.id IS NULL
                    ORDER BY c.claim_number
                """)
                claims = [(r.claim_id, r.claim_number, r.claim_type, r.document_path, r.full_name)
                         for r in session.execute(query).fetchall()]

            for claim_id, claim_num, claim_type, doc_path, full_name in claims:
                is_short = claim_num in short_claims

                if is_short:
                    ocr_text = SHORT_OCR_TEMPLATE.format(name=full_name, date="2025-12")
                    claim_short += 1
                else:
                    import random
                    template = random.choice(OCR_TEMPLATES.get(claim_type, OCR_TEMPLATES["Auto"]))
                    ocr_text = template.format(name=full_name)
                    claim_full += 1

                logger.info(f"  Claim: {claim_num} ({'SHORT' if is_short else 'FULL'})")

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
                            "file_path": doc_path,
                            "ocr_text": ocr_text,
                            "confidence": 0.95 if not is_short else 0.60,
                            "emb": format_embedding(embedding)
                        })
                        session.commit()

                await asyncio.sleep(0.3)

        engine.dispose()

        # Log metrics
        logger.info(f"\n{'='*60}")
        logger.info(f"SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Knowledge Base embeddings: {kb_count}")
        logger.info(f"✅ Claim docs (full OCR): {claim_full}")
        logger.info(f"⚠️  Claim docs (short OCR): {claim_short}")
        logger.info(f"✅ Total: {kb_count + claim_full + claim_short}")
        logger.info(f"{'='*60}")

        # Report to KFP
        metrics.log_metric("kb_embeddings", kb_count)
        metrics.log_metric("claim_full_ocr", claim_full)
        metrics.log_metric("claim_short_ocr", claim_short)
        metrics.log_metric("total_embeddings", kb_count + claim_full + claim_short)

    asyncio.run(process())


@dsl.pipeline(
    name="data-initialization",
    description="Generate embeddings for knowledge base and claims after database init"
)
def data_init_pipeline(
    postgres_host: str = "postgresql.claims-demo.svc.cluster.local",
    postgres_port: str = "5432",
    postgres_db: str = "claims_db",
    postgres_user: str = "claims_user",
    postgres_password: str = "",  # Injected from secret
    llamastack_endpoint: str = "http://llamastack-rhoai-service.claims-demo.svc.cluster.local:8321",
    embedding_model: str = "gemma-300m"
):
    """Data initialization pipeline."""

    generate_embeddings_task = generate_embeddings(
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        postgres_db=postgres_db,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
        llamastack_endpoint=llamastack_endpoint,
        embedding_model=embedding_model
    )

    # Set resource limits
    generate_embeddings_task.set_cpu_limit("2")
    generate_embeddings_task.set_memory_limit("4Gi")


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=data_init_pipeline,
        package_path="data_initialization_pipeline.yaml"
    )
    print("✅ Pipeline compiled to data_initialization_pipeline.yaml")
