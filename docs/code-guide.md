# Code guide

Where the code is, the few conventions it follows, and how to make the usual changes. How the parts
work together is in [architecture.md](architecture.md).

## Repository

```
backend/
  app/
    domains/        the business domains: one file each (claims.py, tenders.py, postal.py) + spec.py
    agents.py       the agent profiles (prompt, names, routing keywords) and their A2A URLs
    api/            HTTP routes: domains.py (generated per domain), review.py, chat.py, admin.py...
    services/       what the routes do: processing, decisions, review, cases, chat/, evaluation,
                    maas_keys (the users' MaaS keys), access_profiles, demo_reset...
    models/         SQLAlchemy tables (case.py holds the columns every domain shares)
    core/           settings, database, authentication, tracing, prompt files
  mcp_servers/
    shared/         what every MCP server uses: @tool, cases.py, personal_data.py, injection.py, db.py, server.py
    <name>_server/  one server each: server.py + Containerfile (+ requirements.txt for extras)
  tests/            backend tests (real PostgreSQL in podman compose)
agents/
  shared/           the A2A agent: executor.py (request → answer), decision.py, streaming.py...
  <domain>-agent/   agent.py: the profiles (prompt + tools) and the skills of the agent card
  tests/            agent unit tests
frontend/src/
  domains/          the business domains as the UI shows them: one file each + types.ts
  pages/            CaseListPage, CaseDetailPage, ReviewInboxPage, ChatPage, AdminPage...
  components/       review/ (review panel), business/ (evidence, steps, tracking...), ui/, chat/
  services/api.ts   the typed API client (casesApi(domain), reviewApi, chatApi, adminApi)
helm/multi-agents/
  files/prompts/    agents/ (system prompts, versioned in MLflow), backend/ (processing requests, chat settings)
  files/catalog/    OpenShift AI catalog entries: tool lists, READMEs
  templates/        one folder per component
guardrails/
  gliner-server/    finds people's names for NeMo Guardrails (GLiNER), with its tests
data-init/          the job that prepares the data at installation
database/           schema, seed, precedent decisions
documents/          the sample PDFs, French with their English translation (_en), and generators/
```

## Conventions

* **Declare, don't duplicate.** What differs between domains is declared once (`DomainSpec` in
  `backend/app/domains/`, `DomainUI` in `frontend/src/domains/`, `CaseTable` in
  `backend/mcp_servers/shared/cases.py`); routes, pages and tools are shared.
* **Prompts are files**, not strings in the code: `helm/multi-agents/files/prompts/`.
* **The backend owns the decisions.** Agents and tools never write a decision; the backend saves the
  agent's decision after a processing and the reviewer's decision after a review.
* **A tool returns a dict** and is declared with `@tool(mcp)`: JSON, errors, timing, personal-data
  masking and the removal of instructions aimed at the AI are done by the decorator
  (`backend/mcp_servers/shared/tools.py`).
* **Comments say why**, the names say what. Module docstrings explain the flow of the module.
* **Tests use the real database** (PostgreSQL with the same schema and seed); only the models and the
  agents are replaced by stubs.

## Common changes

### Change what an agent does

Edit its prompt in `helm/multi-agents/files/prompts/agents/` (claims: `claims-processing-agent.txt`,
tenders: `ao-processing-agent.txt`, postal: `courrier-*-instructions.txt`). A `helm upgrade` versions
it in MLflow and moves the `production` alias; to try a version first, register it in the MLflow UI
and move the alias there.

### Change the tools of a processing

`processing_tools` in `backend/app/domains/<domain>.py`: the agent calls them in this order (the OCR
before the precedent search, which reads the OCR text). A tool must also be in the agent's profile
(`agents/<domain>-agent/agent.py`) and granted to the agent (`auth.agentTools` in `values.yaml`).

### Change the decision rules

`statuses_by_decision` (status after each decision), `review_decision` (the one that hands the case
to a person) and `human_decisions` (what a reviewer can choose) in `backend/app/domains/<domain>.py`.

### Add a fact to the review panel

`evidence()` in `backend/app/domains/<domain>.py` reads the tool results of the processing and
returns sections of facts and items (`section`, `fact`, `item` from `spec.py`). The label of a fact is
the translation `review.facts.<key>` in `frontend/src/i18n/translations.ts`.

### Add a column to a case list

`columns` in `frontend/src/domains/<domain>.tsx`. Domain-specific blocks of the case page go in
`hero` (header) or `Extras` (cards).

### Add an MCP tool

In the server's `server.py`:

```python
@tool(mcp)
async def get_claim_history(claim_id: str) -> Dict[str, Any]:
    """
    Get the past decisions of a claim, the most recent first.

    Args:
        claim_id: The claim number (e.g. CLM-2024-0001)
    """
    claim = await find_case(CLAIMS, claim_id)              # ToolError "Claim ... not found" if unknown
    return {"decisions": await fetch_all("SELECT ... WHERE claim_id = CAST(:id AS uuid)", id=claim["id"])}
```

The docstring is what the model reads to choose the tool: say what it returns and give an example of
each argument. Then add the tool to the agent profile (`agents/<domain>-agent/agent.py`), to
`SERVER_TOOLS` in `agents/shared/ogx_client.py` and `frontend/src/lib/agents.ts`, to
`auth.agentTools` in `values.yaml`, and to the catalog list `files/catalog/mcp-tools.yaml`. A new
field holding personal data goes in `PERSONAL_FIELDS` or `FREE_TEXT_FIELDS` of
`shared/personal_data.py`.

### Add a domain

1. **Database**: the tables in `database/init.sql` (case, documents, decisions, with the columns of
   `backend/app/models/case.py`) and demo records in the seed.
2. **Backend**: the models (`backend/app/models/<domain>.py`, with the `CaseColumns`,
   `DocumentColumns`, `DecisionColumns` mixins), the `DomainSpec` (`backend/app/domains/<domain>.py`)
   registered in `DOMAINS`, the agent profile in `backend/app/agents.py`, the processing request
   `files/prompts/backend/<domain>-processing-message.txt`, the agent URL setting in
   `backend/app/core/config.py`.
3. **MCP**: a `CaseTable` in `backend/mcp_servers/shared/cases.py` and a server exposing its tools.
4. **Agent**: `agents/<domain>-agent/agent.py` (profiles and skills) and its system prompt in
   `files/prompts/agents/`.
5. **Frontend**: the `Domain` type (`src/types/case.ts`), a `DomainUI` (`src/domains/<domain>.tsx`)
   registered in `DOMAINS`, and its translations.
6. **Helm**: the agent and the MCP server in `values.yaml`, an access profile, the tools in
   `auth.agentTools`.
7. **Tests**: the backend tests run for every registered domain (`domain` fixture); add the domain's
   case to the MCP server tests.

## Tests

From the repository root, everything in containers:

```bash
# backend: API, processing, review, chat, access, demo reset (PostgreSQL + seed, agents stubbed)
podman compose -f backend/tests/compose.yaml up --build --abort-on-container-exit --exit-code-from tests
podman compose -f backend/tests/compose.yaml down -v

# MCP servers: every tool through the MCP layer (PostgreSQL + seed, embedding model stubbed)
podman compose -f backend/mcp_servers/tests/compose.yaml up --build --abort-on-container-exit --exit-code-from tests
podman compose -f backend/mcp_servers/tests/compose.yaml down -v

# agents: decision block, streaming with the output rails
podman run --rm -v ./agents:/src:ro,Z -w /src registry.access.redhat.com/ubi9/python-312 \
  bash -c "pip install -q -r shared/requirements.txt pytest pytest-asyncio && python -m pytest -q tests -p no:cacheprovider"

# GLiNER server: text handling (chunks, overlaps)
podman run --rm -v ./guardrails/gliner-server:/src:ro,Z -w /src registry.access.redhat.com/ubi9/python-312 \
  bash -c "pip install -q fastapi pytest && python -m pytest -q -p no:cacheprovider test_server.py"

# frontend: types, lint, build
podman run --rm -v ./frontend:/app:Z -w /app docker.io/library/node:22-alpine \
  sh -c "npm ci && npx tsc --noEmit && npx eslint src --ext .ts,.tsx && npx vite build"
```

The demo itself is validated on the cluster by the business results: a processed case must have
every tool step completed, precedents found by the similarity searches, and a decision with its
reasoning (and a brief when it goes to a reviewer).
