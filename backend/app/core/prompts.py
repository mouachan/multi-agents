"""Texts the backend sends to the agents: the processing requests of each domain.

The files live in helm/multi-agents/files/prompts/backend/ and are mounted in the backend at
PROMPTS_DIR (ConfigMap, see templates/backend): edit a file and run `helm upgrade` to change a text,
no image rebuild. Locally, PROMPTS_DIR points to that folder of the repository.

The agents' own instructions (system prompts) are not here: they are versioned in MLflow and owned
by the agents (agents/shared/prompts.py).
"""
import logging
from functools import lru_cache
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    """Content of the prompt file `name` (empty, with an error in the logs, when it is missing)."""
    path = Path(settings.prompts_dir) / name
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError as e:
        logger.error("Prompt file %s not found (%s)", path, e)
        return ""
