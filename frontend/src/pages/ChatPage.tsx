import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Code2, MessageSquarePlus, PanelLeft, PanelRight, Sparkles } from 'lucide-react'
import { TracePanel } from '../components/chat/TracePanel'
import { AgentAvatar } from '../components/chat/AgentAvatar'
import { AgentGraph } from '../components/chat/AgentGraph'
import { Composer } from '../components/chat/Composer'
import { MessageBubble } from '../components/chat/MessageBubble'
import { PromptEditor } from '../components/chat/PromptEditor'
import { SessionList } from '../components/chat/SessionList'
import { Button, IconButton } from '../components/ui/Button'
import { ErrorBanner, Spinner } from '../components/ui/Feedback'
import { useAuth, type Domain } from '../auth/AuthContext'
import { useAgents } from '../hooks/useAgents'
import { useChat } from '../hooks/useChat'
import { useTranslation } from '../i18n/LanguageContext'
import { agentVisual, toolServer } from '../lib/agents'
import { cn } from '../lib/cn'
import { chatApi } from '../services/api'
import { usePlatform } from '../theme/PlatformContext'
import type { ChatMessage, ChatSession, SuggestedAction } from '../types/chat'

const LAST_SESSION_KEY = 'chat-last-session-id'

const WELCOME_PATTERNS = [
  /^Welcome! I'm the multi-agent orchestrator/,
  /^Bienvenue ! Je suis l'orchestrateur multi-agents/,
  /^Session started with agent \*\*(.+?)\*\*/,
  /^Session demarree avec l'agent \*\*(.+?)\*\*/,
]

const EXAMPLES: { agent: string; key: string }[] = [
  { agent: 'claims', key: 'conv.ex_claims' },
  { agent: 'claims', key: 'conv.ex_payout' },
  { agent: 'tenders', key: 'conv.ex_tenders' },
  { agent: 'courrier_suivi', key: 'conv.ex_tracking' },
  { agent: 'courrier_info', key: 'conv.ex_info' },
]

function usePersistedFlag(key: string, initial: boolean): [boolean, (v: boolean) => void] {
  const [value, setValue] = useState(() => {
    const stored = localStorage.getItem(key)
    return stored === null ? initial : stored === 'true'
  })
  const set = useCallback((v: boolean) => {
    setValue(v)
    localStorage.setItem(key, String(v))
  }, [key])
  return [value, set]
}

export default function ChatPage() {
  const { sessionId } = useParams<{ sessionId?: string }>()
  const [searchParams] = useSearchParams()
  const agentParam = searchParams.get('agent')
  const navigate = useNavigate()
  const location = useLocation()
  const promptFromHome = (location.state as { prompt?: string } | null)?.prompt
  const { t, locale } = useTranslation()
  const { setModelId } = usePlatform()
  const { can } = useAuth()
  const { agents } = useAgents()
  const chat = useChat(sessionId)
  const { messages, isSending } = chat

  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [selectedTurn, setSelectedTurn] = useState<string | null>(null)
  const [promptOpen, setPromptOpen] = useState(false)
  const [leftTab, setLeftTab] = useState<'sessions' | 'agents'>(() => (localStorage.getItem('chat-left-tab') as 'agents') || 'sessions')
  const [showLeft, setShowLeft] = usePersistedFlag('chat-left-open', true)
  const [showPanel, setShowPanel] = usePersistedFlag('chat-a2a-open', true)
  const bootRef = useRef(false)
  const sentPromptRef = useRef<string | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  const refreshSessions = useCallback(() => {
    chatApi.listSessions().then(setSessions).catch(() => {})
  }, [])

  useEffect(() => { refreshSessions() }, [sessionId, refreshSessions])

  // No session in the URL: restore the last one, or create one (optionally for ?agent=)
  useEffect(() => {
    if (sessionId) {
      bootRef.current = false
      localStorage.setItem(LAST_SESSION_KEY, sessionId)
      return
    }
    if (bootRef.current) return
    bootRef.current = true
    const last = localStorage.getItem(LAST_SESSION_KEY)
    if (!agentParam && !promptFromHome && last) {
      navigate(`/chat/${last}`, { replace: true })
      return
    }
    chat.createSession(agentParam || undefined).then((id) => id && navigate(`/chat/${id}`, {
      replace: true, state: promptFromHome ? { prompt: promptFromHome } : null,
    }))
  }, [sessionId, agentParam, navigate, chat.createSession]) // eslint-disable-line react-hooks/exhaustive-deps

  // A question typed on the dashboard: send it once the new session is loaded
  useEffect(() => {
    if (!sessionId || !promptFromHome || chat.loadedSessionId !== sessionId || sentPromptRef.current === sessionId) return
    sentPromptRef.current = sessionId
    navigate(location.pathname, { replace: true, state: null })
    send(promptFromHome)
  }, [sessionId, promptFromHome, chat.loadedSessionId]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (chat.sessionNotFound) {
      localStorage.removeItem(LAST_SESSION_KEY)
      navigate('/chat', { replace: true })
    }
  }, [chat.sessionNotFound, navigate])

  // Keep the conversation scrolled to the bottom while streaming
  const lastContentLength = messages.length ? messages[messages.length - 1].content.length : 0
  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: isSending ? 'auto' : 'smooth' })
  }, [messages.length, lastContentLength, isSending])

  // Model shown in the top bar
  useEffect(() => {
    const last = [...messages].reverse().find((m) => m.role === 'assistant' && m.model_id)
    if (last?.model_id) setModelId(last.model_id)
  }, [messages, setModelId])

  // Welcome message localized from its known patterns
  const displayed = useMemo<ChatMessage[]>(() => {
    if (!messages.length || messages[0].role !== 'assistant') return messages
    const first = messages[0]
    if (!WELCOME_PATTERNS.some((p) => p.test(first.content))) return messages
    const agentName = first.content.match(/\*\*(.+?)\*\*/)?.[1]
    const agent = agentName && agents.find((a) => a.name === agentName || a.name_fr === agentName)
    const content = agentName
      ? t('welcome.agent').replace('{agent}', agent ? t(`agentNames.${agent.id}`) : agentName)
      : t('welcome.orchestrator')
    return [{ ...first, content }, ...messages.slice(1)]
  }, [messages, agents, t])

  const currentSession = sessions.find((s) => s.session_id === sessionId)
  const lastAssistant = [...messages].reverse().find((m) => m.role === 'assistant' && m.agent_id)
  const currentAgentId = lastAssistant?.agent_id || currentSession?.agent_id || agentParam || undefined
  const currentAgent = agents.find((a) => a.id === currentAgentId)
  const hasConversation = messages.some((m) => m.role === 'user')

  const traced = messages.filter((m) => m.role === 'assistant' && m.trace)
  const selectedMsg = traced.find((m) => m.id === selectedTurn) ?? traced[traced.length - 1] ?? null
  const liveMsg = messages.find((m) => m.streaming) ?? selectedMsg

  const { activeServers, usedServers } = useMemo(() => {
    const active = new Set<string>()
    const used = new Set<string>()
    for (const s of liveMsg?.trace?.steps ?? []) {
      if (s.kind !== 'tool') continue
      const server = toolServer(s.name, s.server)
      if (s.status === 'running') active.add(server)
      else used.add(server)
    }
    return { activeServers: active, usedServers: used }
  }, [liveMsg])

  const newChat = async (agentId?: string) => {
    const id = await chat.createSession(agentId)
    if (id) navigate(`/chat/${id}`)
  }

  const send = async (text: string) => {
    setSelectedTurn(null)
    await chat.sendMessage(text)
    refreshSessions()
  }

  const onAction = (action: SuggestedAction) => {
    if (action.action === 'navigate' && action.params?.path) navigate(action.params.path)
    else send(action.label)
  }

  const deleteSession = async (id: string) => {
    await chatApi.deleteSession(id).catch(() => {})
    setSessions((prev) => prev.filter((s) => s.session_id !== id))
    if (id === sessionId) {
      localStorage.removeItem(LAST_SESSION_KEY)
      await newChat()
    }
  }

  const deleteAll = async () => {
    await chatApi.deleteAllSessions().catch(() => {})
    setSessions([])
    localStorage.removeItem(LAST_SESSION_KEY)
    await newChat()
  }

  const openPrompt = () => {
    setPromptOpen(true)
    if (chat.prompt === null) chat.loadPrompt()
  }

  const v = agentVisual(currentAgentId)

  return (
    <div className="flex h-full gap-3 p-3">
      {/* Left: sessions / agents */}
      {showLeft && (
        <aside className="card hidden w-72 shrink-0 flex-col overflow-hidden lg:flex">
          <div className="flex gap-1 border-b border-line p-1.5">
            {(['sessions', 'agents'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => { setLeftTab(tab); localStorage.setItem('chat-left-tab', tab) }}
                className={cn(
                  'flex-1 rounded-lg px-2 py-1.5 text-xs font-medium transition-colors',
                  leftTab === tab ? 'bg-surface-muted text-ink shadow-sm' : 'text-ink-subtle hover:text-ink',
                )}
              >
                {t(`conv.tab_${tab}`)}
              </button>
            ))}
          </div>
          {leftTab === 'sessions' ? (
            <SessionList
              sessions={sessions}
              currentId={sessionId}
              onSelect={(id) => navigate(`/chat/${id}`)}
              onNew={() => newChat()}
              onDelete={deleteSession}
              onDeleteAll={deleteAll}
            />
          ) : (
            <div className="flex-1 overflow-y-auto p-3">
              <p className="mb-3 text-xs text-ink-muted">{t('graph.help')}</p>
              <AgentGraph activeAgentId={liveMsg?.trace?.agentId || currentAgentId}
                live={isSending}
                routing={isSending && !liveMsg?.trace?.routing}
                activeServers={activeServers}
                usedServers={usedServers}
                onAgentClick={(id) => newChat(id)}
              />
            </div>
          )}
        </aside>
      )}

      {/* Conversation */}
      <section className="card flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex items-center justify-between gap-3 border-b border-line px-4 py-2.5">
          <div className="flex min-w-0 items-center gap-2.5">
            <IconButton label={t('conv.toggleSessions')} icon={<PanelLeft className="h-4 w-4" />} onClick={() => setShowLeft(!showLeft)} className="hidden lg:inline-flex" />
            <AgentAvatar agentId={currentAgentId} />
            <div className="min-w-0">
              <h2 className={cn('truncate text-sm font-semibold', currentAgent ? v.accent.text : 'text-ink')}>
                {t(`agentNames.${currentAgentId || 'orchestrator'}`)}
              </h2>
              <p className="truncate text-[11px] text-ink-subtle">
                {currentAgent
                  ? (locale === 'fr' && currentAgent.description_fr ? currentAgent.description_fr : currentAgent.description)
                  : t('chat.orchestratorDesc')}
              </p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-1">
            <IconButton label={t('prompt.systemPrompt')} icon={<Code2 className="h-4 w-4" />} onClick={openPrompt} disabled={!sessionId} />
            <IconButton
              label={showPanel ? t('a2a.hide') : t('a2a.show')}
              icon={<PanelRight className="h-4 w-4" />}
              onClick={() => setShowPanel(!showPanel)}
              className={cn('hidden lg:inline-flex', showPanel && 'bg-surface-muted text-ink')}
            />
            <Button size="sm" icon={<MessageSquarePlus className="h-4 w-4" />} onClick={() => newChat()}>
              <span className="hidden sm:inline">{t('conv.newChat')}</span>
            </Button>
          </div>
        </header>

        {chat.error && (
          <div className="px-4 pt-3"><ErrorBanner>{chat.error}</ErrorBanner></div>
        )}

        <div ref={scrollRef} className="flex-1 overflow-y-auto">
          {chat.isLoading && !messages.length ? (
            <div className="flex h-full items-center justify-center"><Spinner className="h-7 w-7" /></div>
          ) : (
            <div className="mx-auto max-w-3xl space-y-5 px-4 py-6">
              {displayed.map((m) => (
                <MessageBubble
                  key={m.id}
                  message={m}
                  selected={showPanel && selectedMsg?.id === m.id && traced.length > 1}
                  onSelectTrace={(id) => { setSelectedTurn(id); setShowPanel(true) }}
                  onActionClick={onAction}
                />
              ))}

              {!hasConversation && !chat.isLoading && (
                <div className="animate-fade-in pt-4">
                  <div className="mb-4 flex items-center gap-2 text-xs font-medium text-ink-subtle">
                    <Sparkles className="h-3.5 w-3.5 text-brand-500" /> {t('conv.examples')}
                  </div>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {EXAMPLES.filter((ex) => can(agentVisual(ex.agent).domain as Domain)).map((ex) => (
                      <button
                        key={ex.key}
                        onClick={() => send(t(ex.key))}
                        disabled={!sessionId || isSending}
                        className="card group flex items-start gap-3 p-3 text-left transition-all hover:-translate-y-0.5 hover:shadow-elevated disabled:opacity-50"
                      >
                        <AgentAvatar agentId={ex.agent} size="sm" />
                        <div className="min-w-0">
                          <p className="text-[11px] font-medium text-ink-subtle">{t(`agentNames.${ex.agent}`)}</p>
                          <p className="text-sm text-ink">{t(ex.key)}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <Composer
          onSend={send}
          onStop={chat.stop}
          sending={isSending}
          disabled={!sessionId || chat.loadedSessionId !== sessionId}
          placeholder={currentAgent ? `${t('chat.messageFor')} ${t(`agentNames.${currentAgent.id}`)}…` : t('chat.whatToDo')}
        />
      </section>

      {/* Right: live A2A communication */}
      {showPanel && (
        <aside className="card hidden w-[380px] shrink-0 overflow-hidden lg:block">
          <TracePanel message={selectedMsg} onClose={() => setShowPanel(false)} />
        </aside>
      )}

      <PromptEditor
        open={promptOpen}
        onClose={() => setPromptOpen(false)}
        prompt={chat.prompt}
        isCustom={chat.isPromptCustom}
        loading={chat.isPromptLoading}
        onSave={chat.savePrompt}
        onReset={chat.resetPrompt}
      />
    </div>
  )
}
