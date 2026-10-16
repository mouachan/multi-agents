{{/*
Expand the name of the chart.
*/}}
{{- define "multi-agents.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "multi-agents.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "multi-agents.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "multi-agents.labels" -}}
helm.sh/chart: {{ include "multi-agents.chart" . }}
{{ include "multi-agents.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "multi-agents.selectorLabels" -}}
app.kubernetes.io/name: {{ include "multi-agents.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Get cluster domain
*/}}
{{- define "multi-agents.clusterDomain" -}}
{{- .Values.global.clusterDomain }}
{{- end }}

{{/*
Get namespace
*/}}
{{- define "multi-agents.namespace" -}}
{{- .Values.global.namespace }}
{{- end }}

{{/*
Get image registry
*/}}
{{- define "multi-agents.imageRegistry" -}}
{{- .Values.global.imageRegistry }}
{{- end }}

{{/*
Build full image name
*/}}
{{- define "multi-agents.image" -}}
{{- $registry := .registry -}}
{{- $repository := .repository -}}
{{- $tag := .tag -}}
{{- printf "%s/%s:%s" $registry $repository $tag }}
{{- end }}

{{/* multi-arch nodeAffinity */}}
{{- define "multiarch_node_affinity" -}}
nodeAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    nodeSelectorTerms:
      - matchExpressions:
          - key: kubernetes.io/arch
            operator: In
            values:
              - amd64
              - arm64
{{- end -}}

{{/* WARNING: valueFrom secrets isn't CIS compliant */}}
{{/* should export env vars from a script within container, as done with postgres */}}
{{- define "postgres.env" -}}
- name: POSTGRES_DATABASE
  valueFrom:
    secretKeyRef:
      name: {{ quote .Values.postgresql.auth.existingSecret }}
      key: {{ quote .Values.postgresql.auth.secretKeys.databaseKey }}
- name: POSTGRES_HOST
  value: postgresql
- name: POSTGRES_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ quote .Values.postgresql.auth.existingSecret }}
      key: {{ quote .Values.postgresql.auth.secretKeys.userPasswordKey }}
- name: POSTGRES_PORT
  value: "5432"
- name: POSTGRES_USER
  valueFrom:
    secretKeyRef:
      name: {{ quote .Values.postgresql.auth.existingSecret }}
      key: {{ quote .Values.postgresql.auth.secretKeys.userNameKey }}
{{- end }}

{{/* =========================================================================
OGX (RHOAI 3.5, formerly LlamaStack) — OGXServer Service is <name>-service:8321
========================================================================= */}}
{{- define "multi-agents.ogx.endpoint" -}}
http://{{ .Values.ogx.name }}-service.{{ include "multi-agents.namespace" . }}.svc.cluster.local:8321
{{- end -}}

{{/*
OGX model identifiers: OGX 1.2 registers every model as "<provider_id>/<model_id>"
(see templates/ogx/configmap.yaml). Chat models use provider "maas", embeddings "maas-direct".
Usage: include "multi-agents.ogx.chatModel" .Values.models.reasoning
*/}}
{{- define "multi-agents.ogx.chatModel" -}}
maas/{{ . }}
{{- end -}}

{{- define "multi-agents.ogx.embeddingModel" -}}
maas-direct/{{ .Values.models.embedding }}
{{- end -}}

{{/* Cluster MaaS gateway (OpenAI-compatible, body-based routing on "model") */}}
{{- define "multi-agents.maas.gatewayUrl" -}}
{{- .Values.models.maas.gatewayUrl | default (printf "https://maas.%s/v1" (include "multi-agents.clusterDomain" .)) -}}
{{- end -}}

{{/* External MaaS (direct) */}}
{{- define "multi-agents.maas.externalUrl" -}}
https://{{ .Values.models.external.host }}/v1
{{- end -}}

{{/* Base URL used for chat models (cluster MaaS when enabled, external otherwise) */}}
{{- define "multi-agents.maas.chatUrl" -}}
{{- if .Values.models.maas.enabled -}}
{{ include "multi-agents.maas.gatewayUrl" . }}
{{- else -}}
{{ include "multi-agents.maas.externalUrl" . }}
{{- end -}}
{{- end -}}

{{/* Secret holding the API key for chat models (key: api-key) */}}
{{- define "multi-agents.maas.chatKeySecret" -}}
{{- if .Values.models.maas.enabled -}}maas-api-key{{- else -}}maas-external-credentials{{- end -}}
{{- end -}}

{{/* =========================================================================
NeMo Guardrails (TrustyAI) — Service <cr-name>:80
========================================================================= */}}
{{/* NeMo LLM rails endpoint: the cluster MaaS only when its certificate is trusted
     (NeMo's OpenAI client cannot skip TLS verification), else the external MaaS */}}
{{- define "multi-agents.guardrails.llmUrl" -}}
{{- if and .Values.models.maas.enabled .Values.models.maas.tlsVerify -}}
{{ include "multi-agents.maas.gatewayUrl" . }}
{{- else -}}
{{ include "multi-agents.maas.externalUrl" . }}
{{- end -}}
{{- end -}}

{{- define "multi-agents.guardrails.llmKeySecret" -}}
{{- if and .Values.models.maas.enabled .Values.models.maas.tlsVerify -}}maas-api-key{{- else -}}maas-external-credentials{{- end -}}
{{- end -}}

{{- define "multi-agents.guardrails.endpoint" -}}
http://{{ .Values.guardrails.name }}.{{ include "multi-agents.namespace" . }}.svc.cluster.local
{{- end -}}

{{/* =========================================================================
MLflow (RHOAI 3.5) — workspace = namespace, auth = pod ServiceAccount token
Usage: include "multi-agents.mlflow.env" (dict "root" $ "experiment" "<name>")
========================================================================= */}}
{{- define "multi-agents.mlflow.workspace" -}}
{{- .Values.mlflow.workspace | default (include "multi-agents.namespace" .) -}}
{{- end -}}

{{- define "multi-agents.mlflow.env" -}}
{{- $root := .root -}}
- name: MLFLOW_TRACKING_URI
  value: {{ $root.Values.mlflow.trackingUri | quote }}
- name: MLFLOW_EXPERIMENT_NAME
  value: {{ .experiment | quote }}
- name: MLFLOW_WORKSPACE
  value: {{ include "multi-agents.mlflow.workspace" $root | quote }}
- name: PROMPT_ALIAS
  value: {{ $root.Values.mlflow.prompts.alias | quote }}
- name: PROMPT_CACHE_TTL
  value: {{ $root.Values.mlflow.prompts.cacheTtlSeconds | quote }}
{{- end -}}

{{/* =========================================================================
MCP tools for the A2A agents: MCP Gateway (single federated endpoint) or
one Streamable HTTP endpoint per server
========================================================================= */}}
{{- define "multi-agents.mcp.agentEnv" -}}
{{- if .Values.mcpGateway.enabled -}}
- name: MCP_GATEWAY_URL
  value: {{ include "multi-agents.mcpGateway.url" . | quote }}
{{- else -}}
- name: MCP_SERVER_URL_TEMPLATE
  value: {{ printf "http://{server}.%s.svc.cluster.local:8080/mcp" (include "multi-agents.namespace" .) | quote }}
{{- end -}}
{{- end -}}

{{/* =========================================================================
SPIFFE (ZTWIM): Workload API socket from the SPIFFE CSI driver
========================================================================= */}}
{{- define "multi-agents.spiffe.env" -}}
{{- if .Values.spiffe.enabled -}}
- name: SPIFFE_ENDPOINT_SOCKET
  value: unix:///spiffe-workload-api/spire-agent.sock
{{- end -}}
{{- end -}}

{{- define "multi-agents.spiffe.volumeMount" -}}
{{- if .Values.spiffe.enabled -}}
- name: spiffe-workload-api
  mountPath: /spiffe-workload-api
  readOnly: true
{{- end -}}
{{- end -}}

{{- define "multi-agents.spiffe.volume" -}}
{{- if .Values.spiffe.enabled -}}
- name: spiffe-workload-api
  csi:
    driver: {{ .Values.spiffe.csiDriver }}
    readOnly: true
{{- end -}}
{{- end -}}

{{/* OpenShift groups of the access profiles (JSON list) */}}
{{- define "multi-agents.auth.groups" -}}
{{- $groups := list -}}
{{- range $id, $p := .Values.auth.profiles }}{{ $groups = append $groups $p.group }}{{ end -}}
{{- $groups | toJson -}}
{{- end }}
