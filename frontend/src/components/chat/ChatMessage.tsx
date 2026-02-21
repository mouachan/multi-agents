import Markdown from 'react-markdown'
import type { ChatMessage as ChatMessageType, SuggestedAction } from '../../types/chat'
import { useTranslation } from '../../i18n/LanguageContext'
import ToolCallSteps from './ToolCallSteps'

interface ChatMessageProps {
  message: ChatMessageType
  onActionClick?: (action: SuggestedAction) => void
}

/** Shared color config for agent avatars and accents */
const AGENT_STYLES: Record<string, { bg: string; label: string; accent: string; lightBg: string; border: string }> = {
  orchestrator: { bg: 'bg-blue-600', label: 'HUB', accent: 'text-blue-700', lightBg: 'bg-blue-50', border: 'border-blue-200' },
  claims:       { bg: 'bg-emerald-500', label: 'SI', accent: 'text-emerald-700', lightBg: 'bg-emerald-50', border: 'border-emerald-200' },
  tenders:      { bg: 'bg-amber-500', label: 'AO', accent: 'text-amber-700', lightBg: 'bg-amber-50', border: 'border-amber-200' },
}

function getAgentStyle(agentId?: string) {
  return AGENT_STYLES[agentId || 'orchestrator'] || AGENT_STYLES.orchestrator
}

function AgentAvatar({ agentId }: { agentId?: string }) {
  const s = getAgentStyle(agentId)
  return (
    <div className={`w-8 h-8 rounded-lg ${s.bg} flex items-center justify-center flex-shrink-0`}>
      <span className="text-white text-xs font-bold">{s.label}</span>
    </div>
  )
}

function formatDuration(ms: number): string {
  const seconds = Math.round(ms / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (minutes < 60) return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`
}

export default function ChatMessage({ message, onActionClick }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'
  const { t } = useTranslation()

  const agentDisplayName = (agentId?: string): string => {
    if (!agentId) return t('agentNames.orchestrator')
    return t(`agentNames.${agentId}`) || agentId
  }

  if (isSystem) {
    return (
      <div className="flex justify-center my-3">
        <div className="bg-gray-100 text-gray-500 text-xs px-4 py-1.5 rounded-full">
          {message.content}
        </div>
      </div>
    )
  }

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="flex items-end gap-2 max-w-[70%]">
          <div className="bg-blue-600 text-white rounded-2xl rounded-br-md px-4 py-2.5 shadow-sm">
            <div className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</div>
            {message.created_at && (
              <div className="text-[10px] text-blue-200 mt-1 text-right">
                {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            )}
          </div>
          <div className="w-8 h-8 rounded-lg bg-gray-300 flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
            </svg>
          </div>
        </div>
      </div>
    )
  }

  // Assistant message
  const style = getAgentStyle(message.agent_id)
  const toolCalls = message.tool_calls || []

  return (
    <div className="flex justify-start mb-4">
      <div className="flex items-start gap-2 max-w-[75%]">
        <AgentAvatar agentId={message.agent_id} />
        <div>
          {/* Agent name */}
          <div className="text-xs font-medium text-gray-500 mb-1 ml-1">
            {agentDisplayName(message.agent_id)}
          </div>

          {/* Tool calls */}
          {toolCalls.length > 0 && (
            <ToolCallSteps toolCalls={toolCalls} />
          )}

          <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-md px-4 py-2.5 shadow-sm">
            <div className="text-sm text-gray-800 leading-relaxed prose prose-sm max-w-none prose-a:text-blue-600 prose-a:underline">
              <Markdown
                components={{
                  a: ({ href, children }) => (
                    <a href={href} target="_blank" rel="noopener noreferrer">
                      {children}
                    </a>
                  ),
                }}
              >
                {message.content}
              </Markdown>
            </div>

            <div className="flex items-center gap-3 mt-2 pt-1.5 border-t border-gray-100">
              {message.created_at && (
                <span className="text-[11px] text-gray-400">
                  {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
              {message.processing_time_ms && message.processing_time_ms > 0 && (
                <span
                  className="text-[11px] font-semibold text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded"
                  title={`${message.processing_time_ms.toLocaleString()} ms`}
                >
                  {formatDuration(message.processing_time_ms)}
                </span>
              )}
              {message.token_usage && message.token_usage.total_tokens > 0 && (
                <span
                  className="text-[11px] font-semibold text-purple-600 bg-purple-50 px-1.5 py-0.5 rounded"
                  title={`${t('tokens.prompt')}: ${message.token_usage.prompt_tokens} | ${t('tokens.completion')}: ${message.token_usage.completion_tokens}`}
                >
                  {message.token_usage.total_tokens.toLocaleString()} {t('tokens.usage')}
                </span>
              )}
              {message.model_id && (
                <span className="text-[11px] font-semibold text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
                  {message.model_id}
                </span>
              )}
            </div>
          </div>

          {/* Suggested actions */}
          {message.suggested_actions && message.suggested_actions.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5 ml-1">
              {message.suggested_actions.map((action, idx) => (
                <button
                  key={idx}
                  onClick={() => onActionClick?.(action)}
                  className={`text-xs ${style.lightBg} ${style.accent} border ${style.border} rounded-lg px-3 py-1.5 hover:opacity-80 transition-colors`}
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
