"""Seed / version the MLflow Prompt Registry from the Helm prompt files.

Run by the Helm `prompt-sync` job (post-install/post-upgrade):
    python -m shared.prompt_sync

For every <name>.txt found in PROMPTS_DIRS:
  - registers a new prompt version when the text differs from the latest version
  - points PROMPT_ALIAS (default "production") to it when PROMPT_PROMOTE=true,
    or when the alias does not exist yet
Versions created from the MLflow UI are kept; with PROMPT_PROMOTE=false the
alias is never moved by Helm, so a version promoted manually stays live.
"""
import logging
import os
import sys
import time
from pathlib import Path

from .config import AgentSettings
from . import mlflow_auth

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("prompt-sync")


def _latest(client, name):
    try:
        versions = client.search_prompt_versions(name).prompt_versions
    except Exception:
        return None
    return max(versions, key=lambda v: int(v.version)) if versions else None


def _alias_exists(mlflow, name, alias) -> bool:
    try:
        mlflow.genai.load_prompt(f"prompts:/{name}@{alias}")
        return True
    except Exception:
        return False


def main() -> int:
    os.environ.setdefault("AGENT_ID", "prompt-sync")
    settings = AgentSettings()
    if not mlflow_auth.configure(settings):
        logger.error("MLFLOW_TRACKING_URI is not set")
        return 1

    import mlflow
    from mlflow import MlflowClient

    promote = os.getenv("PROMPT_PROMOTE", "true").lower() == "true"
    release = os.getenv("HELM_RELEASE_REVISION", "")
    client = MlflowClient()

    files = sorted({p for d in settings.prompt_dir_list for p in Path(d).glob("*.txt")}, key=lambda p: p.name)
    if not files:
        logger.error("No prompt files found in %s", settings.prompts_dirs)
        return 1

    for attempt in range(30):
        try:
            client.search_experiments(max_results=1)
            break
        except Exception as e:
            logger.info("Waiting for MLflow (%d/30): %s", attempt + 1, e)
            time.sleep(10)
    else:
        logger.error("MLflow not reachable")
        return 1

    failures = 0
    for path in files:
        name = path.stem
        text = path.read_text(encoding="utf-8")
        try:
            latest = _latest(client, name)
            if latest is not None and latest.template == text:
                version = latest.version
                logger.info("%-40s unchanged (v%s)", name, version)
            else:
                pv = mlflow.genai.register_prompt(
                    name=name,
                    template=text,
                    commit_message=f"Synced from Helm chart{f' (revision {release})' if release else ''}",
                    tags={"source": "helm", "file": path.name, "app": "multi-agents"},
                )
                version = pv.version
                logger.info("%-40s registered v%s", name, version)

            if promote or not _alias_exists(mlflow, name, settings.prompt_alias):
                mlflow.genai.set_prompt_alias(name, alias=settings.prompt_alias, version=int(version))
                logger.info("%-40s @%s -> v%s", name, settings.prompt_alias, version)
        except Exception as e:
            failures += 1
            logger.error("%-40s FAILED: %s", name, e)

    logger.info("Prompt sync done: %d prompts, %d failures", len(files), failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
