# Configuration

The Helm values that matter, and the protocols between the components. Installation steps are in
[RHOAI-3.5-SETUP.md](../RHOAI-3.5-SETUP.md).

## Models (MaaS)

Models are declared once in the `models:` block of the Helm values and given to OGX, the agents, the
MCP servers and NeMo:

| Key | Default | Role |
|-----|---------|------|
| `models.reasoning` | `llama-scout-17b` | Agents: reasoning and tool calling |
| `models.processing` | (empty) | Agents, case processing only; empty = `models.reasoning` |
| `models.vision` | `llama-scout-17b` | OCR of the PDF pages |
| `models.guardrails` | `llama-scout-17b` | NeMo LLM rail (self check input) |
| `models.embedding` | `nomic-embed-text-v1-5` | Embeddings of the documents and reference data |
| `models.embeddingDimension` | `768` | pgvector dimension |

```yaml
models:
  external:
    host: "REPLACE_WITH_EXTERNAL_MAAS_HOST"   # FQDN only; key: --set secrets.maasExternalApiKey=...
  maas:
    enabled: true            # chat models through the cluster MaaS gateway
    tlsVerify: false         # self-signed gateway certificate on lab clusters
    subscriptionName: multi-agents
    tokenRateLimit: {limit: 3000000, window: 1h}   # the platform key; 429 above it
    callAsUser: true         # with authentication: the agents call the models as the user
    chatModels: [gpt-oss-120b, llama-scout-17b]
```

* With `models.maas.enabled=true` the chart creates an `ExternalProvider`, one `ExternalModel` and
  `MaaSModelRef` per chat model, and a `MaaSSubscription` and `MaaSAuthPolicy` for the namespace's
  ServiceAccounts. Job `maas-api-key` mints the API key into Secret `maas-api-key`.
* OGX registers the chat models on provider `maas` (cluster gateway) and the embedding model on
  provider `maas-direct` (external MaaS): MaaS external models are chat-only.
* With authentication and `callAsUser` (the default), the agents call the chat models **as the
  user**. The backend mints the user's MaaS API key with the user's own token, bound to the
  subscription of their access profile (`app/services/maas_keys.py`), and OGX calls the cluster MaaS
  with it instead of the platform key (provider data `vllm_api_token`, for that request only). The
  MaaS then applies the token quota of the profile (`auth.profiles.<id>.tokenQuota`, below) and its
  usage view shows each person. A key, rather than the user's token: the MaaS refuses a token that
  matches several subscriptions (it would need the `X-MaaS-Subscription` header, which OGX cannot
  send). The key never goes to the external MaaS: chat models always use the cluster gateway.
* `tokenRateLimit` is the platform key's quota: NeMo, the OCR, and the agents without
  authentication. A case processing uses about 20–30k tokens, a chat answer 3–8k. Above a quota the
  gateway answers `429`; the agent then says the profile's quota is used up (chat), and the
  processing ends `failed` with that message on the case page (it can be processed again).

## Access profiles

An access profile is an OpenShift group; its rights are OpenShift RBAC in the namespace
(`templates/auth/`):

| Profile | Group | Agents | MaaS quota per person (`tokenQuota`) |
|---|---|---|---|
| Administration | `multi-agents-admins` | all, admin page | 3M tokens/h (an evaluation uses ~750k) |
| Finance | `multi-agents-finance` | claims | 500k tokens/h |
| BTP | `multi-agents-btp` | tenders | 500k tokens/h |
| Logistique | `multi-agents-logistics` | postal | 500k tokens/h |

The same rule is applied by the UI (pages, chat routing), the backend API and the MCP Gateway (each
tool call, `auth.agentTools`). Administrators give profiles on the admin page, or with
`oc adm groups add-users <group> <user>`; first members at install:
`--set-json 'auth.profiles.<id>.users=["<user>"]'`.

* **Tools.** The backend asks OpenShift which tools of `auth.agentTools` the user may call (the
  RBAC rule the gateway applies) and gives the agent only those: in a chat, the agent tells the user
  which tools the profile does not allow; a processing (or a reviewer's question) needs every tool
  of its workflow, else the API answers `403` with the missing tools. The admin page lists the tools
  of each profile.
* **Quota.** `tokenQuota: {limit, window, priority}` creates the profile's `MaaSSubscription`
  (`<subscriptionName>-<id>`), one counter per member; the key of a member of several profiles is
  bound to the one of highest priority. Without `tokenQuota`, the members use the `userAccess`
  subscription (`<subscriptionName>-users`). To show a quota live, lower one profile's limit (e.g.
  `--set auth.profiles.logistics.tokenQuota.limit=30000`): after a processing or a few chat
  answers, its members get the quota message while the other profiles keep working.

## Agents (A2A)

Three agents built on a2a-sdk 1.x (JSON-RPC, streaming), one Deployment, Service and ServiceAccount
each, on port 8090:

| Agent | Profiles (`metadata.profile`) | Prompts |
|---|---|---|
| `claims-agent` | `claims` | `claims-processing-agent` |
| `tenders-agent` | `tenders` | `ao-processing-agent` |
| `postal-agent` | `courrier_reclamation`, `courrier_info`, `courrier_suivi` | `courrier-reclamation-instructions`, `courrier-info-instructions`, `courrier-suivi-instructions` |

Each agent serves its card at `/.well-known/agent-card.json` (readiness probe), `/health`, and
JSON-RPC on `/`. The backend finds them with `CLAIMS_AGENT_A2A_URL`, `TENDERS_AGENT_A2A_URL` and
`POSTAL_AGENT_A2A_URL` (set by Helm); an agent that is not deployed gives a clear error.

**Request metadata** (all optional):

| Key | Description |
|---|---|
| `profile` | the agent profile (default: the agent's first) |
| `mode` | `chat` (the chat rules are added to the prompt) or `process` (case processing) |
| `tools` | subset of the profile's tools, in this order |
| `decision_values`, `review_decision`, `human_decisions` | processing: the decisions allowed, the one handing the case to a person, what that person can decide |
| `language` | `fr` / `en`, enforced by the `language-rule` prompt |
| `previous_response_id` | OGX response to continue (the conversation) |
| `instructions_override` | the chat session's own prompt |
| `user_token` | the user's OpenShift token, presented to the MCP Gateway |
| `traceparent` | the caller's trace: the agent's spans join it |

**Answer**: tool activity and guardrails verdicts are `working` status updates
(`event: tool_call | tool_result | guardrails | fallback`), the text is the `response` artifact. The
final status message carries `output`, `decision`, `tool_calls`, `response_id`, `model`, `usage`,
`duration_ms`, `prompt {name, version, source}`, `guardrails {input, output}` and `caller`.

**SPIFFE** (optional, `spiffe.enabled`): the backend sends a JWT-SVID for the audience
`a2a:<agent>-agent`; each agent validates it with its local SPIRE agent and only accepts
`/ns/<ns>/sa/backend` (401 without a valid token, 403 for another identity). The card and `/health`
stay public.

## Chat

`POST /api/v1/chat/sessions/{id}/messages` streams Server-Sent Events:

| Event | Content |
|---|---|
| `routing` | the chosen agent, the method (`semantic`, `llm`, `sticky`, `keywords`), score, candidates |
| `agent_resolved` | the agent profile |
| `a2a` | `phase: request` (agent card, profile, authentication), `phase: status` (task states) |
| `guardrails` | `input` / `output` verdict (`passed`, `modified`, `blocked`) |
| `tool_call`, `tool_result` | MCP tool activity (arguments, sandbox runs) |
| `text_delta`, `text_replace` | the answer (already masked) |
| `heartbeat` | every 10 s, so load balancers never cut a long answer |
| `done` | usage, model, suggested actions, A2A summary, MLflow trace link |

**Routing** (`backend/app/services/chat/routing.py`): the messages are compared with the skills of
the agent cards (embeddings computed once). A clear winner is chosen at once; when two agents are
close, one short LLM call picks; a weak match on a follow-up ("merci", "et le deuxième ?") stays on
the session's agent. Keywords are the fallback (`ROUTER_ENABLED`, `ROUTER_MIN_SCORE=0.62`,
`ROUTER_MARGIN=0.04`).

## Prompts (MLflow Prompt Registry)

* Source: `helm/multi-agents/files/prompts/agents/*.txt`, one prompt per file (name = file name).
* `helm install/upgrade` → Job `prompt-sync` registers a new version of each changed file and moves
  the alias `production` (`mlflow.prompts.promoteOnSync: true`; `false` keeps the versions promoted
  in the MLflow UI).
* The agents load `prompts:/<name>@production` with a 60 s cache (`mlflow.prompts.cacheTtlSeconds`):
  promoting a version in the MLflow UI is live within a minute. Fallback: the ConfigMap file, then
  the last value loaded.
* The backend's prompt files (`files/prompts/backend/`: processing request of each domain, chat
  settings) are not versioned in MLflow.

## NeMo Guardrails

**Input rails** (user messages, in order): `mask sensitive data on input` (Presidio), then
`self check input` (an LLM call that refuses jailbreaks, prompt injections, abusive or off-role
messages; `guardrails.selfCheckInput`). **Output rails** (answers, and the free text of the tool
results): `mask sensitive data on output`.

| Entity | Example |
|--------|---------|
| EMAIL_ADDRESS | `jean@email.com` |
| PHONE_NUMBER, FR_PHONE | `+44 20 7946 0958`, `06 12 34 56 78` |
| IBAN_CODE, FR_IBAN | `FR76 3000 6000 ...` |
| CREDIT_CARD | `4111 1111 1111 1111` |
| FR_NIR | French social security number |
| FR_PLATE | French licence plate (SIV) |

`PERSON` is not in Presidio's lists: its English spaCy model is unreliable on French text. Names are
found by **GLiNER** (rails `gliner mask pii on input / output`, after Presidio): a CPU server
(`guardrails/gliner-server`) running `urchade/gliner_multi_pii-v1` (Apache-2.0; en, fr, de, es, it,
pt), masked as `[PERSON]`. The `FR_*` entities are regex recognizers of the NeMo ConfigMap
(`templates/guardrails/nemo-configmap.yaml`).

| Parameter | Description | Default |
|-----------|-------------|---------|
| `guardrails.enabled` | Deploy NeMo Guardrails | `true` |
| `guardrails.configId` | Config id sent by the agents and the MCP servers | `multi-agents` |
| `guardrails.failOpen` | Agents: let the request through when NeMo does not answer | `true` |
| `guardrails.selfCheckInput` | The LLM `self check input` rail | `true` |
| `guardrails.pii.inputEntities` / `outputEntities` | Entities masked on input / output | see above |
| `guardrails.pii.scoreThreshold` | Presidio detection threshold | `0.4` |
| `guardrails.gliner.enabled` | GLiNER server and rails (names) | `true` |
| `guardrails.gliner.model` | GLiNER model, downloaded at the first start into a PVC | `urchade/gliner_multi_pii-v1` |
| `guardrails.gliner.entities` / `threshold` | GLiNER labels masked, detection threshold | `[person]`, `0.5` |

The MCP servers never return unmasked text: when NeMo does not answer, they mask by patterns.

## MLflow tracing

The backend and the agents export OpenTelemetry spans to MLflow (`/v1/traces`, ServiceAccount token,
workspace header, the cluster's service CA). They write to the same experiment
(`mlflow.experimentName`, default `multi-agent-orchestrator`): one chat turn or one processing is one
trace, the agent's spans joining the backend's through the `traceparent` of the A2A metadata.

```
chat | <message>   or   process | <entity> <number>    backend root: input, answer
├── routing                                        method, score, candidates
└── a2a:<agent>                                    agent card, JWT-SVID audience, task states
    └── <agent>/<profile>                          the agent run
        ├── guardrails                             input / output verdicts
        ├── tool:<name>                            one per MCP call: arguments, output
        └── llm-response                           token usage
```

The root span carries `session.id` (the chat session, `<entity>-<id>` for a processing,
`review-<entity>-<id>` for the reviewer's questions) and `user.id` (the OpenShift user): the
*Sessions* view of the experiment groups the turns of a conversation.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `mlflow.enabled` | Tracing, Prompt Registry and RBAC | `true` |
| `mlflow.trackingUri` | MLflow internal URL (keep the `/mlflow` prefix) | `https://mlflow.redhat-ods-applications.svc:8443/mlflow` |
| `mlflow.experimentName` | Experiment of the backend and the agents | `multi-agent-orchestrator` |
| `mlflow.uiUrl` | MLflow UI, for the trace links of the chat | `https://rh-ai.<apps-domain>/mlflow` |
| `mlflow.prompts.alias` | Prompt alias loaded by the agents | `production` |
| `mlflow.prompts.promoteOnSync` | Move the alias on every `helm upgrade` | `true` |

RoleBinding `mlflow-integration` (ClusterRole `mlflow-operator-mlflow-integration`) gives the backend,
`prompt-sync` and agent ServiceAccounts access to MLflow; without it exports and prompt loading fail
with `403`.
