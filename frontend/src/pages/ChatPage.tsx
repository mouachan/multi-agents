import { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import AgentGraph from '../components/chat/AgentGraph'
import ChatWindow from '../components/chat/ChatWindow'
import { useAgents } from '../hooks/useAgents'
import { useChat } from '../hooks/useChat'
import { orchestratorApi } from '../services/orchestratorService'
import { useTranslation } from '../i18n/LanguageContext'
import type { AgentInfo, ChatSession, SuggestedAction } from '../types/chat'

export default function ChatPage() {
  const { sessionId } = useParams<{ sessionId?: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const agentIdParam = searchParams.get('agent')
  const { t } = useTranslation()

  const { agents } = useAgents()
  const {
    session,
    messages,
    isLoading,
    isSending,
    error,
    sessionNotFound,
    createSession,
    sendMessage,
  } = useChat(sessionId)

  const [currentAgent, setCurrentAgent] = useState<AgentInfo | null>(null)
  const [activatedAgentIds, setActivatedAgentIds] = useState<Set<string>>(new Set())
  const [sessionList, setSessionList] = useState<ChatSession[]>([])

  // Load session list
  useEffect(() => {
    orchestratorApi.listSessions().then((data) => {
      setSessionList(data.sessions)
    }).catch(() => {})
  }, [session])

  // Redirect if session not found (deleted or invalid)
  useEffect(() => {
    if (sessionNotFound && sessionId) {
      navigate('/chat', { replace: true })
    }
  }, [sessionNotFound, sessionId, navigate])

  // Create session on mount if no session ID in URL
  useEffect(() => {
    if (!sessionId && !session && !sessionNotFound) {
      createSession(agentIdParam || undefined)
    }
  }, [sessionId, session, sessionNotFound, agentIdParam, createSession])

  // Update URL when session is created
  useEffect(() => {
    if (session && !sessionId) {
      navigate(`/chat/${session.session_id}`, { replace: true })
    }
  }, [session, sessionId, navigate])

  // Track current agent and activate in graph progressively
  useEffect(() => {
    const agentId = session?.agent_id || agentIdParam
    if (agentId && agents.length > 0) {
      const agent = agents.find((a) => a.id === agentId)
      if (agent) {
        setCurrentAgent(agent)
        setActivatedAgentIds((prev) => new Set(prev).add(agentId))
      }
    }
  }, [session, agentIdParam, agents])

  const handleSendMessage = async (message: string) => {
    const response = await sendMessage(message)
    if (response?.agent_id) {
      const agent = agents.find((a) => a.id === response.agent_id)
      if (agent) {
        setCurrentAgent(agent)
        // Activate agent in graph with a slight delay for visual effect
        setTimeout(() => {
          setActivatedAgentIds((prev) => new Set(prev).add(response.agent_id!))
        }, 300)
      }
    }
  }

  const handleActionClick = (action: SuggestedAction) => {
    if (action.action === 'navigate' && action.params?.path) {
      navigate(action.params.path)
    } else {
      handleSendMessage(action.label)
    }
  }

  const handleAgentClick = (agent: AgentInfo) => {
    navigate(`/chat?agent=${agent.id}`)
    createSession(agent.id)
  }

  const handleSessionClick = (s: ChatSession) => {
    navigate(`/chat/${s.session_id}`)
  }

  const handleDeleteSession = async (e: React.MouseEvent, s: ChatSession) => {
    e.stopPropagation()
    if (!confirm(t('chat.confirmDelete'))) return
    try {
      await orchestratorApi.deleteSession(s.session_id)
      setSessionList((prev) => prev.filter((sess) => sess.session_id !== s.session_id))
      if (session?.session_id === s.session_id) {
        window.location.href = '/chat'
      }
    } catch (err) {
      console.error('Error deleting session:', err)
    }
  }

  const handleDeleteAllSessions = async () => {
    if (!confirm(t('chat.confirmDeleteAll'))) return
    try {
      await orchestratorApi.deleteAllSessions()
      // Hard redirect to get a clean state
      window.location.href = '/chat'
    } catch (err) {
      console.error('Error deleting all sessions:', err)
    }
  }

  const handleNewSession = () => {
    setCurrentAgent(null)
    setActivatedAgentIds(new Set())
    // Navigate to /chat without session ID - useEffect will create one
    window.location.href = '/chat'
  }

  const getAgentLabel = (agentId: string | undefined) => {
    if (!agentId) return t('chat.orchestrator')
    return t(`agentNames.${agentId}`) || agentId
  }

  if (isLoading && !session) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    )
  }

  return (
    <div className="flex h-full gap-3">
      {/* Left sidebar - Agent graph + sessions */}
      <div className="w-72 flex-shrink-0 flex flex-col gap-3 overflow-hidden">
        {/* Interactive agent graph */}
        <AgentGraph
          agents={agents}
          activeAgentId={currentAgent?.id}
          activatedAgentIds={activatedAgentIds}
          onAgentClick={handleAgentClick}
        />

        {/* Active agent detail */}
        {currentAgent ? (
          <div className="bg-white shadow rounded-lg p-3 border border-gray-200">
            <div className="flex items-center gap-2.5 mb-1.5">
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center text-white text-xs font-bold ${
                  currentAgent.color === 'amber' ? 'bg-amber-500' : 'bg-blue-500'
                }`}
              >
                {currentAgent.id === 'claims' ? 'SI' : 'AO'}
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-900">{currentAgent.name}</p>
                <p className="text-xs text-gray-400">{currentAgent.tools.length} {t('chat.mcpTools')}</p>
              </div>
            </div>
            <p className="text-xs text-gray-500 leading-relaxed">{currentAgent.description}</p>
          </div>
        ) : (
          <div className="bg-white shadow rounded-lg p-3 border border-gray-200">
            <p className="text-sm font-medium text-gray-700">{t('chat.orchestrator')}</p>
            <p className="text-xs text-gray-500 mt-1">
              {t('chat.orchestratorDesc')}
            </p>
          </div>
        )}

        {/* Sessions list */}
        <div className="bg-white shadow rounded-lg border border-gray-200 flex-1 overflow-hidden flex flex-col">
          <div className="px-3 py-2.5 border-b border-gray-100 flex items-center justify-between">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('chat.sessions')}</h3>
            <div className="flex items-center gap-2">
              {sessionList.length > 0 && (
                <button
                  onClick={handleDeleteAllSessions}
                  className="text-xs text-red-500 hover:text-red-700 font-medium"
                  title={t('chat.deleteAll')}
                >
                  {t('chat.deleteAll')}
                </button>
              )}
              <button
                onClick={handleNewSession}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium"
              >
                {t('chat.newSessionShort')}
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            {sessionList.length === 0 ? (
              <div className="p-3 text-xs text-gray-400 text-center">{t('chat.noSessions')}</div>
            ) : (
              sessionList.map((s) => (
                <div
                  key={s.session_id}
                  onClick={() => handleSessionClick(s)}
                  className={`w-full text-left px-3 py-2.5 border-b border-gray-50 hover:bg-gray-50 transition-colors cursor-pointer flex items-center justify-between group ${
                    session?.session_id === s.session_id ? 'bg-blue-50 border-l-2 border-l-blue-500' : ''
                  }`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                        s.status === 'active' ? 'bg-green-400' : 'bg-gray-300'
                      }`} />
                      <span className="text-xs font-medium text-gray-700 truncate">
                        {getAgentLabel(s.agent_id)}
                      </span>
                    </div>
                    {s.last_message && (
                      <p className="text-[11px] text-gray-400 mt-0.5 truncate ml-4">
                        {s.last_message}
                      </p>
                    )}
                  </div>
                  <button
                    onClick={(e) => handleDeleteSession(e, s)}
                    className="text-gray-300 hover:text-red-500 transition-colors ml-1 flex-shrink-0 p-1"
                    title={t('chat.deleteSession')}
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 bg-white shadow rounded-lg overflow-hidden flex flex-col border border-gray-200">
        {/* Chat header */}
        <div className="border-b border-gray-200 px-4 py-3 flex items-center justify-between bg-white">
          <div className="flex items-center gap-3">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold ${
              currentAgent
                ? currentAgent.color === 'amber' ? 'bg-amber-500' : 'bg-blue-500'
                : 'bg-blue-600'
            }`}>
              {currentAgent
                ? currentAgent.id === 'claims' ? 'SI' : 'AO'
                : 'HUB'}
            </div>
            <div>
              <h2 className="font-semibold text-gray-900 text-sm">
                {currentAgent ? currentAgent.name : t('chat.orchestratorMulti')}
              </h2>
              {session && (
                <p className="text-xs text-gray-400">{t('chat.session')}: {session.session_id}</p>
              )}
            </div>
          </div>
          <button
            onClick={handleNewSession}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            {t('chat.newSession')}
          </button>
        </div>

        {/* Error display */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-3 mx-4 mt-2 rounded-r">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Chat window */}
        <div className="flex-1 overflow-hidden">
          <ChatWindow
            messages={messages}
            isSending={isSending}
            onSendMessage={handleSendMessage}
            onActionClick={handleActionClick}
            placeholder={
              currentAgent
                ? `${t('chat.messageFor')} ${currentAgent.name}...`
                : t('chat.whatToDo')
            }
          />
        </div>
      </div>
    </div>
  )
}
