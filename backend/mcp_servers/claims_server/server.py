"""MCP server of the insurance claims: read the claims, and compute a payout in the OpenShell sandbox.

The decisions are not written here: the backend saves the agent's decision after a processing, and
the reviewer's decision (backend/app/services/decisions.py, review.py).
"""
import json
import os
import re
from typing import Any, Dict, Optional, Tuple

from shared.cases import CLAIMS, case_documents, case_statistics, find_case, get_case, list_cases
from shared.db import fetch_one
from shared.server import create_mcp, serve
from shared.tools import ToolError, tool

mcp = create_mcp("claims-server")


@tool(mcp)
async def list_claims(status: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """
    List insurance claims, the most recent first, with their current decision. "matching" is the number of
    claims with this status (the answer to "how many"); the list holds the most recent ones.

    Args:
        status: Optional status filter (pending, processing, completed, denied, manual_review, failed)
        limit: Maximum number of claims (default 10, at most 100)
    """
    return await list_cases(CLAIMS, status, limit)


@tool(mcp)
async def get_claim(claim_id: str) -> Dict[str, Any]:
    """
    Get a claim: number, type, status, dates, claimant, metadata, and its current decision.
    If has_document is true, ocr_document(document_id=<claim number>) reads its document.

    Args:
        claim_id: The claim number (e.g. CLM-2024-0001)
    """
    return await get_case(CLAIMS, claim_id)


@tool(mcp)
async def get_claim_documents(claim_id: str) -> Dict[str, Any]:
    """
    Get the documents of a claim with the beginning of their OCR text (empty until ocr_document
    has read them).

    Args:
        claim_id: The claim number (e.g. CLM-2024-0001)
    """
    return await case_documents(CLAIMS, claim_id)


@tool(mcp)
async def get_claim_statistics() -> Dict[str, Any]:
    """Get statistics of the claims: count by status, processing times, current decisions."""
    return await case_statistics(CLAIMS)


# ---------------------------------------------------------------------------------- payout

# run_python tool of the sandbox MCP server (OpenShell); empty when the sandbox is not deployed
SANDBOX_MCP_URL = os.getenv("SANDBOX_MCP_URL", "")
# The contract type that covers each claim type
COVERING_CONTRACT = {"Auto": "Auto Insurance", "Home": "Home Insurance",
                     "Medical": "Health Insurance", "Life": "Life Insurance"}
# The line of the claim form that holds the amount claimed (French form; its English translation)
AMOUNT_LABELS = ("Montant r[ée]clam[ée]", "Amount Claimed")
# "12 600,00 €" (French) or "€12,600.00" (English): digits with spaces, dots or commas, and a currency
AMOUNT = re.compile(r"(€|\$|EUR|USD)?\s*([0-9][0-9 \u00a0\u202f.,]*[0-9])\s*(€|\$|EUR|USD)?")
CURRENCIES = {"€": "EUR", "EUR": "EUR", "$": "USD", "USD": "USD"}
FORMULA = "payout = min(max(claimed - franchise, 0), ceiling); 0 without an active contract of the claim type"


@tool(mcp)
async def compute_payout(claim_id: str) -> Dict[str, Any]:
    """
    Compute the payout of a claim (coverage check and amount) in the OpenShell sandbox.

    Reads the claim type, the claimant's ACTIVE contract matching that type (coverage ceiling,
    franchise) and the amount claimed in the claim document (OCR text: call ocr_document first if
    it is missing). The computation runs in an isolated OpenShell sandbox (no network,
    kernel-enforced policy). Report the returned figures as they are.

    Args:
        claim_id: The claim number (e.g. CLM-2024-0001)

    Returns: claim_number, claim_type, covered, contract (number, type, coverage_amount,
    franchise) or null, claimed_amount, claimed_source, currency, formula, payout, code,
    sandbox_run (exit code, output, sandbox name and timings)
    """
    figures = await _payout_figures(claim_id)
    # without a payout, the figures are still returned: the reviewer sees the contract and the amounts
    if not SANDBOX_MCP_URL:
        return {**figures, "success": False, "error": "The OpenShell sandbox is not deployed"}
    run = await _run_in_sandbox(figures["code"])
    payout = _printed_value(run.get("stdout", ""), "payout")
    if not run.get("success") or payout is None:
        return {**figures, "success": False, "sandbox_run": run,
                "error": f"The sandbox run failed: {run.get('stderr') or run.get('error') or 'no payout printed'}"}
    return {**figures, "payout": payout, "sandbox_run": run}


async def _payout_figures(reference: str) -> Dict[str, Any]:
    """The exact figures of a claim for its payout, and the code that computes it."""
    claim = await find_case(CLAIMS, reference)
    document = await fetch_one("""
        SELECT raw_ocr_text FROM claim_documents WHERE claim_id = CAST(:id AS uuid)
        AND COALESCE(raw_ocr_text, '') <> '' ORDER BY created_at DESC LIMIT 1""", id=claim["id"])
    if document is None:
        raise ToolError(f"No OCR text for claim {claim['number']}: call ocr_document first")
    text = document["raw_ocr_text"]
    claimed, currency, source = _claimed_amount(text)
    contract_type = COVERING_CONTRACT.get(claim["claim_type"])
    contract = await fetch_one("""
        SELECT contract_number, contract_type, coverage_amount, key_terms->>'franchise' AS franchise
        FROM user_contracts WHERE user_id = :user AND is_active AND contract_type = :type
        ORDER BY coverage_amount DESC LIMIT 1""", user=claim["user_id"], type=contract_type) if contract_type else None

    covered = contract is not None
    franchise = float(contract["franchise"] or 0) if covered else 0.0
    ceiling = float(contract["coverage_amount"]) if covered else 0.0
    values = {"claim_type": claim["claim_type"], "contract": contract["contract_number"] if covered else "NONE",
              "claimed": claimed or 0.0, "deductible": franchise, "ceiling": ceiling, "covered": covered}
    code = "\n".join([*(f"{name} = {value!r}" for name, value in values.items()),
                      "payout = min(max(claimed - deductible, 0), ceiling) if covered else 0.0",
                      *(f"print('{name}:', {name})" for name in ("claim_type", "contract", "claimed",
                                                                  "deductible", "ceiling", "payout"))])
    return {
        "claim_number": claim["number"],
        "claim_type": claim["claim_type"],
        "covered": covered,
        "contract": {"number": contract["contract_number"], "type": contract["contract_type"],
                     "coverage_amount": ceiling, "franchise": franchise} if covered else None,
        "claimed_amount": claimed,
        "currency": currency,       # of the claim form; the contracts' amounts share it
        "claimed_source": f"{source} (claim document)" if source else "not found in the claim document",
        "formula": FORMULA,
        "code": code,
    }


def _claimed_amount(document_text: str) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    """(amount, currency, label) of the "amount claimed" line of the claim form, Nones when not found."""
    for label in AMOUNT_LABELS:
        line = re.search(rf"({label})\s*:?\s*(.+)", document_text, re.IGNORECASE)
        amount = AMOUNT.search(line.group(2)) if line else None
        if amount:
            currency = CURRENCIES.get(amount.group(1) or amount.group(3) or "")
            return _number(amount.group(2)), currency, line.group(1)
    return None, None, None


def _number(text: str) -> float:
    """"12 600,00" or "12,600.00" -> 12600.0 (the last separator followed by 1-2 digits is the decimal one)."""
    digits = re.sub(r"[\s\u00a0\u202f]", "", text)
    decimal = re.search(r"[.,](\d{1,2})$", digits)
    whole = digits[:decimal.start()] if decimal else digits
    return float(re.sub(r"[.,]", "", whole) + ("." + decimal.group(1) if decimal else ""))


async def _run_in_sandbox(code: str) -> Dict[str, Any]:
    """Run the code with the run_python tool of the sandbox MCP server."""
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    async with streamablehttp_client(SANDBOX_MCP_URL, timeout=90) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("run_python", {"code": code, "timeout_s": 20})
            return json.loads(result.content[0].text)


def _printed_value(stdout: str, name: str) -> Optional[float]:
    match = re.search(rf"^{name}:\s*([-0-9.]+)\s*$", stdout or "", re.MULTILINE)
    return float(match.group(1)) if match else None


if __name__ == "__main__":
    serve(mcp)
