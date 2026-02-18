"""
Context Builder for Agent Interactions.

Builds context and prompts for agents based on domain data.
Completely reusable for any domain (claims, orders, tickets, etc.)
"""
from typing import Dict, Any, List, Optional
from datetime import datetime


class ContextBuilder:
    """Build context for agent interactions from domain data."""

    def build_processing_context(
        self,
        entity_type: str,
        entity_id: str,
        entity_data: Dict[str, Any],
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build processing context for an agent.

        Args:
            entity_type: Type of entity (e.g., "claim", "order", "ticket")
            entity_id: Unique identifier for the entity
            entity_data: Main entity data
            additional_context: Optional additional context (OCR, RAG results, etc.)

        Returns:
            Formatted context string for the agent
        """
        context_parts = [
            f"# {entity_type.upper()} PROCESSING",
            f"Entity ID: {entity_id}",
            f"Entity Type: {entity_type}",
            ""
        ]

        # Add main entity data
        if entity_data:
            context_parts.append("## Main Data:")
            for key, value in entity_data.items():
                if value is not None:
                    context_parts.append(f"- {key}: {value}")
            context_parts.append("")

        # Add additional context
        if additional_context:
            for section, data in additional_context.items():
                context_parts.append(f"## {section}:")
                if isinstance(data, dict):
                    for key, value in data.items():
                        context_parts.append(f"- {key}: {value}")
                elif isinstance(data, list):
                    for item in data:
                        context_parts.append(f"- {item}")
                else:
                    context_parts.append(str(data))
                context_parts.append("")

        return "\n".join(context_parts)

    def build_review_context(
        self,
        entity_type: str,
        entity_id: str,
        entity_data: Dict[str, Any],
        initial_decision: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Build context for review interactions.

        Args:
            entity_type: Type of entity being reviewed
            entity_id: Entity identifier
            entity_data: Entity data
            initial_decision: Initial automated decision
            conversation_history: Previous Q&A exchanges

        Returns:
            Formatted review context string
        """
        context_parts = [
            f"# {entity_type.upper()} REVIEW",
            f"Entity ID: {entity_id}",
            ""
        ]

        # Add entity summary
        if entity_data:
            context_parts.append("## Entity Summary:")
            for key, value in entity_data.items():
                if key not in ['id', 'created_at', 'updated_at']:
                    context_parts.append(f"- {key}: {value}")
            context_parts.append("")

        # Add initial decision if available
        if initial_decision:
            context_parts.append("## Initial System Decision:")
            decision = initial_decision.get('decision', 'N/A')
            confidence = initial_decision.get('confidence', 0.0)
            reasoning = initial_decision.get('reasoning', '')

            context_parts.append(f"- Decision: {decision}")
            context_parts.append(f"- Confidence: {confidence:.2%}")
            if reasoning:
                context_parts.append(f"- Reasoning: {reasoning}")
            context_parts.append("")

        # Add conversation history
        if conversation_history:
            context_parts.append("## Previous Q&A:")
            for idx, exchange in enumerate(conversation_history, 1):
                question = exchange.get('question', '')
                answer = exchange.get('answer', '')
                context_parts.append(f"{idx}. Q: {question}")
                context_parts.append(f"   A: {answer}")
            context_parts.append("")

        return "\n".join(context_parts)

    def extract_ocr_context(self, ocr_data: Dict[str, Any]) -> str:
        """
        Extract and format OCR context.

        Args:
            ocr_data: OCR result data

        Returns:
            Formatted OCR context
        """
        if not ocr_data:
            return "No OCR data available."

        parts = ["## OCR Extracted Text:"]

        # Raw text
        raw_text = ocr_data.get('raw_ocr_text', '')
        if raw_text:
            parts.append(raw_text[:2000])  # Limit to 2000 chars
            if len(raw_text) > 2000:
                parts.append("... (truncated)")

        # Structured data if available
        structured = ocr_data.get('structured_data', {})
        if structured:
            parts.append("\n## Structured Data:")
            for key, value in structured.items():
                parts.append(f"- {key}: {value}")

        return "\n".join(parts)

    def extract_rag_context(
        self,
        rag_results: List[Dict[str, Any]],
        max_results: int = 5
    ) -> str:
        """
        Extract and format RAG retrieval context.

        Args:
            rag_results: List of RAG retrieval results
            max_results: Maximum number of results to include

        Returns:
            Formatted RAG context
        """
        if not rag_results:
            return "No retrieval results available."

        parts = ["## Retrieved Information:"]

        for idx, result in enumerate(rag_results[:max_results], 1):
            title = result.get('title', f'Result {idx}')
            content = result.get('content', '')
            similarity = result.get('similarity_score', 0.0)

            parts.append(f"\n### {idx}. {title} (similarity: {similarity:.2%})")
            parts.append(content[:500])  # Limit content
            if len(content) > 500:
                parts.append("... (truncated)")

        return "\n".join(parts)
