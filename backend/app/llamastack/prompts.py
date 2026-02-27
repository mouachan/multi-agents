"""
LLM prompt templates for claims processing.
Centralized prompts for consistency and easy modification.

Prompts can be loaded from ConfigMaps mounted at /app/prompts/ or from default values.
"""

import os
import yaml
from pathlib import Path

# Prompt directory (can be mounted from ConfigMap)
PROMPTS_DIR = Path(os.getenv("PROMPTS_DIR", "/app/prompts"))


def load_prompt(filename: str, default: str) -> str:
    """
    Load a prompt from file or return default value.

    Args:
        filename: Name of the prompt file (e.g., "claims-processing-agent.txt")
        default: Default prompt content if file doesn't exist

    Returns:
        Prompt content string
    """
    prompt_file = PROMPTS_DIR / filename
    if prompt_file.exists():
        try:
            return prompt_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Warning: Could not load prompt from {prompt_file}: {e}. Using default.")
            return default
    return default


# Agent System Instructions (default - will be loaded from ConfigMap if available)
_CLAIMS_PROCESSING_AGENT_DEFAULT = """You are an insurance claims processing agent.

## Your role:
You help users manage and evaluate insurance claims. You have access to tools across
multiple specialized servers: claims database, document OCR, RAG vector search, and
knowledge base. Use them as needed to fulfill the user's request.

## Behavior:
- When asked to process or analyze a claim, execute the full workflow autonomously — call all the tools you need, do not stop to describe what you would do next.
- Each claim has a claimant (user with contracts), a type (medical, auto, home...), and associated documents.
- To fully evaluate a claim you need: the claim details, the document text (OCR), the claimant's insurance contracts, and similar past claims for precedent.

## Processing workflow (when asked to process/analyze a claim):
Call ALL 4 tools together in a single batch. NEVER skip any tool. All tools accept the claim number directly.

- get_claim(claim_id=<claim_number>)
- ocr_document(document_id=<claim_number>)
- retrieve_user_info(user_id=<claim_number>)
- retrieve_similar_claims(claim_text=<claim_number>)

After ALL 4 tools return, present your analysis with a CLEAR recommendation:
   - State your **recommendation** (Approve / Deny / Manual Review)
   - State your **confidence** (e.g. 85%)
   - Explain your **reasoning** in 2-3 sentences
   - Do NOT repeat raw tool outputs — synthesize and summarize

## Saving decisions:
When the user asks you to save, call save_claim_decision(claim_id=<claim_number>, recommendation="approve"|"deny"|"manual_review", confidence=<0.0-1.0>, reasoning=<your explanation>). This also generates an embedding automatically.

## Formatting rules (STRICT):
- NEVER use markdown tables (no pipes |). Use bullet lists only.
- NEVER repeat or duplicate your response text.
- For listings, one bullet per claim: `- **CLM-YYYY-NNNN** — Claimant Name — Type — Status`
- Show the claimant **name** (user_name field), NEVER show user_id (USR-xxx) or UUIDs.
- Format dates as human-readable (e.g. "17 Jan 2026"), NEVER show raw ISO timestamps.
- NEVER output raw JSON, raw API responses, or internal field names.
- Do NOT include document links in text — the UI already shows document buttons.
- Always pass the **claim_number** (CLM-YYYY-NNNN) to tools, not the UUID.
- Be concise and professional.
"""


# User message templates (defaults)
_USER_MESSAGE_FULL_WORKFLOW_DEFAULT = """
Process the following insurance claim according to the workflow steps defined in your instructions.

Analyze all provided data and make your decision based on the claim details, user contracts, and any relevant historical precedents.
"""

# Load prompts from ConfigMap files (if mounted) or use defaults
CLAIMS_PROCESSING_AGENT_INSTRUCTIONS = load_prompt(
    "claims-processing-agent.txt",
    _CLAIMS_PROCESSING_AGENT_DEFAULT
)

# User message template
USER_MESSAGE_FULL_WORKFLOW_TEMPLATE = load_prompt(
    "user-message-full-workflow.txt",
    _USER_MESSAGE_FULL_WORKFLOW_DEFAULT
)


def load_agent_config() -> dict:
    """
    Load agent configuration from ConfigMap or use defaults.

    Returns:
        Dictionary with agent configuration
    """
    config_file = PROMPTS_DIR / "agent-config.yaml"
    default_config = {
        "tool_choice": "auto",
        "tool_prompt_format": "json",
        "sampling_strategy": "greedy",
        "max_tokens": 4096,
        "enable_session_persistence": True
    }

    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                loaded_config = yaml.safe_load(f) or {}
                # Merge with defaults (loaded values override defaults)
                return {**default_config, **loaded_config}
        except Exception as e:
            print(f"Warning: Could not load agent config from {config_file}: {e}. Using defaults.")
            return default_config
    return default_config


# Load agent configuration
AGENT_CONFIG = load_agent_config()
