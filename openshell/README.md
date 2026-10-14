# OpenShell — sandboxed code interpreter for the claims agent

[OpenShell](https://github.com/NVIDIA/OpenShell) (NVIDIA, with Red Hat) runs a command
inside a sandbox enforced by the Linux kernel: Landlock filesystem rules, seccomp, a
private network namespace whose outbound traffic goes through a policy proxy (default
deny), and a supervisor that logs every decision. It is a **Developer Preview** in
Red Hat OpenShift AI 3.5 (upstream artifacts, not supported in production).

## Why a code interpreter

The agents' tool calls are executed by OGX against the MCP Gateway, not inside the agent
pods, so wrapping the agents themselves would not constrain anything useful (and would
break the SPIFFE JWT-SVID path). The valuable place is the code the LLM *generates*:
`run_python` executes it in a throw-away OpenShell sandbox with **no network** and a
read-only system, so a model that has been manipulated (e.g. by content of a processed
document) cannot reach the network, read credentials or alter the host, even if NeMo
Guardrails did not catch the manipulation.

```
backend ──A2A + JWT-SVID──▶ claims-agent ──▶ OGX /v1/responses
                                                │ MCP tool run_python
                                                ▼
                                   MCP Gateway (Kuadrant) ──▶ sandbox-server (MCPServer)
                                                                 │ gRPC + mTLS (client bundle)
                                                                 ▼
                                   OpenShell gateway (ns openshell) ──▶ Sandbox CR (Agent Sandbox)
                                                                 ▼
                                   sandbox pod: supervisor + /usr/bin/python3.12 -c <code>
                                   policy: network deny-all, Landlock rw /sandbox /tmp only
```

## Pieces in this repository

| Path | Content |
|---|---|
| `openshell/policies/code-sandbox-policy.yaml` | Sandbox policy: `network_policies: {}` (deny all), read-only `/usr /lib /lib64 /etc /proc`, writable `/sandbox /tmp`, Landlock `hard_requirement`, runs as `sandbox` |
| `openshell/sandbox-image/Containerfile` | UBI 9 minimal + `/usr/bin/python3.12` + numpy (`code-sandbox` image) |
| `backend/mcp_servers/sandbox_exec_server/` | MCP server exposing `run_python(code, timeout_s)`; OpenShell Python SDK `openshell==0.1.2` (same version as the gateway) |
| `helm/multi-agents/templates/openshell/policy-configmap.yaml` | ConfigMap `sandbox-exec-policy` (policy file, symlinked in `files/openshell/`) |
| `helm/multi-agents/values.yaml` → `mcp.sandbox` | `sandbox-server` MCPServer (mounts the mTLS bundle Secret and the policy) + MCP Gateway registration |
| `agents/claims-agent/agent.py`, `cm.claims-prompts/claims-processing-agent.txt` | `run_python` added to the claims tools; prompt: use it for payout computations when available |

`run_python` returns `success`, `exit_code`, `stdout`, `stderr`, `denials` (network /
filesystem denials observed in the sandbox output) and `sandbox` (name, image, policy,
timings). The authoritative OCSF decision events are in the OpenShell supervisor and
gateway logs.

## Install (OpenShift 4.20.26+ / 4.21.21+ / 4.22.2+)

Versions validated by the Red Hat agent-ops guide
(<https://github.com/zanetworker/agent-ops>, path validated on OCP 4.20.27 under the
default `restricted-v2` SCC, no privileged SCC): images
`quay.io/opendatahub/odh-openshell-{gateway,supervisor,sandbox}:v0.1.2-rhaiv.5`, chart
`oci://ghcr.io/nvidia/openshell/helm-chart` `0.0.0-dev.e7fdd6beef98f7f92d86271a169fdd4d3be44cf3`,
Agent Sandbox `0.9.0`. The official guide
(<https://github.com/opendatahub-io/agent-ops>) requires OCP 4.21+ and the privileged SCC.

1. **Agent Sandbox operator** (`agent-sandbox-operator`, channel `preview-0.9`,
   namespace `agent-sandbox-system`, AllNamespaces OperatorGroup). Provides the
   `Sandbox`, `SandboxTemplate`, `SandboxClaim`, `SandboxWarmPool` CRDs.

2. **OpenShell gateway** (namespace `openshell`, telemetry off, in-cluster only — no Route):

   ```bash
   oc create namespace openshell
   helm install openshell oci://ghcr.io/nvidia/openshell/helm-chart \
     --version 0.0.0-dev.e7fdd6beef98f7f92d86271a169fdd4d3be44cf3 \
     --namespace openshell \
     --set podSecurityContext.fsGroup=null \
     --set securityContext.runAsUser=null \
     --set server.auth.allowUnauthenticatedUsers=true \
     --set server.telemetryEnabled=false \
     --set "pkiInitJob.serverDnsNames[0]=openshell.openshell.svc" \
     --set "pkiInitJob.serverDnsNames[1]=openshell.openshell.svc.cluster.local" \
     --set global.image.registry=quay.io/opendatahub \
     --set global.image.tag=v0.1.2-rhaiv.5 \
     --set gateway.image.repository=odh-openshell-gateway \
     --set supervisor.image.repository=odh-openshell-supervisor \
     --set sandboxRuntime.image.repository=odh-openshell-sandbox
   ```

   `server.auth.allowUnauthenticatedUsers=true` is the agent-ops setting for clusters
   without the Keycloak user authentication of its step 2: callers are then identified
   only by the gateway's mTLS client certificate. Review it before using it; the
   alternative is the agent-ops OIDC setup (`install/02-user-auth.md`), with
   `OPENSHELL_BEARER_TOKEN` (or client credentials) on `sandbox-server`.

3. **mTLS client bundle for `sandbox-server`** (created by the chart's PKI job in
   `openshell`, copied by name, never stored in the repository):

   ```bash
   D=$(mktemp -d) && oc extract secret/openshell-client-tls -n openshell --to="$D" \
     && oc create secret generic openshell-client-tls -n multi-agents --from-file="$D"; rm -rf "$D"
   ```

4. **Images** (podman, linux/amd64, private repositories: give the cluster pull
   credentials read access to `code-sandbox` and `sandbox-exec-server`):

   ```bash
   podman build --platform linux/amd64 -t quay.io/<your-org>/multi-agents/code-sandbox:v3.5 openshell/sandbox-image
   podman build --platform linux/amd64 -t quay.io/<your-org>/multi-agents/sandbox-exec-server:v3.5 \
     -f backend/mcp_servers/sandbox_exec_server/Containerfile backend/mcp_servers
   ```

5. **Enable it in the chart** (`mcp.sandbox.enabled`, on in `values-rhoai35.yaml`):

   ```bash
   helm upgrade multi-agents helm/multi-agents -n multi-agents --reuse-values \
     --set mcp.sandbox.enabled=true --set agents.claims.image.tag=v3.5.4
   ```

## Verify

```bash
oc get pods -n openshell
oc exec -n multi-agents deploy/sandbox-server -- curl -s localhost:8080/health   # openshell.status=connected
# tool federated by the MCP Gateway
oc logs -n multi-agents deploy/sandbox-server | grep run_python
```

Then, in the chat, ask the claims agent for a payout computation, e.g. *"Sinistre de
4 800 € avec une franchise de 350 € et un plafond de 4 000 € : quel montant rembourser ?"*.
The A2A panel shows the `run_python` tool call; its result carries the sandbox name and
timings. A snippet that tries to open a network connection returns an error and a
`denials` entry of type `network`, and the supervisor logs the denied connection.

## Limits

* Developer Preview: no support, APIs moving quickly (keep the Python SDK version equal
  to the gateway version).
* Each call creates a sandbox (pod + volume, `WaitForFirstConsumer`): a few seconds of
  cold start. A `SandboxWarmPool` or a long-lived sandbox per conversation would cut it.
* RHCOS 9.6 (kernel 5.14): builds before `v0.1.2-rhaiv.5` needed a `sitecustomize.py`
  shim for Python HTTPS inside sandboxes; not needed here (no network anyway).
* UBI `python-3xx` images keep their virtualenv in `/opt/app-root`, outside the policy:
  the sandbox image calls `/usr/bin/python3.12` directly.
* Network rules can change on a running sandbox; filesystem, Landlock and process rules
  are fixed at creation.
