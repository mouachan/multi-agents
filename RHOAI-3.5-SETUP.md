# Red Hat OpenShift AI 3.5 — Installation & Deployment Guide

Deploys the multi-agent platform on **OpenShift 4.20–4.22 + RHOAI 3.5** with every
feature used by the demo (validated end to end on OCP 4.20.41 + RHOAI 3.5.1, AWS):

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
> re-published through the cluster MaaS gateway. Agents use **llama-scout-17b** for
> reasoning and tool calling: on the external MaaS it answers an agent turn in ~2 s,
> where gpt-oss-120b varied from 2 s to 70 s per call.

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

Install from OperatorHub (Automatic approval, pinned channels):

| Operator | Package / channel | Namespace (OperatorGroup) | Used for |
|---|---|---|---|
| Red Hat OpenShift AI | `rhods-operator` / `stable-3.5` | `redhat-ods-operator` (all namespaces) | the platform |
| Red Hat Connectivity Link | `rhcl-operator` / `stable` | `openshift-operators` | Kuadrant, Authorino, Limitador (MaaS, MCP Gateway) |
| MCP Gateway | `mcp-gateway` / `preview` | `openshift-operators` | `MCPGatewayExtension`, `MCPServerRegistration` |
| Leader Worker Set | `leader-worker-set` / `stable-v1.0` | `openshift-lws-operator` (own namespace) | llm-d (KServe) |
| Red Hat build of Kueue | `kueue-operator` / `stable-v1.4` | `openshift-kueue-operator` (all) | DSC `kueue: Unmanaged` |
| JobSet | `job-set` / `stable-v1.0` | `openshift-jobset-operator` (own namespace) | Trainer |
| Zero Trust Workload Identity Manager | `openshift-zero-trust-workload-identity-manager` / `stable-v1` | **`zero-trust-workload-identity-manager`** (own namespace) | SPIFFE/SPIRE |
| OpenTelemetry, Tempo, Cluster Observability | `opentelemetry-product`, `tempo-product`, `cluster-observability-operator` / `stable` | their `openshift-*` namespaces (all) | DSCI monitoring |
| cert-manager | `openshift-cert-manager-operator` | `cert-manager-operator` | certificates |

> ⚠️ ZTWIM must **not** be installed in `openshift-operators` (unsupported): the SPIRE
> controller manager ignores `openshift-*` namespaces and the OIDC discovery provider
> never gets an SVID.

Operator instances and cluster settings:

```bash
oc apply -f - <<'EOF'
apiVersion: operator.openshift.io/v1
kind: LeaderWorkerSetOperator
metadata: {name: cluster}
spec: {managementState: Managed, logLevel: Normal, operatorLogLevel: Normal}
---
apiVersion: operator.openshift.io/v1
kind: JobSetOperator
metadata: {name: cluster}
spec: {managementState: Managed, logLevel: Normal, operatorLogLevel: Normal}
---
apiVersion: v1
kind: ConfigMap            # user workload monitoring (MaaS metrics)
metadata: {name: cluster-monitoring-config, namespace: openshift-monitoring}
data:
  config.yaml: |
    enableUserWorkload: true
---
apiVersion: v1
kind: Namespace
metadata: {name: kuadrant-system}
---
apiVersion: kuadrant.io/v1beta1
kind: Kuadrant
metadata: {name: kuadrant, namespace: kuadrant-system}
spec: {}
---
# OCP 4.20 has no pre-created openshift-default GatewayClass; the MCP Gateway (chart value
# mcpGateway.gatewayClassName) and the MaaS docs expect it. Same controller as RHOAI's.
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata: {name: openshift-default}
spec: {controllerName: openshift.io/gateway-controller/v1}
EOF
```

Private images: add the registry credentials (e.g. a quay robot) to the cluster pull
secret, scoped to your namespace (`quay.io/<your-org>`), so every ServiceAccount can pull.

---

## 3. Platform PostgreSQL (MaaS, MLflow, Model Registry)

RHOAI does not ship the database used by the MaaS API keys, MLflow and the Model Registry.
One PostgreSQL 16 (`registry.redhat.io/rhel9/postgresql-16`) in its own namespace, with
TLS from the service CA (Service annotation `service.beta.openshift.io/serving-cert-secret-name`,
mounted on `/etc/pgtls`, plus `ssl = on` in `/opt/app-root/src/postgresql-cfg/ssl.conf`):

```bash
# databases
oc exec -n rhoai-db deploy/rhoai-postgres -- psql -U postgres -c 'CREATE DATABASE mlflow_db OWNER maas'
oc exec -n rhoai-db deploy/rhoai-postgres -- psql -U postgres -c 'CREATE DATABASE "model-registry" OWNER maas'

# connection secrets (password read from the database secret, never written to a file)
PW=$(oc get secret rhoai-db-credentials -n rhoai-db -o jsonpath='{.data.POSTGRESQL_PASSWORD}' | base64 -d)
H=rhoai-postgres.rhoai-db.svc.cluster.local:5432
oc create namespace redhat-ai-gateway-infra      # MaaS infrastructure namespace (3.5)
oc create secret generic maas-db-config -n redhat-ai-gateway-infra \
  --from-literal=DB_CONNECTION_URL="postgresql://maas:${PW}@${H}/maas_db?sslmode=require"
oc create secret generic mlflow-db-credentials -n redhat-ods-applications \
  --from-literal=BACKEND_STORE_URI="postgresql://maas:${PW}@${H}/mlflow_db?sslmode=require"
unset PW
```

Clients that verify the server certificate need the service CA: MLflow
`spec.caBundleConfigMap: {name: openshift-service-ca.crt}`, Model Registry
`postgres.sslMode: verify-ca` + `sslRootCertificateConfigMap: {name: openshift-service-ca.crt, key: service-ca.crt}`.

---

## 4. Models-as-a-Service gateway

```bash
# Authorino TLS (Authorino <-> maas-api)
oc annotate service authorino-authorino-authorization -n kuadrant-system \
  service.beta.openshift.io/serving-cert-secret-name=authorino-server-cert --overwrite
oc patch authorino authorino -n kuadrant-system --type=merge \
  -p '{"spec":{"listener":{"tls":{"enabled":true,"certSecretRef":{"name":"authorino-server-cert"}}}}}'
oc -n kuadrant-system set env deployment/authorino \
  SSL_CERT_FILE=/etc/ssl/certs/openshift-service-ca/service-ca-bundle.crt \
  REQUESTS_CA_BUNDLE=/etc/ssl/certs/openshift-service-ca/service-ca-bundle.crt
```

`maas-api` requires an **external hostname on the gateway listener and a LoadBalancer
Service** (otherwise `GET /v1/tenants` fails with "gateway ... is not configured with an
external hostname"). This exposes MaaS publicly on `maas.<apps-domain>` (the wildcard
ingress certificate covers it):

```yaml
apiVersion: v1
kind: ConfigMap
metadata: {name: maas-default-gateway-config, namespace: openshift-ingress}
data:
  service: |
    spec:
      type: LoadBalancer
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: maas-default-gateway
  namespace: openshift-ingress
  annotations:
    opendatahub.io/managed: "false"
    security.opendatahub.io/authorino-tls-bootstrap: "true"
spec:
  gatewayClassName: data-science-gateway-class
  infrastructure:
    parametersRef: {group: "", kind: ConfigMap, name: maas-default-gateway-config}
  listeners:
  - name: https
    hostname: maas.<apps-domain>
    port: 443
    protocol: HTTPS
    tls:
      mode: Terminate
      certificateRefs: [{group: "", kind: Secret, name: <default-ingress-certificate-secret>}]
    allowedRoutes: {namespaces: {from: All}}
```

Until the gateway is exposed, install the chart with `--set models.maas.enabled=false`
(OGX then calls the external MaaS directly).

---

## 5. DataScienceCluster, monitoring, dashboard

```bash
oc patch dsci default-dsci --type=merge -p '{"spec":{"monitoring":{"managementState":"Managed",
  "namespace":"redhat-ods-monitoring","alerting":{},
  "metrics":{"replicas":1,"storage":{"size":"5Gi","retention":"90d"}},
  "traces":{"sampleRatio":"0.1","storage":{"backend":"pv","retention":"2160h"}}}}}'
```

All components on (`datasciencecluster.opendatahub.io/v2`):

| Component | Setting |
|---|---|
| `aigateway` | Managed, `modelsAsAService` Managed, `batchGateway` Managed (MaaS moved here from `kserve.modelsAsService` in 3.5) |
| `kserve` | Managed, `nim` + `wva` Managed, `rawDeploymentServiceConfig: Headless`, `modelCache` Removed (needs node storage) |
| `kueue` | **Unmanaged** (`Managed` is rejected; the Red Hat build of Kueue creates the `Kueue` CR) |
| `ogx` | Managed (`llamastackoperator` is deprecated → Removed) |
| `trustyai` | Managed, `eval.lmeval.permitCodeExecution/permitOnline: allow`, `mcpGuardrailsMode: false` |
| `aipipelines`, `dashboard`, `feastoperator`, `mcplifecycleoperator`, `mlflowoperator`, `modelregistry`, `ray`, `sparkoperator`, `trainer`, `trainingoperator`, `workbenches` | Managed |

Then the `MLflow` CR (`backendStoreUriFrom: {name: mlflow-db-credentials, key: BACKEND_STORE_URI}`,
`caBundleConfigMap`, `serveArtifacts: true`), a `ModelRegistry` in `rhoai-model-registries`,
and the dashboard flags (`OdhDashboardConfig.spec.dashboardConfig`: every `disable*` false
except `disableModelMesh`, every feature flag true). Deprecated flags are rejected by the
3.5 API: `disableAcceleratorProfiles`, `disableFineTuning`, `disableHardwareProfiles`,
`maasAuthPolicies`, `mlflow`.

```bash
oc get dsc default-dsc -o jsonpath='{range .status.conditions[*]}{.type}={.status}{"\n"}{end}'
```

---

## 5b. SPIFFE / SPIRE (optional — `spiffe.enabled`)
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
spec:                                   # without attestors the agents crash
  nodeAttestor: {k8sPSATEnabled: "true"}      # "NodeAttestor ... expected exactly 1 but got 0"
  workloadAttestors: {k8sEnabled: "true", workloadAttestorsVerification: {type: auto}}
---
apiVersion: operator.openshift.io/v1alpha1
kind: SpiffeCSIDriver
metadata: {name: cluster}
spec: {}
---
apiVersion: operator.openshift.io/v1alpha1
kind: SpireOIDCDiscoveryProvider
metadata: {name: cluster}
spec:
  jwtIssuer: https://spire-oidc.<apps.cluster-domain>
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

Every image builds from its Containerfile, on the Mac, for the cluster's architecture:

```bash
podman login quay.io
R=quay.io/<your-org>/multi-agents; T=<tag>
podman build --platform linux/amd64 -t $R/backend:$T backend/
podman build --platform linux/amd64 -t $R/frontend:$T frontend/              # npm build inside the image
podman build --platform linux/amd64 -t $R/data-init:$T data-init/
podman build --platform linux/amd64 -t $R/gliner-server:$T guardrails/gliner-server/   # names, for NeMo
for a in claims tenders postal; do                                           # one Containerfile, three agents
  podman build --platform linux/amd64 -f agents/Containerfile --build-arg AGENT=$a-agent -t $R/$a-agent:$T .
done
for s in ocr rag claims tenders postal tracking sandbox_exec; do             # MCP servers (context holds shared/)
  podman build --platform linux/amd64 -f backend/mcp_servers/${s}_server/Containerfile -t $R/${s//_/-}-server:$T backend/mcp_servers
done
podman push ...    # each image, then set its tag in values.yaml (or --set), and remove the local images
```

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

`values-rhoai35.yaml` turns on the OpenShift login (`auth.enabled=true`). The first members of
the access profiles and the source links of the AI hub catalog entries are given at install:

```bash
  --set-json 'auth.profiles.admin.users=["<admin-user>"]' \
  --set-json 'auth.profiles.finance.users=["<user>"]' \
  --set rhoaiCatalog.repository.url=https://github.com/<org>/<repo> \
  --set rhoaiCatalog.repository.ref=<branch>
```

What the chart creates for the RHOAI 3.5 features:

| Template | Objects |
|---|---|
| `templates/maas/` | `ExternalProvider` → `ExternalModel` + `MaaSModelRef` (gpt-oss-120b, llama-scout-17b), `MaaSSubscription` + `MaaSAuthPolicy` (namespace ServiceAccounts), Job `maas-api-key` (mints an `sk-oai-` key into Secret `maas-api-key`) |
| `templates/ogx/` | `OGXServer` `ogx` + run config (kv/sql on PostgreSQL, pgvector, S3 files, pypdf, MCP) |
| `templates/agents/` | `claims-agent`, `tenders-agent`, `postal-agent` (A2A, port 8090) |
| `templates/mcp-servers/` | 7 `MCPServer` CRs (`/mcp` Streamable HTTP; `/tmp` is an `emptyDir`, the operator mounts the root filesystem read-only), with the AI hub annotations `mcp.opendatahub.io/display-name` / `catalog-server` |
| `templates/mcp-gateway/` | `Gateway`, `MCPGatewayExtension`, `MCPServerRegistration`s, rate limit |
| `templates/guardrails/` | `NemoGuardrails` + config (Presidio PII masking incl. French recognizers, self-check input) |
| `templates/mlflow/` | RoleBinding `mlflow-operator-mlflow-integration`, Job `prompt-sync` |
| `templates/spiffe/` | `ClusterSPIFFEID` |
| `templates/openshell/` | Sandbox policy ConfigMap for `run_python` (`mcp.sandbox`, needs the OpenShell gateway — see [openshell/README.md](openshell/README.md)) |
| `templates/rhoai/` | ConfigMap `multi-agents-catalog` in `rhoai-model-registries` (agents + MCP catalog sources: logos, READMEs, tools, security indicators, license), ConfigMap `gen-ai-aa-mcp-servers` (playground) |
| `templates/auth/` | `Group` per access profile, `Role` per agent (`use` the agent, `call` its MCP tools) and `RoleBinding`s to the groups, `Role` `multi-agents-admin`, `ClusterRoleBinding`s of the backend (`system:auth-delegator`, `<ns>-profile-manager`), `AuthPolicy` `mcp-gateway-users` and `mcp-tools-rbac` on the MCP Gateway |
| `templates/frontend/` | `oauth-proxy` sidecar (OpenShift login) in front of the UI, re-encrypt Route |
| `templates/monitoring/` | `PersesDashboard` `dashboard-5-multi-agents` in `redhat-ods-monitoring` (see [section 10](#10-metrics-dashboard-perses)) |

Models: chat models go through the **cluster MaaS** (`https://maas.<apps-domain>/v1`,
API key bound to the `multi-agents` subscription). MaaS external models are chat-only,
so **embeddings** (`nomic-embed-text-v1-5`, 768 dims) are served straight from the
external MaaS.

**Image tags**: `values.yaml` pins the tag of every image of this release, so a fresh install
deploys the current code. When you rebuild an image, bump its tag in `values.yaml` (or
`--set backend.image.tag=...`, `agents.<name>.image.tag`, `mcp.<name>.image.tag`,
`frontend.image.tag`, `dataInit.image.tag`).

**Upgrades**: use `--reset-then-reuse-values` (`--reuse-values` ignores new chart
defaults); a tag passed with `--set` stays in the release values and overrides the chart
default until it is set again. The install and upgrade notes (`helm status`) list the
remaining manual steps (catalog restart, administrators, sandbox).
Hook Jobs use `before-hook-creation`, so a Job left by an interrupted upgrade does not
block the next one.

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

### Authentication and access profiles

Users log in with their OpenShift account (`oauth-proxy` in front of the UI). An **access
profile** is an OpenShift group; what it may use is OpenShift RBAC in the namespace:

| Profile | Group | Agents (and their MCP tools) |
|---|---|---|
| Administration | `multi-agents-admins` | all, plus the administration page (demo reset, profiles) |
| Finance | `multi-agents-finance` | claims |
| BTP | `multi-agents-btp` | tenders |
| Logistique | `multi-agents-logistics` | postal (complaints, tracking, postal information) |

* **UI and API**: the backend validates the user's token (TokenReview) and asks OpenShift
  (SubjectAccessReview) for verb `use` on `services/<domain>-agent` and `admin` on
  `services/backend`. Pages, chat routing, business APIs, reviews and documents follow it;
  chat sessions are private to their owner.
* **Agents and MCP tools**: the user's token travels with the A2A request to the agent, which
  hands it to OGX for the MCP Gateway. AuthPolicy `mcp-tools-rbac` checks each `tools/call`
  with a SubjectAccessReview: verb `call` on `tools.mcp.multi-agents.io/<tool>`, granted by the
  `Role` of each agent (`auth.agentTools`).
* **Models**: the users' MaaS subscription is granted to the profile groups.
* **Managing profiles**: *Admin → Users and access profiles* lists the OpenShift users and
  the group members; a checkbox adds or removes the user from the profile's group (the
  backend may update these groups only). A user can get a profile before the first login.
  Equivalent: `oc adm groups add-users multi-agents-finance <user>`. Helm upgrades keep the
  current members (`auth.profiles.<id>.users` only seeds the first install). New rights apply
  within ~10 s (OpenShift token cache).

Users come from the cluster identity provider (e.g. an htpasswd provider for demo accounts:
`oc get oauth cluster`). Checks with a user token:

```bash
B=https://backend-<namespace>.<apps-domain>/api/v1
TOKEN=$(oc whoami -t)           # logged in as a profile member (oc login -u <user>)
curl -H "Authorization: Bearer $TOKEN" $B/auth/me         # profiles, domains, admin
curl -H "Authorization: Bearer $TOKEN" $B/tenders/ -o /dev/null -w '%{http_code}\n'   # 403 for Finance
```

### OpenShift AI catalogs and metrics

* **AI hub → Agents / MCP servers**: the chart registers the three A2A agents and the
  seven MCP servers as catalog sources (`rhoaiCatalog` values), in the sections
  *MO supported agents* / *MO supported MCP servers*. Each entry has its logo
  (`files/branding/`), a README (domain part in `files/catalog/{agents,mcp}/<name>.md`,
  the rest generated: tools and the profiles that may call them, endpoints, governance,
  security), the tools with their parameters (`files/catalog/mcp-tools.yaml`, from the
  servers' `tools/list`), the Apache 2.0 license and the *Open repository* / *Source code*
  links (`rhoaiCatalog.repository`). The card badge is `rhoaiCatalog.supportTier`: the
  dashboard only displays `redHatSupported`, `partnerSupported` and `communitySupported`.
  Security indicators: *Verified source*, *Secure endpoint* (MCP Gateway with per-user
  authorization), *SAST* (Bandit, see below) and *Read only tools* (computed from the tools'
  access types).
  **The catalog restarts by itself when our entries change** (Job `catalog-reload`, run after
  every install and upgrade). The catalog reloads a modified source file on its own, but its
  *model* plugin fails that reload (`label with name 'Multi-agents' already exists from another
  origin`) and the pod turns NotReady: the whole AI hub catalog (models, agents, MCP servers)
  would be unavailable. The Job writes the hash of the entries on the catalog's pod template:
  unchanged entries, no restart; changed entries, one rollout, and the Job waits until the
  catalog is ready (`oc logs job/catalog-reload -n <namespace>`). Check the entries with
  `oc logs -n rhoai-model-registries deploy/model-catalog -c catalog | grep multi_agents`
  (`multi_agents_agents`, `multi_agents_mcp`).
* **Deploy an MCP server from the AI hub** (*AI hub → MCP servers → entry → Deploy MCP server*):
  each of our entries carries what the deploy form needs (`runtimeMetadata`, generated from the
  environment of the chart's own `MCPServer`): image, port and path, the configuration variables
  with their values (`defaultValue`), and the platform secret (`postgresql-secret`) as references,
  never values. Choose the release namespace (the database, OGX and NeMo addresses are those of
  the platform) and a new name, e.g. `tracking-catalog`: the dashboard creates an `MCPServer`, the
  MCP lifecycle operator its Deployment and Service (`oc get mcpserver -n <namespace>`). The AI
  hub lists it under *Deployments*; delete it there, or `oc delete mcpserver tracking-catalog`.

  SAST of the MCP servers and agents (no high or medium finding apart from B104, listening
  on all interfaces, required in a container):

  ```bash
  podman run --rm -v $PWD:/src:ro,Z docker.io/library/python:3.12-slim sh -c \
    'pip install -q bandit && cd /src && bandit -r backend/mcp_servers agents -ll -ii'
  ```
* **Observe & monitor → Multi-agents** (Perses): OGX requests, latency, time to first
  token, tokens/s, tool and agentic calls, MLflow requests, MaaS requests and tokens
  (Limitador counters per `<namespace>/<model>`); how it is built: [section 10](#10-metrics-dashboard-perses).
  The tenant telemetry adds `model` and `subscription` labels to the MaaS metrics:

  ```bash
  oc patch maastenantconfig default-tenant -n models-as-a-service --type=merge \
    -p '{"spec":{"telemetry":{"enabled":true,"metrics":{"captureModelUsage":true,"captureUser":true}}}}'
  ```

  The built-in **Usage** tab filters on `user!=""`: without `captureUser` it shows 0
  everywhere. `user` is the identity behind the call: with authentication the agents call the
  models as the user (`models.maas.callAsUser`), so the tab shows each person, with the
  subscription of their profile (`multi-agents-<profile>`); NeMo and the OCR remain under the
  ServiceAccount that minted the platform key
  (`system:serviceaccount:<namespace>:maas-key-minter`). The setting applies to every MaaS caller of the cluster (human API
  keys included): review it for GDPR on shared clusters. Only requests made after the
  change carry the label.

### Gen AI studio: AI asset endpoints

* **Models**: the MaaS models are granted to the cluster users by a second subscription
  (`models.maas.userAccess`: groups, priority below the application subscription, per-user
  token limit); their display name, description and use case come from the `MaaSModelRef`
  annotations (`models.maas.modelInfo`).
* **Agents**: one agent profile per A2A agent profile (`rhoaiCatalog.agentProfiles`,
  ConfigMaps `agent-profile-<id>` labelled `opendatahub.io/agent-profile=true`): reasoning
  model through the users' subscription, prompt from the MLflow Prompt Registry, MCP servers
  with the same tools (all read-only: decisions are saved by the backend, never by a tool).

```bash
oc get maassubscription,maasauthpolicy -n models-as-a-service
oc get cm -n <namespace> -l opendatahub.io/agent-profile=true
```

### OpenShell sandbox

The **Sandbox** page of the application shows the gateway status, the policy in force and
runs fixed isolation scenarios (computation and identity allowed; network, system write and
reads outside the policy denied). Same checks from the API:

```bash
B=https://backend-<namespace>.<apps-domain>/api/v1; H="Authorization: Bearer $(oc whoami -t)"
curl -H "$H" $B/sandbox/policy
curl -H "$H" -X POST $B/sandbox/demo/network   # expect denied
```

`compute_payout` (claims server) builds the payout computation from the claim's figures and
runs it with `run_python` in the sandbox (`SANDBOX_MCP_URL`); each run is visible in the chat
trace panel and on the claim page.

### Business processing

```bash
B=https://backend-<namespace>.<apps-domain>/api/v1; H="Authorization: Bearer $(oc whoami -t)"   # BTP or admin profile
curl -H "$H" -X POST $B/tenders/<id>/process                                    # returns at once
curl -H "$H" $B/tenders/<id> | jq '.status, [.processing_steps[].step_name]'     # poll
curl -H "$H" $B/tenders/<id>/decision | jq '.decision, .agent, .review'          # the agent's decision and brief
```

Every tool step should be `completed`, and the RAG steps should return precedents:
`data-init` embeds the reference data (company references, historical tenders,
capabilities, knowledge bases, contracts) and retries the OCR of the seeded
precedents on every upgrade; the backend embeds each processed document.

---

## 9. Prompt versioning with MLflow

* Source of truth: `helm/multi-agents/files/prompts/agents/*.txt` (one prompt per file,
  prompt name = file name without `.txt`). The backend's own prompt files (processing request
  of each domain, chat settings) are in `files/prompts/backend/` and are not versioned in MLflow.
* `helm upgrade` → Job `prompt-sync` registers a **new version** for every changed file
  and moves the alias `production` (`mlflow.prompts.promoteOnSync`).
* Agents load `prompts:/<name>@production` with a 60 s cache: promoting another version
  in the MLflow UI (*Prompts → version → alias*) is live within a minute, no restart.
* Fallback: ConfigMap file, then last loaded value. Each MLflow trace records
  `prompt.name` / `prompt.version` / `prompt.source`.
* Set `mlflow.prompts.promoteOnSync=false` to keep UI promotions across upgrades.

**Measure a version before promoting it.** The precedents (`precedent_decisions.json`, 30 cases
with a known decision) are the reference. *Admin → Decision quality* (or
`POST /api/v1/admin/evaluations {"prompt_alias": "..."}`) processes them again with the agents,
exactly as a processing but without saving anything, and logs a run in the MLflow experiment
`decision-evaluation`: accuracy overall and per domain, share of cases handed to a person, the
prompt versions used, one line per case. To try a new prompt:

1. register it as a new version of the prompt (MLflow UI, or `mlflow.genai.register_prompt`) and
   give it the alias `candidate`;
2. evaluate `production`, then `candidate` (prompts without a `candidate` alias use their file);
3. compare the two runs in MLflow (*Experiments → decision-evaluation*, select both → *Compare*);
4. promote: move `production` to the version in the MLflow UI, or commit the text in
   `files/prompts/agents/` (the next upgrade registers and promotes it).

The reviewers' decisions are recorded on the processing traces as MLflow feedback
(`reviewer_decision`, `agent_correct`): *Traces → Assessments* shows where the agents and the
reviewers disagree, the cases to add to the reference.

**Traces**: experiment `multi-agent-orchestrator` (*MLflow → Experiments*), one trace per chat
turn or business processing (backend, A2A and agent spans together). The *Sessions* view groups
the turns of a conversation (`session.id`: chat session, or `claim-<id>` / `tender-<id>` /
`reclamation-<id>` for processings); each trace records the OpenShift user (`user.id`). The
chat's *Execution trace* panel links to the trace.

---

## 10. Metrics dashboard (Perses)

The *Multi-agents* tab of **Observe & monitor** in the OpenShift AI dashboard is a
`PersesDashboard` created by the chart (`templates/monitoring/rhoai-dashboard.yaml`,
`observability.enabled`, default `true`).

**How OpenShift AI finds it.** With DSCI monitoring `Managed` (section 5, Cluster
Observability Operator), RHOAI runs Perses in `redhat-ods-monitoring` and shows the
`PersesDashboard` CRs of that namespace named `dashboard-<order>-<name>` as tabs, ordered by
`<order>`, titled by `spec.config.display.name`. The built-in tabs use 0-4
(`dashboard-0-cluster-admin`, `dashboard-1-model`, ..., `dashboard-4-llm-d-performance-admin`);
ours is `dashboard-5-multi-agents` (`apiVersion: perses.dev/v1alpha2`, `spec.config` holds
`display`, `duration`, `panels`, `layouts`). The namespace is
`observability.monitoringNamespace`.

**Where the metrics come from.** Panels reference the Perses datasources that RHOAI creates
in the same namespace:

| Datasource | Backend | Metrics used |
|---|---|---|
| `cluster-prometheus-datasource` | OpenShift Thanos querier (needs user workload monitoring, section 2) | `ogx_*` (scraped through the `ServiceMonitor` the OGXServer creates, port 9464), `mlflow_http_request_total` |
| `data-science-prometheus-datasource` | RHOAI Thanos querier (`redhat-ods-monitoring`) | Limitador `authorized_calls_total` (requests) and `authorized_hits_total` (tokens under a `TokenRateLimitPolicy`), label `limitador_namespace=<namespace>/<model>` |

**Panels.** OGX queries are filtered on the release namespace.

| Panel | Query (simplified) |
|---|---|
| Concurrent requests | `sum(ogx_concurrent_requests)` |
| Agentic calls / min | `rate(ogx_responses_agentic_calls_total[5m]) * 60` |
| Time to first token p90 | `histogram_quantile(0.9, ogx_inference_time_to_first_token_seconds_bucket)` |
| MCP tool calls / min | `rate(ogx_responses_tool_types_used_total{tool_type="mcp"}[5m]) * 60` |
| OGX requests / latency by API | `ogx_requests_total`, `ogx_request_duration_seconds_bucket` by `api` |
| LLM inference duration, generation speed | `ogx_inference_duration_seconds_bucket`, `ogx_inference_tokens_per_second_bucket` |
| Tool usage by type | `ogx_responses_tool_types_used_total` by `tool_type` |
| MLflow requests | `mlflow_http_request_total` |
| MaaS requests / tokens by model | `authorized_calls_total`, `authorized_hits_total` by `limitador_namespace` |

**Add or change a panel.** Add an entry under `spec.config.panels` (`TimeSeriesChart` or
`StatChart`, a `PrometheusTimeSeriesQuery` with one of the datasources above) and reference
it in a `layouts` grid item (`$ref: "#/spec/panels/<key>"`, 24 columns wide), then
`helm upgrade --reset-then-reuse-values`. Test a query first:

```bash
TQ=$(oc get route thanos-querier -n openshift-monitoring -o jsonpath='{.spec.host}')
curl -sk -H "Authorization: Bearer $(oc whoami -t)" "https://$TQ/api/v1/query" \
  --data-urlencode 'query=sum by (api) (rate(ogx_requests_total{namespace="<namespace>"}[5m]))'
```

**Empty panels.** OGX and MaaS panels only show data once requests have been made (rates
over 5 min). Check that `ogx-service-monitor` exists in the release namespace and that
`enableUserWorkload: true` is set; MaaS panels read the RHOAI Prometheus, not the OpenShift
one.

---

## 11. Known limitations

* MaaS **external models** are Technology Preview and chat-only (no embeddings).
* NeMo Presidio runs the **English** spaCy model, unreliable for French names in both
  directions ("Liste les appels" tagged `PERSON`, "Marie Martin" missed): names are masked by
  the GLiNER rail instead (`guardrails.gliner`), French identifiers by the custom regex
  recognizers. The GLiNER pod downloads its model from Hugging Face at the first start.
* The external MaaS latency is variable (gpt-oss-120b: 2–70 s per call): agents use
  llama-scout-17b. AWS Classic load balancers close connections idle for 60 s; the chat
  stream sends a `heartbeat` event every 10 s.
* The MLflow OTLP receiver is at the server root (`https://mlflow...:8443/v1/traces`),
  not under the `/mlflow` UI prefix (404).
* NeMo's OpenAI client cannot skip TLS verification: with `models.maas.tlsVerify=false`
  (self-signed gateway) the guardrails LLM calls the external MaaS directly.
* `MCPServer` has no `imagePullPolicy`: bump image tags on rebuilds.
* Llama via this MaaS turns multi-tool requests into Python-like text calls the
  gateway cannot parse (OGX 500): processing runs one tool per call (guided workflow).
  gpt-oss-120b fails multi-step tool calling through the same MaaS.
* The MaaS gateway stalls on request bodies above ~90 KB: OCR page images are capped
  at 60 KB of base64 (`OCR_MAX_IMAGE_B64_KB`).
* NeMo guardrails fail open: a check that still fails after one retry lets the text
  through unmasked (`guardrails.failOpen=false` blocks instead). The first checks
  after a cluster restart can time out while NeMo and the MaaS warm up.
* Sample documents (`documents/`): the agent reads the French documents; the `_en`
  files are their English translations, shown to English readers. They are generated by
  `documents/generators/` (claims: `generate_claim_pdfs.py`, tenders: `generate_tender_pdfs.py`).
  After a change of the documents, run data-init again with `dataInit.forceReinit=true` and
  `dataInit.documentsArchiveUrl` pointing to the branch that holds them.
* A tool call refused by the MCP Gateway (`mcp-tools-rbac`, 403 when the router opens the
  session to the server) reaches the client as a `500` of the broker; the router log shows
  `server returned 4xx for initialize POST`.
* When the `version` of a catalog entry changes, the catalog keeps the previous record next
  to the new one (duplicate cards). The entries use the chart `appVersion`, so image rebuilds
  do not change it; after an `appVersion` bump, clean up as follows. Disabling the source (`enabled: false` in the
  `sources.yaml` of ConfigMap `multi-agents-catalog`) removes its records: disable it,
  restart `model-catalog` (`oc rollout restart deploy/model-catalog -n rhoai-model-registries`),
  then run the `helm upgrade` (it enables the source again and the `catalog-reload` Job restarts
  the catalog).
* The model-catalog loads the sources only as leader: after a restart, the new pod can log
  `Lock held by another instance` until the lease of the previous pod expires, and serves
  the previous entries meanwhile.
* After a cluster restart, the DSC can stay `Degraded` on `ogx` although the
  `OGXServer` is healthy (stale status). Any change to the `OGX` component
  (e.g. an annotation) makes the operator re-evaluate it.
