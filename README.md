# Agentic Multi-Domain Decision Platform

> **Status: Work in Progress** — This platform is under active development. The multi-agent orchestration layer, chat interface, and inter-agent routing are being built and refined. Core single-agent workflows (claims, tenders) are functional.

An intelligent multi-agent decision platform powered by AI agents on Red Hat OpenShift AI, demonstrating autonomous decision-making through **ReAct (Reasoning + Acting)** workflows with built-in compliance guardrails. The platform supports **multiple business domains** with a shared agent infrastructure and a **multi-agent orchestrator** that dynamically routes user requests to specialized domain agents:

- **Insurance Claims Processing** — Approve/Deny/Manual Review decisions
- **Tender Management (Appels d'Offres)** — Go/No-Go decisions for construction (BTP) tenders
- **Multi-Agent Orchestrator** — Intent-based routing, chat sessions, and cross-domain agent chaining

## Table of Contents

- [Business Overview](#business-overview)
  - [Use Case 1: Insurance Claims](#use-case-1-insurance-claims-processing)
  - [Use Case 2: Tender Management](#use-case-2-tender-management-appels-doffres)
  - [Multi-Agent Orchestrator](#multi-agent-orchestrator-work-in-progress)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Deployment](#deployment)
- [Testing the Application](#testing-the-application)
- [Configuration Management](#configuration-management)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Known Issues](#known-issues)

---

## Business Overview

### What Problem Does This Solve?

Many business processes require expert analysis of documents, comparison with historical data, and structured decision-making — tasks that are time-consuming and prone to inconsistencies. This platform showcases how AI agents can **autonomously** process these tasks through intelligent reasoning and tool usage, while maintaining human oversight where needed.

The platform demonstrates this through two use cases that share the same agent infrastructure:

### Use Case 1: Insurance Claims Processing

- Autonomous document processing via OCR
- Smart policy matching via semantic search through user contracts
- Precedent-based reasoning using similar historical claims
- Decision: **Approve / Deny / Manual Review** with confidence score

### Use Case 2: Tender Management (Appels d'Offres)

- Ingests tender documents (RFPs) and extracts key information via OCR
- Analyzes the tender against the company's past project references, certifications, and historical tender outcomes using RAG similarity search
- Generates a **Go / No-Go / Needs Deeper Review** recommendation with:
  - Risk analysis (technical, financial, resources, competition)
  - Win probability estimate
  - Estimated margin
  - Strengths and weaknesses
- Supports Human-in-the-Loop review when confidence is low

### The ReAct Agentic Workflow

Instead of rigid, pre-programmed rules, the system uses **ReAct (Reasoning + Acting)** pattern where an AI agent:

1. **Thinks** about what information it needs
2. **Acts** by calling appropriate tools (OCR, RAG retrieval)
3. **Observes** the results
4. **Repeats** until it has enough information to make a decision

#### How ReAct Works in Claims Processing

```
Customer Submits Claim
        ↓
┌───────────────────────────────────────────────────────┐
│  ReAct Agent Autonomous Decision Loop                 │
├───────────────────────────────────────────────────────┤
│                                                       │
│  💭 Agent Thinks: "I need to read the document"      │
│  🔧 Agent Acts: Calls ocr_document tool              │
│  👁️ Agent Observes: Receives structured claim data   │
│                                                       │
│  💭 Agent Thinks: "I need the user's policy"         │
│  🔧 Agent Acts: Calls retrieve_user_info tool        │
│  👁️ Agent Observes: Gets coverage limits, terms      │
│                                                       │
│  💭 Agent Thinks: "Let me check similar cases"       │
│  🔧 Agent Acts: Calls retrieve_similar_claims tool   │
│  👁️ Agent Observes: Finds historical precedents      │
│                                                       │
│  💭 Agent Thinks: "I have enough information"        │
│  ✅ Agent Decides: Approve/Deny/Manual Review        │
│     with confidence score and reasoning              │
└───────────────────────────────────────────────────────┘
        ↓
  Compliance Check (PII Detection)
        ↓
  Human Review (if needed)
```

**Key Difference from Traditional Automation**:
- **Traditional**: Fixed workflow (always call tool A, then B, then C)
- **ReAct**: Agent decides which tools to use and when, based on reasoning

### Multi-Agent Orchestrator (Work in Progress)

The platform includes a **multi-agent orchestrator** that acts as a high-level router, classifying user intent via LLM and dispatching requests to the appropriate specialized agent:

```
User Message
    |
    v
+------------------------------+
|   Multi-Agent Orchestrator   |
|   (Intent Classification)    |
+------------------------------+
    |              |
    v              v
+---------+  +-----------+
| Claims  |  | Tenders   |
| Agent   |  | Agent     |
+---------+  +-----------+
```

**Key capabilities (in progress)**:
- **Intent-based routing**: LLM classifies user messages and routes to the correct domain agent (claims or tenders)
- **Chat sessions**: Persistent conversation history with session management
- **Agent registry**: Dynamic registration of specialized agents with metadata and capabilities
- **Suggested actions**: Context-aware follow-up suggestions (navigate, process, chat) after each agent response
- **Cross-domain agent chaining**: After a tender Go decision, the orchestrator can suggest filing an insurance claim
- **Bilingual support**: FR/EN language detection and response generation

**What's working**:
- Orchestrator routing and intent classification
- Chat sessions with message persistence
- Agent registry with claims and tenders agents
- Basic suggested actions
- PII detection on chat messages

**What's in progress**:
- Dynamic LLM-generated suggested actions (replacing hardcoded fallbacks)
- Full i18n for all frontend components
- Session deletion with cascade
- OpenShift OAuth authentication

### Business Capabilities

#### 1. Autonomous Document Processing
- Agent decides when OCR is needed
- Understands claim context, not just text extraction
- 2-4 seconds per document vs minutes of manual review

#### 2. Smart Policy Matching
- Semantic search through user contracts
- Understands coverage limits and exclusions
- Cross-references with claim type and amount

#### 3. Precedent-Based Reasoning
- Finds similar historical claims
- Applies consistent reasoning across cases
- Identifies patterns humans might miss

#### 4. Transparent Decision-Making
- **Reasoning**: Natural language explanation
- **Evidence**: References to policies and precedents
- **Confidence Score**: Agent's certainty level
- **Full Audit Trail**: Every tool call, every thought

### Compliance & Guardrails

#### PII Detection & Protection

**Business Need**: Insurance claims contain sensitive personal information (emails, phone numbers, dates of birth) that must be protected for GDPR/CCPA compliance.

**How It Works**:
- Automatic detection during processing
- Real-time flagging without blocking workflow
- Complete audit trail for regulatory review

**What Gets Detected**:
- Email addresses
- Phone numbers
- Dates of birth
- License plates
- Other PII patterns

**Compliance Benefits**:
- GDPR/CCPA compliance support
- Audit trail for regulators
- Risk mitigation for data exposure
- Automated reporting

#### Human-in-the-Loop (HITL) Review

**When Manual Review Triggers**:
- Low confidence scores (< 70%)
- High-value claims above threshold
- Complex edge cases
- Regulatory requirements

**Review Workflow**:
1. System shows AI recommendation with reasoning
2. Reviewer can ask clarifying questions to the agent ("Ask Agent" feature)
3. Reviewer makes final decision (approve/deny/request info)
4. System tracks both AI and human decisions for audit

**Business Value**:
- Faster processing with human oversight
- Consistent decisions with expert review
- Training data for improving the agent
- Regulatory compliance (human-in-loop requirement)

---

## Architecture

### System Overview

```mermaid
graph TB
    subgraph "User Layer"
        U["Customer / Claims Adjuster"]
    end

    subgraph "OpenShift Cluster"
        subgraph "Application - claims-demo namespace"
            F["Frontend React<br/>Chat UI + Domain Pages"]
            B["Backend FastAPI"]
            ORCH["Multi-Agent Orchestrator<br/>Intent Routing (WIP)"]
            REG["Agent Registry"]
        end

        subgraph "OpenShift AI 3.2 - AI Platform"
            subgraph "LlamaStack Distribution"
                LS["LlamaStack 0.3.5<br/>ReAct Orchestration"]
            end

            subgraph "AI Models - vLLM"
                LLM["Llama 3.3 70B INT8<br/>4xGPU L40 - 20K context"]
                EMB["Gemma 300M<br/>768-dim embeddings"]
            end

            subgraph "Data Science Pipelines"
                DSPA["Kubeflow Pipelines v2"]
                MINIO["MinIO S3 Storage"]
            end

            subgraph "Compliance"
                GR["TrustyAI Guardrails<br/>PII Detection"]
            end
        end

        subgraph "MCP Tool Servers - claims-demo"
            OCR["OCR MCP Server<br/>EasyOCR"]
            RAG["RAG MCP Server<br/>pgvector similarity"]
            CLAIMS_MCP["Claims MCP Server<br/>CRUD tools"]
            TENDERS_MCP["Tenders MCP Server<br/>CRUD tools"]
        end

        subgraph "Data Layer - claims-demo"
            DB[("PostgreSQL 15<br/>+ pgvector<br/>+ chat sessions")]
        end
    end

    U -->|HTTPS| F
    F -->|REST API| B
    B --> ORCH
    ORCH -->|Routes to| REG
    B -->|Responses API| LS
    LS -->|Inference| LLM
    LS -->|Embeddings| EMB
    LS -->|MCP/SSE| OCR
    LS -->|MCP/SSE| RAG
    LS -->|MCP/SSE| CLAIMS_MCP
    LS -->|MCP/SSE| TENDERS_MCP
    LS -->|Shields API| GR
    RAG -->|Vector Search| DB
    B -->|CRUD| DB
    DSPA -->|Artifacts| MINIO

    style LS fill:#f3e5f5
    style LLM fill:#e8f5e9
    style GR fill:#ffebee
    style ORCH fill:#fff3e0
```

### Services Architecture

Clean separation of concerns for maintainability. The modular architecture allows multiple business domains to share the same agent infrastructure:

```
backend/
├── app/
│   ├── api/                  # Thin HTTP layer (routing, validation, schemas)
│   │   ├── claims.py         # Claims REST endpoints
│   │   ├── tenders.py        # Tenders REST endpoints
│   │   ├── orchestrator.py   # Multi-agent chat/orchestrator endpoints
│   │   ├── hitl.py           # Human-in-the-Loop review endpoints
│   │   └── admin.py          # Admin panel (database reset, stats)
│   ├── services/
│   │   ├── claim_service.py              # Claims orchestration
│   │   ├── tender_service.py             # Tenders orchestration
│   │   ├── agents/                       # Multi-agent layer (WIP)
│   │   │   ├── base_agent_service.py     # Common agent pattern
│   │   │   ├── orchestrator_service.py   # Intent routing & chat sessions
│   │   │   └── registry.py              # Dynamic agent registry
│   │   ├── agent/                        # Shared AI components
│   │   │   ├── responses_orchestrator.py # LlamaStack Responses API client
│   │   │   ├── context_builder.py        # Prompt building with domain context
│   │   │   ├── response_parser.py        # Extract structured decisions
│   │   │   └── reviewer.py              # HITL "Ask Agent" logic
│   │   └── pii/                          # PII detection & redaction
│   │       ├── pii_service.py            # Detection service
│   │       └── redactor.py              # Regex-based redaction patterns
│   ├── models/               # Database ORM
│   │   ├── claim.py          # Claims, documents, decisions, users
│   │   ├── tender.py         # Tenders, documents, decisions, references
│   │   └── conversation.py   # Chat sessions & messages (WIP)
│   └── llamastack/           # Prompts & integration config
│       ├── prompts.py              # Claims agent prompts
│       ├── ao_prompts.py           # Tender agent prompts
│       └── orchestrator_prompts.py # Multi-agent router prompts (WIP)
├── mcp_servers/
│   ├── ocr_server/           # Document OCR (EasyOCR)
│   ├── rag_server/           # Vector search (pgvector)
│   ├── claims_server/        # Claims CRUD tools
│   └── tenders_server/       # Tenders CRUD tools
frontend/
├── src/
│   ├── pages/
│   │   ├── HomePage.tsx          # Dashboard with agent cards
│   │   ├── ChatPage.tsx          # Multi-agent chat interface (WIP)
│   │   ├── ClaimsListPage.tsx    # Claims list & filtering
│   │   └── TendersListPage.tsx   # Tenders list & filtering
│   ├── components/
│   │   ├── chat/                 # Chat UI components (WIP)
│   │   │   ├── ChatWindow.tsx    # Message display & input
│   │   │   ├── ChatMessage.tsx   # Message rendering with agent routing
│   │   │   ├── SuggestedActions.tsx # Context-aware action buttons
│   │   │   └── AgentGraph.tsx    # Agent architecture visualization
│   │   └── common/
│   │       ├── AgentCard.tsx     # Agent status cards
│   │       └── PIIBadge.tsx      # PII detection indicators
│   ├── hooks/
│   │   ├── useChat.ts            # Chat session management (WIP)
│   │   └── useAgents.ts          # Agent registry hook
│   ├── services/
│   │   └── orchestratorService.ts # Orchestrator API client (WIP)
│   ├── types/
│   │   └── chat.ts               # Chat type definitions (WIP)
│   └── i18n/                     # Internationalization FR/EN (WIP)
```

**Benefits**: Each domain (claims, tenders) has its own service and API layer, but shares the agent infrastructure (orchestrator, context builder, response parser). Adding a new use case only requires a new service, API, and model — no changes to the AI components. The multi-agent orchestrator layer adds intent-based routing and conversational capabilities on top of the existing domain agents.

### Technology Stack

- **AI Platform**: Red Hat OpenShift AI 3.2
- **LLM**: Llama 3.3 70B INT8 (vLLM, 4x L40 GPUs)
- **Embeddings**: Gemma 300M (768-dim vectors)
- **Orchestration**: LlamaStack 0.3.5 (ReAct)
- **Compliance**: TrustyAI Guardrails
- **Backend**: Python 3.12 + FastAPI
- **Frontend**: React 18 + TypeScript
- **Database**: PostgreSQL 15 + pgvector
- **Pipelines**: Kubeflow Pipelines v2
- **Deployment**: Helm 3.x on OpenShift 4.20+

---

## Prerequisites

### Required Infrastructure

1. **OpenShift 4.20+** with:
   - **GPU Nodes**: 4x NVIDIA L40 (48GB) or equivalent
   - **CPU/Memory**: 32+ vCPU, 128GB+ RAM
   - **Storage**: Dynamic provisioning (RWO, RWX)

2. **Red Hat OpenShift AI 3.2**:
   - Operator installed
   - vLLM ServingRuntime configured
   - LlamaStack operator enabled

3. **Tools**:
   ```bash
   helm version  # 3.12+
   oc version    # 4.20+
   ```

### Accounts

- **HuggingFace Token**: https://huggingface.co/settings/tokens (for model downloads)
- **Container Registry**: Quay.io, Docker Hub, or internal registry

---

## Deployment

### 1. Use Pre-built Images (Recommended)

Pre-built images are available on Quay.io:

```yaml
# In your values file
backend:
  image:
    repository: quay.io/mouachan/agentic-claims-demo/backend
    tag: v2.0.0

frontend:
  image:
    repository: quay.io/mouachan/agentic-claims-demo/frontend
    tag: v2.0.0

ocr:
  image:
    repository: quay.io/mouachan/agentic-claims-demo/ocr-server
    tag: v2.0.0

rag:
  image:
    repository: quay.io/mouachan/agentic-claims-demo/rag-server
    tag: v2.0.0

postgresql:
  image:
    repository: pgvector/pgvector
    tag: pg15
```

**Or build your own**: See [Development Guide](docs/DEVELOPMENT.md#building-container-images)

### 2. Configure Values

```bash
cd helm/agentic-claims-demo
cp values-sample.yaml values-mydeployment.yaml
```

Edit key settings:

```yaml
# Cluster domain
inference:
  endpoint: "https://llama-3-3-70b-llama-3-3-70b.apps.YOUR-CLUSTER.com/v1"

embedding:
  endpoint: "https://embeddinggemma-300m-embeddinggemma-300m.apps.YOUR-CLUSTER.com/v1"

# HuggingFace token
hfcli:
  token: "hf_YOUR_TOKEN"

# MinIO credentials
minio:
  rootPassword: "StrongPassword123!"

# Enable features
dataSciencePipelines:
  enabled: true
  objectStorage:
    scheme: http  # IMPORTANT: must be http

guardrails:
  enabled: true
```

### 3. Deploy

```bash
helm install agentic-claims-demo . \
  -f values-mydeployment.yaml \
  -n claims-demo \
  --create-namespace \
  --timeout=30m
```

**Expected time**: ~25-30 minutes (AI models download ~40GB)

### 4. Verify Deployment

```bash
# Check pods
oc get pods -n claims-demo

# Check DSPA (should be Ready=True)
oc get dspa -n claims-demo

# Get URLs
oc get routes -n claims-demo
```

### 5. Generate Embeddings (Required)

After deployment, run the embedding generation pipeline:

1. **Access OpenShift AI Dashboard** → Data Science Projects → `claims-demo` → Pipelines

2. **Import Pipeline**:

   ![Import Pipeline](assets/pipeline-import.png)

   - Click "Import pipeline"
   - Upload: `pipelines/data_initialization_pipeline.yaml`
   - Name: "Historical Claims Initialization"

3. **Create Pipeline Run**:

   ![Create Run](assets/pipeline-create-run.png)

   - Click "Create run"
   - Set parameters:
     - `batch_size`: 5
     - `embedding_model`: `vllm-embedding/embeddinggemma-300m`
     - `llamastack_endpoint`: `http://llamastack-rhoai-service.claims-demo.svc.cluster.local:8321`
     - `llm_model`: `vllm-inference/llama-3-3-70b-instruct-quantized-w8a8`
     - `max_retries`: 30
     - `num_claims`: 60 (default: 10, recommended: 60 for testing)

4. **Monitor Execution**:

   ![Pipeline Graph](assets/pipeline-run-graph.png)

   - Watch pipeline graph (15-20 minutes with num_claims=60)
   - Steps: Generate PDFs → Parse → Generate Embeddings

5. **Verify**:
   ```bash
   # Check knowledge base (should be 15/15)
   oc exec -n claims-demo statefulset/postgresql -- \
     psql -U claims_user -d claims_db -c \
     "SELECT COUNT(*) FROM knowledge_base WHERE embedding IS NOT NULL;"

   # Check claims (should be 60/60 with num_claims=60)
   oc exec -n claims-demo statefulset/postgresql -- \
     psql -U claims_user -d claims_db -c \
     "SELECT COUNT(*) FROM claim_documents WHERE embedding IS NOT NULL;"
   ```

### 6. Access Application

```bash
# Frontend URL
echo "Frontend: http://$(oc get route frontend -n claims-demo -o jsonpath='{.spec.host}')"

# Backend API
echo "Backend: http://$(oc get route backend -n claims-demo -o jsonpath='{.spec.host}')/api/v1"
```

---

## Testing the Application

### Via Web UI

#### 1. View Claims List

![Claims List](assets/ui-claims-list.png)

- Navigate to Claims page
- See all processed claims with status
- Filter by status, type, user
- Processing time displayed for each claim

#### 2. Process a Pending Claim

![Claim Details](assets/ui-claim-pending.png)

- Click "View Details" on a pending claim
- Review claim information
- Click "Process Claim" button
- Wait 5-10 seconds for processing

#### 3. View Processing Steps

![Processing Steps](assets/ui-processing-steps.png)

After processing completes:
- See all tool executions (OCR, RAG retrieval)
- View agent reasoning and confidence
- Check similar claims found
- Review policy matches

#### 4. PII Detection

![PII Detection](assets/ui-pii-detection.png)

- PII detections shown as warnings
- Details: what was detected, where, confidence
- Non-blocking (claim still processes)

#### 5. Human-in-the-Loop Review

![HITL Review](assets/ui-hitl-review.png)

For claims requiring manual review:
- System decision shown with reasoning
- "Ask Agent" to ask clarifying questions
- Agent responds with context-aware answers
- Reviewer approves/denies with notes

### Via API

```bash
BACKEND_URL=$(oc get route backend -n claims-demo -o jsonpath='{.spec.host}')

# List pending claims
curl "http://$BACKEND_URL/api/v1/claims?status=pending" | jq

# Process a claim
CLAIM_ID="<from-list>"
curl -X POST "http://$BACKEND_URL/api/v1/claims/${CLAIM_ID}/process" \
  -H "Content-Type: application/json" \
  -d '{"skip_ocr": false, "enable_rag": true}'

# Check status
curl "http://$BACKEND_URL/api/v1/claims/${CLAIM_ID}/status" | jq

# Get decision
curl "http://$BACKEND_URL/api/v1/claims/${CLAIM_ID}/decision" | jq
```

---

## Configuration Management

### Helm Values

For detailed configuration options, see [Helm Values Reference](docs/HELM_VALUES.md).

**Quick reference**:

```yaml
global:
  namespace: claims-demo
  clusterDomain: apps.cluster.com

backend:
  image:
    repository: quay.io/mouachan/agentic-claims-demo/backend
    tag: v2.0.0
  replicas: 1

postgresql:
  image:
    repository: pgvector/pgvector
    tag: pg15
  persistence:
    size: 10Gi
    storageClass: ""  # Use cluster default

inference:
  endpoint: "https://llama-3-3-70b-llama-3-3-70b.apps.CLUSTER/v1"
  resources:
    requests:
      nvidia.com/gpu: 4

dataSciencePipelines:
  enabled: true
  objectStorage:
    scheme: http  # CRITICAL for internal MinIO

guardrails:
  enabled: true
```

### Agent Prompts

Agent prompts are stored in `app/llamastack/prompts/` and mounted via ConfigMap.

**Location**: `backend/app/llamastack/prompts/`
- `agent_prompt.txt` - Main ReAct agent instructions
- `claim_processor_prompt.txt` - Claim processing workflow

**Modifying Prompts**:

1. **Development** - Edit files directly in `backend/app/llamastack/prompts/`
2. **Production** - Update ConfigMap:
   ```bash
   oc edit configmap claims-prompts -n claims-demo
   ```
3. **Restart backend** to load changes:
   ```bash
   oc rollout restart deployment/backend -n claims-demo
   ```

**Environment Variable**: `PROMPTS_DIR=/app/prompts`

### Backend Environment Variables

Backend configuration via ConfigMap (`backend-config`) and Secrets.

**Key Variables**:

```yaml
# LlamaStack
LLAMASTACK_ENDPOINT: http://llamastack-rhoai-service.claims-demo.svc.cluster.local:8321
LLAMASTACK_DEFAULT_MODEL: vllm-inference/llama-3-3-70b-instruct-quantized-w8a8
LLAMASTACK_EMBEDDING_MODEL: vllm-embedding/embeddinggemma-300m
LLAMASTACK_MAX_TOKENS: 4096

# MCP Servers
OCR_SERVER_URL: http://ocr-server.claims-demo.svc.cluster.local:8080
RAG_SERVER_URL: http://rag-server.claims-demo.svc.cluster.local:8080

# Guardrails
GUARDRAILS_SERVER_URL: https://guardrails-orchestrator-service.claims-demo.svc.cluster.local:8032
ENABLE_PII_DETECTION: true

# Database (from Secret postgresql-secret)
POSTGRES_HOST: postgresql
POSTGRES_PORT: 5432
POSTGRES_USER: claims_user
POSTGRES_PASSWORD: ***
POSTGRES_DATABASE: claims_db

# Note: DATABASE_URL is constructed automatically from these variables
# as postgresql+asyncpg://user:pass@host:port/database
```

**Modify ConfigMap**:
```bash
oc edit configmap backend-config -n claims-demo
oc rollout restart deployment/backend -n claims-demo
```

**Modify Secret** (database credentials):
```bash
oc edit secret postgresql-secret -n claims-demo
oc rollout restart deployment/backend -n claims-demo
```

### Frontend Configuration

Frontend uses **nginx reverse proxy** for backend communication - no environment variables needed.

**How it works**:

1. Frontend code calls API at `/api/v1/...` (relative path)
2. Nginx reverse proxy routes requests to backend:
   ```nginx
   location /api/ {
       proxy_pass http://backend:8000/api/;
   }
   ```
3. No hardcoded backend URLs in frontend code

**Optional Environment Variable**:

```bash
# Only needed if you want to override the default
VITE_API_URL=/api/v1  # (default fallback in code)
```

**To modify backend routing**: Edit `frontend/nginx-server.conf` and rebuild image.

---

## Troubleshooting

### DSPA Not Ready

**Problem**: DataSciencePipelinesApplication stuck

**Check**:
```bash
oc get dspa -n claims-demo -o yaml
oc logs -l app=ds-pipeline-dspa -n claims-demo
```

**Common fixes**:
- Verify `scheme: http` (not https) in values.yaml
- Wait for MariaDB pod to be Running
- Use short DSPA name (< 10 chars)

### LlamaStack Cannot Connect

**Problem**: LlamaStack fails to query models

**Check**:
```bash
oc get inferenceservice -A
oc logs deployment/llamastack-rhoai -n claims-demo
```

**Solution**: Update model endpoints with correct cluster domain in values.yaml

### Embeddings Zero

**Problem**: RAG tools return no results

**Solution**: Run embedding generation pipeline (see step 5 above)

### More Issues

See full troubleshooting guide in main documentation.

---

## Development

For local development, testing, and contributing:

**[→ Development Guide](docs/DEVELOPMENT.md)**

Includes:
- Local setup (backend, frontend, database)
- Running tests
- Building images
- Database migrations
- Debugging tips

---

## Known Issues

### ReAct Streaming Not Captured

- **Status**: Intermediate reasoning steps (thoughts between tool calls) not stored
- **Cause**: LlamaStack 0.3.5 bug - requires 0.5.0+ for streaming persistence
- **Issue**: https://github.com/llamastack/llama-stack/pull/4738
- **Workaround**: Check LlamaStack pod logs for full trace

### Embeddings

- **Knowledge Base**: Run pipeline to generate 15/15 embeddings
- **Similar Claims**: May return zero results if embeddings missing

### Current Version: v2.1.0 (multi-agents) — Under Construction

**Working**:
- End-to-end claim processing (single-agent)
- End-to-end tender / Appels d'Offres processing (single-agent)
- PII detection & audit trail
- HITL review workflow (claims & tenders)
- Ask Agent feature for interactive review
- Multi-agent orchestrator with intent-based routing
- Agent registry with dynamic agent registration
- Chat sessions with persistent message history
- Basic suggested actions after agent responses
- Chat interface with agent visualization
- Bilingual support FR/EN (partial)

**In Progress**:
- Dynamic LLM-generated suggested actions (replacing hardcoded fallbacks)
- Full i18n for all frontend components (claims, tenders, admin pages)
- Backend language detection and locale-aware agent responses
- Session deletion with cascade cleanup
- Cross-domain agent chaining refinement
- OpenShift OAuth authentication
- A2A (Agent-to-Agent) protocol support

