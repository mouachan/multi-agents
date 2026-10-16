"""What the user's access profile allows (shared/executor.py) and the MaaS quota (shared/ogx_client.py)."""
import pytest

from shared.executor import Profile
from shared.ogx_client import QuotaExceeded, _failure

PROFILE = Profile(prompt="claims-agent", tools=["get_claim", "ocr_document", "run_python"])


def test_without_rights_the_profile_tools_are_offered():
    assert PROFILE.offered_tools({}) == ["get_claim", "ocr_document", "run_python"]
    assert PROFILE.withheld_tools({}) == []


def test_a_task_selects_among_the_profile_tools_in_its_order_and_withholds_nothing():
    meta = {"tools": ["ocr_document", "get_claim", "list_tenders"]}
    assert PROFILE.offered_tools(meta) == ["ocr_document", "get_claim"]
    assert PROFILE.withheld_tools(meta) == []


def test_the_user_rights_withhold_the_other_tools():
    meta = {"allowed_tools": ["get_claim", "ocr_document", "list_tenders"]}
    assert PROFILE.offered_tools(meta) == ["get_claim", "ocr_document"]
    assert PROFILE.withheld_tools(meta) == ["run_python"]


def test_no_right_means_no_tool():
    assert PROFILE.offered_tools({"allowed_tools": []}) == []
    assert PROFILE.withheld_tools({"allowed_tools": []}) == ["get_claim", "ocr_document", "run_python"]


def test_task_and_rights_together():
    meta = {"tools": ["ocr_document", "run_python"], "allowed_tools": ["ocr_document"]}
    assert PROFILE.offered_tools(meta) == ["ocr_document"]
    assert PROFILE.withheld_tools(meta) == ["run_python"]


@pytest.mark.parametrize("message", [
    "OGX response failed: Error code: 429",
    "OGX /v1/responses 429: Too Many Requests",
])
def test_a_quota_refusal_is_recognized(message):
    assert isinstance(_failure(message), QuotaExceeded)


@pytest.mark.parametrize("message", [
    "OGX response failed: Error code: 401",
    "OGX response failed: Expecting ',' delimiter: line 1 column 429",
])
def test_other_failures_stay_runtime_errors(message):
    error = _failure(message)
    assert isinstance(error, RuntimeError) and not isinstance(error, QuotaExceeded)
