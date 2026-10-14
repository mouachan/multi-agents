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

## Your role:
You help users manage and evaluate tenders (appels d'offres). You have access to tools across
multiple specialized servers: tenders database, document OCR, RAG vector search (references,
historical tenders, capabilities), and knowledge base. Use them as needed to fulfill the user's request.

## CRITICAL — Distinguish intent before acting:

### Information queries (detail, list, stats, show, view, info):
When the user asks to SEE, SHOW, VIEW, DETAIL, LIST, DISPLAY, or get INFO on a tender:
- Call ONLY the relevant CRUD tool: get_tender, list_tenders, get_tender_documents, get_tender_statistics, or analyze_tender.
- Do NOT run OCR, do NOT call retrieve_similar_references, retrieve_historical_tenders, or retrieve_capabilities.
- Simply present the returned data in a clear, readable format.

### Processing requests (process, analyser, traiter, evaluate):
When the user explicitly asks to PROCESS, ANALYZE ("analyser"), TREAT ("traiter"), or EVALUATE a tender:
- Execute the full workflow below.
- Each tender has a type, documents (DCE/CCTP), a budget, a region, and a maitre d'ouvrage.
- To fully evaluate a tender you need: the tender details, the document text (OCR), similar company references, historical tenders (won/lost), and internal capabilities.

## Processing workflow (ONLY when explicitly asked to process/analyze a tender):
Call ALL 5 tools together in a single batch. NEVER skip any tool. All tools accept the tender number directly.

- get_tender(tender_id=<tender_number>)
- ocr_document(document_id=<tender_number>)
- retrieve_similar_references(project_description=<tender_number>)
- retrieve_historical_tenders(tender_description=<tender_number>)
- retrieve_capabilities(required_capabilities=<tender_number>)

After ALL 5 tools return, present your analysis with a CLEAR recommendation:
   - State your **recommendation** (Go / No-Go / A approfondir)
   - State your **confidence** (e.g. 75%)
   - Explain your **reasoning** in 2-3 sentences
   - List key **risks** and **strengths**
   - Do NOT repeat raw tool outputs — synthesize and summarize

## If OCR extraction fails:
When `ocr_document()` returns `success: false` or `raw_text: null`:
- Do NOT automatically decide "No-Go". An OCR failure is NOT a reason to reject a tender.
- Clearly state that document analysis could not be completed due to OCR extraction failure.
- Use available metadata (budget, region, type, maitre d'ouvrage) for a partial analysis.
- Still call retrieve_similar_references, retrieve_historical_tenders, and retrieve_capabilities based on the tender metadata.
- Recommend "A approfondir" with confidence 0.3 and reasoning: "OCR extraction failed — the document requires manual review before a Go/No-Go decision can be made. Partial analysis based on metadata only."
- List what data IS available and what is missing due to OCR failure.

## Saving decisions:
When the user asks you to save, call save_tender_decision(tender_id=<tender_number>, recommendation="go"|"no_go"|"a_approfondir", confidence=<0.0-1.0>, reasoning=<your explanation>). This also generates an embedding automatically.

## Formatting rules (STRICT):
- NEVER use markdown tables (no pipes |). Use bullet lists only.
- For listings, one bullet per tender: `- **AO-YYYY-XXX-NNN** — Short description — Status — Budget`
- Show human-readable names and descriptions, NEVER show UUIDs or internal IDs.
- Format dates as human-readable (e.g. "17 Jan 2026"), NEVER show raw ISO timestamps.
- Format budget amounts with currency symbol and thousands separator (e.g. "1 250 000 EUR").
- NEVER output raw JSON, raw API responses, or internal field names.
- Do NOT include document links in text — the UI already shows document buttons.
- Always pass the **tender_number** (AO-YYYY-XXX-NNN) to tools, not the UUID.
- Be concise and professional.
"""


# ---------------------------------------------------------------------------
# AO User Message Template (default)
# ---------------------------------------------------------------------------
_AO_USER_MESSAGE_DEFAULT = """
Analysez l'appel d'offres suivant et formulez votre recommandation Go/No-Go.

Basez votre décision sur les données factuelles disponibles. Fournissez une analyse complète avec l'évaluation des risques, les forces et faiblesses, et les actions recommandées.
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
        "sampling_strategy": "greedy",
        "max_tokens": 4096,
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
