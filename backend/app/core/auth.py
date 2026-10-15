"""Authentication and access control.

Users log in with OpenShift OAuth (oauth-proxy in front of the UI): each API request carries the
user's OpenShift token (X-Forwarded-Access-Token from the proxy, or Authorization: Bearer for
API clients). The backend:
  - validates it with a TokenReview (user name and groups);
  - checks what the user may use with SubjectAccessReviews against OpenShift RBAC
    (helm/multi-agents/templates/auth/profiles-rbac.yaml):
        verb "use"   on services/<domain>-agent -> the agent of a domain (chat, business pages)
        verb "admin" on services/backend        -> administration (demo reset)
  - keeps the token for the request (ContextVar, inherited by the background jobs it starts),
    so it is forwarded to the agents, which present it to the MCP Gateway (tools governance).
Results are cached for a minute. AUTH_ENABLED=false (local stack): every request is an
administrator with every agent.
"""
import hashlib
import json
import logging
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Tuple

import httpx
from fastapi import Depends, HTTPException, Request

from app.core.config import settings

logger = logging.getLogger(__name__)

DOMAINS = ("claims", "tenders", "postal")  # one A2A agent each: <domain>-agent
SA_DIR = Path("/var/run/secrets/kubernetes.io/serviceaccount")
K8S_API = "https://kubernetes.default.svc"
CACHE_TTL = 60  # seconds

_token: ContextVar[Optional[str]] = ContextVar("user_token", default=None)
_cache: Dict[str, Tuple[float, "User"]] = {}


@dataclass(frozen=True)
class User:
    username: str
    groups: Tuple[str, ...]
    domains: FrozenSet[str]          # agents the user may use
    admin: bool
    profiles: Tuple[str, ...] = field(default=())  # access profiles (OpenShift groups) of the user

    def to_dict(self) -> Dict:
        return {"username": self.username, "groups": list(self.groups), "profiles": list(self.profiles),
                "domains": sorted(self.domains), "admin": self.admin}


LOCAL_ADMIN = User("local-admin", (), frozenset(DOMAINS), True, ("admin",))


def current_token() -> Optional[str]:
    """OpenShift token of the user of the current request (None without authentication)."""
    return _token.get()


def _profiles(groups: Tuple[str, ...]) -> Tuple[str, ...]:
    """Access profiles (AUTH_PROFILES: id -> {group, displayName, ...}) the groups belong to."""
    try:
        profiles = json.loads(settings.auth_profiles or "{}")
    except ValueError:
        return ()
    return tuple(pid for pid, p in profiles.items() if p.get("group") in groups)


class _Kubernetes:
    """TokenReview / SubjectAccessReview with the backend's ServiceAccount."""

    def __init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None

    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            token = (SA_DIR / "token").read_text().strip()
            self._client = httpx.AsyncClient(base_url=K8S_API, verify=str(SA_DIR / "ca.crt"), timeout=10,
                                             headers={"Authorization": f"Bearer {token}"})
        return self._client

    async def review_token(self, token: str) -> Optional[Dict]:
        resp = await self._http().post("/apis/authentication.k8s.io/v1/tokenreviews", json={
            "apiVersion": "authentication.k8s.io/v1", "kind": "TokenReview", "spec": {"token": token}})
        resp.raise_for_status()
        status = resp.json().get("status", {})
        return status.get("user") if status.get("authenticated") else None

    async def can(self, username: str, groups: List[str], verb: str, name: str) -> bool:
        resp = await self._http().post("/apis/authorization.k8s.io/v1/subjectaccessreviews", json={
            "apiVersion": "authorization.k8s.io/v1", "kind": "SubjectAccessReview",
            "spec": {"user": username, "groups": groups, "resourceAttributes": {
                "namespace": settings.auth_namespace, "verb": verb, "resource": "services", "name": name}}})
        resp.raise_for_status()
        return bool(resp.json().get("status", {}).get("allowed"))


_k8s = _Kubernetes()


async def _resolve(token: str) -> User:
    key = hashlib.sha256(token.encode()).hexdigest()
    cached = _cache.get(key)
    if cached and cached[0] > time.time():
        return cached[1]
    identity = await _k8s.review_token(token)
    if not identity:
        raise HTTPException(status_code=401, detail="Invalid or expired OpenShift token")
    username, groups = identity["username"], list(identity.get("groups") or [])
    domains = frozenset([d for d in DOMAINS if await _k8s.can(username, groups, "use", f"{d}-agent")])
    admin = await _k8s.can(username, groups, "admin", "backend")
    user = User(username, tuple(groups), domains, admin, _profiles(tuple(groups)))
    _cache[key] = (time.time() + CACHE_TTL, user)
    logger.info("Authenticated %s: agents %s%s", username, sorted(domains), " (admin)" if admin else "")
    return user


async def current_user(request: Request) -> User:
    """FastAPI dependency: the authenticated user (401 without a valid token)."""
    if not settings.auth_enabled:
        return LOCAL_ADMIN
    token = request.headers.get("x-forwarded-access-token")
    authorization = request.headers.get("authorization", "")
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
    return user


def require_domain(domain: str):
    """FastAPI dependency factory: the user may use the agent of this domain."""
    async def dependency(user: User = Depends(current_user)) -> User:
        if domain not in user.domains:
            raise HTTPException(status_code=403, detail=f"Your profile has no access to the {domain} agent")
        return user
    return dependency


async def require_admin(user: User = Depends(current_user)) -> User:
    if not user.admin:
        raise HTTPException(status_code=403, detail="Administrator profile required")
    return user


def agent_domain(a2a_url: Optional[str]) -> Optional[str]:
    """Domain of an A2A agent from its URL (http://<domain>-agent.<ns>.svc...)."""
    if not a2a_url:
        return None
    host = a2a_url.split("://", 1)[-1].split(".", 1)[0].split(":", 1)[0]
    return host[:-len("-agent")] if host.endswith("-agent") else None
