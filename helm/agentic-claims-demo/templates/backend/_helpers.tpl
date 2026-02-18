{{/* route prefix */}}
{{- define "backend_route_prefix_full" -}}
backend-{{ .Values.global.namespace }}
{{- end -}}

{{/* truncated route prefix, complying with 63 chars limit */}}
{{- define "backend_route_prefix" -}}
{{- include "backend_route_prefix_full" . | trunc 63 -}}
{{- end -}}
