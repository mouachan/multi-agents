"""
Agent Orchestrator for LlamaStack.

Manages agent creation, sessions, and turn execution.
Completely domain-agnostic and reusable.
"""
import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrate agent creation, sessions, and interactions."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 300.0):
        """
        Initialize orchestrator.

        Args:
            base_url: LlamaStack endpoint URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or settings.llamastack_endpoint
        self.timeout = timeout

    async def create_agent(
        self,
        agent_config: Dict[str, Any],
        tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new agent.

        Args:
            agent_config: Agent configuration
            tools: List of tool names to enable

        Returns:
            Agent creation response with agent_id

        Raises:
            httpx.HTTPError: If agent creation fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {"agent_config": agent_config}

            if tools:
                payload["agent_config"]["tools"] = tools

            logger.info(f"Creating agent with config: {agent_config.get('model', 'unknown')}")

            response = await client.post(
                f"{self.base_url}/v1/agents",
                json=payload
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Agent created: {result.get('agent_id', 'unknown')}")
            return result

    async def create_session(
        self,
        agent_id: str,
        session_name: str
    ) -> Dict[str, Any]:
        """
        Create a new agent session.

        Args:
            agent_id: Agent identifier
            session_name: Human-readable session name

        Returns:
            Session creation response with session_id

        Raises:
            httpx.HTTPError: If session creation fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "agent_id": agent_id,
                "session_name": session_name
            }

            logger.info(f"Creating session for agent {agent_id}: {session_name}")

            response = await client.post(
                f"{self.base_url}/v1/agents/{agent_id}/session",
                json={"session_name": session_name}
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Session created: {result.get('session_id', 'unknown')}")
            return result

    async def execute_turn(
        self,
        agent_id: str,
        session_id: str,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Execute an agent turn.

        Args:
            agent_id: Agent identifier
            session_id: Session identifier
            messages: List of messages to send
            stream: Whether to stream the response

        Returns:
            Turn response with agent output

        Raises:
            httpx.HTTPError: If turn execution fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "agent_id": agent_id,
                "session_id": session_id,
                "messages": messages,
                "stream": stream
            }

            logger.info(f"Executing turn for session {session_id}")

            response = await client.post(
                f"{self.base_url}/v1/agents/{agent_id}/session/{session_id}/turn",
                json={"messages": messages, "stream": stream}
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Turn completed: {result.get('turn_id', 'unknown')}")
            return result

    async def get_session_history(
        self,
        agent_id: str,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get session conversation history.

        Args:
            agent_id: Agent identifier
            session_id: Session identifier

        Returns:
            List of turns in the session

        Raises:
            httpx.HTTPError: If retrieval fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/v1/agents/{agent_id}/session/{session_id}"
            )

            response.raise_for_status()
            result = response.json()

            turns = result.get('turns', [])
            logger.info(f"Retrieved {len(turns)} turns from session {session_id}")
            return turns

    async def delete_session(
        self,
        agent_id: str,
        session_id: str
    ) -> bool:
        """
        Delete an agent session.

        Args:
            agent_id: Agent identifier
            session_id: Session identifier

        Returns:
            True if deletion successful

        Raises:
            httpx.HTTPError: If deletion fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(
                f"{self.base_url}/v1/agents/{agent_id}/session/{session_id}"
            )

            response.raise_for_status()
            logger.info(f"Session deleted: {session_id}")
            return True

    async def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            True if deletion successful

        Raises:
            httpx.HTTPError: If deletion fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(
                f"{self.base_url}/v1/agents/{agent_id}"
            )

            response.raise_for_status()
            logger.info(f"Agent deleted: {agent_id}")
            return True

    async def process_with_agent(
        self,
        agent_config: Dict[str, Any],
        input_message: str,
        tools: Optional[List[str]] = None,
        session_name: Optional[str] = None,
        cleanup: bool = True
    ) -> Dict[str, Any]:
        """
        High-level method to process a task with an agent.

        Creates agent, session, executes turn, and optionally cleans up.

        Args:
            agent_config: Agent configuration
            input_message: Input message for the agent
            tools: Optional list of tools to enable
            session_name: Optional session name
            cleanup: Whether to delete agent/session after completion

        Returns:
            Agent response with output

        Raises:
            httpx.HTTPError: If any step fails
        """
        agent_id = None
        session_id = None

        try:
            # Create agent
            agent_result = await self.create_agent(agent_config, tools)
            agent_id = agent_result['agent_id']

            # Create session
            session_name = session_name or f"session_{datetime.now().isoformat()}"
            session_result = await self.create_session(agent_id, session_name)
            session_id = session_result['session_id']

            # Execute turn
            messages = [{"role": "user", "content": input_message}]
            turn_result = await self.execute_turn(agent_id, session_id, messages)

            return {
                "agent_id": agent_id,
                "session_id": session_id,
                "turn_result": turn_result,
                "output": turn_result.get('response', {}).get('content', '')
            }

        finally:
            # Cleanup if requested
            if cleanup and session_id and agent_id:
                try:
                    await self.delete_session(agent_id, session_id)
                except Exception as e:
                    logger.warning(f"Failed to delete session: {e}")

                try:
                    await self.delete_agent(agent_id)
                except Exception as e:
                    logger.warning(f"Failed to delete agent: {e}")
