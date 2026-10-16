"""The OCR server keeps the text it read: the same document is not read again (ocr_server)."""
from conftest import call
from shared.db import execute, fetch_one


async def test_a_document_already_read_is_returned_at_once(servers):
    # the seeded claim with a document (CLM-ENT-001), not the Auto claims of the other tests
    claim = await fetch_one("""SELECT c.id, c.claim_number FROM claims c JOIN claim_documents d ON d.claim_id = c.id
        WHERE c.claim_type <> 'Auto' ORDER BY c.claim_number DESC LIMIT 1""")
    await execute("UPDATE claims SET document_path = 'file-test-cache' WHERE id = CAST(:id AS uuid)", id=claim["id"])
    await execute("""UPDATE claim_documents SET raw_ocr_text = 'Texte lu. Contact: a.b@mail.fr', page_count = 1,
        metadata = jsonb_build_object('ocr_file_id', 'file-test-cache') WHERE claim_id = CAST(:id AS uuid)""", id=claim["id"])

    # OGX is not reachable in the tests: an answer proves the cache was used
    result = await call(servers["ocr"], "ocr_document", document_id=claim["claim_number"])
    assert result["success"] and result["already_read"] is True
    assert result["raw_text"] == "Texte lu. Contact: [EMAIL_ADDRESS]"


async def test_other_numbers_are_refused(servers):
    result = await call(servers["ocr"], "ocr_document", document_id="XYZ-1")
    assert result["success"] is False and "not a claim, tender or complaint number" in result["error"]
