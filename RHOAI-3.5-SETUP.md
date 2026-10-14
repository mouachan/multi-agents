# Red Hat OpenShift AI 3.5 — Installation & Deployment Guide

Deploys the multi-agent platform on **OpenShift 4.22 + RHOAI 3.5** with every
feature used by the demo:

| Feature | RHOAI 3.5 component | Status in 3.5 |
|---|---|---|
| Responses API, MCP tools, pgvector, Files | **OGX** (`OGXServer`, formerly LlamaStack) | TP (Responses API GA) |
| LLM access, token rate limits, API keys | **Models-as-a-Service** (`ExternalModel`, `MaaSSubscription`) | GA (external models TP) |
| Decoupled agents | **A2A** agents (a2a-sdk 1.x, JSON-RPC + streaming) | — |
| MCP servers + federated endpoint | **MCP lifecycle operator** (`MCPServer`) + **MCP Gateway** (Kuadrant) | — |
| PII masking, jailbreak check | **NeMo Guardrails** (`NemoGuardrails`, TrustyAI) | GA |
| Traces, versioned prompts | **MLflow** (tracing + **Prompt Registry**) | GA |
| Agent identity without a mesh | **Zero Trust Workload Identity Manager** (SPIFFE/SPIRE, JWT-SVID) | GA (OCP) |

> No GPU is required: models are served by an external OpenAI-compatible MaaS and
> re-published through the cluster MaaS gateway.

---

## 1. Cluster sizing

RHOAI 3.5 minimums: 2 workers × 8 vCPU / 32 GiB, or a single-node cluster with
32 vCPU / 128 GiB. A default StorageClass with dynamic provisioning is required.

| Topology (AWS example) | Nodes | Notes |
|---|---|---|
| 3 control plane + 3 compute | 3 × m6a.xlarge + 3 × m6a.4xlarge | comfortable |
| Compact (3 schedulable control plane) | 3 × m6a.4xlarge | 48 vCPU / 192 GiB |
| Single node | 1 × m6a.8xlarge | supported minimum, no HA |

Application footprint (requests): ~8 vCPU / ~24 GiB.

---

## 2. Operators

Install from OperatorHub:

| Operator | Namespace | Used for |
|---|---|---|
| Red Hat OpenShift AI 3.5 | `redhat-ods-operator` | OGX, MaaS, MLflow, TrustyAI, MCP lifecycle |
| Red Hat Connectivity Link (Kuadrant, Authorino, Limitador) | `openshift-operators` | MaaS gateway auth/rate limits, MCP Gateway policies |
| MCP Gateway | `openshift-operators` | `MCPGatewayExtension`, `MCPServerRegistration` |
| cert-manager | `cert-manager-operator` | MaaS / gateway certificates |
| Zero Trust Workload Identity Manager *(optional, SPIFFE)* | **`zero-trust-workload-identity-manager`** | SPIRE server/agent, SPIFFE CSI driver |
| Red Hat build of OpenTelemetry, Tempo *(optional)* | `openshift-operators` | platform observability |

> ⚠️ ZTWIM must **not** be installed in `openshift-operators` (unsupported): the SPIRE
> controller manager ignores `openshift-*` namespaces and the OIDC discovery provider
> never gets an SVID.

---

## 3. DataScienceCluster

```bash
oc patch datasciencecluster default-dsc --type merge -p '{
  "spec": {"components": {
    "ogx":                  {"managementState": "Managed"},
    "aigateway":            {"managementState": "Managed", "modelsAsAService": {"managementState": "Managed"}},
    "mlflowoperator":       {"managementState": "Managed"},
    "trustyai":             {"managementState": "Managed"},
    "mcplifecycleoperator": {"managementState": "Managed"},
    "dashboard":            {"managementState": "Managed"}
  }}}'

oc get datasciencecluster default-dsc \
  -o jsonpath='{range .status.conditions[*]}{.type}={.status}{"\n"}{end}' \
  | grep -E 'OGX|ModelsAsAService|MLflow|TrustyAI|MCPLifecycle'
```

Leave `trustyai.mcpGuardrailsMode` to `false`.

---

## 4. Platform checks

```bash
# OGX distributions available to OGXServer
oc get ogxs.components.platform.opendatahub.io -o yaml | grep -A3 availableDistributions

# MLflow (tracing + Prompt Registry) — in-cluster URL must keep the /mlflow prefix
oc get mlflow mlflow -o jsonpath='{.status.address.url}{"\n"}'

# MaaS gateway and API
oc get gateway maas-default-gateway -n openshift-ingress
oc get route -n openshift-ingress | grep maas
```

---

## 5. SPIFFE / SPIRE (optional — `spiffe.enabled`)

ZTWIM operands (all named `cluster`, `operator.openshift.io/v1alpha1`):

```yaml
apiVersion: operator.openshift.io/v1alpha1
kind: ZeroTrustWorkloadIdentityManager
metadata: {name: cluster}
spec:
  trustDomain: <apps.cluster-domain>
  clusterName: <cluster-name>
---
apiVersion: operator.openshift.io/v1alpha1
kind: SpireServer
metadata: {name: cluster}
spec:
  caSubject: {commonName: <apps.cluster-domain>, country: FR, organization: demo}
  jwtIssuer: https://spire-oidc.<apps.cluster-domain>
  datastore: {databaseType: sqlite3, connectionString: /run/spire/data/datastore.sqlite3}
  persistence: {size: 1Gi, accessMode: ReadWriteOnce}
---
apiVersion: operator.openshift.io/v1alpha1
kind: SpireAgent
metadata: {name: cluster}
spec: {}
---
apiVersion: operator.openshift.io/v1alpha1
kind: SpiffeCSIDriver
metadata: {name: cluster}
spec: {}
```

The chart creates a `ClusterSPIFFEID` (`className: zero-trust-workload-identity-manager-spire`
is mandatory) so each pod gets `spiffe://<trust-domain>/ns/<ns>/sa/<serviceaccount>`.

How it is used — no mesh, no TLS plumbing:
1. The backend fetches a **JWT-SVID** for audience `a2a:<agent>` from the SPIFFE CSI
   Workload API socket (`SPIFFE_ENDPOINT_SOCKET`) and sends it as `Authorization: Bearer`.
2. Each A2A agent validates it against its local SPIRE agent and only accepts the
   caller `/ns/<ns>/sa/backend` (401 without/invalid token, 403 for another identity).
3. The agent card and `/health` stay public (discovery and probes).

---

## 6. Build & push images (Mac, Podman, linux/amd64)

```bash
podman login quay.io
QUAY_REPO=quay.io/<your-org>/multi-agents IMAGE_TAG=v3.5 ./scripts/build-all.sh --push
```

Agents share one Containerfile: `podman build -f agents/Containerfile --build-arg AGENT=claims-agent .`

---

## 7. Install

```bash
helm upgrade --install multi-agents helm/multi-agents \
  -n multi-agents --create-namespace \
  -f helm/multi-agents/values-rhoai35.yaml \
  --set global.clusterDomain=<apps.cluster-domain> \
  --set global.imageRegistry=quay.io/<your-org>/multi-agents \
  --set models.external.host=<external-maas-host> \
  --set secrets.maasExternalApiKey=<external-maas-api-key> \
  --set secrets.postgresPassword=<password> \
  --set secrets.postgresAdminPassword=<password> \
  --set secrets.ogxDbPassword=<password> \
  --set minio.rootPassword=<password>
```

What the chart creates for the RHOAI 3.5 features:

| Template | Objects |
|---|---|
| `templates/maas/` | `ExternalProvider` → `ExternalModel` + `MaaSModelRef` (gpt-oss-120b, llama-scout-17b), `MaaSSubscription` + `MaaSAuthPolicy` (namespace ServiceAccounts), Job `maas-api-key` (mints an `sk-oai-` key into Secret `maas-api-key`) |
| `templates/ogx/` | `OGXServer` `ogx` + run config (kv/sql on PostgreSQL, pgvector, S3 files, pypdf, MCP) |
| `templates/agents/` | `claims-agent`, `tenders-agent`, `postal-agent` (A2A, port 8090) |
| `templates/mcp-servers/` | 6 `MCPServer` CRs (`/mcp` Streamable HTTP) |
| `templates/mcp-gateway/` | `Gateway`, `MCPGatewayExtension`, `MCPServerRegistration`s, rate limit |
| `templates/guardrails/` | `NemoGuardrails` + config (Presidio PII masking incl. French recognizers, self-check input) |
| `templates/mlflow/` | RoleBinding `mlflow-operator-mlflow-integration`, Job `prompt-sync` |
| `templates/spiffe/` | `ClusterSPIFFEID` |

Models: chat models go through the **cluster MaaS** (`https://maas.<apps-domain>/v1`,
API key bound to the `multi-agents` subscription). MaaS external models are chat-only,
so **embeddings** (`nomic-embed-text-v1-5`, 768 dims) are served straight from the
external MaaS.

---

## 8. Verify

```bash
NS=multi-agents
oc get ogxserver,nemoguardrails,mcpserver,externalmodel,maasmodelref -n $NS
oc get maassubscription,maasauthpolicy -n models-as-a-service
oc get pods -n $NS

# Agents: A2A agent cards
for a in claims tenders postal; do
  oc exec -n $NS deploy/backend -- curl -s http://$a-agent:8090/.well-known/agent-card.json | head -c 200; echo
done

# Prompts synced to MLflow (job logs)
oc logs -n $NS job/prompt-sync

# NeMo masking (input rails)
oc exec -n $NS deploy/backend -- curl -s http://multi-agents-guardrails/v1/checks \
  -H 'Content-Type: application/json' \
  -d '{"model":"llama-scout-17b","messages":[{"role":"user","content":"Mon IBAN est FR76 3000 6000 0112 3456 7890 189, email jean.dupont@example.com"}],"guardrails":{"config_id":"multi-agents"}}'
# -> {"status":"modified","content":"Mon IBAN est <FR_IBAN>, email <EMAIL_ADDRESS>"}  (or <IBAN_CODE>)
```

---

## 9. Prompt versioning with MLflow

* Source of truth: `helm/multi-agents/files/cm.*-prompts/*.txt` (one prompt per file,
  prompt name = file name without `.txt`).
* `helm upgrade` → Job `prompt-sync` registers a **new version** for every changed file
  and moves the alias `production` (`mlflow.prompts.promoteOnSync`).
* Agents load `prompts:/<name>@production` with a 60 s cache: promoting another version
  in the MLflow UI (*Prompts → version → alias*) is live within a minute, no restart.
* Fallback: ConfigMap file, then last loaded value. Each MLflow trace records
  `prompt.name` / `prompt.version` / `prompt.source`.
* Set `mlflow.prompts.promoteOnSync=false` to keep UI promotions across upgrades.

---

## 10. Known limitations

* MaaS **external models** are Technology Preview and chat-only (no embeddings).
* NeMo Presidio runs the **English** spaCy model; French names are detected
  heuristically, French identifiers through the custom regex recognizers.
* NeMo's OpenAI client cannot skip TLS verification: with `models.maas.tlsVerify=false`
  (self-signed gateway) the guardrails LLM calls the external MaaS directly.
* `MCPServer` has no `imagePullPolicy`: bump image tags on rebuilds.
