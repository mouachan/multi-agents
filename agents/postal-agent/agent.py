from a2a.types import AgentSkill

from shared.executor import Profile
from shared.server import run

# One agent, three profiles (selected by the caller via message metadata "profile").
# System prompts live in the MLflow Prompt Registry (alias @production), seeded from the
# Helm chart files (helm/multi-agents/files/cm.*-prompts) by the prompt-sync job.
PROFILES = {
    "courrier_reclamation": Profile(
        prompt="courrier-reclamation-instructions",
        tools=[
            "list_reclamations", "get_reclamation", "get_reclamation_documents",
            "get_reclamation_statistics", "save_reclamation_decision",
            "get_tracking",
            "search_courrier_knowledge", "retrieve_similar_reclamations",
            "ocr_document",
        ],
        tags={"domain": "postal"},
    ),
    "courrier_info": Profile(
        prompt="courrier-info-instructions",
        tools=["search_courrier_knowledge"],
        tags={"domain": "postal"},
    ),
    "courrier_suivi": Profile(
        prompt="courrier-suivi-instructions",
        tools=["get_tracking", "search_tracking"],
        tags={"domain": "postal"},
    ),
}

SKILLS = [
    AgentSkill(
        id="process-complaint",
        name="Process Postal Complaint",
        description="Evaluate a postal/parcel complaint — photos, tracking, precedents — rembourser/réexpédier/rejeter/escalader.",
        tags=["postal", "complaints", "tracking", "ocr", "profile:courrier_reclamation"],
        examples=[
            "Traiter la réclamation RECL-2026-0001", "Process complaint RECL-2026-0012",
            "Mon colis est arrivé endommagé, je veux être remboursé",
            "Je veux déposer une réclamation pour un colis perdu",
            "My parcel was delivered broken, I want a refund",
        ],
    ),
    AgentSkill(
        id="track-parcel",
        name="Track Parcel",
        description="Track a parcel or mail item by tracking number.",
        tags=["postal", "tracking", "profile:courrier_suivi"],
        examples=[
            "Où est mon colis 6C12345678901?", "Suivi du colis 1A98765432100",
            "Suivre un colis", "Quel est le statut de livraison de mon envoi ?",
            "Track my parcel 1A98765432100", "Quand mon colis sera-t-il livré ?",
        ],
    ),
    AgentSkill(
        id="postal-info",
        name="Postal Information",
        description="Answer questions about postal rates, shipping times, packaging, customs.",
        tags=["postal", "rates", "info", "profile:courrier_info"],
        examples=[
            "Combien coûte l'envoi d'un colis en France?", "Délai Colissimo vers l'Allemagne?",
            "Quel est le tarif d'une lettre recommandée ?", "Tarifs Colissimo",
            "Comment emballer un objet fragile ?", "What are the customs rules for a parcel abroad?",
        ],
    ),
    AgentSkill(
        id="query-complaints",
        name="Query Complaints",
        description="List, view details, or get statistics about postal complaints.",
        tags=["postal", "complaints", "query", "profile:courrier_reclamation"],
        examples=[
            "Lister les réclamations en cours", "Détail RECL-2026-0001",
            "Combien de réclamations postales sont en attente ?", "Statistiques des réclamations",
        ],
    ),
]

if __name__ == "__main__":
    run(
        name="Postal Services Agent",
        description="Postal/parcel services — complaint processing, tracking, rates and shipping info.",
        profiles=PROFILES,
        skills=SKILLS,
    )
