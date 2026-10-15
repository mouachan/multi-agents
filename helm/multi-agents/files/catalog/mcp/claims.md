# Claims Records MCP Server

**MCP Server Summary:**
Access to the insurance claims: list, details, documents and statistics, the payout computation and
the recording of the agent's decision.

## Features
- Claim details with the claimant and the previous AI decision (`get_claim`)
- Documents with their OCR text (`get_claim_documents`)
- **`compute_payout`:** deterministic payout — claim type, active contract of the matching type,
  franchise and coverage ceiling, amount claimed in the document — computed by generated Python run
  in the **OpenShell sandbox** (no network, read-only system). Returns the figures, the code and the
  sandbox run, shown in the traceability panel of the application.
- `save_claim_decision`: approve / deny / manual_review, status update and embedding of the case for
  future similarity searches

## Used by
Claims Processing Agent (Finance profile).
