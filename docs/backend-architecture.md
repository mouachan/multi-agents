# Backend Architecture

## Multi-Agents Platform — Backend Technical Documentation

## Overview

The backend follows a **3-layer pattern**: FastAPI API → Business Services → ResponsesOrchestrator → LlamaStack. The React frontend never touches services directly — all calls go through HTTP REST to `/api/v1/...` (via nginx reverse proxy in production).

LlamaStack handles all the ReAct logic and MCP tool execution itself. The Python backend is an intelligent passthrough that routes, builds context, and parses responses, but **never loops on tool calls**.

## The Two Processing Paths

### 1. Chat (primary path, active)

```
Frontend
  → POST /api/v1/orchestrator/chat/stream
    → orchestrator.py (HTTP validation)
      → OrchestratorService (routing, session, post-processing)
        → ResponsesOrchestrator (LlamaStack HTTP client)
          → LlamaStack Responses API (ReAct + MCP tools)
```

This is the **only path used today** for processing. The user writes a message in the chat, the orchestrator identifies the target agent, and LlamaStack executes the complete workflow (OCR, RAG, decision).

### 2. Process Button (direct path, hidden)

```
Frontend
  → POST /api/v1/claims/{id}/process
    → claims.py (HTTP validation)
      → ClaimService.process_entity() (structured context, decision parsing)
        → ResponsesOrchestrator (same LlamaStack HTTP client)
          → LlamaStack Responses API (ReAct + MCP tools)
```

This path still exists in the code but the button is hidden on the frontend side. It is more structured than the chat: the service retrieves the entity from the DB, builds a formatted context via `ContextBuilder`, and parses the response into a JSON decision via `ResponseParser`. The chat path is more conversational — the LLM decides what to do with the free-form message.

Both paths end up at the same `ResponsesOrchestrator.process_with_agent()` and the same MCP servers.

### 3. Display APIs (claims and tenders)

The REST endpoints `GET /claims`, `GET /claims/{id}`, `GET /claims/{id}/status` (and their tenders equivalents) serve the frontend for list and detail pages. The API layer only does Pydantic validation and delegation — zero business logic.

## Chat Flow in Detail

### Step 1 — API Entry Point

Thin FastAPI routing layer (`api/orchestrator.py`). Two main endpoints:

- `POST /chat` → calls `orchestrator_service.process_message()` (complete response)
- `POST /chat/stream` → calls `process_message_stream()` and wraps the result in SSE

The API instantiates an `OrchestratorService()` singleton at startup and delegates everything to it.

### Step 2 — Intent Classification

The orchestrator **does not make an LLM call for routing**. It uses fast keyword matching: it iterates over all agents registered in `AgentRegistry`, each having `routing_keywords`.

- If a keyword matches → the `agent_id` is resolved
- If no match but session has an existing agent → intent `follow_up`

### Step 3 — Agent Resolution

At startup (`main.py → register_agents()`), each agent is registered as an `AgentDefinition` containing: `instructions` (system prompt), `tools` (MCP tool names), `routing_keywords`, and `service_class`. The orchestrator calls `AgentRegistry.get(agent_id)` to retrieve the definition.

### Step 4 — LlamaStack Call

This is the heart of the system. The flow in `ResponsesOrchestrator.process_with_agent()`:

**a) MCP tool construction** — Tool names (e.g., `ocr_document`) are mapped to their servers via `DEFAULT_TOOL_TO_SERVER`. Tools are grouped by server, each server producing a block `type: "mcp", server_url, allowed_tools`.

**b) Single HTTP call** — One `POST` to `{llamastack}/v1/responses` with `model`, `input`, `instructions`, `tools`, `previous_response_id`.

**c) LlamaStack handles all the ReAct** — It calls the LLM, the LLM decides which tools to call, LlamaStack executes the MCP tools via SSE, retrieves the results, reinjects them into the LLM, and returns the complete final response.

**d) Response parsing** — The result contains an `output` array with `message` items (LLM text) and `mcp_call` items (tool results). The code returns `{output, tool_calls, response_id, usage}`.

### Step 5 — Multi-turn Chaining

LlamaStack manages conversational context server-side via the `response_id`. On each response, the orchestrator stores the `response_id` in the session metadata. On the next message, it passes it as `previous_response_id` — no need to send the full history. If the user switches agents, it is reset to `None`.

### Step 6 — Post-processing

- **Automatic retry** — If the LLM wrote tool calls as text instead of function calling, the call is re-triggered
- **Cleanup** — `ConversationHelper.clean_response_for_chat()`
- **PII redaction** — `redact_text_pii()` detects and masks emails, phone numbers, etc.
- **Suggested actions** — Contextual post-response actions (e.g., after a "Go" tender → suggest creating a claim)
- **Persistence** — Assistant message saved to DB with `tool_calls`, `token_usage`, `model_id`

### Step 7 — SSE Streaming Flow

`process_message_stream` follows the same logic but emits typed events in real-time:

- `agent_resolved` → the frontend displays the agent badge
- `tool_call` → "tool in progress" animation
- `tool_result` → completed/error status
- `text_delta` → incremental LLM text
- `done` → final summary with complete tool_calls and usage

## Modular Architecture: The 4 Generic Building Blocks

The backend separates what is common to all agents from what is specific to each domain via 4 reusable components.

### ResponsesOrchestrator — The LlamaStack Client

It knows how to send a message + MCP tools to LlamaStack and retrieve the response (sync or streaming). It knows nothing about claims or tenders — **100% generic**. It handles the tool name → MCP server mapping via `DEFAULT_TOOL_TO_SERVER` and conversational chaining via `previous_response_id`.

### ContextBuilder — The Context Formatter

It takes an `entity_type`, an `entity_id`, `entity_data` (dict), and an optional `additional_context`, and builds a structured markdown text for the LLM. Zero business knowledge — it formats what it is given.

### ResponseParser — The Decision Extractor

It takes raw LLM text and extracts a structured JSON with `recommendation`, `confidence`, `reasoning`. Three strategies in order of reliability: JSON code block, raw JSON containing "recommendation", then regex fallback.

### BaseAgentService — The Processing Template

Abstract class that encodes the standard workflow. Its `process_entity()` method orchestrates the complete flow.

The generic building blocks are injected in the constructor, and the ~10 abstract methods define the "holes" that each domain must fill.

## Concrete Example: ClaimService

As a subclass of `BaseAgentService`, it only provides:

- `get_entity_type()` → `"claim"`
- `get_instructions()` → the claims system prompt from `prompts.py`
- `get_tools()` → `CLAIM_TOOLS` (list of MCP tool names)
- `get_entity_by_id()` → `SELECT` on the claims table
- `build_entity_context()` → dict with `claim_number`, `user_id`, `claim_type`, + OCR
- `map_recommendation_to_status()` → `approve→completed`, `deny→denied`, otherwise `manual_review`

Everything else (LlamaStack call, parsing, formatting) is inherited.

## The Registry (AgentRegistry)

At startup, `main.py` registers each agent with an `AgentDefinition`:

```python
AgentRegistry.register(AgentDefinition(
    id="claims",
    name="Insurance Claims Processing",
    instructions=CLAIMS_PROCESSING_AGENT_INSTRUCTIONS,
    tools=CLAIM_TOOLS,
    routing_keywords=["claim", "sinistre", "CLM-", ...],
    service_class=ClaimService,
))
```

The `OrchestratorService` has **no hardcoded knowledge of agents** — the registry is the single source of truth.

## Adding a New Agent: "HR" Example

The modular architecture allows adding an agent by assembly without touching the orchestrator or the generic building blocks. For an HR agent that analyzes job applications:

1. **Prompt** — Create `llamastack/rh_prompts.py` with instructions and message template.

2. **ORM Model** — Create `models/candidature.py` (SQLAlchemy table, columns, status enums) + SQL migration.

3. **Service** — Create `services/candidature_service.py` extending `BaseAgentService` and implementing the ~10 abstract methods.

4. **API + Schemas** — Create `api/rh.py` (REST endpoints: `GET /candidatures`, `GET /candidatures/{id}`, etc.) + `api/rh_schemas.py` (Pydantic validation).

5. **MCP Server (if needed)** — Create `mcp_servers/rh_server/` with tools like `get_candidature`, `save_rh_decision`. Existing tools (OCR, RAG) are reusable.

6. **Registration** — In `main.py`:

```python
AgentRegistry.register(AgentDefinition(
    id="rh",
    name="Application Analysis",
    tools=["ocr_document", "get_candidature", "save_rh_decision"],
    instructions=RH_AGENT_INSTRUCTIONS,
    routing_keywords=["candidature", "cv", "recrutement", "rh"],
    service_class=CandidatureService,
))
app.include_router(rh_router, prefix="/api/v1/candidatures", tags=["rh"])
```

7. **Tool mapping** — Add entries in `DEFAULT_TOOL_TO_SERVER` if using a new MCP server.

8. **DB migration** — SQL to create the candidatures tables.

The `OrchestratorService` will automatically route messages containing "candidature" or "cv" to the new agent, use its tools and prompt, without a single line of the orchestrator being modified.

## Summary: Responsibilities

| Component | Role |
|---|---|
| **FastAPI API** | HTTP validation, routing, SSE wrapping |
| **OrchestratorService** | Intent classification, agent resolution, session management, post-processing |
| **ResponsesOrchestrator** | Generic LlamaStack HTTP client (sync + streaming) |
| **BaseAgentService** | Abstract processing template (context → LLM → decision) |
| **ClaimService / TenderService** | Domain-specific implementations (entity retrieval, context building, status mapping) |
| **ContextBuilder** | Generic entity → markdown formatter |
| **ResponseParser** | Generic LLM text → structured JSON extractor |
| **AgentRegistry** | Agent definitions registry (single source of truth) |
| **LlamaStack** | ReAct engine, MCP tool execution, conversational memory |
| **MCP Servers** | Domain tools (OCR, RAG, claims CRUD, tenders CRUD) |

All business knowledge is isolated in specialized services (`ClaimService`, `TenderService`), prompts, and MCP servers. This decoupling means adding an agent is **assembly — not rewriting**.
