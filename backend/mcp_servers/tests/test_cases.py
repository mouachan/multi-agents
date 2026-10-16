"""The case tools of the three domains (shared/cases.py): claims, tenders and postal complaints."""
import pytest

from conftest import call
from shared.db import fetch_one

DOMAINS = [
    # server, list tool, get tool, its argument, documents tool, statistics tool, case key, a seeded case
    ("claims", "list_claims", "get_claim", "claim_id", "get_claim_documents", "get_claim_statistics", "claim",
     "SELECT claim_number AS number FROM claims ORDER BY claim_number LIMIT 1"),
    ("tenders", "list_tenders", "get_tender", "tender_id", "get_tender_documents", "get_tender_statistics", "tender",
     "SELECT tender_number AS number FROM tenders ORDER BY tender_number LIMIT 1"),
    ("postal", "list_reclamations", "get_reclamation", "reclamation_id", "get_reclamation_documents",
     "get_reclamation_statistics", "reclamation",
     "SELECT reclamation_number AS number FROM reclamations ORDER BY reclamation_number LIMIT 1"),
]


@pytest.mark.parametrize("server, list_tool, get_tool, argument, documents_tool, statistics_tool, key, seeded", DOMAINS)
async def test_list_read_documents_statistics(servers, server, list_tool, get_tool, argument, documents_tool,
                                              statistics_tool, key, seeded):
    mcp = servers[server]
    number = (await fetch_one(seeded))["number"]

    listing = await call(mcp, list_tool, limit=5)
    assert listing["success"] and 0 < listing["total_found"] == len(listing[f"{key}s"]) <= 5
    assert "processing_time_seconds" in listing

    case = await call(mcp, get_tool, **{argument: number})
    assert case["success"] and case[key]["number"] == number
    assert "decision" in case and "document_path" not in case[key]

    documents = await call(mcp, documents_tool, **{argument: number})
    assert documents["success"] and documents["number"] == number

    statistics = await call(mcp, statistics_tool)
    assert statistics["success"] and sum(statistics["by_status"].values()) == statistics["total"] > 0


async def test_an_unknown_case_is_refused(servers):
    result = await call(servers["claims"], "get_claim", claim_id="CLM-1999-9999")
    assert result == {**result, "success": False, "error": "Claim CLM-1999-9999 not found"}


async def test_a_status_filter_lists_only_that_status(servers):
    listing = await call(servers["claims"], "list_claims", status="pending", limit=100)
    assert listing["claims"] and {c["status"] for c in listing["claims"]} == {"pending"}


async def test_the_complaint_comes_with_its_tracking_events(servers):
    number = (await fetch_one("""SELECT r.reclamation_number AS number FROM reclamations r
        WHERE EXISTS (SELECT 1 FROM tracking_events t WHERE t.numero_suivi = r.numero_suivi) LIMIT 1"""))["number"]
    complaint = await call(servers["postal"], "get_reclamation", reclamation_id=number)
    assert complaint["tracking_events"] and complaint["tracking_events"][0]["event_type"]


async def test_tracking_timeline(servers):
    parcel = (await fetch_one("SELECT numero_suivi FROM tracking_events LIMIT 1"))["numero_suivi"]
    tracking = await call(servers["tracking"], "get_tracking", numero_suivi=parcel)
    assert tracking["success"] and tracking["total_events"] == len(tracking["events"]) > 0
    assert tracking["last_event"] == tracking["events"][-1] and isinstance(tracking["is_delivered"], bool)


async def test_payout_figures_are_returned_without_the_sandbox(servers, auto_claims):
    # no sandbox in the tests: the figures are still returned, with the error
    number, _ = auto_claims
    payout = await call(servers["claims"], "compute_payout", claim_id=number)
    assert payout["success"] is False and "sandbox" in payout["error"]
    assert payout["claim_number"] == number and payout["covered"] is True
    assert payout["contract"]["type"] == "Auto Insurance" and payout["contract"]["coverage_amount"] > 0
    assert payout["claimed_amount"] == 6200.0 and payout["currency"] == "USD"
    assert payout["claimed_source"] == "Estimated Repair Cost (claim document)"
    assert "payout = min(max(claimed - deductible, 0), ceiling)" in payout["code"]
