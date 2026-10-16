# Claims Records MCP Server

**MCP Server Summary:**
Access to the insurance claims: list, details, documents and statistics, and the payout computation.
Decisions are not written here: the platform saves them (agent processing, then human review).

## Features
- Claim details with the claimant and the current decision (`get_claim`)
- Documents with their OCR text (`get_claim_documents`)
- **`compute_payout`:** deterministic payout — claim type, active contract of the matching type,
  franchise and coverage ceiling, amount claimed in the document — computed by generated Python run
  in the **OpenShell sandbox** (no network, read-only system). Returns the figures, the code and the
  sandbox run, shown in the traceability panel of the application.
- **Personal data masked** in every result (names, e-mails, phones, addresses; free text through NeMo
  Guardrails): the model only reads placeholders such as `[PERSON]`

## Used by
Claims Processing Agent (Finance profile).
