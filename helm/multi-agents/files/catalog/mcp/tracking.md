# Parcel Tracking MCP Server

**MCP Server Summary:**
Parcel and mail tracking: full timeline of a parcel by tracking number.

## Features
- `get_tracking(numero_suivi)`: chronological events, delivered or not, last event, related complaint
- Read-only
- **Personal data masked** in every result (names, e-mails, phones, addresses; free text through NeMo
  Guardrails): the model only reads placeholders such as `[PERSON]`

## Used by
Postal Services Agent — tracking profile (Logistique profile).
