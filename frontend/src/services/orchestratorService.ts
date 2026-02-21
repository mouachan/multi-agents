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

  // List available agents
  getAgents: async (): Promise<AgentInfo[]> => {
    const response = await apiClient.get('/agents')
    return response.data
  },
}
