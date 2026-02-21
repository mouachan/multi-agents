import axios from 'axios'
import type {
  AgentInfo,
  ChatMessage,
  ChatResponse,
  ChatSession,
  PromptResponse,
} from '../types/chat'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 300000, // 5 minutes for LLM + MCP tool calling
})

export const orchestratorApi = {
  // Create a new chat session
  createSession: async (agentId?: string, locale?: string): Promise<ChatSession> => {
    const response = await apiClient.post('/orchestrator/sessions', {
      agent_id: agentId || null,
      locale: locale || navigator.language || 'fr',
    })
    return response.data
  },

  // Send a message in a session
  sendMessage: async (
    sessionId: string,
    message: string
  ): Promise<ChatResponse> => {
    const response = await apiClient.post('/orchestrator/chat', {
      session_id: sessionId,
      message,
    })
    return response.data
  },

  // Get session message history
  getMessages: async (
    sessionId: string
  ): Promise<{ session_id: string; messages: ChatMessage[]; total: number }> => {
    const response = await apiClient.get(
      `/orchestrator/sessions/${sessionId}/messages`
    )
    return response.data
  },

  // List sessions
  listSessions: async (): Promise<{ sessions: ChatSession[]; total: number }> => {
    const response = await apiClient.get('/orchestrator/sessions')
    return response.data
  },

  // Delete a session
  deleteSession: async (sessionId: string): Promise<void> => {
    await apiClient.delete(`/orchestrator/sessions/${sessionId}`)
  },

  // Delete all sessions
  deleteAllSessions: async (): Promise<{ count: number }> => {
    const response = await apiClient.delete('/orchestrator/sessions')
    return response.data
  },

  // Get the effective prompt for a session
  getSessionPrompt: async (sessionId: string): Promise<PromptResponse> => {
    const response = await apiClient.get(
      `/orchestrator/sessions/${sessionId}/prompt`
    )
    return response.data
  },

  // Set a custom prompt for a session
  setSessionPrompt: async (
    sessionId: string,
    customPrompt: string
  ): Promise<PromptResponse> => {
    const response = await apiClient.put(
      `/orchestrator/sessions/${sessionId}/prompt`,
      { custom_prompt: customPrompt }
    )
    return response.data
  },

  // Reset session prompt to default
  resetSessionPrompt: async (sessionId: string): Promise<PromptResponse> => {
    const response = await apiClient.delete(
      `/orchestrator/sessions/${sessionId}/prompt`
    )
    return response.data
  },

  // Send a message with SSE streaming
  sendMessageStream: (
    sessionId: string,
    message: string,
    callbacks: {
      onTextDelta?: (delta: string) => void
      onTextReplace?: (text: string) => void
      onToolCall?: (info: { name: string; server: string }) => void
      onToolResult?: (info: { name: string; status: string }) => void
      onAgentResolved?: (agentId: string) => void
      onDone?: (response: ChatResponse) => void
      onError?: (error: string) => void
    }
  ): { cancel: () => void } => {
    const controller = new AbortController()

    const run = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/orchestrator/chat/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId, message }),
          signal: controller.signal,
        })

        if (!response.ok || !response.body) {
          callbacks.onError?.(`HTTP ${response.status}`)
          return
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // Process complete SSE lines
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            const trimmed = line.trim()
            if (!trimmed || !trimmed.startsWith('data: ')) continue

            try {
              const event = JSON.parse(trimmed.slice(6))

              switch (event.type) {
                case 'text_delta':
                  callbacks.onTextDelta?.(event.delta)
                  break
                case 'text_replace':
                  callbacks.onTextReplace?.(event.text)
                  break
                case 'tool_call':
                  callbacks.onToolCall?.({ name: event.name, server: event.server })
                  break
                case 'tool_result':
                  callbacks.onToolResult?.({ name: event.name, status: event.status })
                  break
                case 'agent_resolved':
                  callbacks.onAgentResolved?.(event.agent_id)
                  break
                case 'done':
                  callbacks.onDone?.({
                    session_id: sessionId,
                    intent: 'agent_request',
                    agent_id: event.agent_id,
                    message: '',  // text was already streamed via deltas
                    suggested_actions: event.suggested_actions || [],
                    tool_calls: event.tool_calls,
                    token_usage: event.usage,
                    model_id: event.model_id,
                  })
                  break
                case 'error':
                  callbacks.onError?.(event.message)
                  break
              }
            } catch {
              // Skip malformed JSON lines
            }
          }
        }
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          callbacks.onError?.(err.message || 'Stream failed')
        }
      }
    }

    run()
    return { cancel: () => controller.abort() }
  },

  // List available agents
  getAgents: async (): Promise<AgentInfo[]> => {
    const response = await apiClient.get('/agents')
    return response.data
  },
}
