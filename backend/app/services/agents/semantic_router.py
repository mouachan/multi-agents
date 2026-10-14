"""
Semantic agent router — picks the agent (or postal profile) for a chat message.

Catalog: for every registered agent, its description plus the skills published in the
A2A agent card (description + examples) tagged ``profile:<agent_id>``. Entries are
embedded once with the OGX embedding model (nomic prefixes "search_document: " /
"search_query: ").

Decision for a message:
    1. score = best cosine similarity between the message and each agent's entries
    2. clear winner (score >= min_score and margin over the runner-up) -> that agent
    3. weak match on a follow-up -> keep the session's current agent ("sticky")
    4. two agents too close, or weak match without a current agent -> one short LLM
       call chooses among the top candidates
Thresholds were calibrated on nomic-embed-text-v1-5 (genuine requests score 0.63-0.90,
follow-ups like "merci" or "et le deuxième ?" 0.52-0.60).
Any failure falls back to the caller (keyword routing).
"""
import asyncio
import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.config import settings
from app.services.agents.registry import AgentRegistry

logger = logging.getLogger(__name__)

PROFILE_TAG = "profile:"
DOC_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "
EMBED_BATCH = 16


@dataclass
class RoutingDecision:
    agent_id: str
    method: str  # semantic | llm | sticky
    score: float
    candidates: List[Tuple[str, float]] = field(default_factory=list)
    duration_ms: int = 0

    def to_event(self) -> Dict[str, Any]:
        return {
            "type": "routing",
            "agent_id": self.agent_id,
            "method": self.method,
            "score": round(self.score, 3),
            "candidates": [{"agent_id": a, "score": round(s, 3)} for a, s in self.candidates],
            "duration_ms": self.duration_ms,
        }


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class SemanticRouter:
    def __init__(self, min_score: float = 0.62, margin: float = 0.04, timeout: float = 20.0):
        self.min_score = min_score
        self.margin = margin
        self.timeout = timeout
        self._entries: List[Tuple[str, List[float]]] = []  # (agent_id, embedding)
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------ catalog
    async def _agent_cards(self, client: httpx.AsyncClient) -> Dict[str, Dict[str, Any]]:
        cards: Dict[str, Dict[str, Any]] = {}
        for url in {a.a2a_url for a in AgentRegistry.list_agents() if a.a2a_url}:
            try:
                resp = await client.get(f"{url.rstrip('/')}/.well-known/agent-card.json")
                resp.raise_for_status()
                cards[url] = resp.json()
            except Exception as e:
                logger.warning("Router: agent card unavailable at %s: %s", url, e)
        return cards

    def _catalog_texts(self, cards: Dict[str, Dict[str, Any]]) -> List[Tuple[str, str]]:
        texts: List[Tuple[str, str]] = []
        for agent in AgentRegistry.list_agents():
            texts.append((agent.id, f"{agent.name}: {agent.description}"))
            if agent.description_fr:
                texts.append((agent.id, f"{agent.name_fr or agent.name}: {agent.description_fr}"))
            card = cards.get(agent.a2a_url or "")
            if not card:
                # No agent card: fall back to the registry keywords as a pseudo example
                if agent.routing_keywords:
                    texts.append((agent.id, ", ".join(agent.routing_keywords)))
                continue
            for skill in card.get("skills", []):
                tags = skill.get("tags", [])
                profiles = [t[len(PROFILE_TAG):] for t in tags if t.startswith(PROFILE_TAG)]
                if agent.id not in profiles:
                    continue
                texts.append((agent.id, f"{skill.get('name', '')}: {skill.get('description', '')}"))
                texts.extend((agent.id, ex) for ex in skill.get("examples", []))
        return texts

    async def _embed(self, client: httpx.AsyncClient, inputs: List[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for i in range(0, len(inputs), EMBED_BATCH):  # the MaaS rejects large batches (413)
            resp = await client.post(
                f"{settings.ogx_endpoint}/v1/embeddings",
                json={"model": settings.ogx_embedding_model, "input": inputs[i:i + EMBED_BATCH]},
            )
            resp.raise_for_status()
            data = sorted(resp.json()["data"], key=lambda d: d["index"])
            vectors.extend(d["embedding"] for d in data)
        return vectors

    async def _ensure_catalog(self, client: httpx.AsyncClient) -> None:
        if self._entries:
            return
        async with self._lock:
            if self._entries:
                return
            texts = self._catalog_texts(await self._agent_cards(client))
            vectors = await self._embed(client, [DOC_PREFIX + t for _, t in texts])
            self._entries = [(agent_id, vec) for (agent_id, _), vec in zip(texts, vectors)]
            logger.info("Router catalog: %d entries for %d agents",
                        len(self._entries), len({a for a, _ in self._entries}))

    # ------------------------------------------------------------------ routing
    async def _llm_choice(self, client: httpx.AsyncClient, message: str, candidates: List[str]) -> Optional[str]:
        lines = []
        for agent_id in candidates:
            agent = AgentRegistry.get(agent_id)
            if agent:
                lines.append(f"- {agent_id}: {agent.name} — {agent.description}")
        prompt = (
            "Route the user message to exactly one agent. Answer with the agent id only.\n"
            "Agents:\n" + "\n".join(lines) + f"\n\nUser message: {message}"
        )
        resp = await client.post(
            f"{settings.ogx_endpoint}/v1/chat/completions",
            json={
                "model": settings.ogx_default_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 16,
                "temperature": 0,
            },
        )
        resp.raise_for_status()
        answer = resp.json()["choices"][0]["message"]["content"].strip().strip("`'\".").lower()
        return next((c for c in candidates if c.lower() in answer), None)

    async def route(self, message: str, current_agent_id: Optional[str] = None) -> RoutingDecision:
        start = time.time()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            await self._ensure_catalog(client)
            query = (await self._embed(client, [QUERY_PREFIX + message]))[0]

            best: Dict[str, float] = {}
            for agent_id, vec in self._entries:
                score = _cosine(query, vec)
                if score > best.get(agent_id, -1.0):
                    best[agent_id] = score
            ranked = sorted(best.items(), key=lambda kv: kv[1], reverse=True)
            (top_id, top_score), runner_up = ranked[0], (ranked[1] if len(ranked) > 1 else ("", 0.0))

            if top_score < self.min_score and current_agent_id:
                agent_id, method = current_agent_id, "sticky"
            elif top_score < self.min_score or (runner_up[0] and top_score - runner_up[1] < self.margin):
                candidates = [a for a, _ in ranked[:3 if top_score < self.min_score else 2]]
                choice = await self._llm_choice(client, message, candidates)
                agent_id, method = (choice or top_id), "llm"
            else:
                agent_id, method = top_id, "semantic"

        decision = RoutingDecision(
            agent_id=agent_id,
            method=method,
            score=best.get(agent_id, top_score),
            candidates=ranked[:3],
            duration_ms=int((time.time() - start) * 1000),
        )
        logger.info("Routed to %s (%s, score=%.3f, top=%s)", agent_id, method, decision.score,
                    [(a, round(s, 3)) for a, s in ranked[:3]])
        return decision


_router: Optional[SemanticRouter] = None


def get_semantic_router() -> SemanticRouter:
    global _router
    if _router is None:
        _router = SemanticRouter(min_score=settings.router_min_score, margin=settings.router_margin)
    return _router
