"""Postal complaints (réclamations): refund, re-ship, reject, or escalate to a human (Logistique profile).

The domain is "postal" (API, access profile, agent); one case is a "reclamation" (database tables,
decision values in French, as the business uses them).
"""
from app.domains.spec import DomainSpec, Evidence, ToolOutputs, fact, item, section
from app.models.reclamation import Reclamation, ReclamationDecision, ReclamationDocument


def evidence(outputs: ToolOutputs) -> Evidence:
    """What the reviewer of a complaint needs: the complaint, where the parcel is, the precedents."""
    complaint = outputs.get("get_reclamation", {}).get("reclamation") or outputs.get("get_reclamation", {})
    tracking = outputs.get("get_tracking", {})
    last = tracking.get("last_event") or {}
    similar = outputs.get("retrieve_similar_reclamations", {}).get("similar_reclamations", [])
    return [
        section("complaint", facts=[
            fact("type", complaint.get("reclamation_type")),
            fact("declared_value", complaint.get("valeur_declaree"), "EUR"),
        ]),
        section("tracking", facts=[
            fact("delivered", tracking.get("is_delivered")),
            fact("last_event", " — ".join(filter(None, [last.get("event_type"), last.get("location"), str(last.get("event_date") or "")]))),
        ]),
        section("similar_cases", items=[
            item(c.get("reclamation_number", ""), c.get("reclamation_type", ""), badge=c.get("decision"),
                 score=c.get("similarity") or c.get("similarity_score"))
            for c in similar[:5]
        ]),
    ]


POSTAL = DomainSpec(
    name="postal",
    entity="reclamation",
    number_field="reclamation_number",
    label="Complaint",
    model=Reclamation,
    document_model=ReclamationDocument,
    decision_model=ReclamationDecision,
    fk="reclamation_id",
    agent_profile="courrier_reclamation",
    message_file="postal-processing-message.txt",
    processing_tools=[
        "get_reclamation",
        "get_reclamation_documents",
        "get_tracking",                    # the parcel's tracking timeline
        "retrieve_similar_reclamations",   # precedents and their decisions
        "search_courrier_knowledge",       # refund and compensation rules
    ],
    statuses_by_decision={
        "rembourser": "completed",    # refund
        "reexpedier": "completed",    # re-ship
        "rejeter": "rejected",        # reject
        "escalader": "escalated",     # a human decides
    },
    review_decision="escalader",
    human_decisions=["rembourser", "reexpedier", "rejeter"],
    evidence=evidence,
    precedents_key="reclamations",
)
