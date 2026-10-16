# Postal Complaints Records MCP Server

**MCP Server Summary:**
Access to the postal complaints (réclamations): list, details with the customer and the latest
tracking events, documents with OCR text, statistics, and the recording of the decision.

## Features
- Complaint details with the latest tracking events of the parcel (`get_reclamation`)
- Documents with their OCR text (`get_reclamation_documents`), statistics (`get_reclamation_statistics`)
- Read-only: decisions are saved by the platform (agent processing, then human review)
- **Personal data masked** in every result (names, e-mails, phones, addresses; free text through NeMo
  Guardrails): the model only reads placeholders such as `[PERSON]`

## Used by
Postal Services Agent (Logistique profile).
