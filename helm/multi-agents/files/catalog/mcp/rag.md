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
- `generate_document_embedding` indexes a processed document for the next similarity searches

## Used by
Claims Processing Agent, Tenders Analysis Agent, Postal Services Agent.
