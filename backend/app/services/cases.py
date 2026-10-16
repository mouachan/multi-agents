"""How a case is described: to the agent (the processing request) and to the UI (the API)."""
from typing import Any, Dict, List

from sqlalchemy import inspect

from app.domains import DomainSpec
from app.domains.spec import fact, section
from app.models.case import CaseColumns

_SHARED_COLUMNS = {name for name in vars(CaseColumns) if not name.startswith("_")}


def case_number(spec: DomainSpec, case) -> str:
    return getattr(case, spec.number_field)


def case_data(spec: DomainSpec, case) -> Dict[str, Any]:
    """The domain's own columns of a case: number, type, claimant, tracking number..."""
    data = {}
    for column in inspect(spec.model).column_attrs:
        if column.key in _SHARED_COLUMNS or column.key == "status":
            continue
        value = getattr(case, column.key)
        data[column.key] = getattr(value, "value", value)   # enums -> their value
    return data


def case_to_api(spec: DomainSpec, case) -> Dict[str, Any]:
    """A case as the API returns it: the fields shared by all domains, then the domain's own columns."""
    meta = case.meta or {}
    extras = case.api_extras() if hasattr(case, "api_extras") else {}   # e.g. the claimant's name
    return {
        "id": str(case.id),
        "domain": spec.name,
        "number": case_number(spec, case),
        "status": getattr(case.status, "value", case.status),
        "submitted_at": case.submitted_at,
        "processed_at": case.processed_at,
        "total_processing_time_ms": case.total_processing_time_ms,
        **case_data(spec, case),
        **extras,
        "metadata": meta,
        "processing_steps": meta.get("processing_steps", []),
        # the facts of the last processing, taken from the agent's tool outputs (the domain's evidence())
        "evidence": evidence(spec, case) if meta.get("processing_steps") else [],
        "trace": meta.get("trace"),     # MLflow trace of the last processing
    }


def evidence(spec: DomainSpec, case) -> List[Dict[str, Any]]:
    """The domain's evidence, and a security section when tools removed instructions aimed at the AI."""
    outputs = tool_outputs(case)
    sections = spec.evidence(outputs)
    removed = sum(output.get("security", {}).get("instructions_removed", 0) for output in outputs.values())
    if removed:
        sections = [section("security", facts=[fact("instructions_removed", removed)]), *sections]
    return sections


def tool_outputs(case) -> Dict[str, Dict[str, Any]]:
    """{tool name: output} of the case's last processing."""
    return {step["step_name"]: step.get("output_data") or {}
            for step in (case.meta or {}).get("processing_steps", [])}
