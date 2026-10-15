# Parcel Tracking MCP Server

**MCP Server Summary:**
Parcel and mail tracking: full timeline of a parcel by tracking number, or every parcel of a
customer by email with its latest status.

## Features
- `get_tracking(numero_suivi)`: chronological events, delivered or not, last event, related complaint
- `search_tracking(client_email)`: the customer's parcels and their latest status
- Read-only

## Used by
Postal Services Agent — tracking profile (Logistique profile).
