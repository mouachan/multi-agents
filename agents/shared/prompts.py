"""Versioned system prompts from the MLflow Prompt Registry (RHOAI 3.5 MLflow).

Resolution order for a prompt name (e.g. "claims-processing-agent"):
  1. MLflow Prompt Registry  prompts:/<name>@<alias>   (cached PROMPT_CACHE_TTL seconds,
     so promoting a new version to the alias in the MLflow UI takes effect without restart)
  2. the chart's prompt file  <PROMPTS_DIR>/<name>.txt (ConfigMap)
  3. last value successfully loaded (if MLflow becomes unreachable)

Prompts are seeded/versioned by the Helm `prompt-sync` job (shared/prompt_sync.py).
"""
import asyncio
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from . import mlflow_auth
from .config import AgentSettings

logger = logging.getLogger(__name__)

_VAR_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}|\{(\w+)\}")


def render(template: str, **variables: str) -> str:
    """Fill {{var}} (MLflow style) and {var} placeholders; other braces (JSON examples) are kept."""
    def _sub(m: re.Match) -> str:
        key = m.group(1) or m.group(2)
        return str(variables[key]) if key in variables else m.group(0)
    return _VAR_RE.sub(_sub, template)


@dataclass
class PromptValue:
    name: str
    text: str
    version: Optional[str] = None
    source: str = "none"  # mlflow | file | none

    def info(self) -> Dict[str, Optional[str]]:
        return {"name": self.name, "version": self.version, "source": self.source}


class PromptStore:
    def __init__(self, settings: AgentSettings):
        self.alias = settings.prompt_alias
        self.ttl = settings.prompt_cache_ttl
        self.dir = Path(settings.prompts_dir)
        self.enabled = mlflow_auth.configure(settings)
        self._cache: Dict[str, tuple[float, PromptValue]] = {}

    def _from_file(self, name: str) -> Optional[PromptValue]:
        path = self.dir / f"{name}.txt"
        if not path.is_file():
            return None
        return PromptValue(name, path.read_text(encoding="utf-8"), None, "file")

    def _from_mlflow(self, name: str) -> Optional[PromptValue]:
        import mlflow

        prompt = mlflow.genai.load_prompt(f"prompts:/{name}@{self.alias}")
        return PromptValue(name, prompt.template, str(prompt.version), "mlflow")

    async def get(self, name: str) -> PromptValue:
        cached = self._cache.get(name)
        if cached and time.monotonic() - cached[0] < self.ttl:
            return cached[1]

        value: Optional[PromptValue] = None
        if self.enabled:
            try:
                value = await asyncio.to_thread(self._from_mlflow, name)
            except Exception as e:
                logger.warning("Prompt '%s@%s' not loaded from MLflow (%s) — using fallback",
                               name, self.alias, e)
        if value is None:
            value = self._from_file(name) or (cached[1] if cached else PromptValue(name, ""))
        if not value.text:
            logger.error("Prompt '%s' unavailable (MLflow and %s)", name, self.dir)

        self._cache[name] = (time.monotonic(), value)
        return value
