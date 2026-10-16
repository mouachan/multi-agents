/**
 * The backend API (/api/v1), one object per area — mirrors backend/app/api/:
 *   casesApi(domain)  the cases of a business domain        api/domains.py
 *   reviewApi         human review                          api/review.py
 *   chatApi           conversations with the agents         api/chat.py
 *   adminApi          administration                        api/admin.py
 *   sandboxApi        the OpenShell sandbox page            api/sandbox.py
 */
import { http } from './http'
import type { Case, Decision, Domain, PersonalDataFinding, Statistics, TrackingEvent } from '../types/case'
import type { InboxItem, JournalEntry, ReviewBrief } from '../types/review'
import type { AgentInfo, ChatMessage, ChatSession, PromptResponse, StreamEvent } from '../types/chat'
import type { SandboxDemoResult, SandboxInfo, SandboxScenario } from '../types/sandbox'

export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

// ------------------------------------------------------------------------------------------ cases

export const casesApi = (domain: Domain) => ({
  list: async (): Promise<Case[]> => (await http.get(`/${domain}/`)).data.items,
  get: async (id: string): Promise<Case> => (await http.get(`/${domain}/${id}`)).data,
  statistics: async (): Promise<Statistics> => (await http.get(`/${domain}/statistics`)).data,
  /** starts the processing by the agent; the case page polls the case until it is done */
  process: async (id: string) => (await http.post(`/${domain}/${id}/process`)).data,
  /** the current decision, or null before the first processing */
  decision: async (id: string): Promise<Decision | null> =>
    http.get(`/${domain}/${id}/decision`).then((r) => r.data, (e) => (e?.response?.status === 404 ? null : Promise.reject(e))),
  documentUrl: (id: string, lang: string) => `${API_BASE_URL}/${domain}/${id}/document?lang=${lang}`,
  // routes of a single domain
  tracking: async (id: string): Promise<TrackingEvent[]> => (await http.get(`/${domain}/${id}/tracking`)).data,
  personalData: async (id: string): Promise<PersonalDataFinding[]> => (await http.get(`/${domain}/${id}/personal-data`)).data,
})

// ----------------------------------------------------------------------------------------- review

export const reviewApi = {
  inbox: async (): Promise<InboxItem[]> => (await http.get('/review/inbox')).data,
  brief: async (domain: Domain, id: string): Promise<ReviewBrief> => (await http.get(`/review/${domain}/${id}`)).data,
  ask: async (domain: Domain, id: string, question: string, language: string): Promise<JournalEntry> =>
    (await http.post(`/review/${domain}/${id}/questions`, { question, language })).data,
  decide: async (domain: Domain, id: string, decision: string, justification: string): Promise<Decision> =>
    (await http.post(`/review/${domain}/${id}/decision`, { decision, justification })).data,
}

// ------------------------------------------------------------------------------------------- chat

export const chatApi = {
  agents: async (): Promise<AgentInfo[]> => (await http.get('/chat/agents')).data,
  toolDisplay: async () => (await http.get('/chat/tool-display')).data,
  createSession: async (agentId?: string, locale?: string): Promise<ChatSession> =>
    (await http.post('/chat/sessions', { agent_id: agentId || null, locale: locale || 'fr' })).data,
  listSessions: async (): Promise<ChatSession[]> => (await http.get('/chat/sessions')).data,
  messages: async (sessionId: string): Promise<ChatMessage[]> => (await http.get(`/chat/sessions/${sessionId}/messages`)).data,
  deleteSession: async (sessionId: string) => http.delete(`/chat/sessions/${sessionId}`),
  deleteAllSessions: async () => http.delete('/chat/sessions'),
  getPrompt: async (sessionId: string): Promise<PromptResponse> => (await http.get(`/chat/sessions/${sessionId}/prompt`)).data,
  setPrompt: async (sessionId: string, prompt: string): Promise<PromptResponse> =>
    (await http.put(`/chat/sessions/${sessionId}/prompt`, { prompt })).data,
  resetPrompt: async (sessionId: string): Promise<PromptResponse> => (await http.delete(`/chat/sessions/${sessionId}/prompt`)).data,

  /**
   * Send a message; the answer streams as server-sent events, each handed to `onEvent`
   * (contract: backend/app/services/chat/turn.py). Aborting `signal` stops the stream.
   */
  streamMessage: async (sessionId: string, message: string, onEvent: (event: StreamEvent) => void, signal: AbortSignal) => {
    const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
      body: JSON.stringify({ message }),
      signal,
    })
    if (response.status === 401) window.location.reload()   // session expired: back to the login
    if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`)

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    try {
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        for (const line of lines.map((l) => l.trim()).filter((l) => l.startsWith('data:'))) {
          try {
            onEvent(JSON.parse(line.slice(5)) as StreamEvent)
          } catch {
            // a malformed line is skipped
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') throw err
    }
  },
}

// ---------------------------------------------------------------------------------- administration

/** Access profile = OpenShift group; its rights are OpenShift RBAC (agents and their MCP tools). */
export interface AccessProfile {
  id: string
  displayName: string
  group: string
  agents: string[]
  admin: boolean
  exists: boolean
}

export interface ManagedUser {
  username: string
  fullName?: string | null
  profiles: string[]
}

export interface Overview {
  domains: { domain: Domain; by_status: Record<string, number>; documents: number; documents_with_embedding: number }[]
  references: Record<string, { rows: number; with_embedding: number }>
}

/** An evaluation of the agents' decisions on the precedents (admin page). */
export interface Evaluation {
  prompt_alias: string
  started_at: string
  status: 'running' | 'completed' | 'failed'
  total: number
  done: number
  results: { domain: Domain; number: string; expected: string; decision?: string | null; confidence?: number | null; correct?: boolean | null; error?: string | null }[]
  metrics: Record<string, number>
  prompts: Record<string, string>
  mlflow_url?: string | null
  error?: string | null
}

export const adminApi = {
  overview: async (): Promise<Overview> => (await http.get('/admin/overview')).data,
  evaluation: async (): Promise<Evaluation | null> => (await http.get('/admin/evaluations/current')).data,
  evaluate: async (promptAlias: string): Promise<Evaluation> => (await http.post('/admin/evaluations', { prompt_alias: promptAlias })).data,
  reset: async () => (await http.post('/admin/reset')).data,
  users: async (): Promise<{ profiles: AccessProfile[]; users: ManagedUser[] }> => (await http.get('/admin/users')).data,
  setProfiles: async (username: string, profiles: string[]): Promise<ManagedUser> =>
    (await http.put(`/admin/users/${encodeURIComponent(username)}/profiles`, { profiles })).data,
}

// -------------------------------------------------------------------------------------------- sandbox

export const sandboxApi = {
  info: async (): Promise<SandboxInfo> => (await http.get('/sandbox/policy')).data,
  demo: async (scenario: SandboxScenario): Promise<SandboxDemoResult> => (await http.post(`/sandbox/demo/${scenario}`)).data,
}
