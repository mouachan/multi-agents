import { useCallback, useEffect, useRef, useState } from 'react'
import { orchestratorApi } from '../services/orchestratorService'
import type { ChatMessage, ChatResponse, ChatSession } from '../types/chat'

interface UseChatReturn {
  session: ChatSession | null
  messages: ChatMessage[]
  isLoading: boolean
  isSending: boolean
  error: string | null
  sessionNotFound: boolean
  createSession: (agentId?: string) => Promise<void>
  sendMessage: (message: string) => Promise<ChatResponse | null>
  loadMessages: (sessionId: string) => Promise<void>
  // Prompt editor
  prompt: string | null
  isPromptCustom: boolean
  isPromptLoading: boolean
  loadPrompt: () => Promise<void>
  savePrompt: (text: string) => Promise<boolean>
  resetPrompt: () => Promise<boolean>
}

export function useChat(initialSessionId?: string): UseChatReturn {
  const [session, setSession] = useState<ChatSession | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sessionNotFound, setSessionNotFound] = useState(false)
  const creatingRef = useRef(false)

  // Prompt editor state
  const [prompt, setPrompt] = useState<string | null>(null)
  const [isPromptCustom, setIsPromptCustom] = useState(false)
  const [isPromptLoading, setIsPromptLoading] = useState(false)

  const getSessionId = useCallback(() => {
    return session?.session_id || initialSessionId
  }, [session, initialSessionId])

  const createSession = useCallback(async (agentId?: string) => {
    if (creatingRef.current) return
    creatingRef.current = true
    setIsLoading(true)
    setError(null)
    try {
      const newSession = await orchestratorApi.createSession(agentId)
      setSession(newSession)
      // Load initial messages (welcome message)
      const result = await orchestratorApi.getMessages(newSession.session_id)
      setMessages(result.messages)
    } catch (err: any) {
      setError(err.message || 'Failed to create session')
    } finally {
      setIsLoading(false)
      creatingRef.current = false
    }
  }, [])

  const loadMessages = useCallback(async (sessionId: string) => {
    setIsLoading(true)
    try {
      const result = await orchestratorApi.getMessages(sessionId)
      setMessages(result.messages)
      setSessionNotFound(false)
    } catch (err: any) {
      if (err.response?.status === 404) {
        setSessionNotFound(true)
      } else {
        setError(err.message || 'Failed to load messages')
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  const sendMessage = useCallback(async (message: string): Promise<ChatResponse | null> => {
    if (!session) return null

    // Optimistically add user message
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, tempUserMsg])

    setIsSending(true)
    setError(null)
    try {
      const startTime = Date.now()
      const response = await orchestratorApi.sendMessage(
        session.session_id,
        message
      )
      const processingTimeMs = Date.now() - startTime

      // Add assistant response
      const assistantMsg: ChatMessage = {
        id: `resp-${Date.now()}`,
        role: 'assistant',
        content: response.message,
        agent_id: response.agent_id || undefined,
        suggested_actions: response.suggested_actions,
        tool_calls: response.tool_calls,
        token_usage: response.token_usage,
        processing_time_ms: processingTimeMs,
        model_id: response.model_id || undefined,
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, assistantMsg])

      return response
    } catch (err: any) {
      setError(err.message || 'Failed to send message')
      // Remove optimistic message on error
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMsg.id))
      return null
    } finally {
      setIsSending(false)
    }
  }, [session])

  // Prompt editor actions (lazy loading)
  const loadPrompt = useCallback(async () => {
    const sid = getSessionId()
    if (!sid) return
    setIsPromptLoading(true)
    try {
      const result = await orchestratorApi.getSessionPrompt(sid)
      setPrompt(result.prompt)
      setIsPromptCustom(result.is_custom)
    } catch (err: any) {
      setError(err.message || 'Failed to load prompt')
    } finally {
      setIsPromptLoading(false)
    }
  }, [getSessionId])

  const savePrompt = useCallback(async (text: string): Promise<boolean> => {
    const sid = getSessionId()
    if (!sid) return false
    try {
      const result = await orchestratorApi.setSessionPrompt(sid, text)
      setPrompt(result.prompt)
      setIsPromptCustom(result.is_custom)
      return true
    } catch (err: any) {
      setError(err.message || 'Failed to save prompt')
      return false
    }
  }, [getSessionId])

  const resetPrompt = useCallback(async (): Promise<boolean> => {
    const sid = getSessionId()
    if (!sid) return false
    try {
      const result = await orchestratorApi.resetSessionPrompt(sid)
      setPrompt(result.prompt)
      setIsPromptCustom(result.is_custom)
      return true
    } catch (err: any) {
      setError(err.message || 'Failed to reset prompt')
      return false
    }
  }, [getSessionId])

  // Auto-load messages if initial session ID provided
  useEffect(() => {
    if (initialSessionId) {
      loadMessages(initialSessionId)
    }
  }, [initialSessionId, loadMessages])

  return {
    session,
    messages,
    isLoading,
    isSending,
    error,
    sessionNotFound,
    createSession,
    sendMessage,
    loadMessages,
    // Prompt editor
    prompt,
    isPromptCustom,
    isPromptLoading,
    loadPrompt,
    savePrompt,
    resetPrompt,
  }
}
