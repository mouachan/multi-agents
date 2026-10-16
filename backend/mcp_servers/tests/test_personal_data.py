"""Personal data never leaves an MCP server (shared/personal_data.py)."""
from conftest import call
from shared.db import fetch_one
from shared.personal_data import mask, mask_by_patterns


async def test_personal_fields_are_replaced_by_their_type(servers):
    number = (await fetch_one("SELECT claim_number AS number FROM claims c JOIN users u ON u.user_id = c.user_id "
                              "WHERE u.email IS NOT NULL ORDER BY claim_number LIMIT 1"))["number"]
    claim = (await call(servers["claims"], "get_claim", claim_id=number))["claim"]
    assert claim["user_name"] == "[PERSON]" and claim["user_email"] == "[EMAIL_ADDRESS]"

    user = (await call(servers["rag"], "retrieve_user_info", user_id=number))["user_info"]
    assert user["full_name"] == "[PERSON]" and user["email"] == "[EMAIL_ADDRESS]" and user["user_id"]


async def test_free_text_is_masked_and_the_rest_is_kept():
    result = await mask({"claim": {"description": "Contact jean.dupont@mail.fr or 06 12 34 56 78, IBAN "
                                                  "FR76 3000 6000 0112 3456 7890 189, claim CLM-2024-0001, $12,500.00",
                                   "claim_type": "Auto"}})
    text = result["claim"]["description"]
    assert "jean.dupont" not in text and "06 12" not in text and "FR76" not in text
    assert "[EMAIL_ADDRESS]" in text and "CLM-2024-0001" in text and "$12,500.00" in text
    assert result["claim"]["claim_type"] == "Auto"


def test_patterns_keep_dates_amounts_and_case_numbers():
    text = "AO-2026-IDF-001 du 2024-01-15, budget 2 500 000 EUR, colis 6C123456789FR"
    assert mask_by_patterns(text) == text
