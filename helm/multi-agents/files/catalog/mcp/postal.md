# Postal Complaints Records MCP Server

**MCP Server Summary:**
Access to the postal complaints (réclamations): list, details with the customer and the latest
tracking events, documents with OCR text, statistics, and the recording of the decision.

## Features
- Complaint details with the tracking timeline of the parcel (`get_reclamation`, `analyze_reclamation`)
- `save_reclamation_decision`: rembourser / reexpedier / rejeter / escalader, status update and
  embedding of the case for future similarity searches

## Used by
Postal Services Agent (Logistique profile).
