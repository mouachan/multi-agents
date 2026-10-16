"""Authentication and access control.

Users log in with OpenShift OAuth (oauth-proxy in front of the UI): each API request carries the
user's OpenShift token (X-Forwarded-Access-Token from the proxy, or Authorization: Bearer for
API clients). The backend:
  - validates it with a TokenReview (user name and groups);
  - checks what the user may use with SubjectAccessReviews against OpenShift RBAC
    (helm/multi-agents/templates/auth/profiles-rbac.yaml):
        verb "use"   on services/<domain>-agent           -> the agent of a domain (chat, business pages)
        verb "call"  on tools.mcp.multi-agents.io/<tool>  -> an MCP tool of these agents (AUTH_AGENT_TOOLS);
                                                             the MCP Gateway enforces the same rule
        verb "admin" on services/backend                  -> administration (demo reset)
    The agents are only given the tools the user may call: a tool the profile does not allow is
    explained to the user instead of failing at the gateway.
  - keeps the token for the request (ContextVar, inherited by the background jobs it starts),
    so it is forwarded to the agents, which present it to the MCP Gateway (tools governance).
Results are cached for a minute. AUTH_ENABLED=false (local stack): every request is an
administrator with every agent.
"""
import asyncio
import hashlib
import json
import logging
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Tuple

import httpx
from fastapi import Depends, HTTPException
from starlette.requests import HTTPConnection

from app.core.config import settings

logger = logging.getLogger(__name__)

DOMAINS = ("claims", "tenders", "postal")  # app/domains; one A2A agent each: <domain>-agent
SA_DIR = Path("/var/run/secrets/kubernetes.io/serviceaccount")
K8S_API = "https://kubernetes.default.svc"
MCP_TOOLS_GROUP = "mcp.multi-agents.io"   # RBAC resource "tools" of the MCP Gateway AuthPolicy
CACHE_TTL = 60  # seconds

_token: ContextVar[Optional[str]] = ContextVar("user_token", default=None)
_username: ContextVar[Optional[str]] = ContextVar("username", default=None)
_user: ContextVar[Optional["User"]] = ContextVar("user", default=None)
_cache: Dict[str, Tuple[float, "User"]] = {}


@dataclass(frozen=True)
class User:
    username: str
    groups: Tuple[str, ...]
    domains: FrozenSet[str]          # agents the user may use
    admin: bool
    profiles: Tuple[str, ...] = field(default=())  # access profiles (OpenShift groups) of the user
    # MCP tools the user may call; None: no restriction (authentication off)
    tools: Optional[FrozenSet[str]] = None

    def missing_tools(self, tools: List[str]) -> List[str]:
        """The tools of the list this user may not call."""
        return [] if self.tools is None else [t for t in tools if t not in self.tools]

    def to_dict(self) -> Dict:
        return {"username": self.username, "groups": list(self.groups), "profiles": list(self.profiles),
                "domains": sorted(self.domains), "admin": self.admin,
                "tools": None if self.tools is None else sorted(self.tools)}


LOCAL_ADMIN = User("local-admin", (), frozenset(DOMAINS), True, ("admin",))


def current_token() -> Optional[str]:
    """OpenShift token of the user of the current request (None without authentication)."""
    return _token.get()


def current_username() -> Optional[str]:
    """User of the current request (MLflow traces: user.id), None without authentication."""
    return _username.get()


def request_user() -> Optional["User"]:
    """User of the current request, also in the background jobs it started (None without authentication)."""
    return _user.get()


def load_profiles() -> Dict[str, Dict]:
    """Access profiles (AUTH_PROFILES): id -> {group, displayName, agents, admin}."""
    try:
        return json.loads(settings.auth_profiles or "{}")
    except ValueError:
        logger.error("AUTH_PROFILES is not valid JSON")
        return {}


def agent_tools(domains) -> List[str]:
    """MCP tools granted with the agents of these domains (AUTH_AGENT_TOOLS)."""
    try:
        granted = json.loads(settings.auth_agent_tools or "{}")
    except ValueError:
        logger.error("AUTH_AGENT_TOOLS is not valid JSON")
        return []
    return sorted({tool for domain in domains for tool in granted.get(domain, [])})


def _profiles(groups: Tuple[str, ...]) -> Tuple[str, ...]:
    """Access profiles the groups belong to."""
    return tuple(pid for pid, p in load_profiles().items() if p.get("group") in groups)


class KubernetesApi:
    """OpenShift API calls with the backend's ServiceAccount: TokenReview / SubjectAccessReview,
    and the profile groups for the administration (app/services/access_profiles.py)."""

    def __init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None

    def http(self) -> httpx.AsyncClient:
        if self._client is None:
            token = (SA_DIR / "token").read_text().strip()
            self._client = httpx.AsyncClient(base_url=K8S_API, verify=str(SA_DIR / "ca.crt"), timeout=10,
                                             headers={"Authorization": f"Bearer {token}"})
        return self._client

    async def review_token(self, token: str) -> Optional[Dict]:
        resp = await self.http().post("/apis/authentication.k8s.io/v1/tokenreviews", json={
            "apiVersion": "authentication.k8s.io/v1", "kind": "TokenReview", "spec": {"token": token}})
        resp.raise_for_status()
        status = resp.json().get("status", {})
        return status.get("user") if status.get("authenticated") else None

    async def can(self, username: Optional[str], groups: List[str], verb: str, name: str,
                  resource: str = "services", api_group: str = "") -> bool:
        """RBAC check in the release namespace (username None: what the groups alone may do)."""
        spec: Dict = {"groups": groups, "resourceAttributes": {
            "namespace": settings.auth_namespace, "group": api_group, "resource": resource,
            "verb": verb, "name": name}}
        if username:
            spec["user"] = username
        resp = await self.http().post("/apis/authorization.k8s.io/v1/subjectaccessreviews", json={
            "apiVersion": "authorization.k8s.io/v1", "kind": "SubjectAccessReview", "spec": spec})
        resp.raise_for_status()
        return bool(resp.json().get("status", {}).get("allowed"))

    async def callable_tools(self, username: Optional[str], groups: List[str], tools: List[str]) -> FrozenSet[str]:
        """The tools of the list the user (or the groups) may call through the MCP Gateway."""
        allowed = await asyncio.gather(*(
            self.can(username, groups, "call", tool, resource="tools", api_group=MCP_TOOLS_GROUP) for tool in tools))
        return frozenset(tool for tool, ok in zip(tools, allowed) if ok)


kubernetes = KubernetesApi()


async def _resolve(token: str) -> User:
    key = hashlib.sha256(token.encode()).hexdigest()
    cached = _cache.get(key)
    if cached and cached[0] > time.time():
        return cached[1]
    identity = await kubernetes.review_token(token)
    if not identity:
        raise HTTPException(status_code=401, detail="Invalid or expired OpenShift token")
    username, groups = identity["username"], list(identity.get("groups") or [])
    domains = frozenset([d for d in DOMAINS if await kubernetes.can(username, groups, "use", f"{d}-agent")])
    admin = await kubernetes.can(username, groups, "admin", "backend")
    tools = await kubernetes.callable_tools(username, groups, agent_tools(domains))
    user = User(username, tuple(groups), domains, admin, _profiles(tuple(groups)), tools)
    _cache[key] = (time.time() + CACHE_TTL, user)
    logger.info("Authenticated %s: agents %s, %d tools%s", username, sorted(domains), len(tools),
                " (admin)" if admin else "")
    return user


def forget_user(username: str) -> None:
    """Drop the cached rights of a user (profiles changed): applied at the next request."""
    for key in [k for k, (_, user) in _cache.items() if user.username == username]:
        _cache.pop(key, None)


async def current_user(connection: HTTPConnection) -> User:
    """FastAPI dependency: the authenticated user (401 without a valid token).
    HTTPConnection: the same dependency serves the HTTP and the WebSocket routes."""
    if not settings.auth_enabled:
        return LOCAL_ADMIN
    token = connection.headers.get("x-forwarded-access-token")
    authorization = connection.headers.get("authorization", "")
    if not token and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        user = await _resolve(token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Authentication check failed: %s", e)
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    _token.set(token)
    _username.set(user.username)
    _user.set(user)
    return user


def require_domain(domain: str):
    """FastAPI dependency factory: the user may use the agent of this domain."""
    async def dependency(user: User = Depends(current_user)) -> User:
        if domain not in user.domains:
            raise HTTPException(status_code=403, detail=f"Your profile has no access to the {domain} agent")
        return user
    return dependency


def require_tools(user: User, tools: List[str], purpose: str) -> None:
    """403 when the user's profile does not allow every tool a task needs (e.g. a processing)."""
    missing = user.missing_tools(tools)
    if missing:
        raise HTTPException(status_code=403, detail=f"Your profile does not allow the tools {', '.join(missing)}, "
                                                    f"needed {purpose}. An administrator can grant them.")


async def require_admin(user: User = Depends(current_user)) -> User:
    if not user.admin:
        raise HTTPException(status_code=403, detail="Administrator profile required")
    return user
