"""Quality of the agents' decisions, measured on the precedents (admin page, MLflow).

The precedents (database/seed_data/precedent_decisions.json) are cases with a known decision. An
evaluation processes each of them again with its domain's agent, exactly as a processing does (same
request, tools and guardrails), but saves nothing: it compares the agent's decision with the expected
one. The result is kept for the admin page and logged as a run of the MLflow experiment
"decision-evaluation": accuracy overall and per domain, share of cases handed to a person, the prompt
versions used, and one line per case.

prompt_alias chooses the version of the agents' prompts ("production" by default): evaluate the
"candidate" alias after registering a new version in MLflow, compare the two runs, then promote.
One evaluation at a time; the last one is kept in memory (one backend replica).
"""
import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import tracing
from app.core.config import settings
from app.domains import DomainSpec, all_domains
from app.services.processing import ask_agent, handed_over, instructions_removed, processing_request

logger = logging.getLogger(__name__)

EXPERIMENT = "decision-evaluation"
CONCURRENCY = 3        # cases processed at the same time (the MaaS rate limit is shared)


@dataclass
class CaseResult:
    domain: str
    number: str
    expected: str
    decision: Optional[str] = None
    confidence: Optional[float] = None
    correct: Optional[bool] = None
    error: Optional[str] = None


@dataclass
class Evaluation:
    prompt_alias: str
    started_at: str
    status: str = "running"            # running | completed | failed
    total: int = 0
    results: List[CaseResult] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    prompts: Dict[str, str] = field(default_factory=dict)      # prompt name -> version used
    mlflow_url: Optional[str] = None
    error: Optional[str] = None

    def to_api(self) -> Dict[str, Any]:
        return {**asdict(self), "done": len(self.results)}


_current: Optional[Evaluation] = None


def current() -> Optional[Dict[str, Any]]:
    return _current.to_api() if _current else None


def is_running() -> bool:
    return _current is not None and _current.status == "running"


def precedents() -> List[tuple]:
    """(domain spec, case number, expected decision) of every precedent."""
    data = json.loads(Path(settings.precedents_file).read_text(encoding="utf-8"))
    return [(spec, item[spec.number_field], item["recommendation"])
            for spec in all_domains() for item in data.get(spec.precedents_key, [])]


def start(prompt_alias: str) -> Evaluation:
    """A new evaluation (run it with run(); app/api/admin.py starts it in the background)."""
    global _current
    _current = Evaluation(prompt_alias=prompt_alias, started_at=datetime.now(timezone.utc).isoformat(),
                          total=len(precedents()))
    return _current


async def run(db_factory, evaluation: Evaluation) -> None:
    """Process every precedent without saving, compare, compute the metrics, log the MLflow run."""
    started = time.monotonic()
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def evaluate(spec: DomainSpec, number: str, expected: str) -> None:
        async with semaphore, db_factory() as db:
            evaluation.results.append(await evaluate_case(db, spec, number, expected, evaluation))

    try:
        await asyncio.gather(*(evaluate(*p) for p in precedents()))
        evaluation.metrics = metrics(evaluation.results, time.monotonic() - started)
        evaluation.mlflow_url = await log_run(evaluation)
        evaluation.status = "completed"
    except Exception as e:
        logger.exception("Evaluation failed")
        evaluation.status, evaluation.error = "failed", str(e)


async def evaluate_case(db: AsyncSession, spec: DomainSpec, number: str, expected: str,
                        evaluation: Evaluation) -> CaseResult:
    result = CaseResult(spec.name, number, expected)
    case = (await db.execute(select(spec.model).where(getattr(spec.model, spec.number_field) == number))).scalar_one_or_none()
    if case is None:
        result.error = "case not found"
        return result
    try:
        answer = await ask_agent(spec, case, await processing_request(db, spec, case),
                                 prompt_alias=evaluation.prompt_alias, session=f"evaluation-{evaluation.started_at}")
    except Exception as e:
        result.error = str(e)[:300]
        return result
    decision = answer.get("decision") or {}
    removed = instructions_removed(answer.get("tool_calls", []))
    if removed:                                   # as a processing would
        decision = handed_over(spec, decision, removed)
    prompt = answer.get("prompt") or {}
    if prompt.get("name"):
        evaluation.prompts[prompt["name"]] = f"{prompt.get('version') or prompt.get('source')}"
    value = decision.get("recommendation")
    result.decision = value if value in spec.statuses_by_decision else spec.review_decision
    result.confidence = decision.get("confidence")
    result.correct = result.decision == expected
    return result


def metrics(results: List[CaseResult], seconds: float) -> Dict[str, float]:
    """Accuracy overall and per domain, share of cases handed to a person, errors, duration."""
    scored = [r for r in results if r.correct is not None]
    values = {"accuracy": _share(scored, lambda r: r.correct), "errors": float(len(results) - len(scored)),
              "duration_s": round(seconds, 1)}
    for spec in all_domains():
        mine = [r for r in scored if r.domain == spec.name]
        if mine:
            values[f"accuracy_{spec.name}"] = _share(mine, lambda r: r.correct)
            values[f"review_rate_{spec.name}"] = _share(mine, lambda r: r.decision == spec.review_decision)
    return values


def _share(items: list, test) -> float:
    return round(sum(1 for i in items if test(i)) / len(items), 3) if items else 0.0


# ------------------------------------------------------------------------------------- MLflow run

async def log_run(evaluation: Evaluation) -> Optional[str]:
    """The evaluation as an MLflow run; returns its UI link (None when MLflow is not configured)."""
    if not settings.mlflow_tracking_uri:
        return None
    base = f"{settings.mlflow_tracking_uri.rstrip('/')}/api/2.0/mlflow"
    now = int(time.time() * 1000)
    try:
        async with httpx.AsyncClient(timeout=20, verify=tracing.mlflow_verify(), headers=tracing.mlflow_headers()) as client:
            experiment_id = await _experiment(client, base)
            run = (await _post(client, f"{base}/runs/create", {
                "experiment_id": experiment_id, "run_name": f"{evaluation.prompt_alias} {evaluation.started_at[:16]}",
                "start_time": now, "tags": [{"key": "prompt_alias", "value": evaluation.prompt_alias}]}))["run"]["info"]
            params = [{"key": "prompt_alias", "value": evaluation.prompt_alias}]
            params += [{"key": f"prompt.{name}", "value": version} for name, version in evaluation.prompts.items()]
            params += [{"key": f"case.{r.number}", "value": f"expected {r.expected}, agent {r.decision or r.error}"[:500]}
                       for r in evaluation.results]
            await _post(client, f"{base}/runs/log-batch", {
                "run_id": run["run_id"], "params": params,
                "metrics": [{"key": k, "value": v, "timestamp": now, "step": 0} for k, v in evaluation.metrics.items()]})
            await _post(client, f"{base}/runs/update", {"run_id": run["run_id"], "status": "FINISHED", "end_time": now})
    except Exception as e:
        logger.warning("Evaluation not logged in MLflow: %s", e)
        return None
    if not settings.mlflow_ui_url:
        return None
    return f"{settings.mlflow_ui_url.rstrip('/')}/#/experiments/{experiment_id}/runs/{run['run_id']}"


async def _experiment(client: httpx.AsyncClient, base: str) -> str:
    found = await client.get(f"{base}/experiments/get-by-name", params={"experiment_name": EXPERIMENT})
    if found.status_code == 200:
        return found.json()["experiment"]["experiment_id"]
    return (await _post(client, f"{base}/experiments/create", {"name": EXPERIMENT}))["experiment_id"]


async def _post(client: httpx.AsyncClient, url: str, body: Dict[str, Any]) -> Dict[str, Any]:
    response = await client.post(url, json=body)
    response.raise_for_status()
    return response.json()
