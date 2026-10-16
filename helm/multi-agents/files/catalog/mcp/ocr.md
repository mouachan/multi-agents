# Document OCR MCP Server

**MCP Server Summary:**
Extracts the text of claim, tender and complaint documents (PDF or images) with the vision model
served by Models-as-a-Service. Documents are read from the OGX Files API by business number, so the
agents never handle file paths.

## Features
- One call per document: `ocr_document(document_id="CLM-2024-0011")`
- PDF pages rendered to images, then read by the vision model (multilingual: French and English)
- Text stored with the document: a document already read is returned at once (`refresh=true` reads it
  again); the text is reused by the payout and the similarity searches
- Claims, tenders and postal complaints
- **Personal data masked** in every result (names, e-mails, phones, addresses; free text through NeMo
  Guardrails): the model only reads placeholders such as `[PERSON]`

## Used by
Claims Processing Agent, Tenders Analysis Agent, Postal Services Agent.
