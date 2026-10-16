from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    agent_id: str
    agent_port: int = 8090
    # Public URL advertised in the AgentCard (in-cluster Service URL by default)
    agent_public_url: str = ""

    # OGX (Responses API, OpenAI-compatible) — RHOAI 3.5
    ogx_endpoint: str = ""
    ogx_default_model: str = "gpt-oss-120b"
    # Model for batch processing (metadata mode=process); default: ogx_default_model.
    # When an OGX response fails, the executor retries once with the other model.
    ogx_process_model: str = ""
    ogx_timeout: int = 300
    ogx_max_tokens: int = 4096

    # MCP tools — either one MCP Gateway URL for all tools, or one URL per server
    # (MCP_SERVER_URL_TEMPLATE is formatted with the server name, e.g. claims-server)
    mcp_gateway_url: str = ""
    mcp_server_url_template: str = "http://{server}:8080/mcp"
    # Without the gateway: the servers deployed, comma-separated (empty = all). OGX fails the whole
    # response when one server of the request is unreachable (e.g. no sandbox in the local stack).
    mcp_servers: str = ""

    # NeMo Guardrails (TrustyAI) — PII masking + input/output rails
    guardrails_endpoint: str = ""
    guardrails_config_id: str = "multi-agents"
    # NeMo /v1/checks requires a model name (used by LLM-based rails such as self check)
    guardrails_model: str = "llama-scout-17b"
    guardrails_timeout: float = 15.0
    guardrails_fail_open: bool = True
    # When output rails are active, mask the answer sentence by sentence before streaming
    # it (no unmasked PII ever reaches the UI); tool activity is always streamed live.
    guardrails_buffer_output: bool = True

    # MLflow (RHOAI) — tracing + Prompt Registry
    mlflow_tracking_uri: str = ""
    mlflow_experiment_name: str = ""
    mlflow_workspace: str = ""
    prompt_alias: str = "production"
    prompt_cache_ttl: int = 60
    # Prompt files of the Helm chart (helm/multi-agents/files/prompts/agents), mounted from a
    # ConfigMap: used until the MLflow alias exists, and what prompt-sync versions in MLflow
    prompts_dir: str = "/opt/app-root/prompts"

    # SPIFFE (ZTWIM): allowed caller SPIFFE ID paths, comma-separated (active when
    # SPIFFE_ENDPOINT_SOCKET is set by the SPIFFE CSI driver mount)
    spiffe_allowed_ids: str = ""

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
