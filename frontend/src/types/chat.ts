// Type definitions for Chat / Orchestrator

export interface ChatSession {
  session_id: string
  id: string
  agent_id?: string
  status: string
  welcome_message?: string
  created_at?: string
  updated_at?: string
  last_message?: string
}

export interface SuggestedAction {
  label: string
  action: string
  params?: Record<string, any>
}

export interface ToolCallInfo {
  name: string
  status: string
  server_label?: string
  output?: string
  error?: string
}

export interface ToolDisplayMeta {
  label: Record<string, string>
  short: string
  category: string
}

export interface ToolDisplayConfig {
  tools: Record<string, ToolDisplayMeta>
  servers: Record<string, { label: string; color: string }>
  categories: Record<string, { label: Record<string, string>; icon: string }>
}

export interface TokenUsage {
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  agent_id?: string
  entity_id?: string
  entity_type?: string
  suggested_actions?: SuggestedAction[]
  tool_calls?: ToolCallInfo[]
  token_usage?: TokenUsage
  processing_time_ms?: number
  model_id?: string
  created_at?: string
  /** Live A2A / orchestration trace of this assistant turn (streamed turns only) */
  trace?: TurnTrace
  /** True while the turn is streaming */
  streaming?: boolean
  /** Turn stopped by the user */
  stopped?: boolean
  /** Turn failed */
  error?: string
}

export interface ChatResponse {
  session_id: string
  intent: string
  agent_id?: string
  message: string
  suggested_actions: SuggestedAction[]
  entity_reference?: {
    type: string
    id: string
  }
  tool_calls?: ToolCallInfo[]
  token_usage?: TokenUsage
  model_id?: string
}

export interface PromptResponse {
  prompt: string
  is_custom: boolean
  agent_id?: string
}

export interface AgentInfo {
  id: string
  name: string
  name_fr?: string
  description: string
  description_fr?: string
  entity_type: string
  path: string
  api_prefix: string
  color: string
  icon: string
  tools: string[]
  decision_values: string[]
}

// ---------------------------------------------------------------------------
// SSE stream contract — POST /api/v1/orchestrator/chat/stream
// ---------------------------------------------------------------------------

export type RoutingMethod = 'semantic' | 'llm' | 'sticky' | 'keywords'

export interface RoutingEvent {
  type: 'routing'
  agent_id: string
  method: RoutingMethod
  score: number | null
  candidates: { agent_id: string; score: number }[]
  duration_ms: number
}

export interface A2AAgentCard {
  name: string
  description?: string
  version?: string
  url?: string
  skills?: string[]
}

export interface A2ARequestEvent {
  type: 'a2a'
  phase: 'request'
  method?: string
  agent: A2AAgentCard
  auth: { scheme: string; audience?: string | null }
  profile?: string
  mode?: string
  context_id?: string
  message_id?: string
}

export type A2ATaskState = 'submitted' | 'working' | 'completed' | 'failed' | 'rejected' | 'canceled' | string

export interface A2AStatusEvent {
  type: 'a2a'
  phase: 'status'
  state: A2ATaskState
  task_id?: string
  context_id?: string
  elapsed_ms?: number
}

export type GuardrailStatus = 'passed' | 'modified' | 'blocked' | 'skipped' | 'error' | string

export interface GuardrailsEvent {
  type: 'guardrails'
  stage: 'input' | 'output' | string
  status: GuardrailStatus
  rail?: string | null
}

export interface ToolEvent {
  type: 'tool_call' | 'tool_result'
  name: string
  server?: string
  status?: string
}

export interface DoneA2ASummary {
  task_id?: string
  context_id?: string
  state?: string
  duration_ms?: number
  agent_duration_ms?: number
  caller?: string | null
  agent?: string
  status?: string
  prompt?: { name?: string; version?: string | number | null; source?: string }
  guardrails?: { input?: { status?: string; rail?: string | null }; output?: { status?: string; rail?: string | null } }
}

export interface DoneEvent {
  type: 'done'
  response_id?: string | null
  usage?: TokenUsage | null
  tool_calls?: ToolCallInfo[]
  agent_id?: string
  model_id?: string | null
  suggested_actions?: SuggestedAction[]
  a2a?: DoneA2ASummary | null
}

export type StreamEvent =
  | RoutingEvent
  | { type: 'agent_resolved'; agent_id: string }
  | A2ARequestEvent
  | A2AStatusEvent
  | GuardrailsEvent
  | ToolEvent
  | { type: 'text_delta'; delta: string }
  | { type: 'text_replace'; text: string }
  | { type: 'heartbeat'; elapsed_ms: number }
  | DoneEvent
  | { type: 'error'; message: string }

/** One entry of the per-turn timeline shown in the A2A panel */
export type TraceStep =
  | { kind: 'routing'; at: number; event: RoutingEvent }
  | { kind: 'request'; at: number; event: A2ARequestEvent }
  | { kind: 'state'; at: number; state: A2ATaskState; elapsedMs?: number; taskId?: string }
  | { kind: 'guardrails'; at: number; event: GuardrailsEvent }
  | { kind: 'tool'; at: number; name: string; server?: string; status: 'running' | 'completed' | 'error' | string; doneAt?: number }

export interface TurnTrace {
  startedAt: number
  /** ms since start of the first streamed text */
  firstTextAt?: number
  lastHeartbeatMs?: number
  agentId?: string
  routing?: RoutingEvent
  request?: A2ARequestEvent
  taskId?: string
  contextId?: string
  state?: A2ATaskState
  steps: TraceStep[]
  summary?: DoneA2ASummary | null
  modelId?: string | null
  usage?: TokenUsage | null
  finishedAt?: number
}
