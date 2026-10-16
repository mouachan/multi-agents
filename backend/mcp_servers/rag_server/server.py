"""MCP server of the similarity searches (pgvector) and the knowledge bases.

The searches join business tables (decisions of the precedents, results of past tenders, validity
of certifications...), which the generic vector stores of OGX cannot do: the vectors are stored next
to the business rows, and only the embedding model is called through OGX (shared/ogx.py).

A tool that searches "similar" records accepts a case number (CLM-..., AO-..., RECL-...) as well as
a text: with a number it searches with the text of that case (its document), and leaves it out of
the results. A precedent comes with its decision and reasoning, not its document: that is what the
agent compares, and the less text, the less personal data to mask.

The company's reference data (references, past tenders, capabilities) and the knowledge bases hold no
personal data: their tools are declared personal_data=False, their results do not go through NeMo
(masking a page of text takes seconds).
"""
from typing import Any, Dict, List, Optional, Tuple

from shared.cases import CLAIMS, COMPLAINTS, case_text, domain_of, find_case
from shared.db import Row, fetch_all
from shared.ogx import as_vector, embed
from shared.server import create_mcp, serve
from shared.tools import ToolError, required, tool

mcp = create_mcp("rag-server")



async def _search_text(text_or_number: str, name: str) -> Tuple[str, Optional[str]]:
    """(text to search with, the case number to leave out of the results or None)."""
    value = required(text_or_number, name)
    domain = domain_of(value)
    if domain is None:
        return value, None
    return await case_text(domain, value), value


async def _nearest(sql: str, text: str, **params) -> List[Row]:
    """Rows of the query ordered by similarity to the text (the query uses :vector)."""
    return await fetch_all(sql, vector=as_vector(await embed(text)), **params)


def similarity(column: str = "embedding") -> str:
    """SQL: the cosine similarity (0 to 1) of the column to the searched text."""
    return f"ROUND((1 - ({column} <=> CAST(:vector AS vector)))::numeric, 3)"


def by_similarity(column: str = "embedding") -> str:
    return f"ORDER BY {column} <=> CAST(:vector AS vector)"


# ---------------------------------------------------------------------------------- claims

@tool(mcp)
async def retrieve_user_info(user_id: str, query: str = "", top_k: int = 5) -> Dict[str, Any]:
    """
    Get a claimant and their ACTIVE insurance contracts (type, coverage amount, key terms such as
    the franchise, contract text).

    Args:
        user_id: The claimant's id (e.g. USR026) or a claim number (e.g. CLM-2024-0026)
        query: Optional text to rank the contracts by relevance (e.g. "water damage")
        top_k: Maximum number of contracts (default 5)
    """
    user_id = required(user_id, "user_id")
    if domain_of(user_id) is CLAIMS:
        user_id = (await find_case(CLAIMS, user_id))["user_id"]
    users = await fetch_all("SELECT user_id, full_name, email, phone_number, address, date_of_birth "
                            "FROM users WHERE user_id = :user", user=user_id)
    if not users:
        raise ToolError(f"User {user_id} not found")
    columns = "contract_number, contract_type, coverage_amount, key_terms, full_text, is_active"
    limit = min(max(top_k, 1), 50)
    if query.strip():
        contracts = await _nearest(f"""
            SELECT {columns}, {similarity()} AS similarity FROM user_contracts
            WHERE user_id = :user AND is_active AND embedding IS NOT NULL {by_similarity()} LIMIT :limit""",
            query, user=user_id, limit=limit)
    else:
        contracts = await fetch_all(f"SELECT {columns} FROM user_contracts WHERE user_id = :user AND is_active "
                                    "ORDER BY contract_type LIMIT :limit", user=user_id, limit=limit)
    return {"user_info": users[0], "contracts": contracts, "total_contracts": len(contracts)}


@tool(mcp)
async def retrieve_similar_claims(claim_text: str, claim_type: Optional[str] = None, top_k: int = 5,
                                  min_similarity: float = 0.5) -> Dict[str, Any]:
    """
    Find decided claims similar to a claim (precedents), each with its decision, confidence and
    reasoning. With a claim number, the precedents are of the same claim type.

    Args:
        claim_text: A claim number (e.g. CLM-2024-0026) or the text of a claim
        claim_type: Optional claim type filter (Auto, Home, Medical, Life)
        top_k: Maximum number of precedents (default 5)
        min_similarity: Minimum similarity, 0.0 to 1.0 (default 0.5)
    """
    text, current = await _search_text(claim_text, "claim_text")
    if current and not claim_type:
        claim_type = (await find_case(CLAIMS, current))["claim_type"]
    precedents = await _nearest(f"""
        SELECT c.claim_number, c.claim_type, c.status::text AS outcome, {similarity('doc.embedding')} AS similarity_score,
               d.initial_decision::text AS decision, d.initial_confidence AS confidence, LEFT(d.initial_reasoning, 300) AS reasoning
        FROM claim_documents doc JOIN claims c ON c.id = doc.claim_id
        JOIN LATERAL (SELECT initial_decision, initial_confidence, initial_reasoning FROM claim_decisions
                      WHERE claim_id = c.id ORDER BY created_at DESC LIMIT 1) d ON true
        WHERE doc.embedding IS NOT NULL AND c.status::text IN ('completed', 'manual_review', 'denied')
          AND (CAST(:type AS text) IS NULL OR c.claim_type = :type)
          AND (CAST(:current AS text) IS NULL OR c.claim_number <> :current)
          AND {similarity('doc.embedding')} >= :min_similarity
        {by_similarity('doc.embedding')} LIMIT :limit""",
        text, type=claim_type, current=current,
        min_similarity=min(max(min_similarity, 0.0), 1.0), limit=min(max(top_k, 1), 100))
    return {"similar_claims": precedents, "total_found": len(precedents), "claim_type": claim_type}


@tool(mcp, personal_data=False)
async def search_knowledge_base(query: str, top_k: int = 5, category: Optional[str] = None) -> Dict[str, Any]:
    """
    Search the insurance knowledge base (policies, coverage rules, procedures).

    Args:
        query: What to search for
        top_k: Maximum number of articles (default 5)
        category: Optional category filter
    """
    articles = await _nearest(f"""
        SELECT title, content, category, {similarity()} AS similarity_score FROM knowledge_base
        WHERE is_active AND embedding IS NOT NULL AND (CAST(:category AS text) IS NULL OR category = :category)
        {by_similarity()} LIMIT :limit""", required(query, "query"), category=category, limit=min(max(top_k, 1), 50))
    return {"articles": articles, "total_found": len(articles)}


# ---------------------------------------------------------------------------------- tenders

@tool(mcp, personal_data=False)
async def retrieve_similar_references(project_description: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Find the company's past projects (references) similar to a tender: client, type of works,
    amount, region.

    Args:
        project_description: A tender number (e.g. AO-2026-IDF-001) or the description of the project
        top_k: Maximum number of references (default 5)
    """
    text, _ = await _search_text(project_description, "project_description")
    references = await _nearest(f"""
        SELECT reference_number, project_name, maitre_ouvrage, nature_travaux, montant, region,
               LEFT(description, 200) AS description, {similarity()} AS similarity
        FROM company_references WHERE embedding IS NOT NULL {by_similarity()} LIMIT :limit""",
        text, limit=min(max(top_k, 1), 100))
    return {"references": references, "total_found": len(references)}


@tool(mcp, personal_data=False)
async def retrieve_historical_tenders(tender_description: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Find past tenders similar to a tender, won or lost, with the reason of the result, the
    technical and price marks, and the win rate among them.

    Args:
        tender_description: A tender number (e.g. AO-2026-IDF-001) or the description of the tender
        top_k: Maximum number of past tenders (default 5)
    """
    text, _ = await _search_text(tender_description, "tender_description")
    tenders = await _nearest(f"""
        SELECT ao_number, nature_travaux, maitre_ouvrage, montant_estime, region, resultat,
               LEFT(raison_resultat, 150) AS raison_resultat, note_technique, note_prix, {similarity()} AS similarity
        FROM historical_tenders WHERE embedding IS NOT NULL {by_similarity()} LIMIT :limit""",
        text, limit=min(max(top_k, 1), 100))
    won = sum(1 for t in tenders if t["resultat"] == "gagne")
    return {"historical_tenders": tenders, "total_found": len(tenders),
            "win_rate_percentage": round(100 * won / len(tenders), 1) if tenders else 0}


@tool(mcp, personal_data=False)
async def retrieve_capabilities(required_capabilities: str, category: Optional[str] = None,
                                top_k: int = 10) -> Dict[str, Any]:
    """
    Find the company's capabilities matching a need: certifications, equipment, staff, with their
    validity, region and availability.

    Args:
        required_capabilities: A tender number (e.g. AO-2026-IDF-001) or the capabilities needed
        category: Optional category filter (certification, materiel, personnel)
        top_k: Maximum number of capabilities (default 10)
    """
    text, _ = await _search_text(required_capabilities, "required_capabilities")
    capabilities = await _nearest(f"""
        SELECT name, category, LEFT(description, 150) AS description, valid_until, region, availability,
               {similarity()} AS similarity
        FROM company_capabilities WHERE is_active AND embedding IS NOT NULL
          AND (CAST(:category AS text) IS NULL OR category = :category)
        {by_similarity()} LIMIT :limit""", text, category=category, limit=min(max(top_k, 1), 50))
    return {"capabilities": capabilities, "total_found": len(capabilities)}


# ---------------------------------------------------------------------------------- postal

@tool(mcp, personal_data=False)
async def search_courrier_knowledge(query: str, category: str = "", limit: int = 5) -> Dict[str, Any]:
    """
    Search the postal knowledge base: rates, delivery times, packaging, customs, refunds, rules.

    Args:
        query: What to search for (e.g. "tarif colissimo international")
        category: Optional category filter (tarifs, delais, emballage, douane, remboursement)
        limit: Maximum number of articles (default 5)
    """
    articles = await _nearest(f"""
        SELECT title, content, category, tags, {similarity()} AS similarity_score FROM courrier_knowledge_base
        WHERE is_active AND embedding IS NOT NULL AND (CAST(:category AS text) IS NULL OR category = :category)
        {by_similarity()} LIMIT :limit""",
        required(query, "query"), category=category.strip() or None, limit=min(max(limit, 1), 20))
    return {"articles": articles, "total_found": len(articles)}


@tool(mcp)
async def retrieve_similar_reclamations(reclamation_text: str, limit: int = 5) -> Dict[str, Any]:
    """
    Find past postal complaints similar to a complaint (precedents), with their decision.

    Args:
        reclamation_text: A complaint number (e.g. RECL-2026-0001) or the text of a complaint
        limit: Maximum number of precedents (default 5)
    """
    text, current = await _search_text(reclamation_text, "reclamation_text")
    if current and domain_of(current) is not COMPLAINTS:
        raise ToolError("reclamation_text must be a complaint number (RECL-...) or a text")
    precedents = await _nearest(f"""
        SELECT r.reclamation_number, r.reclamation_type::text AS reclamation_type, r.status::text AS status,
               r.description,
               d.decision::text AS decision, d.confidence, d.reasoning,
               {similarity('doc.embedding')} AS similarity_score
        FROM reclamation_documents doc JOIN reclamations r ON r.id = doc.reclamation_id
        LEFT JOIN LATERAL (SELECT decision, confidence, reasoning FROM reclamation_decisions
                           WHERE reclamation_id = r.id ORDER BY created_at DESC LIMIT 1) d ON true
        WHERE doc.embedding IS NOT NULL AND (CAST(:current AS text) IS NULL OR r.reclamation_number <> :current)
        {by_similarity('doc.embedding')} LIMIT :limit""",
        text, current=current, limit=min(max(limit, 1), 20))
    return {"similar_reclamations": precedents, "total_found": len(precedents)}


if __name__ == "__main__":
    serve(mcp)
