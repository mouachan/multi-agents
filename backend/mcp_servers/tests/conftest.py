"""The MCP servers, called as the agents call them (tools/call), on the seeded test database.

The embedding model is replaced by a stub: a text always gets the same vector, so a case is closest
to its own document. Personal data is masked by patterns (no NeMo in the tests).
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any, Dict, List

import pytest

from shared import db
from shared.ogx import as_vector

SERVERS = Path(__file__).parent.parent
DIMENSION = 768


def fake_embedding(text: str) -> List[float]:
    """A unit vector derived from the text (same text, same vector)."""
    seed = hashlib.sha256(text.strip()[:2000].encode()).digest()
    values = [((seed[i % 32] * (i + 1)) % 251) / 251 - 0.5 for i in range(DIMENSION)]
    norm = math.sqrt(sum(v * v for v in values))
    return [v / norm for v in values]


def load(name: str):
    """The module of an MCP server (each server is a server.py in its own folder)."""
    spec = importlib.util.spec_from_file_location(f"{name}_server", SERVERS / f"{name}_server" / "server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def servers():
    modules = {name: load(name) for name in ("claims", "tenders", "postal", "tracking", "rag", "ocr")}

    async def embed(text: str) -> List[float]:
        return fake_embedding(text)
    modules["rag"].embed = embed
    return modules


async def call(server, tool: str, **arguments) -> Dict[str, Any]:
    """Call a tool through the MCP layer; returns its JSON result."""
    result = await server.mcp.call_tool(tool, arguments)
    content = result[0] if isinstance(result, tuple) else result
    return json.loads(content[0].text)


@pytest.fixture(scope="session", autouse=True)
async def documents_embedded():
    """The seeded documents get the stub embedding of their text (data-init does it with the model)."""
    for table in ("claim_documents", "tender_documents", "reclamation_documents", "company_references",
                  "historical_tenders", "company_capabilities", "user_contracts", "knowledge_base",
                  "courrier_knowledge_base"):
        text_column = {"claim_documents": "raw_ocr_text", "tender_documents": "raw_ocr_text",
                       "reclamation_documents": "raw_ocr_text", "company_references": "description",
                       "historical_tenders": "description", "company_capabilities": "description",
                       "user_contracts": "full_text", "knowledge_base": "content",
                       "courrier_knowledge_base": "content"}[table]
        rows = await db.fetch_all(f"SELECT id, {text_column} AS text FROM {table} WHERE COALESCE({text_column}, '') <> ''")
        for row in rows:
            await db.execute(f"UPDATE {table} SET embedding = CAST(:vector AS vector) WHERE id = :id",
                             vector="[" + ",".join(map(str, fake_embedding(row["text"]))) + "]", id=row["id"])


CLAIM_TEXT = """DÉCLARATION DE SINISTRE AUTOMOBILE
Nom : Jean Martin
E-mail : jean.martin@mail.fr
Téléphone : 06 12 34 56 78
Accident sur l'A6, pare-chocs arrière et coffre endommagés.
Montant réclamé : 6 200,00 €"""


@pytest.fixture(scope="session")
async def auto_claims():
    """Two Auto claims of claimants with an active Auto contract, with a document text (as the OCR server
    stores it): the first is the case, the second a precedent decided "deny"."""
    claims = await db.fetch_all("""
        SELECT c.id, c.claim_number FROM claims c
        WHERE c.claim_type = 'Auto' AND EXISTS (SELECT 1 FROM user_contracts u WHERE u.user_id = c.user_id
                                                AND u.is_active AND u.contract_type = 'Auto Insurance')
        ORDER BY c.claim_number LIMIT 2""")
    for claim in claims:
        await db.execute("DELETE FROM claim_documents WHERE claim_id = CAST(:id AS uuid)", id=claim["id"])
        await db.execute("""INSERT INTO claim_documents (claim_id, file_path, raw_ocr_text, embedding)
            VALUES (CAST(:id AS uuid), 'claims/test.pdf', :text, CAST(:vector AS vector))""",
            id=claim["id"], text=CLAIM_TEXT, vector=as_vector(fake_embedding(CLAIM_TEXT)))
    precedent = claims[1]
    await db.execute("UPDATE claims SET status = 'denied' WHERE id = CAST(:id AS uuid)", id=precedent["id"])
    await db.execute("""INSERT INTO claim_decisions (claim_id, initial_decision, initial_confidence, initial_reasoning,
                            decision, confidence, reasoning)
        VALUES (CAST(:id AS uuid), 'deny', 0.8, 'Damage before the contract start', 'deny', 0.8, 'Damage before the contract start')""",
        id=precedent["id"])
    return claims[0]["claim_number"], precedent["claim_number"]
