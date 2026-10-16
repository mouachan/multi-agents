"""Decisions of the 10 claims, 10 tenders and 10 reclamations processed at installation.

Loaded from database/seed_data/precedent_decisions.json (PRECEDENTS_FILE), the single source
shared with the backend admin reset, which restores these precedents after reloading the seed.
The file is mounted from the init-postgres ConfigMap (Helm) or ./database/seed_data (compose).
"""
import json
import os

PRECEDENTS_FILE = os.getenv("PRECEDENTS_FILE", "/seed/precedent_decisions.json")

with open(PRECEDENTS_FILE, encoding="utf-8") as f:
    _data = json.load(f)

CLAIM_DECISIONS = _data["claims"]
TENDER_DECISIONS = _data["tenders"]
RECLAMATION_DECISIONS = _data["reclamations"]
