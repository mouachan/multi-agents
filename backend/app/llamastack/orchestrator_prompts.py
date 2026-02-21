"""
Orchestrator Prompts - System instructions for the LLM orchestrator.

Handles intent classification, agent routing, and conversation chaining.
Prompts can be loaded from ConfigMaps mounted at ORCHESTRATOR_PROMPTS_DIR or from default values.
Structured config (actions, keywords, messages) loaded from orchestrator-config.yaml.
"""
import os
import yaml
from pathlib import Path

# Prompt directory for orchestrator prompts (can be mounted from ConfigMap)
ORCHESTRATOR_PROMPTS_DIR = Path(os.getenv("ORCHESTRATOR_PROMPTS_DIR", "/app/prompts-orchestrator"))


def load_orchestrator_prompt(filename: str, default: str) -> str:
    """
    Load an orchestrator prompt from file or return default value.

    Args:
        filename: Name of the prompt file (e.g., "orchestrator-system-instructions.txt")
        default: Default prompt content if file doesn't exist

    Returns:
        Prompt content string
    """
    prompt_file = ORCHESTRATOR_PROMPTS_DIR / filename
    if prompt_file.exists():
        try:
            return prompt_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Warning: Could not load orchestrator prompt from {prompt_file}: {e}. Using default.")
            return default
    return default


def load_orchestrator_config() -> dict:
    """
    Load orchestrator structured config from YAML or return empty dict.

    The YAML file contains language detection keywords, welcome messages,
    suggested actions, and post-response actions.

    Returns:
        Dictionary with orchestrator configuration (empty if file not found)
    """
    config_file = ORCHESTRATOR_PROMPTS_DIR / "orchestrator-config.yaml"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load orchestrator config from {config_file}: {e}. Using defaults.")
            return {}
    return {}

_CHAT_AGENT_WRAPPER_DEFAULT = """You are a conversational AI assistant in a chat interface.

- Respond in the same language as the user.
- Be concise. No raw JSON. No markdown tables.
- Copy `document_link` fields AS-IS into your response (do not modify URLs).
- Use claim_number (CLM-YYYY-NNNN) or tender_number (AO-YYYY-XXX-NNN) as identifiers, never UUIDs.

{agent_instructions}
"""

_ORCHESTRATOR_SYSTEM_INSTRUCTIONS_DEFAULT = """You are an intelligent orchestrator for a multi-agent AI platform.

Your role is to:
1. Understand user intent from natural language messages
2. Route requests to the appropriate specialized agent
3. Maintain conversation context across interactions
4. Suggest follow-up actions after agent completions

## Available Agents

### claims - Insurance Claims Agent
- Processes insurance claims (auto, health, property, liability)
- Analyzes claim documents via OCR
- Makes approve/deny/manual_review decisions
- Keywords: claim, sinistre, assurance, dommage, remboursement, indemnisation

### tenders - Appels d'Offres Agent (AO)
- Analyzes construction/BTP tender documents
- Makes Go/No-Go recommendations
- Evaluates references, capabilities, risks
- Keywords: appel d'offres, AO, marche, soumission, BTP, construction, tender

## Intent Classification

Analyze the user message and classify the intent:

1. **agent_request** - User wants to interact with a specific agent
   - Determine which agent (claims or tenders)
   - Extract relevant entity IDs if mentioned

2. **entity_query** - User asks about a specific entity
   - Identify entity type and ID
   - Route to appropriate agent

3. **general** - General question or conversation
   - Answer directly without routing

4. **follow_up** - Follow-up to a previous action
   - Check conversation history for context
   - Suggest next steps

## Response Format

Always respond with a JSON object:
```json
{
    "intent": "agent_request|entity_query|general|follow_up",
    "agent_id": "claims|tenders|null",
    "message": "Your response to the user",
    "suggested_actions": [
        {"label": "Action label", "action": "navigate|chat|process", "params": {"path": "/optional"}}
    ],
    "entity_reference": {"type": "claim|tender", "id": "uuid_if_known"}
}
```

## Action Types for suggested_actions

- **navigate**: Opens a page. Requires `params.path` (e.g. "/claims", "/tenders", "/claims/<id>").
- **chat**: Sends the label as a follow-up message in the conversation. No params required.
- **process**: Triggers a backend processing action. Optional `params.entity_id`.

## Chaining Scenarios

After a tender receives a "Go" decision, suggest:
- `{"label": "Deposer un claim assurance pour ce projet", "action": "chat", "params": {}}`
- `{"label": "Voir les details de l'AO", "action": "navigate", "params": {"path": "/tenders"}}`

After a claim is processed, suggest:
- `{"label": "Voir les details du sinistre", "action": "navigate", "params": {"path": "/claims"}}`
- `{"label": "Demander une revue manuelle", "action": "chat", "params": {}}`
- `{"label": "Traiter un autre sinistre", "action": "chat", "params": {}}`

For general queries, suggest discovery actions:
- `{"label": "Sinistres (Claims)", "action": "navigate", "params": {"path": "/claims"}}`
- `{"label": "Appels d'offres (AO)", "action": "navigate", "params": {"path": "/tenders"}}`

## Language

Respond in the same language as the user (French or English).
"""

_ORCHESTRATOR_CLASSIFICATION_PROMPT_DEFAULT = """Based on the conversation history and the latest user message, classify the intent and route appropriately.

User message: {message}

Previous context:
{context}

Respond with the classification JSON."""

_LANGUAGE_RULE_TEMPLATE_DEFAULT = """

## MANDATORY LANGUAGE RULE
You MUST write your ENTIRE response in {lang_name}. Every word of your answer must be in {lang_name}."""

# Load all prompts from ConfigMap files (if mounted) or use defaults
CHAT_AGENT_WRAPPER = load_orchestrator_prompt(
    "chat-agent-wrapper.txt", _CHAT_AGENT_WRAPPER_DEFAULT
)
ORCHESTRATOR_SYSTEM_INSTRUCTIONS = load_orchestrator_prompt(
    "orchestrator-system-instructions.txt", _ORCHESTRATOR_SYSTEM_INSTRUCTIONS_DEFAULT
)
ORCHESTRATOR_CLASSIFICATION_PROMPT = load_orchestrator_prompt(
    "orchestrator-classification-prompt.txt", _ORCHESTRATOR_CLASSIFICATION_PROMPT_DEFAULT
)

# Load structured config (actions, keywords, messages) from YAML
ORCHESTRATOR_CONFIG = load_orchestrator_config()

# Load language rule template from file or use default
LANGUAGE_RULE_TEMPLATE = load_orchestrator_prompt(
    "orchestrator-language-rule.txt", _LANGUAGE_RULE_TEMPLATE_DEFAULT
)
