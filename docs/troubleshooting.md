# Troubleshooting

## OGX Cannot Reach the Models

**Check**:
```bash
oc get ogxserver -n <NAMESPACE>
oc get pods -n <NAMESPACE> | grep ogx
oc logs <ogx-pod> -n <NAMESPACE> | grep -iE "error|401|403|model"

# MaaS objects and API key
oc get externalmodel,maasmodelref -n <NAMESPACE>
oc get maassubscription,maasauthpolicy -n models-as-a-service
oc logs job/maas-api-key -n <NAMESPACE>
oc get secret maas-api-key -n <NAMESPACE>
```

Common causes:
- **401/403 from the MaaS gateway**: the `maas-api-key` Secret is missing or expired (`models.maas.keyExpiration`), or the `MaaSSubscription` does not list the model.
- **Embedding errors**: embeddings are served by the external MaaS (`maas-direct` provider) — check `models.external.host` and `secrets.maasExternalApiKey`. The model id must match exactly (`nomic-embed-text-v1-5` with hyphens, not dots).
- **TLS errors**: with a self-signed MaaS gateway keep `models.maas.tlsVerify: false`.

## A2A Agent Calls Fail

```bash
oc get pods -l component=a2a-agent -n <NAMESPACE>
oc logs deploy/claims-agent -n <NAMESPACE>
oc exec -n <NAMESPACE> deploy/backend -- curl -s http://claims-agent:8090/health
```

Common issues:
- **401 / 403 with SPIFFE enabled**: the backend has no SPIFFE CSI socket (ZTWIM not installed, or installed in `openshift-operators`), or the caller is not `/ns/<ns>/sa/backend`.
- **Unknown profile**: the backend's agent profile id must match a profile of the agent (`agents/<domain>-agent/agent.py`).
- **Empty prompt**: MLflow unreachable and no ConfigMap fallback — check `oc logs job/prompt-sync`.

## RAG Returns No Similar Claims

**Check**:
```bash
# Verify embeddings exist
oc exec postgresql-0 -n <NAMESPACE> -- \
  psql -U multi_agent_user -d multi_agent_db -c \
  "SELECT COUNT(*) FROM claim_documents WHERE embedding IS NOT NULL;"
```

**Solution**: ensure `data-init` completed (`oc logs job/<release>-data-init`): it embeds the documents of
the precedents and the reference data, and retries the missing ones on every `helm upgrade`. The
backend embeds the document of each case it processes.

## OCR Fails or Times Out

The OCR server sends PDF page images to the vision model (`models.vision`) through OGX `/v1/chat/completions`. If it fails:
- Check the OCR server and OGX logs for inference errors
- Verify the vision model is listed in `models.maas.chatModels`
- Each page takes ~5-10 seconds, multi-page documents take longer
- Page images are sent as grayscale JPEG shrunk to at most `OCR_MAX_IMAGE_B64_KB` (default 60 KB of base64): the MaaS gateway stalls on request bodies above ~90 KB

## NeMo Guardrails Not Working

```bash
# Check NemoGuardrails CR status
oc get nemoguardrails -n <NAMESPACE>

# Check guardrails pod logs
oc get pods -n <NAMESPACE> | grep guardrails
oc logs <guardrails-pod> -n <NAMESPACE>

# Verify the config is mounted
oc describe nemoguardrails multi-agents-guardrails -n <NAMESPACE>
```

Common issues:
- **Wrong endpoint or port**: the service listens on port **80** (`http://<guardrails.name>.<ns>.svc.cluster.local`) and the agents call `POST /v1/checks`.
- **Model 401**: the `model` field must be the LLM name (`models.guardrails`, e.g. `llama-scout-17b`), not the config id.
- **Unknown config**: `guardrails.config_id` must equal `guardrails.configId` (`multi-agents`).
- **Pod not starting**: the `trustyai` component must be `Managed` in the DataScienceCluster.

## MLflow Traces Not Appearing

```bash
# Check backend / agent logs for trace export
oc logs deployment/backend -n <NAMESPACE> | grep -iE "mlflow|otlp|trace"
oc logs deployment/claims-agent -n <NAMESPACE> | grep -iE "mlflow|otlp|trace|prompt"

# Verify RBAC
oc get rolebinding mlflow-integration -n <NAMESPACE>

# MLflow URL (must keep the /mlflow prefix)
oc get mlflow mlflow -o jsonpath='{.status.address.url}{"\n"}'
```

Common issues:
- **403 Forbidden**: Missing `mlflow-integration` RoleBinding — set `mlflow.enabled=true` in Helm values
- **404 on `/v1/traces` or prompts**: the tracking URI lost its `/mlflow` prefix
- **RESOURCE_DOES_NOT_EXIST**: the experiment does not exist yet — the backend creates it at startup; check the MLflow connectivity
- **Connection refused at startup**: MLflow not ready when the backend starts — it retries (5 attempts, 3 s apart)

## Data Init Fails

```bash
# OpenShift
oc get jobs -n <NAMESPACE>
oc logs job/<release>-data-init -n <NAMESPACE>

# Local
podman logs multi-agents-data-init
```

Common causes: OGX not healthy yet, the OCR server not started, the vision model unreachable (the
precedents are read again on the next run).

## A tool answers `success: false`

The MCP servers return `{"success": false, "error": "..."}` for an expected refusal (unknown case
number, no OCR text yet) and for a failure (logged with its traceback in the server's pod):

```bash
oc logs deploy/claims-server -n <NAMESPACE> | grep -B2 -A20 "Tool .* failed"
```

## Personal data appears in an agent answer

* In the user's own message: the input rails mask it; check `guardrails` in the chat trace panel
  (`modified`), and NeMo's logs.
* In tool results: the MCP servers mask the personal fields always, and the free text through NeMo
  (`GUARDRAILS_ENDPOINT` of the MCP server pods); a warning `NeMo masking failed` in their logs means
  the patterns were used instead (names are then not masked).
* Person names in French free text are not detected by Presidio's English model (known limitation).

## A tool call is refused (MCP Gateway)

A tool the user's profile does not grant is refused by the gateway (`mcp-tools-rbac`, 403 when the
router opens the session to the server); it reaches the client as a `500` of the broker. Check the
user's groups (`oc get groups`) and `auth.agentTools`.
