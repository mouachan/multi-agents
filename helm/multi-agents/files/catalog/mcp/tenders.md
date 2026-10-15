# Tenders Records MCP Server

**MCP Server Summary:**
Access to the BTP tenders (appels d'offres): list, details (title, budget, region, contracting
authority), documents with OCR text, statistics, and the recording of the Go / No-Go decision.

## Features
- Tender details with the previous AI analysis: risks, similar references, history (`get_tender`)
- One-call context for an evaluation (`analyze_tender`)
- `save_tender_decision`: go / no_go / a_approfondir, status update and embedding of the tender for
  future similarity searches

## Used by
Tenders Analysis Agent (BTP profile).
