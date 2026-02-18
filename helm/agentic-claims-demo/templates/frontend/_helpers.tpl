{{/* route prefix */}}
{{- define "frontend_route_prefix_full" -}}
frontend-{{ .Values.global.namespace }}
{{- end -}}

{{/* truncated route prefix, complying with 63 chars limit */}}
{{- define "frontend_route_prefix" -}}
{{- include "frontend_route_prefix_full" . | trunc 63 -}}
{{- end -}}
