{{- /*
README sections of the AI hub catalog entries generated from the chart values, so they follow the
deployment (endpoints, profiles, tools, images). The domain part of each README is a markdown file
in files/catalog/{mcp,agents}/<name>.md.
*/ -}}

{{- /* Display names of the access profiles that may use one of the given agents ("All users" without authentication) */ -}}
{{- define "multi-agents.catalog.profilesFor" -}}
{{- $root := .root -}}
{{- if not $root.Values.auth.enabled -}}
All users (authentication disabled)
{{- else -}}
{{- $names := list -}}
{{- range $id, $p := $root.Values.auth.profiles -}}
{{- range $a := $p.agents -}}
{{- if has $a $.agents -}}{{- $names = append $names $p.displayName -}}{{- end -}}
{{- end -}}
{{- end -}}
{{- $names | uniq | sortAlpha | join ", " | default "none" -}}
{{- end -}}
{{- end -}}

{{- /* Agents (of auth.agentTools) granted a tool */ -}}
{{- define "multi-agents.catalog.agentsWithTool" -}}
{{- $agents := list -}}
{{- range $agent, $tools := .root.Values.auth.agentTools -}}
{{- if has $.tool $tools -}}{{- $agents = append $agents $agent -}}{{- end -}}
{{- end -}}
{{- $agents | toJson -}}
{{- end -}}

{{- define "multi-agents.catalog.access" -}}
{{- if eq . "read_only" }}read only{{ else if eq . "read_write" }}read / write{{ else }}{{ . }}{{ end -}}
{{- end -}}

{{- define "multi-agents.catalog.license" -}}
## License
[{{ .Values.rhoaiCatalog.license.name }}]({{ .Values.rhoaiCatalog.license.link }})
{{- end -}}

{{- /* MCP server README: tools, endpoints, governance, security, license.
       Context: root, name, tools (from files/catalog/mcp-tools.yaml), readOnly, image */ -}}
{{- define "multi-agents.catalog.mcpReadme" -}}
{{- $root := .root -}}
{{- $ns := include "multi-agents.namespace" $root -}}
{{- $secured := and $root.Values.auth.enabled $root.Values.mcpGateway.enabled -}}
## Tools
| Tool | Access | Profiles |
|---|---|---|
{{- range .tools }}
{{- $agents := include "multi-agents.catalog.agentsWithTool" (dict "root" $root "tool" .name) | fromJsonArray }}
| `{{ .name }}` | {{ include "multi-agents.catalog.access" .accessType }} | {{ if $agents }}{{ include "multi-agents.catalog.profilesFor" (dict "root" $root "agents" $agents) }}{{ else }}not granted{{ end }} |
{{- end }}

## Endpoints
{{- if $root.Values.mcpGateway.enabled }}
- **MCP Gateway** (used by the agents): `{{ include "multi-agents.mcpGateway.url" $root }}`, the tools of every server federated in one endpoint
{{- end }}
- **In-cluster:** `http://{{ .name }}-server.{{ $ns }}.svc.cluster.local:8080/mcp` (Streamable HTTP), `/sse` (SSE), `/health`
- **Image:** `{{ .image }}`

## Deploy from the AI hub
*Deploy MCP server* runs another instance of this server (an `MCPServer`, run by the MCP lifecycle
operator). Deploy it in the platform namespace `{{ $ns }}`, under a new name (e.g. `{{ .name }}-catalog`).
The YAML of the form leaves the configuration as `<NAME>` placeholders: replace them with these values.
{{- $runtime := include "multi-agents.catalog.mcpRuntimeMetadata" (dict "root" $root "name" .name "cfg" .cfg) | fromJson }}

| Variable | Value |
|---|---|
{{- range $runtime.requiredEnvironmentVariables }}
| `{{ .name }}` | `{{ .defaultValue }}` |
{{- end }}

The credentials come from the platform's secrets, already referenced:
{{- range $runtime.prerequisites.secrets }} `{{ .name }}`{{ end }}.

## Governance
{{- if $secured }}
Each tool call through the MCP Gateway carries the OpenShift token of the user who asked the agent.
The gateway (Kuadrant AuthPolicy `mcp-tools-rbac`) checks it with a TokenReview, then asks OpenShift
with a SubjectAccessReview whether this user may `call` the tool (resource
`tools.mcp.multi-agents.io/<tool>`). The permission comes from the Role `agent-<agent>` of each agent,
bound to the groups of the access profiles: the *Profiles* column above.
{{- else }}
Authentication is disabled in this deployment: the tools are not filtered per user.
{{- end }}

## Security
- **Verified source:** built from the project sources (see *Source code*), image published in the project registry
- **Secure endpoint:** {{ if $secured }}reachable inside the cluster only, authorized per user and per tool by the MCP Gateway{{ else }}reachable inside the cluster only (no per-user authorization in this deployment){{ end }}
- **SAST:** Bandit (Python static analysis): no high or medium severity finding, apart from B104 (listening on all interfaces, required in a container)
- **Read-only tools:** {{ if .readOnly }}yes, no tool modifies data{{ else }}no, see the *Access* column{{ end }}

{{ include "multi-agents.catalog.license" $root }}
{{- end -}}

{{- /* Agent README: skills, how it works, security and governance, license.
       Context: root, name, agent (rhoaiCatalog.agents entry), tools (MCP tools by server) */ -}}
{{- define "multi-agents.catalog.agentReadme" -}}
{{- $root := .root -}}
{{- $ns := include "multi-agents.namespace" $root -}}
{{- $cfg := index $root.Values.agents .name -}}
{{- $model := $cfg.model | default $root.Values.models.reasoning -}}
## Skills
{{ range .agent.skills }}`{{ . }}` {{ end }}

## How it works
- **Protocol:** A2A (a2a-sdk), JSON-RPC with SSE streaming on port 8090 — agent card `http://{{ .name }}-agent.{{ $ns }}.svc.cluster.local:8090/.well-known/agent-card.json`
- **Model:** `{{ $model }}` through Models-as-a-Service, with the OGX Responses API; prompts versioned in MLflow
- **Traceability:** each chat turn is one MLflow trace (orchestrator → A2A → agent → LLM and tool spans), also stored with the conversation
{{- with index $root.Values.auth.agentTools .name }}

## MCP tools
Called through the MCP Gateway:

| Tool | MCP server |
|---|---|
{{- range $tool := . }}
| `{{ $tool }}` | {{ index $.tools $tool | default "—" }} |
{{- end }}
{{- end }}

## Security and governance
{{- if $root.Values.spiffe.enabled }}
- **Workload identity:** callers present a SPIFFE JWT-SVID (audience `a2a:{{ .name }}-agent`), validated by the agent
{{- end }}
- **Access profiles:** {{ include "multi-agents.catalog.profilesFor" (dict "root" $root "agents" (list .name)) }}{{ if $root.Values.auth.enabled }} — OpenShift Role `agent-{{ .name }}` (verb `use` on the agent, `call` on its MCP tools) bound to the profile groups{{ end }}
{{- if $root.Values.auth.enabled }}
- **Per-user tools:** the OpenShift token of the user is forwarded with the request, so the MCP Gateway authorizes every tool call for that user
{{- end }}

{{ include "multi-agents.catalog.license" $root }}
{{- end -}}
