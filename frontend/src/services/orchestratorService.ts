import { http } from './http'
import type {
  AgentInfo,
  ChatMessage,
  ChatResponse,
  ChatSession,
  PromptResponse,
  StreamEvent,
} from '../types/chat'

export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

export const orchestratorApi = {
  createSession: async (agentId?: string, locale?: string): Promise<ChatSession> => {
    const { data } = await http.post('/orchestrator/sessions', {
      agent_id: agentId || null,
      locale: locale || navigator.language || 'fr',
    })
    return data
  },

  sendMessage: async (sessionId: string, message: string): Promise<ChatResponse> => {
    const { data } = await http.post('/orchestrator/chat', { session_id: sessionId, message })
    return data
  },

  getMessages: async (sessionId: string): Promise<{ session_id: string; messages: ChatMessage[]; total: number }> => {
    const { data } = await http.get(`/orchestrator/sessions/${sessionId}/messages`)
    return data
  },

  listSessions: async (): Promise<{ sessions: ChatSession[]; total: number }> => {
    const { data } = await http.get('/orchestrator/sessions')
    return data
  },

  deleteSession: async (sessionId: string): Promise<void> => {
    await http.delete(`/orchestrator/sessions/${sessionId}`)
  },

  deleteAllSessions: async (): Promise<{ count: number }> => {
    const { data } = await http.delete('/orchestrator/sessions')
    return data
  },

  getSessionPrompt: async (sessionId: string): Promise<PromptResponse> => {
    const { data } = await http.get(`/orchestrator/sessions/${sessionId}/prompt`)
    return data
  },

  setSessionPrompt: async (sessionId: string, customPrompt: string): Promise<PromptResponse> => {
    const { data } = await http.put(`/orchestrator/sessions/${sessionId}/prompt`, { custom_prompt: customPrompt })
    return data
  },

  resetSessionPrompt: async (sessionId: string): Promise<PromptResponse> => {
    const { data } = await http.delete(`/orchestrator/sessions/${sessionId}/prompt`)
    return data
  },

  getAgents: async (): Promise<AgentInfo[]> => {
    const { data } = await http.get('/agents')
    return data
  },

  /**
   * Stream a chat turn (SSE over fetch). Every `data:` line is parsed and handed to
   * `onEvent`; aborting `signal` stops the stream (the promise then resolves).
   */
  streamMessage: async (
    sessionId: string,
    message: string,
    onEvent: (event: StreamEvent) => void,
    signal: AbortSignal,
  ): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/orchestrator/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
      body: JSON.stringify({ session_id: sessionId, message }),
      signal,
    })
    if (!response.ok || !response.body) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed.startsWith('data:')) continue
          try {
            onEvent(JSON.parse(trimmed.slice(5).trim()) as StreamEvent)
          } catch {
            // ignore malformed lines
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') throw err
    }
  },
}
