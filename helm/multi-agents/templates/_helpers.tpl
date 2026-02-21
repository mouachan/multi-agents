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
{{- define "inference.namespace" -}}
{{- if ne .Values.inference.namespace "" -}}
{{- .Values.inference.namespace }}
{{- else -}}
{{- .Values.global.namespace }}
{{- end -}}
{{- end -}}
{{- define "embedding.namespace" -}}
{{- if ne .Values.embedding.namespace "" -}}
{{- .Values.embedding.namespace }}
{{- else -}}
{{- .Values.global.namespace }}
{{- end -}}
{{- end -}}
{{- define "gptoss.namespace" -}}
{{- .Values.gptoss.namespace | default .Values.global.namespace }}
{{- end -}}
{{- define "gptoss.endpoint" -}}
https://{{ .Values.gptoss.name }}-{{ .Values.gptoss.namespace }}.{{ .Values.global.clusterDomain }}/v1
{{- end -}}

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

{{/* route prefix */}}
{{- define "llamastack_route_prefix_full" -}}
llamastack-rhoai-{{ .Values.global.namespace }}
{{- end -}}

{{/* truncated route prefix, complying with 63 chars limit */}}
{{- define "llamastack_route_prefix" -}}
{{- include "llamastack_route_prefix_full" . | trunc 63 -}}
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

{{- define "llamastack.endpoint" -}}
http://llamastack-rhoai-service.{{ include "multi-agents.namespace" . }}.svc.cluster.local:8321
{{- end -}}

{{- define "llamastack.model" -}}
{{ .Values.inference.model.name }}
{{- end -}}

{{- define "llamastack.inferenceEndpoint" -}}
https://llama-llama-3-3-70b.{{ .Values.global.clusterDomain }}/v1
{{- end -}}

{{- define "llamastack.embeddingModel" -}}
{{ .Values.embedding.model.name }}
{{- end -}}

{{- define "llamastack.embeddingEndpoint" -}}
https://gemma-embeddinggemma-300m.{{ .Values.global.clusterDomain }}/v1
{{- end -}}
