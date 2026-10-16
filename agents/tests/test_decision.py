"""The decision block that ends a processing (shared/decision.py).

From the repository root:
    podman run --rm -v ./agents:/src:ro,Z -w /src registry.access.redhat.com/ubi9/python-312 \
      bash -c "pip install -q -r shared/requirements.txt pytest pytest-asyncio && python -m pytest -q tests -p no:cacheprovider"
"""
from shared.decision import final_request, parse_decision


def test_the_request_lists_the_decisions_and_asks_for_the_brief_only_for_a_review():
    request = final_request(["approve", "deny", "manual_review"], "manual_review", ["approve", "deny"])
    assert '"approve", "deny", "manual_review"' in request
    assert 'When your recommendation is "manual_review"' in request and '"suggestion"' in request
    assert "When your recommendation" not in final_request(["go", "no_go"])


def test_a_review_decision_comes_with_its_brief():
    answer = """The invoice is missing.
```json
{"recommendation": "manual_review", "confidence": 0.55, "reasoning": "Facture absente.",
 "reasoning_en": "Invoice missing.",
 "review": {"reasons": ["No invoice"], "checks": ["Ask for the invoice", ""], "suggestion": "approve"}}
```"""
    assert parse_decision(answer) == {
        "recommendation": "manual_review", "confidence": 0.55, "reasoning": "Facture absente.",
        "reasoning_en": "Invoice missing.",
        "review": {"reasons": ["No invoice"], "checks": ["Ask for the invoice"], "suggestion": "approve"},
    }


def test_common_model_slips_are_accepted():
    # no code block, a trailing comma, a confidence in percent
    decision = parse_decision('Decision: {"recommendation": "go", "confidence": "85%", "reasoning": "ok",}')
    assert decision["recommendation"] == "go" and decision["confidence"] == 0.85 and decision["review"] is None


def test_the_last_block_wins():
    answer = '```json\n{"recommendation": "deny"}\n```\nCorrection:\n```json\n{"recommendation": "approve"}\n```'
    assert parse_decision(answer)["recommendation"] == "approve"


def test_an_answer_without_a_block_has_no_recommendation():
    # the backend then hands the case to a reviewer, with the answer as the reasoning
    assert parse_decision("I could not decide.") == {
        "recommendation": None, "confidence": 0.0, "reasoning": "I could not decide."}
