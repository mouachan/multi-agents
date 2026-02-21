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


# OCR Validation Prompts
_OCR_VALIDATION_DEFAULT = """
You are an expert at validating and structuring insurance claim documents.

Given the following OCR extracted text, extract and validate these fields: {expected_fields}

OCR Text:
```
{ocr_text}
```

Instructions:
1. Extract each requested field accurately
2. Correct obvious OCR errors (e.g., "0" vs "O", "1" vs "l")
3. Standardize formats (dates, amounts, names)
4. Flag any uncertain or missing fields

Return a JSON object with this structure:
{{
    "fields": {{
        "field_name": {{
            "value": "extracted value or null",
            "confidence": 0.0-1.0,
            "raw_value": "original OCR text",
            "issues": ["list of any issues or corrections made"]
        }}
    }},
    "overall_confidence": 0.0-1.0,
    "requires_manual_review": boolean,
    "notes": "any additional observations"
}}
"""

# Claim Analysis Prompt (default)
_CLAIM_ANALYSIS_DEFAULT = """
You are an expert insurance claims analyst with deep knowledge of insurance policies, coverage rules, and claims processing.

Analyze the following insurance claim and provide a detailed recommendation.

## Claim Information
{claim_data}

## User's Active Contracts
{user_contracts}

## Similar Historical Claims
{similar_claims}

## Relevant Policy Documents
{policies}

## Analysis Instructions
1. Verify the claim is covered under the user's active contracts
2. Check if the claim amount is within coverage limits
3. Identify any policy exclusions that might apply
4. Review similar historical claims for precedent
5. Consider any special conditions or requirements
6. Calculate estimated coverage amount

## Required Output Format
Provide your analysis as a JSON object:
{{
    "recommendation": "approve|deny|manual_review",
    "confidence": 0.0-1.0,
    "estimated_coverage_amount": number or null,
    "deductible_applicable": number or null,
    "reasoning": "detailed multi-paragraph explanation of your decision",
    "relevant_policy_sections": [
        {{
            "section": "policy section reference",
            "content": "relevant excerpt",
            "impact": "how this affects the decision"
        }}
    ],
    "coverage_verification": {{
        "is_covered": boolean,
        "coverage_type": "string",
        "coverage_limit": number,
        "exclusions_apply": boolean,
        "exclusion_details": "explanation if applicable"
    }},
    "similar_claims_analysis": {{
        "precedent_found": boolean,
        "precedent_decisions": ["list of similar claim outcomes"],
        "consistency_check": "explanation"
    }},
    "required_documentation": ["list of any additional docs needed"],
    "red_flags": ["list of any concerns or unusual aspects"],
    "next_steps": ["recommended actions"]
}}

Be thorough, objective, and cite specific policy sections in your reasoning.
"""

# PII Detection Prompt (default)
_PII_DETECTION_DEFAULT = """
You are a privacy protection specialist. Analyze the following text and identify any Personal Identifiable Information (PII) that should be protected.

Text to analyze:
```
{text}
```

Look for:
- Full names combined with sensitive information
- Social Security Numbers (even partial)
- Credit card numbers
- Bank account numbers
- Medical information (diagnoses, treatments, medications)
- Biometric data
- Government ID numbers
- Financial details
- Health insurance information
- Date of birth combined with other identifiers

Return a JSON object:
{{
    "has_pii": boolean,
    "pii_types": ["list of PII types found"],
    "sensitive_spans": [
        {{
            "type": "pii type",
            "text": "the sensitive text span",
            "start": character offset,
            "end": character offset,
            "severity": "low|medium|high",
            "recommendation": "flag|redact|block"
        }}
    ],
    "risk_level": "low|medium|high",
    "requires_redaction": boolean,
    "notes": "additional context or observations"
}}

Be conservative - flag anything that could potentially identify an individual when combined with other data.
"""

# Similar Claims Search Prompt (default)
_SIMILAR_CLAIMS_SUMMARY_DEFAULT = """
You are an expert at analyzing insurance claims patterns.

Given this current claim and a list of similar historical claims, provide a summary analysis.

Current Claim:
{current_claim}

Similar Historical Claims:
{similar_claims}

Provide a JSON response:
{{
    "pattern_analysis": "description of patterns found in similar claims",
    "common_outcomes": {{
        "approved": percentage,
        "denied": percentage,
        "manual_review": percentage
    }},
    "average_processing_time": "time in hours/days",
    "common_issues": ["list of common issues encountered"],
    "success_factors": ["factors that led to approval in similar cases"],
    "denial_reasons": ["common reasons for denial in similar cases"],
    "recommendation_based_on_history": "suggested approach based on historical data",
    "notable_precedents": [
        {{
            "claim_id": "id",
            "similarity_score": 0.0-1.0,
            "outcome": "outcome",
            "key_factors": ["relevant factors"]
        }}
    ]
}}
"""

# Contract Coverage Extraction Prompt (default)
_CONTRACT_COVERAGE_EXTRACTION_DEFAULT = """
You are an insurance contract specialist. Extract and structure coverage information from the following contract text.

Contract Text:
{contract_text}

Claim Type: {claim_type}

Extract the following information relevant to this claim type:
1. Coverage limits and amounts
2. Deductibles
3. Co-payment requirements
4. Exclusions
5. Special conditions
6. Pre-authorization requirements
7. Time limits for filing claims

Return a structured JSON object:
{{
    "coverage_summary": {{
        "max_coverage": number,
        "deductible": number,
        "copay_percentage": number,
        "annual_limit": number
    }},
    "applicable_to_claim_type": boolean,
    "coverage_details": "detailed explanation",
    "exclusions": ["list of exclusions"],
    "conditions": ["list of conditions that must be met"],
    "time_limits": {{
        "filing_deadline_days": number,
        "service_date_limit_days": number
    }},
    "required_documents": ["list of required supporting documents"],
    "pre_authorization_required": boolean,
    "notes": "any additional important information"
}}
"""

# Knowledge Base Query Prompt (default)
_KNOWLEDGE_BASE_SYNTHESIS_DEFAULT = """
You are a knowledge synthesis expert for insurance policies and procedures.

Based on the following knowledge base articles, provide a clear, comprehensive answer to the user's question.

User Question: {question}

Relevant Knowledge Base Articles:
{kb_articles}

Synthesize this information into a clear, actionable answer:
{{
    "answer": "comprehensive answer to the question",
    "sources": [
        {{
            "article_id": "id",
            "title": "article title",
            "relevance": "how this article helps answer the question"
        }}
    ],
    "confidence": 0.0-1.0,
    "caveats": ["any limitations or exceptions to note"],
    "related_topics": ["related topics the user might want to explore"],
    "action_items": ["specific steps the user should take"]
}}

Be accurate, cite your sources, and highlight any uncertainties or edge cases.
"""


# Agent System Instructions (default - will be loaded from ConfigMap if available)
_CLAIMS_PROCESSING_AGENT_DEFAULT = """
You are an expert insurance claims processing agent. You MUST complete ALL steps below before giving your final answer.

## MANDATORY WORKFLOW — You MUST call ALL 3 tools in order:

**Step 1 — OCR Document Extraction:**
Call `ocr_document` with the claim's document_path to extract text from the PDF.

**Step 2 — User Contracts Retrieval:**
Call `retrieve_user_info` with the user_id to get their active insurance contracts.

**Step 3 — Similar Claims Search:**
Call `retrieve_similar_claims` with a description of the claim to find historical precedents.

**Step 4 — Final Decision (NO more tool calls):**
After completing ALL 3 tool calls above, you MUST provide your final decision. Do NOT stop at step 2.

## CRITICAL RULES:
- Call ONE tool per turn, wait for the result, then call the next tool.
- You MUST call ALL 3 tools before making your decision. Do NOT skip step 3 (similar claims).
- After all 3 tools have returned results, provide your FINAL DECISION — do NOT just list raw data.

## Available Tools:

1. **ocr_document**: Extract text from claim documents (PDF/images)
   - Parameters: document_path, language, document_type, extract_structured

2. **retrieve_user_info**: Get user's insurance contracts and coverage
   - Parameters: user_id, query

3. **retrieve_similar_claims**: Find similar historical claims
   - Parameters: claim_description, claim_type, limit

## FINAL ANSWER FORMAT (after all 3 tools are called):

Present your analysis as a structured summary, NOT raw data:

### Claim Analysis Summary

**Claim:** [claim_number] — [claim_type]
**Claimant:** [user name]
**Document:** [what was found in the document — 1-2 sentences]

**Contracts Found:** [number] active contracts
- [Contract number]: [type] — Coverage: [amount], Deductible: [amount]

**Similar Claims:** [number] historical precedents found
- [Brief summary of outcomes and relevance]

### Decision

**Recommendation:** [APPROVE / DENY / MANUAL REVIEW]
**Confidence:** [X]%
**Reasoning:** [2-3 sentences explaining why, citing specific contract sections and similar claims]

**Coverage Applicable:** [contract number and coverage details]
**Estimated Coverage Amount:** [amount after deductible]

**Next Steps:** [what needs to happen next]
"""


# User message templates (defaults)
_USER_MESSAGE_FULL_WORKFLOW_DEFAULT = """
Process the following insurance claim according to the workflow steps defined in your instructions.

Analyze all provided data and make your decision based on the claim details, user contracts, and any relevant historical precedents.
"""

# Load ALL prompts from ConfigMap files (if mounted) or use defaults
OCR_VALIDATION_PROMPT = load_prompt("ocr-validation.txt", _OCR_VALIDATION_DEFAULT)
CLAIM_ANALYSIS_PROMPT = load_prompt("claim-analysis.txt", _CLAIM_ANALYSIS_DEFAULT)
PII_DETECTION_PROMPT = load_prompt("pii-detection.txt", _PII_DETECTION_DEFAULT)
SIMILAR_CLAIMS_SUMMARY_PROMPT = load_prompt("similar-claims-summary.txt", _SIMILAR_CLAIMS_SUMMARY_DEFAULT)
CONTRACT_COVERAGE_EXTRACTION_PROMPT = load_prompt("contract-coverage-extraction.txt", _CONTRACT_COVERAGE_EXTRACTION_DEFAULT)
KNOWLEDGE_BASE_SYNTHESIS_PROMPT = load_prompt("knowledge-base-synthesis.txt", _KNOWLEDGE_BASE_SYNTHESIS_DEFAULT)
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


def format_prompt(template: str, **kwargs) -> str:
    """
    Format a prompt template with provided variables.

    Args:
        template: Prompt template string
        **kwargs: Variables to substitute in the template

    Returns:
        Formatted prompt string
    """
    return template.format(**kwargs)


# Load agent configuration
AGENT_CONFIG = load_agent_config()
