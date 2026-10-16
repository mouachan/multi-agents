# Tenders Records MCP Server

**MCP Server Summary:**
Access to the BTP tenders (appels d'offres): list, details (title, budget, region, contracting
authority), documents with OCR text, statistics, and the recording of the Go / No-Go decision.

## Features
- Tender details (title, client, budget, region, lots, award criteria) and current decision (`get_tender`)
- Documents with their OCR text (`get_tender_documents`), statistics (`get_tender_statistics`)
- Read-only: decisions are saved by the platform (agent processing, then human review)

## Used by
Tenders Analysis Agent (BTP profile).
