import { useCallback, useEffect, useRef, useState } from 'react'
import { orchestratorApi } from '../services/orchestratorService'
import { useTranslation } from '../i18n/LanguageContext'
import type { ChatMessage, StreamEvent, TraceStep, TurnTrace } from '../types/chat'

// ---------------------------------------------------------------------------
// Per-session cache of the A2A traces (history messages from the backend carry no
// trace): traces are attached back to assistant messages by their ordinal.
// ---------------------------------------------------------------------------
const TRACE_KEY = (sessionId: string) => `chat-traces-${sessionId}`

function loadTraces(sessionId: string): (TurnTrace | null)[] {
  try {
    return JSON.parse(sessionStorage.getItem(TRACE_KEY(sessionId)) || '[]')
  } catch {
    return []
  }
}

function saveTraces(sessionId: string, messages: ChatMessage[]) {
  const traces = messages.filter((m) => m.role === 'assistant').map((m) => m.trace ?? null)
  try {
    sessionStorage.setItem(TRACE_KEY(sessionId), JSON.stringify(traces))
  } catch {
    // storage full — traces are a convenience only
  }
}

function attachTraces(sessionId: string, messages: ChatMessage[]): ChatMessage[] {
  const traces = loadTraces(sessionId)
  let i = 0
  return messages.map((m) => {
    if (m.role !== 'assistant') return m
    const trace = traces[i++]
    return trace ? { ...m, trace } : m
  })
}

/** Apply one SSE event to the streaming assistant message. */
function applyEvent(msg: ChatMessage, event: StreamEvent): ChatMessage {
  const trace: TurnTrace = msg.trace ?? { startedAt: Date.now(), steps: [] }
  const at = Date.now() - trace.startedAt
  const steps: TraceStep[] = [...trace.steps]

  switch (event.type) {
    case 'routing':
      steps.push({ kind: 'routing', at, event })
      return { ...msg, agent_id: event.agent_id, trace: { ...trace, routing: event, agentId: event.agent_id, steps } }

    case 'agent_resolved':
      return { ...msg, agent_id: event.agent_id, trace: { ...trace, agentId: event.agent_id } }

    case 'a2a':
      if (event.phase === 'request') {
        steps.push({ kind: 'request', at, event })
        return { ...msg, trace: { ...trace, request: event, contextId: event.context_id, steps } }
      }
      if (event.state !== trace.state) {
        steps.push({ kind: 'state', at, state: event.state, elapsedMs: event.elapsed_ms, taskId: event.task_id })
      }
      return {
        ...msg,
        trace: {
          ...trace, steps, state: event.state,
          taskId: event.task_id || trace.taskId, contextId: event.context_id || trace.contextId,
        },
      }

    case 'guardrails':
      steps.push({ kind: 'guardrails', at, event })
      return { ...msg, trace: { ...trace, steps } }

    case 'tool_call': {
      steps.push({ kind: 'tool', at, name: event.name, server: event.server, status: 'running' })
      const tool_calls = [...(msg.tool_calls ?? []), { name: event.name, status: 'running', server_label: event.server }]
      return { ...msg, tool_calls, trace: { ...trace, steps } }
    }

    case 'tool_result': {
      const status = event.status === 'error' || event.status === 'failed' ? 'error' : 'completed'
      const details = { arguments: event.arguments, sandbox: event.sandbox, error: event.error }
      const idx = steps.findIndex((s) => s.kind === 'tool' && s.name === event.name && s.status === 'running')
      if (idx >= 0) {
        steps[idx] = { ...(steps[idx] as Extract<TraceStep, { kind: 'tool' }>), status, doneAt: at, ...details }
      } else {
        steps.push({ kind: 'tool', at, name: event.name, server: event.server, status, doneAt: at, ...details })
      }
      let updated = false
      const tool_calls = (msg.tool_calls ?? []).map((tc) => {
        if (!updated && tc.name === event.name && tc.status === 'running') {
          updated = true
          return { ...tc, status }
        }
        return tc
      })
      if (!updated) tool_calls.push({ name: event.name, status, server_label: event.server })
      return { ...msg, tool_calls, trace: { ...trace, steps } }
    }

    case 'text_delta':
      return {
        ...msg,
        content: msg.content + event.delta,
        trace: { ...trace, firstTextAt: trace.firstTextAt ?? at },
      }

    case 'text_replace':
      return { ...msg, content: event.text }

    case 'heartbeat':
      return { ...msg, trace: { ...trace, lastHeartbeatMs: event.elapsed_ms } }

    case 'done':
      return {
        ...msg,
        streaming: false,
        agent_id: event.agent_id || msg.agent_id,
        suggested_actions: event.suggested_actions ?? [],
        tool_calls: event.tool_calls?.length ? event.tool_calls : msg.tool_calls,
        token_usage: event.usage ?? undefined,
        model_id: event.model_id ?? undefined,
        processing_time_ms: at,
        trace: {
          ...trace, summary: event.a2a ?? null, modelId: event.model_id, usage: event.usage, finishedAt: at,
          state: event.a2a?.state || trace.state,
        },
      }

    case 'error':
      if (trace.state !== 'failed') steps.push({ kind: 'state', at, state: 'failed', taskId: trace.taskId })
      return { ...msg, streaming: false, error: event.message, trace: { ...trace, steps, state: 'failed', finishedAt: at } }

    default:
      return msg
  }
}

export interface UseChatReturn {
  messages: ChatMessage[]
  isLoading: boolean
  isSending: boolean
  error: string | null
  sessionNotFound: boolean
  /** session whose history is loaded (null while loading) */
  loadedSessionId: string | null
  createSession: (agentId?: string) => Promise<string | null>
  sendMessage: (text: string) => Promise<ChatMessage | null>
  stop: () => void
  reload: () => Promise<void>
  // System prompt editor
  prompt: string | null
  isPromptCustom: boolean
  isPromptLoading: boolean
  loadPrompt: () => Promise<void>
  savePrompt: (text: string) => Promise<boolean>
  resetPrompt: () => Promise<boolean>
}

export function useChat(sessionId?: string): UseChatReturn {
  const { locale } = useTranslation()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sessionNotFound, setSessionNotFound] = useState(false)
  const [loadedSessionId, setLoadedSessionId] = useState<string | null>(null)
  const controllerRef = useRef<AbortController | null>(null)

  const [prompt, setPrompt] = useState<string | null>(null)
  const [isPromptCustom, setIsPromptCustom] = useState(false)
  const [isPromptLoading, setIsPromptLoading] = useState(false)

  const reload = useCallback(async () => {
    if (!sessionId) return
    setIsLoading(true)
    setError(null)
    try {
      const result = await orchestratorApi.getMessages(sessionId)
      setMessages(attachTraces(sessionId, result.messages))
      setSessionNotFound(false)
      setLoadedSessionId(sessionId)
    } catch (err: any) {
      if (err.response?.status === 404) setSessionNotFound(true)
      else setError(err.message || 'Failed to load messages')
    } finally {
      setIsLoading(false)
    }
  }, [sessionId])

  // Load history when the session changes (abort any stream of the previous one)
  useEffect(() => {
    controllerRef.current?.abort()
    setMessages([])
    setLoadedSessionId(null)
    setPrompt(null)
    setSessionNotFound(false)
    if (sessionId) reload()
  }, [sessionId, reload])

  // Persist traces whenever messages change
  useEffect(() => {
    if (sessionId && messages.some((m) => m.trace)) saveTraces(sessionId, messages)
  }, [sessionId, messages])

  const createSession = useCallback(async (agentId?: string): Promise<string | null> => {
    setError(null)
    try {
      const session = await orchestratorApi.createSession(agentId, locale)
      return session.session_id
    } catch (err: any) {
      setError(err.message || 'Failed to create session')
      return null
    }
  }, [locale])

  const stop = useCallback(() => {
    controllerRef.current?.abort()
  }, [])

  const sendMessage = useCallback(async (text: string): Promise<ChatMessage | null> => {
    if (!sessionId || !text.trim()) return null
    const now = Date.now()
    const userMsg: ChatMessage = { id: `user-${now}`, role: 'user', content: text, created_at: new Date().toISOString() }
    const assistantId = `stream-${now}`
    const assistantMsg: ChatMessage = {
      id: assistantId, role: 'assistant', content: '', streaming: true,
      created_at: new Date().toISOString(), trace: { startedAt: now, steps: [] },
    }
    setMessages((prev) => [...prev, userMsg, assistantMsg])
    setIsSending(true)
    setError(null)

    const controller = new AbortController()
    controllerRef.current = controller
    let finalMsg: ChatMessage | null = null

    const update = (fn: (m: ChatMessage) => ChatMessage) =>
      setMessages((prev) => prev.map((m) => {
        if (m.id !== assistantId) return m
        const next = fn(m)
        finalMsg = next
        return next
      }))

    try {
      await orchestratorApi.streamMessage(sessionId, text, (event) => update((m) => applyEvent(m, event)), controller.signal)
    } catch (err: any) {
      update((m) => ({ ...m, streaming: false, error: err.message || 'Stream failed' }))
      setError(err.message || 'Stream failed')
    } finally {
      update((m) => (m.streaming
        ? { ...m, streaming: false, stopped: controller.signal.aborted, trace: m.trace && { ...m.trace, finishedAt: Date.now() - m.trace.startedAt } }
        : m))
      if (controllerRef.current === controller) controllerRef.current = null
      setIsSending(false)
    }
    return finalMsg
  }, [sessionId])

  const loadPrompt = useCallback(async () => {
    if (!sessionId) return
    setIsPromptLoading(true)
    try {
      const result = await orchestratorApi.getSessionPrompt(sessionId)
      setPrompt(result.prompt)
      setIsPromptCustom(result.is_custom)
    } catch (err: any) {
      setError(err.message || 'Failed to load prompt')
    } finally {
      setIsPromptLoading(false)
    }
  }, [sessionId])

  const savePrompt = useCallback(async (value: string) => {
    if (!sessionId) return false
    try {
      const result = await orchestratorApi.setSessionPrompt(sessionId, value)
      setPrompt(result.prompt)
      setIsPromptCustom(result.is_custom)
      return true
    } catch (err: any) {
      setError(err.message || 'Failed to save prompt')
      return false
    }
  }, [sessionId])

  const resetPrompt = useCallback(async () => {
    if (!sessionId) return false
    try {
      const result = await orchestratorApi.resetSessionPrompt(sessionId)
      setPrompt(result.prompt)
      setIsPromptCustom(result.is_custom)
      return true
    } catch (err: any) {
      setError(err.message || 'Failed to reset prompt')
      return false
    }
  }, [sessionId])

  return {
    messages, isLoading, isSending, error, sessionNotFound, loadedSessionId,
    createSession, sendMessage, stop, reload,
    prompt, isPromptCustom, isPromptLoading, loadPrompt, savePrompt, resetPrompt,
  }
}
