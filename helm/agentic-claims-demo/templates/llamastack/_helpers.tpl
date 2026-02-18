{{/* WARNING: valueFrom secrets isn't CIS compliant */}}
{{/* should export env vars from a script within container, as done with postgres */}}
{{- define "llamastack.env" -}}
{{- include "postgres.env" . }}
- name: EMBEDDING_MODEL
  value: {{ quote .Values.embedding.model.name }}
- name: GEMMA_TLS_VERIFY
  # I guess that one's welcome, in a context where InferenceServices is exposed behind a Route
  # knowing we have our own PKI ...
  # however it is not acceptable going prod.
- name: GEMMA_URL
{{- if .Values.llamastack.embedding.endpoint }}
  value: {{ .Values.llamastack.embedding.endpoint | replace "CLUSTER_DOMAIN" .Values.global.clusterDomain }}
{{- else }}
{{- if eq (include "agentic-claims-demo.namespace" .) (include "embedding.namespace" .) }}
  # value: http://gemma-predictor:8080/v1
  value: http://gemma-predictor/v1
{{- else }}
  value: https://gemma-{{ include "embedding.namespace" . }}.{{ .Values.global.clusterDomain }}/v1
{{- end }}
{{- end }}
- name: INFERENCE_MODEL
  value: {{ quote .Values.inference.model.name }}
- name: VLLM_TLS_VERIFY
  # I guess that one's welcome, in a context where InferenceServices is exposed behind a Route
  # knowing we have our own PKI ...
  # however it is not acceptable going prod.
  value: 'false'
- name: VLLM_URL
{{- if .Values.llamastack.model.endpoint }}
  value: {{ .Values.llamastack.model.endpoint | replace "CLUSTER_DOMAIN" .Values.global.clusterDomain }}
{{- else }}
{{- if eq (include "agentic-claims-demo.namespace" .) (include "inference.namespace" .) }}
  # WARNING, port 80 works ONLY IF DataScienceCluster was deployed with .spec.components.kserve.rawDeploymentServiceConfig == Headed
  # Usully/everywhere I looked, it comes with Headless. Then, the frontend port for that Service (80) is not used. Service resolves
  # to Pod addresses, where you won't get port redirection => go with :8080 then.
  # I think we have a RH case about that?
  # value: http://llama-predictor:8080/v1
  # in our case:
  value: http://llama-predictor/v1
{{- else }}
  value: https://llama-{{ include "inference.namespace" . }}.{{ .Values.global.clusterDomain }}/v1
{{- end }}
{{- end }}
{{- end }}
{{/* also considered:
        # docs don't say where that FMS_ORCHESTRATOR_URL came from
        # "orchestrator" => most likely related to GuardRailsOrchestrator?
        # for now, we didn't plan on enabling Guardrails/we're told to hold on until it works with that demo?
        # - name: FMS_ORCHESTRATOR_URL
        #   value: '${FMS_ORCHESTRATOR_URL}'
        # What is FAISS?!
        # google says "Facebook AI Similarity Search"
        # oc -n ai-poc-agentic-claims-demo-dev-ats-openpaas-cc exec -it llamastack-rhoai-8 -- cat run.yaml
        # shows vector_io providers: milvus, and that faiss, only one
        # allowing for postgres coordinates?
        # but nooo ... that's not it. type=inline::faiss
        # the one in demo configmap has remote::pgvector ...
        # - name: FAISS_KVSTORE_DB
        #   # WARNING: not CIS compliant!
        #   valueFrom:
        #     secretKeyRef:
        #       name: {{ .Values.postgresql.auth.existingSecret }}
        #       key: POSTGRES_DATABASE
        # - name: FAISS_KVSTORE_PASSWORD
        #   # WARNING: not CIS compliant!
        #   valueFrom:
        #     secretKeyRef:
        #       name: {{ .Values.postgresql.auth.existingSecret }}
        #       key: POSTGRES_PASSWORD
        # - name: FAISS_KVSTORE_HOST
        #   value: postgresql
        # - name: FAISS_KVSTORE_PORT
        #   value: "5432"
        # - name: FAISS_KVSTORE_TYPE
        #   value: postgres
        # - name: FAISS_KVSTORE_USER
        #   # WARNING: not CIS compliant!
        #   valueFrom:
        #     secretKeyRef:
        #       name: {{ .Values.postgresql.auth.existingSecret }}
        #       key: POSTGRES_USER
/*}}

{{/* route prefix */}}
{{- define "llamastack_route_prefix_full" -}}
llamastack-rhoai-{{ .Values.global.namespace }}
{{- end -}}

{{/* truncated route prefix, complying with 63 chars limit */}}
{{- define "llamastack_route_prefix" -}}
{{- include "llamastack_route_prefix_full" . | trunc 63 -}}
{{- end -}}

{{/* Helper for inference endpoint URL */}}
{{- define "llamastack.inferenceEndpoint" -}}
{{- if .Values.llamastack.model.endpoint -}}
{{ .Values.llamastack.model.endpoint | replace "CLUSTER_DOMAIN" .Values.global.clusterDomain }}
{{- else -}}
{{- if eq (include "agentic-claims-demo.namespace" .) (include "inference.namespace" .) -}}
http://llama-predictor/v1
{{- else -}}
https://llama-{{ include "inference.namespace" . }}.{{ .Values.global.clusterDomain }}/v1
{{- end -}}
{{- end -}}
{{- end -}}

{{/* Helper for inference model name */}}
{{- define "llamastack.model" -}}
{{ .Values.inference.model.name }}
{{- end -}}

{{/* Helper for embedding endpoint URL */}}
{{- define "llamastack.embeddingEndpoint" -}}
{{- if .Values.llamastack.embedding.endpoint -}}
{{ .Values.llamastack.embedding.endpoint | replace "CLUSTER_DOMAIN" .Values.global.clusterDomain }}
{{- else -}}
{{- if eq (include "agentic-claims-demo.namespace" .) (include "embedding.namespace" .) -}}
http://gemma-predictor/v1
{{- else -}}
https://gemma-{{ include "embedding.namespace" . }}.{{ .Values.global.clusterDomain }}/v1
{{- end -}}
{{- end -}}
{{- end -}}

{{/* Helper for embedding model name */}}
{{- define "llamastack.embeddingModel" -}}
{{ .Values.embedding.model.name }}
{{- end -}}
