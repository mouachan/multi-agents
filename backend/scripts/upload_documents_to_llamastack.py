"""
Upload documents to LlamaStack Files API using claim/tender number as filename.

For each claim/tender in the database, uploads its PDF to LlamaStack.
LlamaStack generates its own file_id, which is stored back in claims/tenders
document_path field so it can be retrieved later.

Usage:
    python upload_documents_to_llamastack.py

Environment variables:
    LLAMASTACK_ENDPOINT  - LlamaStack URL (default: http://llamastack:8321)
    DOCUMENTS_DIR        - Path to documents directory (default: /documents)
    POSTGRES_HOST        - PostgreSQL host (default: postgresql)
    POSTGRES_PORT        - PostgreSQL port (default: 5432)
    POSTGRES_DATABASE    - Database name (default: claims_db)
    POSTGRES_USER        - Database user (default: claims_user)
    POSTGRES_PASSWORD    - Database password (default: claims_pass)
"""

import os
import sys
import time
import httpx
import psycopg2
from pathlib import Path

LLAMASTACK = os.getenv("LLAMASTACK_ENDPOINT", "http://llamastack:8321")
DOCUMENTS_DIR = Path(os.getenv("DOCUMENTS_DIR", "/documents"))

PG_HOST = os.getenv("POSTGRES_HOST", "postgresql")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_DB = os.getenv("POSTGRES_DATABASE", "claims_db")
PG_USER = os.getenv("POSTGRES_USER", "claims_user")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "claims_pass")

MAX_RETRIES = 30
RETRY_DELAY = 5


def wait_for_llamastack():
    """Wait until LlamaStack /v1/health returns 200."""
    url = f"{LLAMASTACK}/v1/health"
    for i in range(MAX_RETRIES):
        try:
            resp = httpx.get(url, timeout=5)
            if resp.status_code == 200:
                print(f"LlamaStack ready at {LLAMASTACK}")
                return True
        except Exception:
            pass
        print(f"Waiting for LlamaStack... ({i+1}/{MAX_RETRIES})")
        time.sleep(RETRY_DELAY)
    print("ERROR: LlamaStack not reachable")
    return False


def wait_for_postgres():
    """Wait until PostgreSQL accepts connections."""
    for i in range(MAX_RETRIES):
        try:
            conn = psycopg2.connect(
                host=PG_HOST, port=PG_PORT, dbname=PG_DB,
                user=PG_USER, password=PG_PASS
            )
            conn.close()
            print(f"PostgreSQL ready at {PG_HOST}:{PG_PORT}")
            return True
        except Exception:
            pass
        print(f"Waiting for PostgreSQL... ({i+1}/{MAX_RETRIES})")
        time.sleep(RETRY_DELAY)
    print("ERROR: PostgreSQL not reachable")
    return False


def upload_file(client: httpx.Client, filepath: Path, entity_number: str) -> str | None:
    """Upload a file to LlamaStack Files API. Returns the generated file_id or None."""
    url = f"{LLAMASTACK}/v1/files"
    try:
        with open(filepath, "rb") as f:
            resp = client.post(
                url,
                files={"file": (f"{entity_number}.pdf", f, "application/pdf")},
                data={"purpose": "assistants"},
            )
        if resp.status_code == 200:
            result = resp.json()
            file_id = result.get("id")
            print(f"  {entity_number} <- {filepath.name} -> {file_id}")
            return file_id
        else:
            print(f"  FAILED {entity_number}: HTTP {resp.status_code} {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"  ERROR {entity_number}: {e}")
        return None


def main():
    print("=" * 60)
    print("Upload documents to LlamaStack Files API")
    print(f"LlamaStack: {LLAMASTACK}")
    print(f"Documents:  {DOCUMENTS_DIR}")
    print(f"Database:   {PG_HOST}:{PG_PORT}/{PG_DB}")
    print("=" * 60)

    if not wait_for_llamastack():
        sys.exit(1)
    if not wait_for_postgres():
        sys.exit(1)

    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB,
        user=PG_USER, password=PG_PASS
    )
    cur = conn.cursor()

    # Get claims: claim_number -> document_path (e.g. "claims/claim_auto_001.pdf")
    cur.execute("""
        SELECT claim_number, document_path FROM claims
        WHERE document_path IS NOT NULL AND document_path NOT LIKE 'file-%%'
    """)
    claims = cur.fetchall()

    # Get tenders: tender_number -> document_path
    cur.execute("""
        SELECT tender_number, document_path FROM tenders
        WHERE document_path IS NOT NULL AND document_path NOT LIKE 'file-%%'
    """)
    tenders = cur.fetchall()

    print(f"\nFound {len(claims)} claims and {len(tenders)} tenders to upload")

    if not claims and not tenders:
        print("Nothing to upload (already done?)")
        cur.close()
        conn.close()
        return

    uploaded = 0
    skipped = 0
    failed = 0

    with httpx.Client(timeout=60) as client:
        # Upload claim documents
        print("\n--- Claims ---")
        for claim_number, doc_path in claims:
            filepath = DOCUMENTS_DIR / doc_path
            if not filepath.exists():
                print(f"  SKIP {claim_number}: file not found ({doc_path})")
                skipped += 1
                continue
            file_id = upload_file(client, filepath, claim_number)
            if file_id:
                cur.execute(
                    "UPDATE claims SET document_path = %s WHERE claim_number = %s",
                    (file_id, claim_number),
                )
                uploaded += 1
            else:
                failed += 1

        # Upload tender documents
        print("\n--- Tenders ---")
        for tender_number, doc_path in tenders:
            filepath = DOCUMENTS_DIR / doc_path
            if not filepath.exists():
                print(f"  SKIP {tender_number}: file not found ({doc_path})")
                skipped += 1
                continue
            file_id = upload_file(client, filepath, tender_number)
            if file_id:
                cur.execute(
                    "UPDATE tenders SET document_path = %s WHERE tender_number = %s",
                    (file_id, tender_number),
                )
                uploaded += 1
            else:
                failed += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"\nResult: {uploaded} uploaded, {skipped} skipped, {failed} failed")
    print("Done.")


if __name__ == "__main__":
    main()
