from a2a.types import AgentSkill

from shared.executor import Profile
from shared.server import run

# System prompts live in the MLflow Prompt Registry (alias @production), seeded from the
# Helm chart files (helm/multi-agents/files/cm.*-prompts) by the prompt-sync job.
PROFILES = {
    "tenders": Profile(
        prompt="ao-processing-agent",
        tools=[
            "list_tenders", "get_tender", "get_tender_documents", "get_tender_statistics",
            "save_tender_decision",
            "retrieve_similar_references", "retrieve_historical_tenders", "retrieve_capabilities",
            "search_knowledge_base",
            "ocr_document",
        ],
        tags={"domain": "btp"},
    ),
}

SKILLS = [
    AgentSkill(
        id="analyze-tender",
        name="Analyze Tender (Appel d'Offres)",
        description="Evaluate a BTP tender — OCR, references, history, capabilities — Go/No-Go/A approfondir.",
        tags=["btp", "tenders", "construction", "ocr", "rag", "profile:tenders"],
        examples=[
            "Analyser l'AO AO-2026-IDF-001", "Process tender AO-2026-PAC-015",
            "Faut-il répondre à cet appel d'offres de construction ?",
            "Go ou No-Go pour le marché public de rénovation du lycée ?",
            "Quelles références similaires avons-nous pour ce chantier ?",
        ],
    ),
    AgentSkill(
        id="query-tenders",
        name="Query Tenders",
        description="List, view details, or get statistics about tenders.",
        tags=["btp", "tenders", "query", "profile:tenders"],
        examples=[
            "Lister les appels d'offres en cours", "Detail AO-2026-IDF-001",
            "Combien d'appels d'offres sont en attente ?",
            "Statistiques des appels d'offres BTP", "Show tenders in Île-de-France",
        ],
    ),
]

if __name__ == "__main__":
    run(
        name="Tenders Analysis Agent",
        description="BTP tender analysis — OCR, references, capabilities — Go/No-Go decisions.",
        profiles=PROFILES,
        skills=SKILLS,
    )
