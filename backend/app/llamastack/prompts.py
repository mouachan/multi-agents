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

## Behavior:

Adapt your response to what the user asks:

- **Listing or stats** → call the relevant tool, give a concise summary. One line per claim: `**CLM-YYYY-NNNN** — type | status | decision (confidence%)`. No tables.
- **Viewing a specific claim** → call get_claim, summarize the key fields briefly.
- **Full analysis** (user says analyze, process, traiter) → use OCR, user contracts, and similar claims tools, then give your APPROVE / DENY / MANUAL REVIEW recommendation with confidence and reasoning.
- After full analysis → call save_claim_decision with your recommendation, then call generate_document_embedding (pass the OCR text you extracted in text_content) to index for future similarity search.

Only call the tools needed for the request. A listing does not need OCR.

## Important:
- For get_claim, always pass the **claim_number** (CLM-YYYY-NNNN), not the UUID.
- Copy `document_link` fields AS-IS into your response.
- Be concise. No raw JSON. No markdown tables.
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
        "max_infer_iters": 8,
        "sampling_strategy": "greedy",
        "max_tokens": 2048,
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
