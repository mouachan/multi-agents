"""The agent profiles the chat can talk to, and the A2A agent behind each one.

Three A2A agents run in the cluster (agents/), one per domain: claims-agent, tenders-agent,
postal-agent. An agent offers one or more profiles: a system prompt (MLflow) and a set of MCP tools
(agents/<name>-agent/agent.py). The postal agent has three: complaints, tracking, information.

The chat router (app/services/chat/routing.py) picks a profile for each message among those the
user's access profile allows (the profile's domain, app/core/auth.py).

Adding a profile = a Profile in the agent's agent.py, its prompt file (helm/.../files/prompts/agents),
and an entry below.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.core.config import settings


@dataclass(frozen=True)
class AgentProfile:
    id: str                # the profile, sent to the agent in the A2A metadata ("claims", "courrier_suivi")
    domain: str            # the domain: its A2A agent, and who may use the profile (app/domains)
    prompt: str            # the profile's system prompt in the MLflow Prompt Registry
    name: str
    name_fr: str
    description: str
    description_fr: str
    color: str             # UI accent
    icon: str
    page: str              # UI page of the domain
    # Routing by keywords, used when the semantic router is off or fails (the semantic router
    # uses the skills of the agent cards instead)
    routing_keywords: List[str] = field(default_factory=list)

    @property
    def a2a_url(self) -> Optional[str]:
        """URL of the profile's A2A agent (None when the agent is not deployed)."""
        return settings.agent_urls().get(self.domain)

    def to_api(self) -> Dict:
        return {
            "id": self.id, "domain": self.domain, "name": self.name, "name_fr": self.name_fr,
            "description": self.description, "description_fr": self.description_fr,
            "color": self.color, "icon": self.icon, "path": self.page,
        }


PROFILES: List[AgentProfile] = [
    AgentProfile(
        id="claims", domain="claims", prompt="claims-processing-agent",
        name="Insurance Claims Processing", name_fr="Traitement des Sinistres",
        description="Insurance claims analysis with OCR, RAG and decision-making",
        description_fr="Analyse des sinistres assurance avec OCR, RAG et prise de décision",
        color="emerald", icon="document", page="/claims",
        routing_keywords=["claim", "claims", "clm-", "sinistre", "sinistres", "assurance", "dommage",
                          "remboursement", "indemnisation", "police d'assurance", "contrat d'assurance"],
    ),
    AgentProfile(
        id="tenders", domain="tenders", prompt="ao-processing-agent",
        name="Tender Analysis", name_fr="Analyse d'Appels d'Offres",
        description="BTP tenders analysis with references, history and capabilities",
        description_fr="Analyse des appels d'offres BTP avec références, historique et capacités",
        color="amber", icon="building", page="/tenders",
        routing_keywords=["appel d'offres", "appels d'offres", "appel d offres", "ao", "tender", "tenders",
                          "marche public", "marches publics", "soumission", "btp", "construction",
                          "go/no-go", "go no go", "offre", "offres"],
    ),
    AgentProfile(
        id="courrier_reclamation", domain="postal", prompt="courrier-reclamation-instructions",
        name="Postal Complaints Processing", name_fr="Réclamations Courrier & Colis",
        description="Postal complaints analysis with OCR, tracking, RAG and decision-making",
        description_fr="Analyse des réclamations postales avec OCR, suivi, RAG et prise de décision",
        color="rose", icon="package", page="/postal",
        routing_keywords=["reclamation", "reclamations", "recl-", "la poste", "poste", "courrier", "colis",
                          "colis endommage", "colis perdu", "colis abime", "non livre", "pas recu",
                          "mauvaise adresse", "vol point relais", "retard livraison", "lettre", "recommande"],
    ),
    AgentProfile(
        id="courrier_info", domain="postal", prompt="courrier-info-instructions",
        name="Postal Information", name_fr="Informations Postales",
        description="Postal services Q&A: rates, delays, packaging, customs, refunds",
        description_fr="Questions sur les services postaux : tarifs, délais, emballage, douane, remboursements",
        color="sky", icon="info", page="/postal",
        routing_keywords=["tarif", "tarifs", "colissimo", "chronopost", "affranchissement", "emballage", "douane",
                          "delai livraison", "delais", "conditions transport", "quel est le prix", "combien coute"],
    ),
    AgentProfile(
        id="courrier_suivi", domain="postal", prompt="courrier-suivi-instructions",
        name="Parcel Tracking", name_fr="Suivi de Colis",
        description="Parcel tracking and delivery status",
        description_fr="Suivi des colis et statut de livraison",
        color="teal", icon="truck", page="/postal",
        routing_keywords=["suivi", "suivre", "tracking", "numero suivi", "ou est mon colis", "ou en est",
                          "livraison", "statut colis"],
    ),
]

_BY_ID: Dict[str, AgentProfile] = {profile.id: profile for profile in PROFILES}


def get_profile(profile_id: Optional[str]) -> Optional[AgentProfile]:
    return _BY_ID.get(profile_id) if profile_id else None


def profiles_for_domains(domains) -> List[AgentProfile]:
    """The profiles of the given domains (those a user may use)."""
    return [profile for profile in PROFILES if profile.domain in domains]
