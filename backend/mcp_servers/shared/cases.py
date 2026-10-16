"""The cases of the three business domains (claims, tenders, postal complaints), read the same way.

A case has a business number (CLM-2024-0001, AO-2026-IDF-001, RECL-2026-0001), a status, documents
(with their OCR text) and decisions: one row per processing, the latest is the current one. What
differs between domains is declared in a CaseTable (CLAIMS, TENDERS, COMPLAINTS at the end of this
file); the domain servers expose these functions as tools with their own names and descriptions.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .db import Row, fetch_all, fetch_one
from .tools import ToolError, required

OCR_PREVIEW_CHARS = 1000   # document text returned by the documents tools


@dataclass(frozen=True)
class CaseTable:
    key: str             # "claim": a case is returned as "claim", a list as "claims"
    label: str           # "Claim", in messages
    prefix: str          # of the business numbers: "CLM-"
    table: str           # claims (alias c in the columns below)
    number: str          # claim_number
    documents: str       # claim_documents
    decisions: str       # claim_decisions
    fk: str              # claim_id, in the documents and decisions tables
    columns: str         # columns of the domain, listed and read (c.claim_type, u.full_name AS user_name)
    details: str = ""    # more columns, read only (c.metadata, u.email AS user_email)
    joins: str = ""      # tables of those columns (LEFT JOIN users u ON u.user_id = c.user_id)
    summary: str = "NULL"  # what the case is about, when its document has not been read yet

    def select(self, details: bool) -> str:
        columns = f"c.id, c.{self.number} AS number, c.status::text AS status, c.submitted_at, c.processed_at, " \
                  f"c.total_processing_time_ms, c.document_path IS NOT NULL AS has_document, {self.columns}"
        if details and self.details:
            columns += f", {self.details}"
        return f"SELECT {columns} FROM {self.table} c {self.joins}"


async def list_cases(t: CaseTable, status: Optional[str], limit: int) -> Dict[str, Any]:
    """The most recent cases, optionally of one status, with their current decision."""
    cases = await fetch_all(f"""
        {t.select(details=False)}
        WHERE c.is_archived = false AND (CAST(:status AS text) IS NULL OR c.status::text = :status)
        ORDER BY c.submitted_at DESC LIMIT :limit""", status=status or None, limit=min(max(limit, 1), 100))
    for case in cases:
        case["decision"] = await _current_decision(t, case["id"], summary=True)
    return {f"{t.key}s": cases, "total_found": len(cases)}


async def find_case(t: CaseTable, reference: str) -> Row:
    """A case by its business number (or its id); ToolError when there is none."""
    reference = required(reference, f"{t.label} number")
    case = await fetch_one(f"{t.select(details=True)} WHERE c.{t.number} = :ref OR CAST(c.id AS text) = :ref",
                           ref=reference)
    if case is None:
        raise ToolError(f"{t.label} {reference} not found")
    return case


async def get_case(t: CaseTable, reference: str) -> Dict[str, Any]:
    """A case with its current decision (the agent's, or the reviewer's when there is one)."""
    case = await find_case(t, reference)
    return {t.key: case, "decision": await _current_decision(t, case["id"])}


async def case_documents(t: CaseTable, reference: str) -> Dict[str, Any]:
    """The documents of a case, with the beginning of their OCR text."""
    case = await find_case(t, reference)
    documents = await fetch_all(f"""
        SELECT document_type, mime_type, page_count, language, ocr_confidence, ocr_processed_at,
               structured_data, LEFT(raw_ocr_text, :chars) AS raw_ocr_text
        FROM {t.documents} WHERE {t.fk} = CAST(:id AS uuid) ORDER BY created_at DESC""",
        id=case["id"], chars=OCR_PREVIEW_CHARS)
    return {"number": case["number"], "documents": documents, "total_documents": len(documents)}


async def case_statistics(t: CaseTable) -> Dict[str, Any]:
    """Cases by status, processing times, current decisions."""
    by_status = await fetch_all(f"""
        SELECT status::text AS status, COUNT(*) AS count FROM {t.table}
        WHERE is_archived = false GROUP BY status ORDER BY count DESC""")
    times = await fetch_one(f"""
        SELECT AVG(total_processing_time_ms) AS average_ms, MIN(total_processing_time_ms) AS min_ms,
               MAX(total_processing_time_ms) AS max_ms
        FROM {t.table} WHERE is_archived = false AND total_processing_time_ms IS NOT NULL""")
    decisions = await fetch_all(f"""
        SELECT d.decision::text AS decision, COUNT(*) AS count, ROUND(AVG(d.confidence)::numeric, 3) AS average_confidence
        FROM {t.table} c JOIN LATERAL (SELECT decision, confidence FROM {t.decisions} WHERE {t.fk} = c.id
                                       ORDER BY created_at DESC LIMIT 1) d ON true
        WHERE c.is_archived = false GROUP BY d.decision""")
    return {
        "total": sum(row["count"] for row in by_status),
        "by_status": {row["status"]: row["count"] for row in by_status},
        "processing_time_ms": times,
        "decisions": {row["decision"]: {"count": row["count"], "average_confidence": row["average_confidence"]}
                      for row in decisions},
    }


async def case_text(t: CaseTable, reference: str) -> str:
    """What a case is about, to search similar records: the OCR text of its latest document, else its
    summary (title, description). ToolError when the case is unknown or has neither."""
    row = await fetch_one(f"""
        SELECT c.{t.number} AS number, {t.summary} AS summary,
               (SELECT d.raw_ocr_text FROM {t.documents} d WHERE d.{t.fk} = c.id AND COALESCE(d.raw_ocr_text, '') <> ''
                ORDER BY d.created_at DESC LIMIT 1) AS document_text
        FROM {t.table} c WHERE c.{t.number} = :number""", number=reference)
    if row is None:
        raise ToolError(f"{t.label} {reference} not found")
    if not (row["document_text"] or row["summary"]):
        raise ToolError(f"No text for {t.label.lower()} {reference}: call ocr_document first")
    return row["document_text"] or row["summary"]


def domain_of(reference: str) -> Optional[CaseTable]:
    """The domain of a business number (CLM-..., AO-..., RECL-...), None for any other text."""
    reference = (reference or "").strip().upper()
    return next((t for t in DOMAINS if reference.startswith(t.prefix)), None)


async def _current_decision(t: CaseTable, case_id: str, summary: bool = False) -> Optional[Row]:
    columns = "decision::text AS decision, confidence" if summary else """
        decision::text AS decision, confidence, reasoning, decided_at, llm_model, requires_manual_review,
        initial_decision::text AS agent_decision, final_decision::text AS reviewer_decision,
        final_decision_at AS reviewed_at, final_decision_notes"""
    return await fetch_one(f"""
        SELECT {columns} FROM {t.decisions} WHERE {t.fk} = CAST(:id AS uuid)
        ORDER BY created_at DESC LIMIT 1""", id=case_id)


# ---------------------------------------------------------------------------------- the domains

CLAIMS = CaseTable(
    key="claim", label="Claim", prefix="CLM-", table="claims", number="claim_number",
    documents="claim_documents", decisions="claim_decisions", fk="claim_id",
    columns="c.claim_type, u.full_name AS user_name",
    details="c.user_id, c.metadata, u.email AS user_email, u.phone_number AS user_phone, u.address AS user_address",
    joins="LEFT JOIN users u ON u.user_id = c.user_id",
    summary="c.metadata->>'description'",
)
TENDERS = CaseTable(
    key="tender", label="Tender", prefix="AO-", table="tenders", number="tender_number",
    documents="tender_documents", decisions="tender_decisions", fk="tender_id",
    columns="c.entity_id, c.tender_type, c.metadata",
    summary="concat_ws(E'\\n', c.metadata->>'titre', c.metadata->>'nature_travaux', c.metadata->>'description')",
)
COMPLAINTS = CaseTable(
    key="reclamation", label="Complaint", prefix="RECL-", table="reclamations", number="reclamation_number",
    documents="reclamation_documents", decisions="reclamation_decisions", fk="reclamation_id",
    columns="c.numero_suivi, c.reclamation_type::text AS reclamation_type, c.client_nom, c.valeur_declaree",
    details="c.client_email, c.client_telephone, c.description, c.metadata",
    summary="c.description",
)
DOMAINS = (CLAIMS, TENDERS, COMPLAINTS)
