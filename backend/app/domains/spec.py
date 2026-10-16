"""What the platform needs to know about a business domain (claims, tenders, postal complaints).

A domain is a kind of case that an A2A agent processes and a human may review. Everything that
differs between domains is declared here once, in a `DomainSpec`; the API (app/api/domains.py),
the processing (app/services/processing.py), the decisions and the review (app/services/decisions.py,
app/services/review.py) and the demo reset only read these declarations.

Adding a domain = ORM models in app/models, one `DomainSpec` in app/domains/<name>.py, registered in
app/domains/__init__.py, plus its agent profile and MCP tools (docs/add-a-domain.md).
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type

# Facts from a processing, shown to a reviewer: the outputs of the agent's tools ({tool name: output})
# turned into sections of facts, without any LLM (see evidence() in each domain module and
# app/services/review.py)
ToolOutputs = Dict[str, Dict[str, Any]]
Evidence = List[Dict[str, Any]]


def section(key: str, facts: Optional[List[Dict[str, Any]]] = None, items: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """One block of the evidence: `key` names it (translated by the UI: review.evidence.<key>),
    `facts` are label/value pairs, `items` a list of related records (precedents, references...)."""
    return {"key": key, "facts": [f for f in facts or [] if f["value"] not in (None, "")], "items": items or []}


def fact(key: str, value: Any, unit: str = "") -> Dict[str, Any]:
    return {"key": key, "value": value, "unit": unit}


def item(title: str, detail: str = "", badge: Optional[str] = None, score: Optional[float] = None) -> Dict[str, Any]:
    return {"title": title, "detail": detail, "badge": badge, "score": round(score, 2) if score is not None else None}


@dataclass(frozen=True)
class DomainSpec:
    # ---- identity
    name: str               # "claims": API prefix /api/v1/claims, access domain (RBAC "<name>-agent")
    entity: str             # "claim": one case; used in review URLs and MLflow sessions ("claim-<id>")
    number_field: str       # "claim_number": the business key shown to users (CLM-2024-0011)
    label: str              # "Claim": for logs and error messages

    # ---- database (app/models)
    model: Type             # the case table (Claim)
    document_model: Type    # its documents: OCR text and embedding (ClaimDocument)
    decision_model: Type    # agent and human decisions (ClaimDecision)
    fk: str                 # foreign key of the document and decision tables ("claim_id")

    # ---- processing by the A2A agent
    agent_profile: str      # the agent profile that processes a case (app/agents.py)
    message_file: str       # processing request sent to the agent (prompt file, see app/core/prompts.py)
    processing_tools: List[str]  # MCP tools of the guided processing, in the order they run

    # ---- decisions: value -> status of the case after it
    statuses_by_decision: Dict[str, str]
    review_decision: str    # the agent decision that hands the case to a human ("manual_review")
    human_decisions: List[str]   # what a reviewer can decide (the final decisions)

    # ---- review: facts of the processing shown to the reviewer (see ToolOutputs above)
    evidence: Callable[[ToolOutputs], Evidence] = lambda outputs: []

    # ---- optional features
    pii_report: bool = False     # scan the documents for personal data after processing (claims page)
    precedents_key: Optional[str] = None  # section of precedent_decisions.json (demo reset)

    def status_after(self, decision: str) -> str:
        """Status of a case once `decision` is taken (an unknown value goes to human review)."""
        return self.statuses_by_decision.get(decision, self.review_status)

    @property
    def review_status(self) -> str:
        """Status of the cases waiting for a human decision."""
        return self.statuses_by_decision[self.review_decision]

    @property
    def decision_values(self) -> List[str]:
        """Every decision the agent may take (sent to the agent with the processing request)."""
        return list(self.statuses_by_decision)
