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

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  agent_id?: string
  entity_id?: string
  entity_type?: string
  suggested_actions?: SuggestedAction[]
  created_at?: string
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
}

export interface AgentInfo {
  id: string
  name: string
  description: string
  entity_type: string
  path: string
  api_prefix: string
  color: string
  icon: string
  tools: string[]
  decision_values: string[]
}
