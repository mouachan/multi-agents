# Knowledge & Similarity Search MCP Server

**MCP Server Summary:**
Retrieval-augmented generation over PostgreSQL + pgvector: the claimant's contracts, past decisions
of similar cases (precedents), company references and capabilities, and the knowledge bases of each
business domain. Embeddings are computed through the OGX `/v1/embeddings` API.

## Features
- **Insurance:** active contracts of a claimant (`retrieve_user_info`), similar past claims with their
  decision (`retrieve_similar_claims`), policy knowledge base (`search_knowledge_base`)
- **BTP:** similar project references, won/lost tender history, internal capabilities and certifications
- **Postal:** postal knowledge base (rates, delays, customs, refunds), similar past complaints
- Business filters on top of the vector search (claim type, region, budget, validity dates...)
- A case number (CLM-..., AO-..., RECL-...) is accepted instead of a text: the search uses the case's
  document, and leaves the case itself out of the results
- **Personal data masked** in every result (names, e-mails, phones, addresses; free text through NeMo
  Guardrails): the model only reads placeholders such as `[PERSON]`

## Used by
Claims Processing Agent, Tenders Analysis Agent, Postal Services Agent.
