"""Demo reset: back to the state right after installation, keeping what is costly to rebuild.

The seed SQL (the same file as the database init) brings every business record back to its
initial state. What data-init and the processings computed since then is kept, so that the
precedent searches work right away instead of starting from zero:

  1. snapshot  documents (OCR text + embedding), links to the PDFs in OGX Files,
               embeddings of the reference data, decisions of the installation precedents
  2. reload    truncate the business tables (the chat history is kept) and run the seed
  3. restore   put the snapshot back, matching records by their business key

Everything runs in one transaction: a failure leaves the database untouched. Rows travel as
JSON (row_to_json / json_populate_record), so every column type (enum, jsonb, vector) is
restored without listing the columns.
"""
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domains import DomainSpec, all_domains

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Domain:
    """The tables of a domain, as the reset's SQL uses them (from its DomainSpec)."""
    entities: str        # the cases, e.g. claims
    number: str          # business key column, e.g. claim_number
    fk: str              # foreign key of the child tables, e.g. claim_id
    documents: str       # OCR documents (text + embedding)
    decisions: str       # agent decisions
    precedents_key: str  # section of precedent_decisions.json
    spec: DomainSpec

    @classmethod
    def of(cls, spec: DomainSpec) -> "Domain":
        return cls(spec.model.__tablename__, spec.number_field, spec.fk, spec.document_model.__tablename__,
                   spec.decision_model.__tablename__, spec.precedents_key, spec)


DOMAINS = [Domain.of(spec) for spec in all_domains()]

# Reference data searched by the RAG tools: business key of each row
REFERENCE_KEYS = {
    "company_references": "reference_number",
    "historical_tenders": "ao_number",
    "company_capabilities": "category || '/' || name",
    "knowledge_base": "title",
    "courrier_knowledge_base": "title",
    "user_contracts": "contract_number",
}

# Tables loaded by the seed or written by the processings (chat_sessions/messages are kept)
BUSINESS_TABLES = [
    "users", "user_contracts", "knowledge_base", "claims", "claim_documents", "claim_decisions",
    "processing_logs", "guardrails_detections",
    "tenders", "tender_documents", "tender_decisions", "tender_processing_logs",
    "company_references", "historical_tenders", "company_capabilities",
    "reclamations", "reclamation_documents", "reclamation_decisions", "reclamation_processing_logs",
    "tracking_events", "courrier_knowledge_base",
]


def _precedent_numbers() -> Dict[str, List[str]]:
    """Business numbers of the precedents processed at installation, per domain."""
    data = json.loads(Path(settings.precedents_file).read_text(encoding="utf-8"))
    return {d.precedents_key: [p[d.number] for p in data.get(d.precedents_key, [])] for d in DOMAINS}


async def _rows(db: AsyncSession, sql: str, **params) -> List[Any]:
    return list((await db.execute(text(sql), params)).all())


# ---------------------------------------------------------------------------------- snapshot
async def _snapshot(db: AsyncSession, precedents: Dict[str, List[str]]) -> Dict[str, Any]:
    snap: Dict[str, Any] = {"documents": {}, "links": {}, "decisions": {}, "references": {}}
    for d in DOMAINS:
        snap["documents"][d.entities] = await _rows(db, f"""
            SELECT e.{d.number}, row_to_json(doc)::text FROM {d.documents} doc
            JOIN {d.entities} e ON e.id = doc.{d.fk}
            WHERE doc.raw_ocr_text IS NOT NULL OR doc.embedding IS NOT NULL""")
        snap["links"][d.entities] = await _rows(db, f"""
            SELECT {d.number}, document_path, metadata->>'document_file_id_en' FROM {d.entities}
            WHERE document_path LIKE 'file-%'""")
        # The first decision of each precedent is the installation one
        snap["decisions"][d.entities] = await _rows(db, f"""
            SELECT e.{d.number}, row_to_json(dec)::text FROM {d.entities} e
            JOIN LATERAL (SELECT * FROM {d.decisions} WHERE {d.fk} = e.id
                          ORDER BY created_at LIMIT 1) dec ON true
            WHERE e.{d.number} = ANY(:numbers)""", numbers=precedents[d.precedents_key])
    for table, key in REFERENCE_KEYS.items():
        snap["references"][table] = await _rows(
            db, f"SELECT {key}, embedding::text FROM {table} WHERE embedding IS NOT NULL")
    return snap


# ------------------------------------------------------------------------------------ reload
async def _reload_seed(db: AsyncSession) -> None:
    seed_sql = Path(settings.seed_data_file).read_text(encoding="utf-8")
    await db.execute(text(f"TRUNCATE TABLE {', '.join(BUSINESS_TABLES)} CASCADE"))
    # The seed holds many statements: run it with the simple query protocol of asyncpg,
    # on the session's connection (same transaction)
    connection = await db.connection()
    raw = await connection.get_raw_connection()
    await raw.driver_connection.execute(seed_sql)


# ----------------------------------------------------------------------------------- restore
async def _entity_ids(db: AsyncSession, d: Domain) -> Dict[str, str]:
    return {num: str(id_) for num, id_ in await _rows(db, f"SELECT {d.number}, id FROM {d.entities}")}


def _with_fk(row_json: str, fk: str, entity_id: str) -> str:
    row = json.loads(row_json)
    row[fk] = entity_id  # ids generated by the seed may differ from the snapshot ones
    return json.dumps(row)


async def _restore(db: AsyncSession, snap: Dict[str, Any]) -> Dict[str, int]:
    counts = {"documents": 0, "document_links": 0, "precedent_decisions": 0, "reference_embeddings": 0}
    for d in DOMAINS:
        ids = await _entity_ids(db, d)

        for number, row_json in snap["documents"][d.entities]:
            if number not in ids:
                continue  # record created during the demo: gone with the reset
            row = _with_fk(row_json, d.fk, ids[number])
            # Seeded documents keep their columns and get back their OCR text and embedding.
            # Matched by business key (entity + file): the seed may generate new ids.
            updated = await db.execute(text(f"""
                UPDATE {d.documents} doc SET raw_ocr_text = COALESCE(doc.raw_ocr_text, r.raw_ocr_text),
                    embedding = COALESCE(doc.embedding, r.embedding)
                FROM json_populate_record(NULL::{d.documents}, CAST(:row AS json)) r
                WHERE doc.{d.fk} = r.{d.fk} AND COALESCE(doc.file_path, '') = COALESCE(r.file_path, '')"""),
                {"row": row})
            if not updated.rowcount:
                await db.execute(text(f"""
                    INSERT INTO {d.documents}
                    SELECT * FROM json_populate_record(NULL::{d.documents}, CAST(:row AS json))
                    ON CONFLICT DO NOTHING"""), {"row": row})
            counts["documents"] += 1

        for number, path, file_en in snap["links"][d.entities]:
            result = await db.execute(text(f"""
                UPDATE {d.entities} SET document_path = :path,
                    metadata = CASE WHEN CAST(:file_en AS text) IS NULL THEN metadata ELSE
                        jsonb_set(COALESCE(metadata, '{{}}'::jsonb), '{{document_file_id_en}}', to_jsonb(CAST(:file_en AS text))) END
                WHERE {d.number} = :number"""), {"path": path, "file_en": file_en, "number": number})
            counts["document_links"] += result.rowcount

        for number, row_json in snap["decisions"][d.entities]:
            if number not in ids:
                continue
            await db.execute(text(f"""
                INSERT INTO {d.decisions}
                SELECT * FROM json_populate_record(NULL::{d.decisions}, CAST(:row AS json))"""),
                {"row": _with_fk(row_json, d.fk, ids[number])})
            # Status of the installation decision (not the current one: the precedent may have
            # been processed again during the demo). json_populate_record casts the text to
            # the column type (enum or varchar).
            recommendation = json.loads(row_json).get("initial_decision")
            status = d.spec.status_after(recommendation)
            await db.execute(text(f"""
                UPDATE {d.entities} e SET status = r.status
                FROM json_populate_record(NULL::{d.entities}, CAST(:row AS json)) r
                WHERE e.id = CAST(:id AS uuid)"""), {"row": json.dumps({"status": status}), "id": ids[number]})
            counts["precedent_decisions"] += 1

    for table, key in REFERENCE_KEYS.items():
        for value, embedding in snap["references"][table]:
            result = await db.execute(
                text(f"UPDATE {table} SET embedding = CAST(:embedding AS vector) WHERE {key} = :value"),
                {"embedding": embedding, "value": value})
            counts["reference_embeddings"] += result.rowcount
    return counts


# -------------------------------------------------------------------------------------- entry
async def reset_demo_data(db: AsyncSession) -> Dict[str, Any]:
    """Run the reset in one transaction; returns what was reloaded and restored."""
    precedents = _precedent_numbers()
    try:
        snap = await _snapshot(db, precedents)
        await _reload_seed(db)
        restored = await _restore(db, snap)
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    loaded = {table: (await db.execute(text(f"SELECT COUNT(*) FROM {table}"))).scalar()
              for table in ("users", "user_contracts", "claims", "tenders", "reclamations", "knowledge_base")}
    logger.info("Demo reset: loaded %s, restored %s", loaded, restored)
    return {"loaded": loaded, "restored": restored}
