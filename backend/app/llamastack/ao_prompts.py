"""
LLM prompt templates for AO (Appels d'Offres) processing.
Centralized prompts for tender analysis and Go/No-Go decision making.

Prompts can be loaded from ConfigMaps mounted at /app/prompts-ao/ or from default values.
"""

import os
import yaml
from pathlib import Path

# Prompt directory for AO prompts (can be mounted from ConfigMap)
AO_PROMPTS_DIR = Path(os.getenv("AO_PROMPTS_DIR", "/app/prompts-ao"))


def load_ao_prompt(filename: str, default: str) -> str:
    """
    Load an AO prompt from file or return default value.

    Args:
        filename: Name of the prompt file (e.g., "ao-processing-agent.txt")
        default: Default prompt content if file doesn't exist

    Returns:
        Prompt content string
    """
    prompt_file = AO_PROMPTS_DIR / filename
    if prompt_file.exists():
        try:
            return prompt_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Warning: Could not load AO prompt from {prompt_file}: {e}. Using default.")
            return default
    return default


# ---------------------------------------------------------------------------
# AO Processing Agent System Instructions (default)
# ---------------------------------------------------------------------------
_AO_PROCESSING_AGENT_DEFAULT = """You are a tender analysis agent for a BTP/Infrastructure construction company.

## Behavior:

Adapt your response to what the user asks:

- **Listing or stats** → call the relevant tool, give a concise summary. One line per tender: `**AO-YYYY-XXX-NNN** — description | status | budget`. No tables.
- **Viewing a specific tender** → call get_tender, summarize the key fields briefly.
- **Full Go/No-Go analysis** (user says analyze, traiter, go/no-go) → use OCR, similar references, historical tenders, and capabilities tools, then give your GO / NO-GO / A APPROFONDIR recommendation with confidence and reasoning.
- After full Go/No-Go analysis → call save_tender_decision with your recommendation, then call generate_document_embedding (pass the OCR text you extracted in text_content) to index for future similarity search.

Only call the tools needed for the request. A listing does not need OCR.

## Important:
- For get_tender, always pass the **tender_number** (AO-YYYY-XXX-NNN), not the UUID.
- Copy `document_link` fields AS-IS into your response.
- Be concise. No raw JSON. No markdown tables.
"""


# ---------------------------------------------------------------------------
# AO User Message Template (default)
# ---------------------------------------------------------------------------
_AO_USER_MESSAGE_DEFAULT = """
Analysez l'appel d'offres suivant en respectant le workflow défini dans vos instructions.

Suivez les étapes séquentielles : extraction du document, recherche de références, analyse de l'historique, vérification des capacités, puis formulez votre recommandation Go/No-Go.

Basez votre décision sur les données factuelles extraites à chaque étape. Fournissez une analyse complète avec l'évaluation des risques, les forces et faiblesses, et les actions recommandées.
"""


# ---------------------------------------------------------------------------
# Load prompts from ConfigMap files (if mounted) or use defaults
# ---------------------------------------------------------------------------
AO_PROCESSING_AGENT_INSTRUCTIONS = load_ao_prompt(
    "ao-processing-agent.txt",
    _AO_PROCESSING_AGENT_DEFAULT
)

AO_USER_MESSAGE_TEMPLATE = load_ao_prompt(
    "ao-user-message.txt",
    _AO_USER_MESSAGE_DEFAULT
)


# ---------------------------------------------------------------------------
# Agent configuration for AO processing
# ---------------------------------------------------------------------------
def load_ao_agent_config() -> dict:
    """
    Load AO agent configuration from ConfigMap or use defaults.

    Returns:
        Dictionary with AO agent configuration
    """
    config_file = AO_PROMPTS_DIR / "ao-agent-config.yaml"
    default_config = {
        "tool_choice": "auto",
        "tool_prompt_format": "json",
        "max_infer_iters": 16,
        "sampling_strategy": "greedy",
        "max_tokens": 2048,
    }

    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                loaded_config = yaml.safe_load(f) or {}
                return {**default_config, **loaded_config}
        except Exception as e:
            print(f"Warning: Could not load AO agent config from {config_file}: {e}. Using defaults.")
            return default_config
    return default_config


AO_AGENT_CONFIG = load_ao_agent_config()
