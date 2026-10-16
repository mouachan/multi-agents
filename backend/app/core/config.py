"""Backend settings, read from environment variables (Helm: templates/backend/configmap.backend-config.yaml).

Locally (podman compose), the values come from the environment of the compose file and from .env.
"""
from typing import Dict, List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---- application
    app_name: str = "Multi-Agent AI Platform"
    app_version: str = "3.5.0"
    debug: bool = False
    environment: str = "production"
    api_v1_prefix: str = "/api/v1"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    # ---- database (PostgreSQL + pgvector)
    postgres_host: str = "postgresql"
    postgres_port: int = 5432
    postgres_database: str = "multi_agent_db"
    postgres_user: str
    postgres_password: str
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_pre_ping: bool = True
    database_pool_recycle: int = 3600

    @property
    def async_database_url(self) -> str:
        return (f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}")

    # ---- A2A agents (one per domain, app/agents.py); empty = not deployed
    claims_agent_a2a_url: str = ""
    tenders_agent_a2a_url: str = ""
    postal_agent_a2a_url: str = ""
    agent_timeout: int = 300          # seconds, for one agent task

    def agent_urls(self) -> Dict[str, str]:
        """A2A URL of the agent of each domain."""
        urls = {"claims": self.claims_agent_a2a_url, "tenders": self.tenders_agent_a2a_url,
                "postal": self.postal_agent_a2a_url}
        return {domain: url for domain, url in urls.items() if url}

    # ---- OGX (embeddings, document files, routing model)
    ogx_endpoint: str = ""
    ogx_default_model: str = ""       # model of the router's tie-break between two close agents
    ogx_embedding_model: str = "nomic-embed-text-v1-5"

    # ---- chat routing (app/services/chat/routing.py)
    router_enabled: bool = True
    router_min_score: float = 0.62
    router_margin: float = 0.04
    chat_config_file: str = "/app/prompts/chat-config.yaml"   # welcome messages, suggested actions...

    # ---- prompt files (app/core/prompts.py)
    prompts_dir: str = "/app/prompts"

    # ---- NeMo Guardrails (app/services/guardrails.py)
    guardrails_server_url: str = ""
    guardrails_config_id: str = "multi-agents"
    guardrails_model_name: str = "llama-scout-17b"

    # ---- MLflow tracing (app/core/tracing.py) and prompts
    mlflow_tracking_uri: str = ""
    mlflow_experiment_name: str = "multi-agent-orchestrator"
    mlflow_rhoai_workspace: str = ""
    mlflow_ui_url: str = ""           # base URL of the MLflow UI, for the trace links of the chat

    # ---- authentication (app/core/auth.py): OpenShift token + RBAC access profiles
    auth_enabled: bool = False
    auth_profiles: str = "{}"         # JSON {id: {group, displayName, agents, admin, tokenQuota}}
    auth_namespace: str = "multi-agents"
    auth_agent_tools: str = "{}"      # JSON {agent: [MCP tools]}: what the RBAC grants with each agent

    # ---- models called as the user (app/services/maas_keys.py); empty URL: the platform key
    maas_api_url: str = ""            # cluster MaaS API, e.g. https://maas.<cluster-domain>/maas-api/v1
    maas_subscription_prefix: str = "multi-agents"   # profile <id> -> MaaSSubscription <prefix>-<id>
    maas_tls_verify: bool = True

    # ---- OpenShell sandbox page (app/api/sandbox.py); empty = not deployed
    sandbox_server_url: str = ""

    # ---- demo reset (app/services/demo_reset.py): the database seed and the installation precedents
    seed_data_file: str = "/app/seed/seed.sql"
    precedents_file: str = "/app/seed/precedent_decisions.json"

    # ---- CORS: JSON list of the web origins allowed to call the API directly. The UI calls it through
    # its own nginx (same origin), so only the local development servers need it
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")


settings = Settings()
