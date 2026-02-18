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
}

export function useChat(initialSessionId?: string): UseChatReturn {
  const [session, setSession] = useState<ChatSession | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sessionNotFound, setSessionNotFound] = useState(false)
  const creatingRef = useRef(false)

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
      const response = await orchestratorApi.sendMessage(
        session.session_id,
        message
      )

      // Add assistant response
      const assistantMsg: ChatMessage = {
        id: `resp-${Date.now()}`,
        role: 'assistant',
        content: response.message,
        agent_id: response.agent_id || undefined,
        suggested_actions: response.suggested_actions,
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
  }
}
