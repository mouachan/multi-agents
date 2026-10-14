from a2a.types import AgentSkill

from shared.executor import Profile
from shared.server import run

# System prompts live in the MLflow Prompt Registry (alias @production), seeded from the
# Helm chart files (helm/multi-agents/files/cm.*-prompts) by the prompt-sync job.
PROFILES = {
    "claims": Profile(
        prompt="claims-processing-agent",
        tools=[
            "list_claims", "get_claim", "get_claim_documents", "get_claim_statistics",
            "save_claim_decision",
            "retrieve_user_info", "retrieve_similar_claims", "search_knowledge_base",
            "ocr_document",
        ],
        tags={"domain": "insurance"},
    ),
}

SKILLS = [
    AgentSkill(
        id="process-claim",
        name="Process Insurance Claim",
        description="Analyze a claim using OCR, contracts, and precedents to produce approve/deny/manual_review.",
        tags=["insurance", "claims", "ocr", "rag"],
        examples=["Process claim CLM-2026-0001", "Traiter le sinistre CLM-2026-0042"],
    ),
    AgentSkill(
        id="query-claims",
        name="Query Claims",
        description="List, view details, or get statistics about insurance claims.",
        tags=["insurance", "claims", "query"],
        examples=["Show me all pending claims", "Detail claim CLM-2026-0001"],
    ),
]

if __name__ == "__main__":
    run(
        name="Claims Processing Agent",
        description="Insurance claims processing — OCR, RAG, approve/deny/manual_review decisions.",
        profiles=PROFILES,
        skills=SKILLS,
    )
