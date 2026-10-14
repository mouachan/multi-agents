"""MLflow (RHOAI 3.5) connection settings shared by tracing and the Prompt Registry.

RHOAI MLflow is multi-tenant: requests are authenticated with the pod's
ServiceAccount token (Kubernetes RBAC) and scoped to a workspace (= namespace).
"""
import logging
import os
from typing import Dict, Optional

from .config import AgentSettings

logger = logging.getLogger(__name__)

SA_TOKEN_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/token"
SA_NAMESPACE_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
SERVICE_CA_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt"


def _read(path: str) -> Optional[str]:
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def workspace(settings: AgentSettings) -> str:
    return settings.mlflow_workspace or _read(SA_NAMESPACE_PATH) or ""


def ca_bundle() -> Optional[str]:
    return SERVICE_CA_PATH if os.path.exists(SERVICE_CA_PATH) else None


def headers(settings: AgentSettings) -> Dict[str, str]:
    h: Dict[str, str] = {}
    token = _read(SA_TOKEN_PATH)
    if token:
        h["Authorization"] = f"Bearer {token}"
    ws = workspace(settings)
    if ws:
        h["X-Mlflow-Workspace"] = ws
    return h


def configure(settings: AgentSettings) -> bool:
    """Configure the mlflow client (env-based) for the RHOAI server. Returns True if enabled."""
    if not settings.mlflow_tracking_uri:
        return False
    os.environ["MLFLOW_TRACKING_URI"] = settings.mlflow_tracking_uri
    token = _read(SA_TOKEN_PATH)
    if token:
        os.environ["MLFLOW_TRACKING_TOKEN"] = token
    ca = ca_bundle()
    if ca:
        os.environ.setdefault("MLFLOW_TRACKING_SERVER_CERT_PATH", ca)
    ws = workspace(settings)
    if ws:
        os.environ["MLFLOW_WORKSPACE"] = ws
    return True
