{{/*
Expand the name of the chart.
*/}}
{{- define "agentic-claims-demo.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "agentic-claims-demo.fullname" -}}
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
{{- define "agentic-claims-demo.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "agentic-claims-demo.labels" -}}
helm.sh/chart: {{ include "agentic-claims-demo.chart" . }}
{{ include "agentic-claims-demo.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "agentic-claims-demo.selectorLabels" -}}
app.kubernetes.io/name: {{ include "agentic-claims-demo.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Get cluster domain
*/}}
{{- define "agentic-claims-demo.clusterDomain" -}}
{{- .Values.global.clusterDomain }}
{{- end }}

{{/*
Get namespace
*/}}
{{- define "agentic-claims-demo.namespace" -}}
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

{{/*
Get image registry
*/}}
{{- define "agentic-claims-demo.imageRegistry" -}}
{{- .Values.global.imageRegistry }}
{{- end }}

{{/*
Build full image name
*/}}
{{- define "agentic-claims-demo.image" -}}
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
http://llamastack-rhoai-service.{{ include "agentic-claims-demo.namespace" . }}.svc.cluster.local:8321
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
