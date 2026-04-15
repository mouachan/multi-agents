# From Mono-Agent to Multi-Agent: Lessons Learned Building an Enterprise AI Decision Platform on OpenShift AI

*How we evolved a single-purpose insurance claims agent into a production-ready multi-agent platform using LlamaStack, MCP, and Model as a Service*

---

## Introduction

When we started building our first agentic AI proof of concept for a major European insurance company, we had a simple goal: automate insurance claim decisions using an AI agent that could read documents, cross-reference policies, and make approve/deny/manual-review recommendations. What began as a single-agent prototype quickly revealed both the power and the limitations of monolithic agent architectures — and pushed us to rethink our approach entirely.

This post traces our journey from a mono-agent demo to a multi-agent orchestration platform, the technology choices we made along the way, and the hard-won lessons we learned about building enterprise-grade agentic systems on Red Hat OpenShift AI.

## The Starting Point: A Mono-Agent PoC

### The Use Case

Our client processes thousands of insurance claims daily — medical, automotive, property damage. Each claim requires:

1. **Document extraction** — reading handwritten or scanned reports (medical certificates, police reports, invoices)
2. **Policy verification** — checking the claimant's active contracts and coverage limits
3. **Precedent analysis** — finding similar historical claims and their outcomes
4. **Decision making** — recommending approval, denial, or escalation to human review

This is a textbook ReAct (Reasoning + Acting) workflow: the agent needs to *think* about what information it needs, *act* by calling the right tools, *observe* the results, and iterate until it reaches a decision.

### Architecture v1: One Agent, Two Tools

Our first architecture was deliberately simple:

```
User Request → FastAPI Backend → LlamaStack Agent → Decision
                                       │
                          ┌─────────────┼─────────────┐
                          │             │             │
                     OCR Server    RAG Server    (Agent Logic)
                     (EasyOCR)     (pgvector)
```

- **LlamaStack 0.3.5** served as the agentic runtime, providing the Responses API with automatic tool execution
- **Llama 3.3 70B INT8** ran on 4x NVIDIA L40 GPUs for reasoning
- **Gemma 300M** handled embedding generation on a dedicated L40
- **Two MCP servers** exposed domain tools: OCR for document reading, RAG for vector search
- **PostgreSQL + pgvector** stored claims data and 768-dimensional embeddings
- **TrustyAI Guardrails** provided PII detection and content safety

The agent followed a simple ReAct loop: extract the document via OCR, retrieve the user's insurance contracts, find similar historical claims, then synthesize a recommendation with a confidence score and reasoning.

**It worked.** Processing a claim took 10-15 seconds end-to-end. The agent made reasonable decisions. The client was impressed.

But the success of this PoC raised a bigger question: **could we turn this into a reusable platform?**

## Why Mono-Agent Wasn't Enough

### Problem 1: One Application, Multiple Domains

The insurance claims PoC proved that the agentic pattern — ReAct reasoning, MCP tools, RAG-based context retrieval — works for document-driven decision making. But we quickly realized this pattern isn't specific to insurance. Another client needed to analyze construction tenders (appels d'offres) — a completely different industry with different documents, different data sources, and different decision criteria (Go/No-Go instead of Approve/Deny).

The business question became: **can we build a single platform that serves multiple clients across different domains**, rather than rebuilding a bespoke application for each engagement?

The mono-agent's system prompt, tool set, and decision logic were all hardcoded for insurance claims. Supporting a second domain meant either:

- **Cramming everything into one giant prompt** (brittle, confusing for the LLM)
- **Building a second standalone application** (duplicating 90% of the code)
- **Rethinking the architecture** to support multiple specialized agents within one platform

We chose option three.

### Problem 2: GPU Cost and Availability

Running Llama 3.3 70B on 4x L40 GPUs is not cheap. Every PoC, every demo, every development iteration required dedicated GPU hardware. On-cluster GPU provisioning was slow, expensive, and created friction between teams competing for the same hardware. Multiplying this by every new client engagement was clearly not viable.

### Problem 3: OCR Quality

EasyOCR worked for clean PDFs but struggled with handwritten documents, complex layouts, and mixed-language content. We needed something better, but integrating a vision model would mean yet another GPU workload to manage.

### Problem 4: The Mono-Agent Was Not Reusable

The mono-agent codebase had claim-specific logic woven throughout — in the service layer, the prompts, the tool configurations, even the database schema. Adding a new domain for a new client required touching almost every file. If we wanted to serve multiple industries from a single codebase, we needed a fundamentally different approach.

## The Multi-Agent Architecture

### Design Principles

We established three principles for the redesign:

1. **One platform, many domains**: The same application should serve insurance claims, construction tenders, or any future domain — without forking the codebase. Each domain gets its own specialized agent, but the infrastructure, orchestration, and UI patterns are shared.
2. **No GPU on cluster**: All model inference happens via remote Model as a Service endpoints.
3. **Adding a new agent should be trivial**: Define an agent in a registry, write a prompt, configure tools — done.

### Architecture v2: Orchestrated Specialization

```
User Request → Multi-Agent Orchestrator → Intent Classification → Specialized Agent
                                                                        │
                                              ┌─────────────────────────┼───────────────┐
                                              │              │          │               │
                                         OCR Server    RAG Server  Claims Server  Tenders Server
                                        (Qwen2.5-VL)   (pgvector)    (CRUD)         (CRUD)
                                              │              │          │               │
                                              └──────────────┴──────────┴───────────────┘
                                                             │
                                                    LiteMaaS (Model as a Service)
                                                    ├── Llama 4 Scout 17B (reasoning)
                                                    ├── Qwen2.5-VL 7B (vision OCR)
                                                    └── Nomic Embed v1.5 (embeddings)
```

The key components:

**Multi-Agent Orchestrator**: Receives user requests, classifies intent via keyword matching (no LLM call — saves ~10 seconds per request), and routes to the appropriate specialized agent.

**Agent Registry**: A dynamic registry where each agent is defined by its identity, system prompt, tool set, decision values, and routing keywords. Adding a new domain is a single Python class registration.

**BaseAgentService**: A DRY base class that encapsulates the 90% identical pattern across agents — load entity, build context, call LlamaStack, parse decision, save result. Domain-specific services extend this with minimal code.

**Four MCP Servers**: OCR, RAG, Claims CRUD, and Tenders CRUD. Each is a standalone FastMCP service with SSE transport, independently deployable and scalable.

**LlamaStack RHOAI 3.3 (0.4.x)**: Upgraded from 0.3.5, providing the Responses API with automatic parallel tool execution, conversation chaining via `previous_response_id`, and native MCP tool runtime.

### Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS, Vite |
| Backend | Python 3.12, FastAPI |
| AI Orchestration | LlamaStack 0.4.x (RHOAI 3.3) |
| LLM Inference | Llama 4 Scout 17B via LiteMaaS |
| Vision/OCR | Qwen2.5-VL 7B via LiteMaaS |
| Embeddings | Nomic Embed Text v1.5 (768-dim) |
| Database | PostgreSQL 16 + pgvector (HNSW) |
| Document Storage | MinIO (S3-compatible) |
| MCP Servers | FastMCP with SSE transport |
| Deployment | Helm 3.x on OpenShift 4.x |

## The MCP Architecture: Why It Matters

Our MCP (Model Context Protocol) architecture deserves special attention because it solved several problems simultaneously.

### Why MCP Over Direct API Calls?

In the mono-agent version, tools were tightly coupled to the backend. The OCR server was "just a microservice." With MCP, each tool server becomes a **standardized, discoverable, composable** capability that any agent can use without custom integration code.

LlamaStack's native MCP tool runtime means we declare tool servers in configuration:

```yaml
tool_groups:
  - mcp::ocr-server → http://ocr-server:8080/sse
  - mcp::rag-server → http://rag-server:8080/sse
  - mcp::claims-server → http://claims-server:8080/sse
  - mcp::tenders-server → http://tenders-server:8080/sse
```

The agent doesn't know or care how tools are implemented. It sees tool descriptions, decides which to call, and LlamaStack handles execution. This is the real power of MCP: **agents compose tools, they don't integrate with services**.

### Why Custom RAG Over LlamaStack's Built-in Vector IO?

This was a pragmatic decision. LlamaStack's native Vector IO works well for generic document retrieval, but our RAG queries needed **domain-specific SQL JOINs** — joining `claim_documents` with `claims`, or `company_references` with `tenders`. Vector similarity alone wasn't enough; we needed business context alongside semantic search results.

So we kept embedding **generation** on LlamaStack's `/v1/embeddings` API, but embedding **storage and retrieval** stayed in our custom MCP RAG server where we could write proper queries.

### MCP Security Considerations

As highlighted in [Red Hat's recent analysis of MCP security](https://www.redhat.com/en/blog/mcp-security-current-situation), the MCP protocol introduces new attack surfaces — remote code execution, data exfiltration, and privilege escalation are real risks when agents can autonomously call external tools.

In our architecture, we mitigate these risks through:

- **Network isolation**: MCP servers run in the same OpenShift namespace, accessible only via internal service mesh. No external exposure.
- **Tool allowlists**: Each agent declares exactly which MCP tools it can use. The claims agent cannot call tender tools and vice versa.
- **Input validation**: Every MCP tool validates its inputs before executing. Document IDs are resolved via database lookup, not user-supplied paths.
- **Audit trail**: Every tool call is logged with timestamps, inputs, outputs, and the agent that invoked it. Full traceability for compliance.
- **No arbitrary code execution**: Our MCP tools perform specific, bounded operations (OCR a document, query a database, save a decision). There is no `execute_command` or `run_script` tool.

MCP security is not optional for enterprise deployments. The protocol's flexibility is its strength and its risk — and it requires deliberate architectural choices to keep it safe.

## Model as a Service: The Game Changer

The single most impactful decision in our evolution was moving from **on-cluster GPU inference** to **Model as a Service (MaaS)**.

### Before: On-Cluster GPUs

In the mono-agent PoC:

- Llama 3.3 70B required **4x NVIDIA L40 GPUs**
- Gemma 300M embeddings required **1x L40**
- Total: **5 dedicated GPUs** per environment
- GPU provisioning took days, sometimes weeks
- Development was blocked when GPUs were unavailable
- Each team running a PoC needed their own GPU allocation

### After: LiteMaaS

With Model as a Service (via LiteMaaS — a LiteLLM-based proxy to shared vLLM endpoints):

- **Zero GPUs on cluster**. All inference is a remote API call.
- Same API interface as local inference (OpenAI-compatible via vLLM)
- Models are shared across teams and projects
- Switching models is a configuration change, not a hardware migration
- Cost is usage-based, not allocation-based

LlamaStack connects to LiteMaaS through its `remote::vllm` provider:

```yaml
providers:
  inference:
    - provider_type: remote::vllm
      config:
        url: https://litemaas-llm.example.com/v1
        api_token: ${env.LITEMAAS_API_KEY}
```

This completely decoupled our application from GPU infrastructure. The backend, MCP servers, database, and frontend all run on standard CPU nodes. The "AI" part is an API call to a shared, centrally managed model fleet.

### The OCR Breakthrough

MaaS also unlocked a major quality improvement: **vision-model-based OCR**. Instead of EasyOCR (a traditional OCR library running on CPU), we now send document page images to **Qwen2.5-VL 7B** via LiteMaaS. The vision model understands document structure, handles handwriting, reads tables, and produces dramatically better extraction quality — all without adding a single GPU to our cluster.

The OCR MCP server simply:
1. Fetches the PDF from LlamaStack's Files API
2. Converts pages to images
3. Sends images to Qwen2.5-VL via LlamaStack's inference API
4. Returns structured text

No local model loading. No GPU scheduling. Just an API call.

## Lessons Learned

### 1. Start Mono, Design for Multi

Our mono-agent PoC was essential for understanding the problem space, proving the ReAct pattern works for document-driven decisions, and building client confidence. But we designed the multi-agent version from scratch rather than patching the mono-agent. The investment in `BaseAgentService`, the agent registry, and the MCP-based tool architecture paid for itself immediately: when a second client needed tender analysis — a completely different industry — we onboarded their domain without touching the core platform code.

**Lesson**: Build the prototype to learn, then rebuild to scale. A PoC that works for one client is valuable; a platform that works across domains is transformative.

### 2. MCP Is Powerful but Demands Discipline

MCP makes it trivially easy to add tools. That's also its danger. Every tool you expose is an action an agent can take autonomously. We learned to:

- Keep tools **specific and bounded** (no generic "query anything" tools)
- **Validate all inputs** at the tool level, not just the agent level
- **Allowlist tools per agent** rather than giving every agent access to everything
- **Log everything** — when an agent makes a bad decision, you need to trace which tool returned what

### 3. Model as a Service Is Not Just Cost Optimization

We initially adopted MaaS to save on GPU costs. But the real benefits were:

- **Development velocity**: No waiting for GPU provisioning. `docker compose up` and you're running.
- **Model flexibility**: We switched from Mistral-Small-24B to Llama 4 Scout 17B in a single config change. No redeployment.
- **Multi-namespace deployment**: Each client gets an isolated instance on the same cluster, all sharing the same model endpoints. Data isolation with infrastructure efficiency.
- **Separation of concerns**: The infrastructure team manages models; the application team builds agents. Clean boundary.

### 4. Intent Classification Doesn't Need an LLM

Our first multi-agent orchestrator used an LLM call to classify user intent. It added ~10 seconds of latency and was wrong 15% of the time. We replaced it with simple keyword matching against the agent registry's routing keywords. It's instant, deterministic, and correct 95% of the time. For the remaining 5%, the agent gracefully falls back to a general conversation mode.

**Lesson**: Not every decision needs AI. Use the simplest tool that works.

### 5. RAG Needs Business Context, Not Just Vectors

Pure vector similarity search returns semantically similar documents, but for enterprise decision-making, you need **business context** alongside similarity scores. "This claim is similar to claim X" is useful; "This claim is similar to claim X, which was denied because the policy excluded flood damage, and the claimant had a 3-year history of late payments" is actionable.

This is why our RAG MCP server does SQL JOINs alongside vector search — combining semantic similarity with structured business data.

### 6. Streaming Changes the UX Game

In the mono-agent version, users clicked "Process" and waited 15 seconds for a result. In the multi-agent version, we stream everything via SSE: which agent was selected, which tools are being called, what each tool returned, and the agent's reasoning as it generates. Users can see the agent "thinking" in real time. This transformed perceived performance even though actual processing time is similar.

### 7. LlamaStack's Responses API Is the Right Abstraction

We initially considered building our own tool execution loop (call LLM → parse tool calls → execute → feed results back → repeat). LlamaStack's Responses API handles all of this automatically, including parallel tool execution, conversation chaining, and retry logic. It let us focus on business logic rather than agent plumbing.

The upgrade from LlamaStack 0.3.5 to 0.4.x (RHOAI 3.3) brought breaking changes (config key naming, provider URLs, embedding model ID formats), but the API abstraction meant our application code barely changed.

### 8. Guardrails Are Table Stakes, Not Features

PII detection, content safety, and audit logging aren't optional for enterprise deployments. We integrated TrustyAI guardrails from day one — detecting emails, phone numbers, dates of birth, and license plates in agent outputs. These are logged but non-blocking; we don't want guardrails to prevent a legitimate claim from being processed. The key is **observability**: know what PII flows through your system, even if you choose not to block it.

## What's Next

Our platform now serves two distinct clients across two industries (insurance claims processing and construction tender analysis) from a single codebase, with a clear path to adding more. The agent registry pattern means onboarding a new domain requires:

1. A system prompt
2. A set of MCP tools (often reusing existing ones)
3. A registry entry with routing keywords
4. A database schema for domain entities

No new containers, no new infrastructure, no new GPU allocations.

We're currently exploring:

- **Inter-agent collaboration**: Today, agents are independent. We want agent A to be able to ask agent B for input.
- **Dynamic tool discovery**: Instead of static allowlists, agents could discover available tools at runtime based on the task.
- **Feedback loops**: Using human review decisions to improve agent accuracy over time.

## Conclusion

The journey from a mono-agent PoC to a multi-agent platform taught us that **the hard part of enterprise AI isn't the model — it's the architecture around it**. MCP gives agents composable tools. LlamaStack provides the agentic runtime. Model as a Service decouples applications from hardware. OpenShift AI ties it all together with enterprise-grade deployment and operations.

But none of these technologies matter without deliberate architectural choices: separating concerns, validating tool inputs, logging everything, and designing for extensibility from the start.

The mono-agent proved the concept. The multi-agent architecture made it real.

---

*This post is part of a series on building enterprise agentic AI systems on Red Hat OpenShift AI. The projects discussed are open source and available for reference.*
