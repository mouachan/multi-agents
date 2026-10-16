"""Insurance claims: approve, deny, or hand over to a human (Finance profile)."""
from app.domains.spec import DomainSpec, Evidence, ToolOutputs, fact, item, section
from app.models.claim import Claim, ClaimDecision, ClaimDocument


def evidence(outputs: ToolOutputs) -> Evidence:
    """What the reviewer of a claim needs: the payout calculation, the contracts, the precedents."""
    payout = outputs.get("compute_payout", {})
    contract = payout.get("contract") or {}
    contracts = outputs.get("retrieve_user_info", {}).get("contracts", [])
    similar = outputs.get("retrieve_similar_claims", {}).get("similar_claims", [])
    currency = payout.get("currency", "")
    return [
        section("payout", facts=[
            fact("covered", payout.get("covered")),
            fact("contract", " — ".join(filter(None, [contract.get("number"), contract.get("type")]))),
            fact("claimed_amount", payout.get("claimed_amount"), currency),
            fact("franchise", contract.get("franchise"), currency),
            fact("coverage_amount", contract.get("coverage_amount"), currency),
            fact("payout", payout.get("payout"), currency),
            fact("computed_in_sandbox", (payout.get("sandbox_run") or {}).get("success")),
        ]),
        section("contracts", items=[
            item(c.get("contract_number", ""), c.get("contract_type", ""),
                 badge="active" if c.get("is_active") else "inactive")
            for c in contracts
        ]),
        section("similar_cases", items=[
            item(c.get("claim_number", ""), c.get("claim_type", ""), badge=c.get("decision"), score=c.get("similarity_score"))
            for c in similar[:5]
        ]),
    ]


CLAIMS = DomainSpec(
    name="claims",
    entity="claim",
    number_field="claim_number",
    label="Claim",
    model=Claim,
    document_model=ClaimDocument,
    decision_model=ClaimDecision,
    fk="claim_id",
    agent_profile="claims",
    message_file="claims-processing-message.txt",
    processing_tools=[
        "ocr_document",              # the claim document (before the precedent search, which reads it)
        "retrieve_user_info",        # the claimant's contracts
        "retrieve_similar_claims",   # precedents and their decisions
        "search_knowledge_base",     # policy rules
        "compute_payout",            # coverage and amount, computed in the OpenShell sandbox
    ],
    statuses_by_decision={
        "approve": "completed",
        "deny": "denied",
        "manual_review": "manual_review",
    },
    review_decision="manual_review",
    human_decisions=["approve", "deny"],
    evidence=evidence,
    pii_report=True,
    precedents_key="claims",
)
