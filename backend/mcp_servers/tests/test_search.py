"""The similarity searches and knowledge bases (rag_server), with the stub embedding model."""
from conftest import call
from shared.db import fetch_one


async def a_case_with_text(table: str, documents: str, fk: str, number: str) -> str:
    row = await fetch_one(f"""SELECT c.{number} AS number FROM {table} c JOIN {documents} d ON d.{fk} = c.id
        WHERE COALESCE(d.raw_ocr_text, '') <> '' ORDER BY c.{number} LIMIT 1""")
    return row["number"]


async def test_similar_claims_find_the_decided_precedent(servers, auto_claims):
    number, precedent = auto_claims
    result = await call(servers["rag"], "retrieve_similar_claims", claim_text=number)
    found = {p["claim_number"]: p for p in result["similar_claims"]}
    assert result["claim_type"] == "Auto" and number not in found       # the claim itself is left out
    assert found[precedent]["decision"] == "deny" and found[precedent]["similarity_score"] == 1.0
    assert "claim_text" not in found[precedent]       # the decision and its reasoning, not the document


async def test_tender_searches_accept_a_tender_number(servers):
    number = (await fetch_one("SELECT tender_number AS number FROM tenders ORDER BY tender_number LIMIT 1"))["number"]
    for tool, argument, key in (("retrieve_similar_references", "project_description", "references"),
                                ("retrieve_historical_tenders", "tender_description", "historical_tenders"),
                                ("retrieve_capabilities", "required_capabilities", "capabilities")):
        result = await call(servers["rag"], tool, **{argument: number})
        assert result["success"] and result["total_found"] == len(result[key]) > 0, (tool, result)
    history = await call(servers["rag"], "retrieve_historical_tenders", tender_description=number)
    assert 0 <= history["win_rate_percentage"] <= 100


async def test_similar_complaints(servers):
    number = await a_case_with_text("reclamations", "reclamation_documents", "reclamation_id", "reclamation_number")
    result = await call(servers["rag"], "retrieve_similar_reclamations", reclamation_text=number)
    assert result["success"] and all(p["reclamation_number"] != number for p in result["similar_reclamations"])


async def test_knowledge_bases(servers):
    for tool in ("search_knowledge_base", "search_courrier_knowledge"):
        result = await call(servers["rag"], tool, query="délai de remboursement")
        assert result["success"] and result["articles"], (tool, result)


async def test_an_unknown_case_number_is_refused(servers):
    result = await call(servers["rag"], "retrieve_similar_claims", claim_text="CLM-1999-9999")
    assert result["success"] is False and "not found" in result["error"]
