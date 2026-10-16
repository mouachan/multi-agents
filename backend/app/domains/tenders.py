"""BTP tenders (appels d'offres): bid (go), do not bid (no_go), or look closer (BTP profile)."""
from app.domains.spec import DomainSpec, Evidence, ToolOutputs, fact, item, section
from app.models.tender import Tender, TenderDecision, TenderDocument


def evidence(outputs: ToolOutputs) -> Evidence:
    """What the reviewer of a tender needs: the project, the company's references, the win/loss
    history of similar tenders, and the capabilities it requires."""
    tender = (outputs.get("get_tender", {}).get("tender") or {}).get("metadata") or {}
    references = outputs.get("retrieve_similar_references", {}).get("references", [])
    history = outputs.get("retrieve_historical_tenders", {})
    capabilities = outputs.get("retrieve_capabilities", {}).get("capabilities", [])
    return [
        section("tender", facts=[
            fact("title", tender.get("titre")),
            fact("estimated_amount", tender.get("montant_estime"), "EUR"),
            fact("region", tender.get("region")),
            fact("deadline", tender.get("date_limite_remise")),
        ]),
        section("references", items=[
            item(r.get("project_name", ""), f"{r.get('region', '')} · {r.get('montant', '')} EUR", score=r.get("similarity"))
            for r in references[:5]
        ]),
        section("history", facts=[fact("win_rate", history.get("win_rate_percentage"), "%")], items=[
            item(h.get("ao_number", ""), h.get("raison_resultat", ""), badge=h.get("resultat"), score=h.get("similarity"))
            for h in history.get("historical_tenders", [])[:5]
        ]),
        section("capabilities", items=[
            item(c.get("name", ""), c.get("category", ""), badge=c.get("availability"), score=c.get("similarity"))
            for c in capabilities[:5]
        ]),
    ]


TENDERS = DomainSpec(
    name="tenders",
    entity="tender",
    number_field="tender_number",
    label="Tender",
    model=Tender,
    document_model=TenderDocument,
    decision_model=TenderDecision,
    fk="tender_id",
    agent_profile="tenders",
    message_file="tenders-processing-message.txt",
    processing_tools=[
        "get_tender",
        "ocr_document",
        "retrieve_similar_references",   # the company's similar projects
        "retrieve_historical_tenders",   # similar tenders won or lost
        "retrieve_capabilities",         # certifications, teams, equipment
    ],
    statuses_by_decision={
        "go": "completed",
        "no_go": "declined",
        "a_approfondir": "manual_review",
    },
    review_decision="a_approfondir",
    human_decisions=["go", "no_go"],
    evidence=evidence,
    precedents_key="tenders",
)
